from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_socketio import SocketIO, emit

from config.settings import (
    AppConfig,
    ScheduleConfig,
    get_data_dir,
    is_first_run,
    load_config,
    save_config,
)
from core.ai_engine import check_claude_code_available as _ai_check_claude
from core.scheduler import BotScheduler
from db.database import Database
from bot.state import BotState

app = Flask(__name__)
app.config["SECRET_KEY"] = "autoapply-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
db = Database(get_data_dir() / "autoapply.db")
bot_state = BotState()
_bot_thread: threading.Thread | None = None


def _get_schedule() -> ScheduleConfig | None:
    """Get current schedule config (used by scheduler)."""
    config = load_config()
    if config is None:
        return None
    return config.bot.schedule


def _scheduler_start_bot() -> None:
    """Start bot from scheduler (delegates to bot_start logic)."""
    global _bot_thread
    if _bot_thread and _bot_thread.is_alive():
        return
    config = load_config()
    if config is None:
        return
    bot_state.start()

    def _run():
        from bot.bot import run_bot

        def _emit(event_name, data):
            socketio.emit(event_name, data)
            status_dict = bot_state.get_status_dict()
            status_dict["claude_code_available"] = check_claude_code_available()
            socketio.emit("bot_status", status_dict)

        try:
            run_bot(state=bot_state, config=config, db=db, emit_func=_emit)
        finally:
            bot_state.stop()
            status_dict = bot_state.get_status_dict()
            status_dict["claude_code_available"] = check_claude_code_available()
            socketio.emit("bot_status", status_dict)

    _bot_thread = threading.Thread(target=_run, daemon=True, name="bot-worker")
    _bot_thread.start()


def _scheduler_stop_bot() -> None:
    """Stop bot from scheduler."""
    bot_state.stop()
    if _bot_thread and _bot_thread.is_alive():
        _bot_thread.join(timeout=10)


def _is_bot_running() -> bool:
    """Check if bot thread is alive."""
    return _bot_thread is not None and _bot_thread.is_alive()


bot_scheduler = BotScheduler(
    get_schedule=_get_schedule,
    start_bot=_scheduler_start_bot,
    stop_bot=_scheduler_stop_bot,
    is_bot_running=_is_bot_running,
)

SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_\- ]+\.txt$")


def check_claude_code_available() -> bool:
    """Check if Claude Code CLI is available (delegates to core.ai_engine)."""
    return _ai_check_claude()


def validate_filename(filename: str) -> str | None:
    """Returns error message if filename is invalid, None if valid."""
    if not filename:
        return "Filename is required"
    if ".." in filename or "/" in filename or "\\" in filename:
        return "Invalid filename"
    if not SAFE_FILENAME_RE.match(filename):
        return "Invalid filename. Use only letters, numbers, hyphens, underscores, spaces, and .txt extension"
    return None


@app.errorhandler(Exception)
def handle_exception(e):
    if hasattr(e, "code") and isinstance(e.code, int):
        return jsonify({"error": str(e)}), e.code
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": "Method not allowed"}), 405


# ---------------------------------------------------------------------------
# Page route
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Bot Control
# ---------------------------------------------------------------------------

@app.route("/api/bot/start", methods=["POST"])
def bot_start():
    # Prevent duplicate threads
    if _bot_thread and _bot_thread.is_alive():
        return jsonify({"error": "Bot is already running"}), 409

    config = load_config()
    if config is None:
        return jsonify({"error": "Configuration not found. Complete setup first."}), 400

    _scheduler_start_bot()
    return jsonify({"status": "running"})


@app.route("/api/bot/pause", methods=["POST"])
def bot_pause():
    bot_state.pause()
    return jsonify({"status": "paused"})


@app.route("/api/bot/stop", methods=["POST"])
def bot_stop():
    bot_state.stop()
    # Wait briefly for thread to exit
    if _bot_thread and _bot_thread.is_alive():
        _bot_thread.join(timeout=10)
    return jsonify({"status": "stopped"})


@app.route("/api/bot/status", methods=["GET"])
def bot_status():
    status_dict = bot_state.get_status_dict()
    status_dict["claude_code_available"] = check_claude_code_available()
    status_dict["schedule_enabled"] = bot_scheduler.running
    return jsonify(status_dict)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

@app.route("/api/bot/schedule", methods=["GET"])
def get_schedule():
    config = load_config()
    if config is None:
        return jsonify(ScheduleConfig().model_dump())
    return jsonify(config.bot.schedule.model_dump())


