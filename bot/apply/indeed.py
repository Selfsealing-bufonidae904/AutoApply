"""Indeed Quick Apply automation.

Implements: FR-048 (Indeed Quick Apply).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from bot.apply.base import ApplyResult, BaseApplier

if TYPE_CHECKING:
    from config.settings import UserProfile
    from core.filter import ScoredJob

logger = logging.getLogger(__name__)


class IndeedApplier(BaseApplier):
    """Automate Indeed Quick Apply submissions."""

    def apply(
        self,
        job: "ScoredJob",
        resume_pdf_path: Path | None,
        cover_letter_text: str,
        profile: "UserProfile",
    ) -> ApplyResult:
        """Submit an Indeed Quick Apply application.

        Steps:
        1. Navigate to job URL
        2. Click "Apply now" button
        3. Fill form, upload resume
        4. Submit

        Returns:
            ApplyResult with success/failure details.
        """
        try:
            return self._do_apply(job, resume_pdf_path, cover_letter_text, profile)
        except Exception as e:
            logger.error("Indeed apply failed for %s: %s", job.raw.company, e)
            return ApplyResult(success=False, error_message=str(e))

    def _do_apply(
        self, job, resume_pdf_path, cover_letter_text, profile
    ) -> ApplyResult:
        page = self.page

        logger.info("Indeed: applying to %s at %s", job.raw.title, job.raw.company)
        page.goto(job.raw.apply_url, wait_until="domcontentloaded", timeout=30000)
        self._random_pause(1, 3)

        # Check for CAPTCHA
        if self._detect_captcha():
            return ApplyResult(
                success=False, captcha_detected=True,
                error_message="CAPTCHA detected",
            )

        # Find apply button
        apply_btn = page.query_selector(
            "button#indeedApplyButton, "
            "button[id*='indeedApply'], "
            ".jobsearch-IndeedApplyButton-newDesign, "
            "button[aria-label*='Apply now']"
        )

        if not apply_btn:
            # Check if redirected to external site
            if "indeed.com" not in page.url:
                return ApplyResult(
                    success=False, manual_required=True,
                    error_message="Redirected to external ATS",
                )
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Apply button not found",
            )

        apply_btn.click()
        self._random_pause(2, 3)

        # Check for redirect to external ATS
        if "indeed.com" not in page.url:
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Redirected to external ATS",
            )

        # Process the application form (may have multiple steps)
        max_steps = 8
        for step in range(max_steps):
            if self._detect_captcha():
                return ApplyResult(
                    success=False, captcha_detected=True,
                    error_message="CAPTCHA detected in application form",
                )

            # Fill form fields
            self._fill_form_fields(profile)

            # Upload resume
            if resume_pdf_path:
                self._upload_resume(resume_pdf_path)

            # Check for final submit
            submit_btn = page.query_selector(
                "button[aria-label*='Submit'], "
                "button.ia-continueButton[type='submit'], "
                "button[id*='submit']"
            )

            continue_btn = page.query_selector(
                "button.ia-continueButton, "
                "button[aria-label*='Continue'], "
                "button[id*='continue']"
            )

            if submit_btn and submit_btn.is_visible():
                submit_btn.click()
                self._random_pause(2, 4)
                return ApplyResult(success=True)

            if continue_btn and continue_btn.is_visible():
                continue_btn.click()
                self._random_pause(1, 2)
            else:
                break

        return ApplyResult(
            success=False,
            error_message="Could not complete Indeed application — ran out of steps",
        )

    def _fill_form_fields(self, profile) -> None:
        """Fill common form fields if they are empty."""
        page = self.page

        field_map = {
            "input[name*='name'], input[id*='name']": profile.full_name,
            "input[name*='email'], input[id*='email']": profile.email,
            "input[name*='phone'], input[id*='phone']": profile.phone_full,
        }

        for selector, value in field_map.items():
            el = page.query_selector(selector)
            if el and not el.input_value():
                self._human_type(el, value)
                self._random_pause(0.3, 0.8)

    def _upload_resume(self, resume_path: Path) -> None:
        """Upload resume if a file input is visible."""
        file_input = self.page.query_selector(
            "input[type='file'][name*='resume'], "
            "input[type='file']"
        )
        if file_input:
            try:
                file_input.set_input_files(str(resume_path))
                self._random_pause(1, 2)
            except Exception as e:
                logger.debug("Resume upload failed: %s", e)
