"""Lever ATS application automation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from bot.apply.base import ApplyResult, BaseApplier

if TYPE_CHECKING:
    from config.settings import UserProfile
    from core.filter import ScoredJob

logger = logging.getLogger(__name__)


class LeverApplier(BaseApplier):
    """Automate Lever job application submissions.

    Lever application pages live at ``jobs.lever.co/{company}/{id}/apply``
    and present a single-page form with personal info, resume upload,
    cover letter textarea, and optional custom questions.
    """

    def apply(
        self,
        job: "ScoredJob",
        resume_pdf_path: Path | None,
        cover_letter_text: str,
        profile: "UserProfile",
    ) -> ApplyResult:
        """Submit a Lever application.

        Steps:
        1. Navigate to job URL (append /apply if needed)
        2. Fill personal info (name, email, phone, LinkedIn, website)
        3. Upload resume
        4. Fill cover letter
        5. Submit

        Returns:
            ApplyResult with success/failure details.
        """
        try:
            return self._do_apply(job, resume_pdf_path, cover_letter_text, profile)
        except Exception as e:
            logger.error("Lever apply failed for %s: %s", job.raw.company, e)
            return ApplyResult(success=False, error_message=str(e))

    def _do_apply(
        self, job, resume_pdf_path, cover_letter_text, profile
    ) -> ApplyResult:
        page = self.page

        # Lever job pages need /apply appended to reach the form
        apply_url = job.raw.apply_url
        if "/apply" not in apply_url:
            apply_url = apply_url.rstrip("/") + "/apply"

        logger.info("Lever: applying to %s at %s", job.raw.title, job.raw.company)
        page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
        self._random_pause(1, 3)

        # Check for CAPTCHA
        if self._detect_captcha():
            return ApplyResult(
                success=False, captcha_detected=True,
                error_message="CAPTCHA detected",
            )

        # Verify we're on the application form
        form = page.query_selector(
            "form.application-form, "
            "form[action*='apply'], "
            ".application-form, "
            "form.postings-form"
        )
        if not form:
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Lever application form not found",
            )

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
            "button.postings-btn[type='submit'], "
            "button[type='submit'], "
            "button.postings-btn-submit, "
            "input[type='submit']"
        )

        if not submit_btn:
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Submit button not found on Lever form",
            )

        submit_btn.click()
        self._random_pause(2, 4)

        # Check for errors
        error_el = page.query_selector(
            ".application-error, "
            ".error-message, "
            ".form-error"
        )
        if error_el and error_el.is_visible():
            error_text = error_el.inner_text()[:200]
            return ApplyResult(
                success=False,
                error_message=f"Lever form error: {error_text}",
            )

        return ApplyResult(success=True)

    def _fill_form_fields(self, profile) -> None:
        """Fill Lever standard personal info fields."""
        page = self.page

        # Lever uses name-based fields: name, email, phone, org (current company),
        # urls[LinkedIn], urls[Portfolio]
        field_map = {
            "input[name='name']": profile.full_name,
            "input[name='email']": profile.email,
            "input[name='phone']": profile.phone_full,
        }

        for selector, value in field_map.items():
            if not value:
                continue
            el = page.query_selector(selector)
            if el and not el.input_value():
                self._human_type(el, value)
                self._random_pause(0.3, 0.8)

        # LinkedIn URL (Lever labels it as "LinkedIn URL" or urls[LinkedIn])
        if profile.linkedin_url:
            linkedin_input = page.query_selector(
                "input[name='urls[LinkedIn]'], "
                "input[name*='linkedin'], "
                "input[placeholder*='LinkedIn']"
            )
            if linkedin_input and not linkedin_input.input_value():
                self._human_type(linkedin_input, profile.linkedin_url)
                self._random_pause(0.3, 0.8)

        # Website/portfolio URL
        if profile.portfolio_url:
            website_input = page.query_selector(
                "input[name='urls[Portfolio]'], "
                "input[name='urls[Other]'], "
                "input[name*='website'], "
                "input[placeholder*='Website']"
            )
            if website_input and not website_input.input_value():
                self._human_type(website_input, profile.portfolio_url)
                self._random_pause(0.3, 0.8)

    def _upload_resume(self, resume_path: Path) -> None:
        """Upload resume via Lever file input."""
        file_input = self.page.query_selector(
            "input[type='file'][name='resume'], "
            "input[type='file'][name*='resume'], "
            "input[type='file']"
        )
        if file_input:
            try:
                file_input.set_input_files(str(resume_path))
                self._random_pause(1, 2)
            except Exception as e:
                logger.debug("Lever resume upload failed: %s", e)

    def _fill_cover_letter(self, text: str) -> None:
        """Fill cover letter textarea on Lever form."""
        if not text:
            return

        textarea = self.page.query_selector(
            "textarea[name='comments'], "
            "textarea[name*='cover'], "
            "textarea.application-answer-alternative"
        )
        if textarea and not textarea.input_value():
            textarea.fill(text)
            self._random_pause(0.5, 1)
