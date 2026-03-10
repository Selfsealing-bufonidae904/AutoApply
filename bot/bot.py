"""Main bot loop — search, filter, generate documents, apply, repeat."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from bot.apply.base import ApplyResult
from bot.apply.ashby import AshbyApplier
from bot.apply.greenhouse import GreenhouseApplier
from bot.apply.indeed import IndeedApplier
from bot.apply.lever import LeverApplier
from bot.apply.linkedin import LinkedInApplier
from bot.apply.workday import WorkdayApplier
from bot.browser import BrowserManager
from bot.search.indeed import IndeedSearcher
from bot.search.linkedin import LinkedInSearcher
from core.filter import ScoredJob, detect_ats, score_job

if TYPE_CHECKING:
    from config.settings import AppConfig
    from db.database import Database
    from bot.state import BotState

logger = logging.getLogger(__name__)

SEARCHERS = {
    "linkedin": LinkedInSearcher,
    "indeed": IndeedSearcher,
}

APPLIERS = {
    "linkedin": LinkedInApplier,
    "indeed": IndeedApplier,
    "greenhouse": GreenhouseApplier,
    "lever": LeverApplier,
    "workday": WorkdayApplier,
    "ashby": AshbyApplier,
}


def run_bot(
    state: "BotState",
    config: "AppConfig",
    db: "Database",
    emit_func=None,
) -> None:
    """Main bot loop.

    Iterates: search → filter → generate docs → apply → save to DB.
    Respects stop_flag, pause state, and daily application limits.

    Args:
        state: Thread-safe bot state (status, counters, stop flag).
        config: Application configuration.
        db: Database for saving applications and dedup checks.
        emit_func: Callable to emit SocketIO events. Signature:
                   ``emit_func(event_name, data_dict)``.
    """
    profile_dir = Path.home() / ".autoapply" / "profile"
    browser = None

    def emit(event_type: str, **kwargs):
        """Emit a feed event via SocketIO and save to DB."""
        data = {"type": event_type, **kwargs}
        if emit_func:
            try:
                emit_func("feed_event", data)
            except Exception:
                pass
        try:
            db.save_feed_event(
                event_type=event_type,
                job_title=kwargs.get("job_title"),
                company=kwargs.get("company"),
                platform=kwargs.get("platform"),
                message=kwargs.get("message"),
            )
        except Exception:
            pass

    try:
        browser = BrowserManager(config)
        page = browser.get_page()

        enabled_searchers = [
            SEARCHERS[p]()
            for p in config.bot.enabled_platforms
            if p in SEARCHERS
        ]

        if not enabled_searchers:
            logger.warning("No enabled search platforms configured")
            return

        while not state.stop_flag:
            _wait_while_paused(state)
            if state.stop_flag:
                break

            for searcher in enabled_searchers:
                if state.stop_flag:
                    break

                try:
                    for raw_job in searcher.search(config.search_criteria, page=page):
                        if state.stop_flag:
                            break

                        _wait_while_paused(state)
                        if state.stop_flag:
                            break

                        state.increment_found()
                        emit(
                            "FOUND",
                            job_title=raw_job.title,
                            company=raw_job.company,
                            platform=raw_job.platform,
                            message=f"Found: {raw_job.title} at {raw_job.company}",
                        )

                        # Check daily limit
                        if state.applied_today >= config.bot.max_applications_per_day:
                            logger.info(
                                "Daily limit reached (%d). Waiting for next cycle.",
                                config.bot.max_applications_per_day,
                            )
                            break

                        # Score and filter
                        scored = score_job(raw_job, config, db)
                        if not scored.pass_filter:
                            emit(
                                "FILTERED",
                                job_title=raw_job.title,
                                company=raw_job.company,
                                platform=raw_job.platform,
                                message=f"Filtered: {scored.skip_reason}",
                            )
                            continue

                        # Generate documents
                        emit(
                            "GENERATING",
                            job_title=raw_job.title,
                            company=raw_job.company,
                            platform=raw_job.platform,
                            message="Generating resume and cover letter via Claude Code...",
                        )

                        resume_path, cl_path, cover_letter_text = _generate_docs(
                            scored, config, profile_dir
                        )

                        # Review gate — pause for user approval in review/watch modes
                        if config.bot.apply_mode in ("review", "watch"):
                            emit(
                                "REVIEW",
                                job_title=raw_job.title,
                                company=raw_job.company,
                                platform=raw_job.platform,
                                match_score=scored.score,
                                cover_letter=cover_letter_text,
                                apply_url=raw_job.apply_url,
                                message=f"Review: {raw_job.title} at {raw_job.company} (score {scored.score})",
                            )

                            decision, edited_cl = _wait_for_review(state)
                            if decision == "stop":
                                break
                            if decision == "skip":
                                emit(
                                    "SKIPPED",
                                    job_title=raw_job.title,
                                    company=raw_job.company,
                                    platform=raw_job.platform,
                                    message=f"Skipped: {raw_job.title} at {raw_job.company}",
                                )
                                continue
                            if decision == "edit" and edited_cl:
                                cover_letter_text = edited_cl
                            if decision == "manual":
                                # User will apply themselves — save as manual_required
                                manual_result = ApplyResult(
                                    success=False,
                                    status="manual_required",
                                    message="User chose to apply manually",
                                )
                                _save_application(
                                    db, scored, resume_path, cl_path,
                                    cover_letter_text, manual_result,
                                )
                                emit(
                                    "APPLIED",
                                    job_title=raw_job.title,
                                    company=raw_job.company,
                                    platform=raw_job.platform,
                                    message=f"Marked for manual apply: {raw_job.title} at {raw_job.company}",
                                )
                                continue

                        # Apply
                        emit(
                            "APPLYING",
                            job_title=raw_job.title,
                            company=raw_job.company,
                            platform=raw_job.platform,
                            message=f"Applying via {detect_ats(raw_job.apply_url) or raw_job.platform}...",
                        )

                        result = _apply_to_job(
                            scored, resume_path, cover_letter_text, config, page
                        )

                        # Save to DB
                        _save_application(
                            db, scored, resume_path, cl_path,
                            cover_letter_text, result,
                        )

                        # Emit result
                        if result.success:
                            state.increment_applied()
                            emit(
                                "APPLIED",
                                job_title=raw_job.title,
                                company=raw_job.company,
                                platform=raw_job.platform,
                                message=f"Applied to {raw_job.title} at {raw_job.company}",
                            )
                        elif result.captcha_detected:
                            state.increment_errors()
                            emit(
                                "CAPTCHA",
                                job_title=raw_job.title,
                                company=raw_job.company,
                                platform=raw_job.platform,
                                message=f"CAPTCHA detected at {raw_job.company}",
                            )
                        else:
                            state.increment_errors()
                            emit(
                                "ERROR",
                                job_title=raw_job.title,
                                company=raw_job.company,
                                platform=raw_job.platform,
                                message=result.error_message or "Application failed",
                            )

                        # Rate limit between applications
                        if not state.stop_flag:
                            time.sleep(config.bot.delay_between_applications_seconds)

                except Exception as e:
                    logger.error("Search/apply cycle error: %s", e)
                    state.increment_errors()
                    emit(
                        "ERROR",
                        message=f"Search cycle error: {e}",
                    )

            # Wait for next search interval
            if not state.stop_flag:
                logger.info(
                    "Search cycle complete. Waiting %ds for next cycle.",
                    config.bot.search_interval_seconds,
                )
                _interruptible_sleep(state, config.bot.search_interval_seconds)

    except Exception as e:
        logger.error("Bot crashed: %s", e)
        state.increment_errors()
        emit("ERROR", message=f"Bot crashed: {e}")
    finally:
        if browser:
            browser.close()
        logger.info("Bot loop exited")


def _wait_while_paused(state: "BotState") -> None:
    """Block while bot is paused, checking every second."""
    while state.status == "paused" and not state.stop_flag:
        time.sleep(1)


def _interruptible_sleep(state: "BotState", seconds: int) -> None:
    """Sleep for `seconds` but wake up immediately if stop_flag is set."""
    for _ in range(seconds):
        if state.stop_flag:
            return
        time.sleep(1)


def _wait_for_review(state: "BotState") -> tuple[str, str | None]:
    """Block the bot thread until the user makes a review decision.

    Returns:
        (decision, edited_cover_letter) where decision is
        "approve", "skip", "edit", or "stop".
    """
    state.begin_review()
    return state.wait_for_review()


def _generate_docs(scored: ScoredJob, config, profile_dir: Path):
    """Generate resume and cover letter, with fallback on failure."""
    from core.ai_engine import generate_documents

    resume_path = None
    cl_path = None
    cover_letter_text = ""

    try:
        resume_path, cl_path = generate_documents(
            job=scored,
            profile=config.profile,
            experience_dir=profile_dir / "experiences",
            output_dir_resumes=profile_dir / "resumes",
            output_dir_cover_letters=profile_dir / "cover_letters",
        )
        cover_letter_text = cl_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Document generation failed, using fallback: %s", e)
        # Fallback to static templates
        if config.profile.fallback_resume_path:
            fallback = Path(config.profile.fallback_resume_path)
            if fallback.exists():
                resume_path = fallback
        cover_letter_text = config.bot.cover_letter_template or ""

    return resume_path, cl_path, cover_letter_text


def _apply_to_job(scored, resume_path, cover_letter_text, config, page):
    """Apply to a job using the appropriate platform applier."""
    platform = detect_ats(scored.raw.apply_url) or scored.raw.platform

    applier_cls = APPLIERS.get(platform)
    if not applier_cls:
        return ApplyResult(
            success=False, manual_required=True,
            error_message=f"No applier for platform: {platform}",
        )

    applier = applier_cls(page)
    return applier.apply(scored, resume_path, cover_letter_text, config.profile)


def _save_application(db, scored, resume_path, cl_path, cover_letter_text, result):
    """Save an application record to the database."""
    try:
        status = "applied" if result.success else (
            "manual_required" if result.manual_required else "error"
        )
        db.save_application(
            external_id=scored.raw.external_id,
            platform=scored.raw.platform,
            job_title=scored.raw.title,
            company=scored.raw.company,
            location=scored.raw.location,
            salary=scored.raw.salary,
            apply_url=scored.raw.apply_url,
            match_score=scored.score,
            resume_path=str(resume_path) if resume_path else None,
            cover_letter_path=str(cl_path) if cl_path else None,
            cover_letter_text=cover_letter_text,
            status=status,
            error_message=result.error_message,
        )
    except Exception as e:
        logger.error("Failed to save application to DB: %s", e)
