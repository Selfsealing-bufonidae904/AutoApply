from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoApply — Job Application Bot")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Skip auto-opening browser (used when launched by Electron)",
    )
    args = parser.parse_args()

    port = int(os.environ.get("AUTOAPPLY_PORT", "5000"))

    from config.settings import get_data_dir

    data_dir = get_data_dir()
    (data_dir / "profile" / "experiences").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "jobs").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "resumes").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "cover_letters").mkdir(parents=True, exist_ok=True)
    (data_dir / "browser_profile").mkdir(parents=True, exist_ok=True)
    (data_dir / "backups").mkdir(parents=True, exist_ok=True)

    readme_path = data_dir / "profile" / "experiences" / "README.txt"
    if not readme_path.exists():
        readme_path.write_text(
            "HOW TO USE THIS FOLDER\n"
            "=====================\n\n"
            "Add .txt files describing your work experience, skills, and achievements.\n"
            "Write in plain language — Claude Code will read these to generate tailored\n"
            "resumes and cover letters for each job application.\n\n"
            "Tips:\n"
            "- One file per job/role works well, but any organization is fine\n"
            "- Include specific achievements with numbers where possible\n"
            "- Mention technologies, tools, and methodologies you've used\n"
            "- Describe projects you've led or contributed to\n"
            "- Include education, certifications, and relevant training\n\n"
            "Example files:\n"
            "  senior_engineer_acme.txt\n"
            "  skills_and_tools.txt\n"
            "  education.txt\n"
            "  projects_and_achievements.txt\n",
            encoding="utf-8",
        )

    from app import app, socketio

    if not args.no_browser:
        def open_browser() -> None:
            import time
            time.sleep(1.5)
            webbrowser.open(f"http://localhost:{port}")

        threading.Thread(target=open_browser, daemon=True).start()

    print(f"AutoApply starting at http://localhost:{port}")
    socketio.run(app, host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
