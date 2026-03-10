"""Greenhouse ATS application automation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from bot.apply.base import ApplyResult, BaseApplier

if TYPE_CHECKING:
    from config.settings import UserProfile
    from core.filter import ScoredJob

logger = logging.getLogger(__name__)


class GreenhouseApplier(BaseApplier):
    """Automate Greenhouse job application submissions.

    Greenhouse application pages typically live at
    ``boards.greenhouse.io/{company}/jobs/{id}`` and present a single-page
    form with personal info fields, resume upload, cover letter textarea,
    and optional custom questions.
    """

    def apply(
        self,
        job: "ScoredJob",
        resume_pdf_path: Path | None,
        cover_letter_text: str,
        profile: "UserProfile",
    ) -> ApplyResult:
        """Submit a Greenhouse application.

        Steps:
        1. Navigate to job URL
        2. Fill personal info (name, email, phone)
        3. Upload resume
        4. Fill cover letter
        5. Submit

        Returns:
            ApplyResult with success/failure details.
        """
        try:
            return self._do_apply(job, resume_pdf_path, cover_letter_text, profile)
        except Exception as e:
            logger.error("Greenhouse apply failed for %s: %s", job.raw.company, e)
            return ApplyResult(success=False, error_message=str(e))

    def _do_apply(
        self, job, resume_pdf_path, cover_letter_text, profile
    ) -> ApplyResult:
        page = self.page

        logger.info("Greenhouse: applying to %s at %s", job.raw.title, job.raw.company)
        page.goto(job.raw.apply_url, wait_until="domcontentloaded", timeout=30000)
        self._random_pause(1, 3)

        # Check for CAPTCHA
        if self._detect_captcha():
            return ApplyResult(
                success=False, captcha_detected=True,
                error_message="CAPTCHA detected",
            )

        # Greenhouse uses an "Apply for this job" button or renders the form
        # directly.  Try clicking the apply button first.
        apply_btn = page.query_selector(
            "a#apply_button, "
            "a[href*='#app'], "
            "button[id*='apply'], "
            "a.btn[href*='apply']"
        )
        if apply_btn and apply_btn.is_visible():
            apply_btn.click()
            self._random_pause(1, 2)

        # Fill personal info
        self._fill_form_fields(profile)

        # Upload resume
        if resume_pdf_path:
            self._upload_resume(resume_pdf_path)

        # Fill cover letter
        self._fill_cover_letter(cover_letter_text)

        self._random_pause(0.5, 1)

        # Submit the form
        submit_btn = page.query_selector(
            "input[type='submit']#submit_app, "
            "input[type='submit'][value*='Submit'], "
            "button[type='submit'], "
            "input#submit_app"
        )

        if not submit_btn:
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Submit button not found on Greenhouse form",
            )

        submit_btn.click()
        self._random_pause(2, 4)

        # Check for confirmation or error after submission
        error_el = page.query_selector(
            ".field_with_errors, "
            ".error, "
            "#application_errors"
        )
        if error_el and error_el.is_visible():
            error_text = error_el.inner_text()[:200]
            return ApplyResult(
                success=False,
                error_message=f"Greenhouse form error: {error_text}",
            )

        return ApplyResult(success=True)

    def _fill_form_fields(self, profile) -> None:
        """Fill Greenhouse standard personal info fields."""
        page = self.page

        # Greenhouse uses id-based fields: first_name, last_name, email, phone
        field_map = {
            "#first_name, input[name*='first_name']": profile.first_name,
            "#last_name, input[name*='last_name']": profile.last_name,
            "#email, input[name*='email']": profile.email,
            "#phone, input[name*='phone']": profile.phone_full,
        }

        for selector, value in field_map.items():
            if not value:
                continue
            el = page.query_selector(selector)
            if el and not el.input_value():
                self._human_type(el, value)
                self._random_pause(0.3, 0.8)

        # LinkedIn profile URL (optional field, common on Greenhouse)
        if profile.linkedin_url:
            linkedin_input = page.query_selector(
                "input[name*='linkedin'], "
                "input[id*='linkedin'], "
                "input[autocomplete*='url']"
            )
            if linkedin_input and not linkedin_input.input_value():
                self._human_type(linkedin_input, profile.linkedin_url)
                self._random_pause(0.3, 0.8)

    def _upload_resume(self, resume_path: Path) -> None:
        """Upload resume via Greenhouse file input."""
        # Greenhouse wraps the file input — look for the data-field variant too
        file_input = self.page.query_selector(
            "input[type='file'][name*='resume'], "
            "input[type='file'][id*='resume'], "
            "input[type='file'][data-field*='resume'], "
            "input[type='file']"
        )
        if file_input:
            try:
                file_input.set_input_files(str(resume_path))
                self._random_pause(1, 2)
            except Exception as e:
                logger.debug("Greenhouse resume upload failed: %s", e)

    def _fill_cover_letter(self, text: str) -> None:
        """Fill cover letter textarea on Greenhouse form."""
        if not text:
            return

        textarea = self.page.query_selector(
            "textarea[name*='cover_letter'], "
            "textarea[id*='cover_letter'], "
            "textarea[name*='cover'], "
            "#cover_letter"
        )
        if textarea and not textarea.input_value():
            textarea.fill(text)
            self._random_pause(0.5, 1)