@app.route("/api/bot/schedule", methods=["PUT"])
def update_schedule():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Validate days_of_week values
    valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    if "days_of_week" in data:
        invalid = [d for d in data["days_of_week"] if d.lower() not in valid_days]
        if invalid:
            return jsonify({"error": f"Invalid days: {invalid}"}), 400

    # Validate time format
    for field in ("start_time", "end_time"):
        if field in data:
            try:
                h, m = map(int, data[field].split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
            except (ValueError, AttributeError):
                return jsonify({"error": f"Invalid {field} format. Use HH:MM (24-hour)"}), 400

    config = load_config()
    if config is None:
        return jsonify({"error": "Configuration not found. Complete setup first."}), 400

    # Merge with existing schedule
    current = config.bot.schedule.model_dump()
    current.update(data)
    config.bot.schedule = ScheduleConfig(**current)
    save_config(config)

    # Start or stop scheduler based on enabled flag
    if config.bot.schedule.enabled:
        if not bot_scheduler.running:
            bot_scheduler.start()
    else:
        if bot_scheduler.running:
            bot_scheduler.stop()

    return jsonify(config.bot.schedule.model_dump())


# ---------------------------------------------------------------------------
# Review Gate
# ---------------------------------------------------------------------------

@app.route("/api/bot/review/approve", methods=["POST"])
def review_approve():
    if not bot_state.awaiting_review:
        return jsonify({"error": "No application awaiting review"}), 409
    bot_state.set_review_decision("approve")
    return jsonify({"status": "approved"})


@app.route("/api/bot/review/skip", methods=["POST"])
def review_skip():
    if not bot_state.awaiting_review:
        return jsonify({"error": "No application awaiting review"}), 409
    bot_state.set_review_decision("skip")
    return jsonify({"status": "skipped"})


@app.route("/api/bot/review/edit", methods=["POST"])
def review_edit():
    if not bot_state.awaiting_review:
        return jsonify({"error": "No application awaiting review"}), 409
    data = request.get_json()
    if not data or "cover_letter" not in data:
        return jsonify({"error": "cover_letter is required"}), 400
    bot_state.set_review_decision("edit", edits=data["cover_letter"])
    return jsonify({"status": "edited"})


@app.route("/api/bot/review/manual", methods=["POST"])
def review_manual():
    """Mark current review as 'manual' — user will apply themselves."""
    if not bot_state.awaiting_review:
        return jsonify({"error": "No application awaiting review"}), 409
    bot_state.set_review_decision("manual")
    return jsonify({"status": "manual"})


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@app.route("/api/applications", methods=["GET"])
def get_applications():
    status = request.args.get("status")
    platform_filter = request.args.get("platform")
    search = request.args.get("search")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    applications = db.get_all_applications(
        status=status,
        platform=platform_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    return jsonify([a.model_dump() for a in applications])


@app.route("/api/applications/<int:app_id>", methods=["GET"])
def get_application_detail(app_id: int):
    application = db.get_application(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(application.model_dump())


@app.route("/api/applications/<int:app_id>/events", methods=["GET"])
def get_application_events(app_id: int):
    application = db.get_application(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    events = db.get_feed_events_for_job(application.job_title, application.company)
    return jsonify([e.model_dump() for e in events])


@app.route("/api/applications/export", methods=["GET"])
def export_applications():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.close()
    csv_path = Path(tmp.name)
    db.export_csv(csv_path)
    return send_file(
        csv_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    )


@app.route("/api/applications/<int:app_id>", methods=["PATCH"])
def update_application(app_id: int):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    application = db.get_application(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    status = data.get("status", application.status)
    notes = data.get("notes", application.notes)
    db.update_status(app_id, status=status, notes=notes)
    return jsonify({"success": True})


@app.route("/api/applications/<int:app_id>/cover_letter", methods=["GET"])
def get_cover_letter(app_id: int):
    application = db.get_application(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({
        "cover_letter_text": application.cover_letter_text,
        "file_path": application.cover_letter_path,
    })


@app.route("/api/applications/<int:app_id>/resume", methods=["GET"])
def get_resume(app_id: int):
    application = db.get_application(app_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    resume_path = application.resume_path
    if not resume_path or not Path(resume_path).exists():
        return jsonify({"error": "Resume not found"}), 404
    return send_file(resume_path, mimetype="application/pdf")


# ---------------------------------------------------------------------------
# Profile / Experience Files
# ---------------------------------------------------------------------------

@app.route("/api/profile/experiences", methods=["GET"])
def list_experiences():
    experiences_dir = get_data_dir() / "profile" / "experiences"
    experiences_dir.mkdir(parents=True, exist_ok=True)
    files: list[dict] = []
    for file_path in sorted(experiences_dir.glob("*.txt")):
        stat = file_path.stat()
        files.append({
            "name": file_path.name,
            "content": file_path.read_text(encoding="utf-8"),
            "size": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return jsonify({"files": files})


@app.route("/api/profile/experiences", methods=["POST"])
def create_experience():
    data = request.get_json()
    if not data or "filename" not in data or "content" not in data:
        return jsonify({"error": "filename and content are required"}), 400
    filename: str = data["filename"]
    content: str = data["content"]
    error = validate_filename(filename)
    if error:
        return jsonify({"error": error}), 400
    experiences_dir = get_data_dir() / "profile" / "experiences"
    experiences_dir.mkdir(parents=True, exist_ok=True)
    (experiences_dir / filename).write_text(content, encoding="utf-8")
    return jsonify({"success": True})


@app.route("/api/profile/experiences/<filename>", methods=["PUT"])
def update_experience(filename: str):
    error = validate_filename(filename)
    if error:
        return jsonify({"error": error}), 400
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "content is required"}), 400
    content: str = data["content"]
    experiences_dir = get_data_dir() / "profile" / "experiences"
    file_path = experiences_dir / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    file_path.write_text(content, encoding="utf-8")
    return jsonify({"success": True})


@app.route("/api/profile/experiences/<filename>", methods=["DELETE"])
def delete_experience(filename: str):
    error = validate_filename(filename)
    if error:
        return jsonify({"error": error}), 400
    experiences_dir = get_data_dir() / "profile" / "experiences"
    file_path = experiences_dir / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    file_path.unlink()
    return jsonify({"success": True})


@app.route("/api/profile/status", methods=["GET"])
def profile_status():
    experiences_dir = get_data_dir() / "profile" / "experiences"
    experiences_dir.mkdir(parents=True, exist_ok=True)
    txt_files = list(experiences_dir.glob("*.txt"))
    total_words = 0
    for file_path in txt_files:
        total_words += len(file_path.read_text(encoding="utf-8").split())
    return jsonify({
        "file_count": len(txt_files),
        "total_words": total_words,
        "claude_code_available": check_claude_code_available(),
    })


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@app.route("/api/config", methods=["GET"])
def get_config():
    config = load_config()
    if config is None:
        return jsonify({})
    return jsonify(config.model_dump())


@app.route("/api/config", methods=["PUT"])
def update_config():
    data = request.get_json()
    existing = load_config()
    if existing:
        merged = existing.model_dump()
        for key, value in data.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = value
        config = AppConfig(**merged)
    else:
        config = AppConfig(**data)
    save_config(config)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@app.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    return jsonify(db.get_analytics_summary())


@app.route("/api/analytics/daily", methods=["GET"])
def analytics_daily():
    days = request.args.get("days", 30, type=int)
    return jsonify(db.get_daily_analytics(days))


# ---------------------------------------------------------------------------
# Feed Events
# ---------------------------------------------------------------------------

@app.route("/api/feed", methods=["GET"])
def get_feed_events():
    limit = request.args.get("limit", 50, type=int)
    events = db.get_feed_events(limit=limit)
    return jsonify([e.model_dump() for e in events])


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

@app.route("/api/setup/status", methods=["GET"])
def setup_status():
    return jsonify({
        "is_first_run": is_first_run(),
        "claude_code_available": check_claude_code_available(),
    })


# ---------------------------------------------------------------------------
# Platform Login
# ---------------------------------------------------------------------------


def _find_system_chrome() -> str | None:
    """Find system-installed Chrome/Chromium for faster browser sessions."""
    import platform
    candidates = []
    if platform.system() == "Windows":
        for base in [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.path.expandvars(r"%LOCALAPPDATA%"),
        ]:
            candidates.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
    elif platform.system() == "Darwin":
        candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    else:
        candidates.extend(["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"])

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


_login_proc = None  # subprocess.Popen for login Chrome window
_login_lock = threading.Lock()


@app.route("/api/login/open", methods=["POST"])
def login_open():
    """Open system Chrome with a dedicated profile for platform login.

    Launches Chrome directly via subprocess — no Playwright overhead.
    The browser_profile directory preserves cookies so the bot can reuse
    the login session later.
    """
    global _login_proc
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "url is required"}), 400

    url = data["url"]
    allowed_domains = ["linkedin.com", "indeed.com"]
    if not any(domain in url for domain in allowed_domains):
        return jsonify({"error": "Only LinkedIn and Indeed URLs are supported"}), 400

    chrome_path = _find_system_chrome()
    if not chrome_path:
        return jsonify({
            "error": "Google Chrome not found. Please install Chrome.",
        }), 500

    profile_dir = str(get_data_dir() / "browser_profile")

    with _login_lock:
        # Kill existing login browser if still running
        if _login_proc is not None:
            try:
                _login_proc.terminate()
            except Exception:
                pass
            _login_proc = None

    try:
        proc = subprocess.Popen(
            [
                chrome_path,
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--new-window",
                url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with _login_lock:
            _login_proc = proc
        logging.getLogger(__name__).info(
            "Login browser opened (Chrome PID %d): %s", proc.pid, url,
        )
    except Exception as e:
        logging.getLogger(__name__).error("Failed to open login browser: %s", e)
        return jsonify({"error": f"Failed to open Chrome: {e}"}), 500

    return jsonify({"status": "opening"})


@app.route("/api/login/close", methods=["POST"])
def login_close():
    """Close the login browser."""
    global _login_proc
    with _login_lock:
        if _login_proc is None:
            return jsonify({"status": "already_closed"})
        proc = _login_proc
        _login_proc = None

    try:
        proc.terminate()
    except Exception:
        pass
    return jsonify({"status": "closed"})


@app.route("/api/login/status", methods=["GET"])
def login_status():
    """Check if a login browser is currently open."""
    global _login_proc
    with _login_lock:
        if _login_proc is None:
            return jsonify({"open": False})
        if _login_proc.poll() is not None:
            # Process exited (user closed Chrome)
            _login_proc = None
            return jsonify({"open": False})
        return jsonify({"open": True})


@app.route("/api/login/sessions", methods=["GET"])
def login_sessions():
    """Check which platforms have active login sessions.

    Reads the Chrome Cookies SQLite DB in browser_profile to detect
    session cookies for LinkedIn and Indeed.
    """
    import shutil
    import sqlite3

    profile_cookies = get_data_dir() / "browser_profile" / "Default" / "Network" / "Cookies"
    result = {"linkedin": False, "indeed": False}

    if not profile_cookies.exists():
        return jsonify(result)

    # Chrome locks the Cookies DB — copy to a temp file to read safely
    tmp_cookies = get_data_dir() / "browser_profile" / "_cookies_check.db"
    try:
        shutil.copy2(str(profile_cookies), str(tmp_cookies))
        conn = sqlite3.connect(str(tmp_cookies))
        cursor = conn.cursor()

        # LinkedIn: li_at is the main session cookie
        cursor.execute(
            "SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%linkedin.com' "
            "AND name = 'li_at'"
        )
        result["linkedin"] = cursor.fetchone()[0] > 0

        # Indeed: INDEED_CSRF_TOKEN or indeed_rcc indicate an active session
        cursor.execute(
            "SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%indeed.com' "
            "AND name IN ('INDEED_CSRF_TOKEN', 'indeed_rcc')"
        )
        result["indeed"] = cursor.fetchone()[0] > 0

        conn.close()
    except Exception as e:
        logging.getLogger(__name__).debug("Could not read cookies DB: %s", e)
    finally:
        try:
            tmp_cookies.unlink(missing_ok=True)
        except Exception:
            pass

    return jsonify(result)


# ---------------------------------------------------------------------------
# Lifecycle (used by Electron shell)
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify({"error": "Forbidden"}), 403
    pid = os.getpid()

    def _shutdown():
        import time
        time.sleep(0.5)
        os.kill(pid, signal.SIGTERM)

    import threading
    threading.Thread(target=_shutdown, daemon=True).start()
    return jsonify({"status": "shutting_down"})


# ---------------------------------------------------------------------------
# SocketIO
# ---------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    status_dict = bot_state.get_status_dict()
    status_dict["schedule_enabled"] = bot_scheduler.running
    emit("bot_status", status_dict)


# ---------------------------------------------------------------------------
# Auto-start scheduler if schedule is enabled in config
# ---------------------------------------------------------------------------

def _init_scheduler():
    """Start scheduler on app startup if schedule is enabled."""
    schedule = _get_schedule()
    if schedule and schedule.enabled:
        bot_scheduler.start()

_init_scheduler()
