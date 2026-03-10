"""LinkedIn Easy Apply automation."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from bot.apply.base import ApplyResult, BaseApplier

if TYPE_CHECKING:
    from config.settings import UserProfile
    from core.filter import ScoredJob

logger = logging.getLogger(__name__)


class LinkedInApplier(BaseApplier):
    """Automate LinkedIn Easy Apply submissions."""

    def apply(
        self,
        job: "ScoredJob",
        resume_pdf_path: Path | None,
        cover_letter_text: str,
        profile: "UserProfile",
    ) -> ApplyResult:
        """Submit a LinkedIn Easy Apply application.

        Steps:
        1. Navigate to job URL
        2. Click "Easy Apply" button
        3. Fill form fields across modal steps
        4. Upload resume
        5. Submit

        Returns:
            ApplyResult with success/failure details.
        """
        try:
            return self._do_apply(job, resume_pdf_path, cover_letter_text, profile)
        except Exception as e:
            logger.error("LinkedIn apply failed for %s: %s", job.raw.company, e)
            return ApplyResult(success=False, error_message=str(e))

    def _do_apply(
        self, job, resume_pdf_path, cover_letter_text, profile
    ) -> ApplyResult:
        page = self.page

        # Navigate to job
        logger.info("LinkedIn: applying to %s at %s", job.raw.title, job.raw.company)
        page.goto(job.raw.apply_url, wait_until="domcontentloaded", timeout=30000)
        self._random_pause(1, 3)

        # Check for CAPTCHA
        if self._detect_captcha():
            return ApplyResult(
                success=False, captcha_detected=True,
                error_message="CAPTCHA detected",
            )

        # Find Easy Apply button
        easy_apply_btn = page.query_selector(
            "button.jobs-apply-button, "
            "button[aria-label*='Easy Apply'], "
            ".jobs-apply-button--top-card"
        )

        if not easy_apply_btn:
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Easy Apply button not found — external application required",
            )

        easy_apply_btn.click()
        self._random_pause(1, 2)

        # Process multi-step Easy Apply modal
        max_steps = 10
        for step in range(max_steps):
            # Check for CAPTCHA in modal
            if self._detect_captcha():
                return ApplyResult(
                    success=False, captcha_detected=True,
                    error_message="CAPTCHA detected in application form",
                )

            # Fill any visible form fields
            self._fill_form_fields(profile)

            # Upload resume if file input is visible
            if resume_pdf_path:
                self._upload_resume(resume_pdf_path)

            # Fill cover letter if textarea is visible
            self._fill_cover_letter(cover_letter_text)

            # Check for submit button (final step)
            submit_btn = page.query_selector(
                "button[aria-label*='Submit application'], "
                "button[aria-label*='Submit']"
            )
            if submit_btn and submit_btn.is_visible():
                submit_btn.click()
                self._random_pause(2, 4)

                # Verify submission
                confirmation = page.query_selector(
                    ".artdeco-modal__content h2, "
                    "[data-test-modal-close-btn], "
                    ".jpac-modal-header"
                )
                if confirmation:
                    # Close confirmation modal
                    close_btn = page.query_selector(
                        "button[aria-label*='Dismiss'], "
                        "[data-test-modal-close-btn]"
                    )
                    if close_btn:
                        close_btn.click()

                return ApplyResult(success=True)

            # Click "Next" or "Review" to advance
            next_btn = page.query_selector(
                "button[aria-label*='Continue'], "
                "button[aria-label*='Next'], "
                "button[aria-label*='Review']"
            )
            if next_btn and next_btn.is_visible():
                next_btn.click()
                self._random_pause(1, 2)
            else:
                break

        return ApplyResult(
            success=False,
            error_message="Could not complete Easy Apply — ran out of steps",
        )

    def _fill_form_fields(self, profile) -> None:
        """Fill common form fields if they are empty."""
        page = self.page

        # Phone number
        phone_input = page.query_selector(
            "input[name*='phone'], "
            "input[id*='phone']"
        )
        if phone_input and not phone_input.input_value():
            self._human_type(phone_input, profile.phone_full)
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

    def _fill_cover_letter(self, text: str) -> None:
        """Fill cover letter textarea if visible."""
        if not text:
            return

        textarea = self.page.query_selector(
            "textarea[name*='cover'], "
            "textarea[id*='cover'], "
            "textarea[aria-label*='cover']"
        )
        if textarea and not textarea.input_value():
            textarea.fill(text)
            self._random_pause(0.5, 1)
