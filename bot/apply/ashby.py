"""Ashby ATS application automation.

Implements: FR-071 (Ashby ATS).

Ashby is used by OpenAI, YC startups, and other tech companies.
Application pages live at ``jobs.ashbyhq.com/{company}/application/{id}``
and present a single-page form with personal info, resume upload,
cover letter, and custom questions.
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


class AshbyApplier(BaseApplier):
    """Automate Ashby job application submissions.

    Ashby uses a clean single-page React form with standard HTML inputs,
    file upload, and optional custom questions.
    """

    def apply(
        self,
        job: "ScoredJob",
        resume_pdf_path: Path | None,
        cover_letter_text: str,
        profile: "UserProfile",
    ) -> ApplyResult:
        """Submit an Ashby application.

        Steps:
        1. Navigate to job URL
        2. Fill personal info (name, email, phone, LinkedIn)
        3. Upload resume
        4. Fill cover letter / additional info
        5. Answer custom questions
        6. Submit

        Returns:
            ApplyResult with success/failure details.
        """
        try:
            return self._do_apply(job, resume_pdf_path, cover_letter_text, profile)
        except Exception as e:
            logger.error("Ashby apply failed for %s: %s", job.raw.company, e)
            return ApplyResult(success=False, error_message=str(e))

    def _do_apply(
        self, job, resume_pdf_path, cover_letter_text, profile
    ) -> ApplyResult:
        page = self.page

        logger.info("Ashby: applying to %s at %s", job.raw.title, job.raw.company)
        page.goto(job.raw.apply_url, wait_until="domcontentloaded", timeout=30000)
        self._random_pause(1, 3)

        if self._detect_captcha():
            return ApplyResult(
                success=False, captcha_detected=True,
                error_message="CAPTCHA detected",
            )

        # Ashby may show a job detail page first — click "Apply" if present
        apply_btn = page.query_selector(
            'a:has-text("Apply for this job"), '
            'button:has-text("Apply for this job"), '
            'a:has-text("Apply"), '
            'button:has-text("Apply")'
        )
        if apply_btn and apply_btn.is_visible():
            apply_btn.click()
            self._random_pause(1, 2)

        # Fill personal info
        self._fill_form_fields(profile)

        # Upload resume
        if resume_pdf_path:
            self._upload_resume(resume_pdf_path)

        # Fill cover letter / additional info
        self._fill_cover_letter(cover_letter_text)

        # Answer custom questions
        self._answer_custom_questions(profile)

        self._random_pause(0.5, 1)

        # Submit
        submit_btn = page.query_selector(
            'button[type="submit"]:has-text("Submit"), '
            'button[type="submit"]:has-text("Apply"), '
            'button[type="submit"]'
        )

        if not submit_btn:
            return ApplyResult(
                success=False, manual_required=True,
                error_message="Submit button not found on Ashby form",
            )

        submit_btn.click()
        self._random_pause(2, 4)

        # Check for success
        success_el = page.query_selector(
            'text="Your application has been submitted", '
            'text="Application submitted", '
            'text="Thank you", '
            'h1:has-text("Thank"), '
            'h2:has-text("Thank")'
        )
        if success_el:
            return ApplyResult(success=True)

        # Check for errors
        error_el = page.query_selector(
            '[role="alert"], '
            '.error-message, '
            '.form-error'
        )
        if error_el and error_el.is_visible():
            error_text = error_el.inner_text()[:200]
            return ApplyResult(
                success=False,
                error_message=f"Ashby form error: {error_text}",
            )

        # No clear success or error — assume success if no error visible
        return ApplyResult(success=True)

    def _fill_form_fields(self, profile) -> None:
        """Fill Ashby personal info fields."""
        page = self.page

        # Ashby uses standard label+input pairs with name attributes
        field_map = {
            'input[name="name"], input[name*="Name"]:not([name*="last"])': profile.full_name,
            'input[name*="firstName"], input[name*="first_name"]': profile.first_name,
            'input[name*="lastName"], input[name*="last_name"]': profile.last_name,
            'input[name="email"], input[name*="email"], input[type="email"]': profile.email,
            'input[name="phone"], input[name*="phone"], input[type="tel"]': profile.phone_full,
        }

        for selector, value in field_map.items():
            if not value:
                continue
            el = page.query_selector(selector)
            if el and el.is_visible() and not el.input_value():
                self._human_type(el, value)
                self._random_pause(0.2, 0.5)

        # LinkedIn URL
        if profile.linkedin_url:
            linkedin_input = page.query_selector(
                'input[name*="linkedin"], '
                'input[name*="LinkedIn"], '
                'input[placeholder*="LinkedIn"], '
                'input[placeholder*="linkedin"]'
            )
            if linkedin_input and linkedin_input.is_visible() and not linkedin_input.input_value():
                self._human_type(linkedin_input, profile.linkedin_url)
                self._random_pause(0.3, 0.6)

        # Portfolio / website
        if profile.portfolio_url:
            website_input = page.query_selector(
                'input[name*="website"], '
                'input[name*="portfolio"], '
                'input[placeholder*="Website"], '
                'input[placeholder*="Portfolio"]'
            )
            if website_input and website_input.is_visible() and not website_input.input_value():
                self._human_type(website_input, profile.portfolio_url)
                self._random_pause(0.3, 0.6)

        # Location / current location
        location_input = page.query_selector(
            'input[name*="location"], '
            'input[name*="Location"], '
            'input[placeholder*="location"]'
        )
        if location_input and location_input.is_visible() and not location_input.input_value():
            self._human_type(location_input, profile.location)
            self._random_pause(0.3, 0.6)

    def _upload_resume(self, resume_path: Path) -> None:
        """Upload resume via Ashby file input."""
        page = self.page

        file_input = page.query_selector(
            'input[type="file"][name*="resume"], '
            'input[type="file"][accept*="pdf"], '
            'input[type="file"]'
        )
        if file_input:
            try:
                file_input.set_input_files(str(resume_path))
                self._random_pause(1, 2)
                logger.debug("Ashby: resume uploaded")
            except Exception as e:
                logger.debug("Ashby resume upload failed: %s", e)

    def _fill_cover_letter(self, text: str) -> None:
        """Fill cover letter textarea on Ashby form."""
        if not text:
            return

        page = self.page

        textarea = page.query_selector(
            'textarea[name*="cover"], '
            'textarea[name*="Cover"], '
            'textarea[name*="letter"], '
            'textarea[placeholder*="cover letter"], '
            'textarea[placeholder*="Cover Letter"]'
        )
        if textarea and textarea.is_visible() and not textarea.input_value():
            textarea.fill(text)
            self._random_pause(0.5, 1)
            return

        # Ashby sometimes uses a generic "Additional information" textarea
        additional = page.query_selector(
            'textarea[name*="additional"], '
            'textarea[placeholder*="additional"], '
            'textarea[placeholder*="anything else"]'
        )
        if additional and additional.is_visible() and not additional.input_value():
            additional.fill(text)
            self._random_pause(0.5, 1)

    def _answer_custom_questions(self, profile) -> None:
        """Attempt to answer Ashby custom questions from screening_answers."""
        answers = profile.screening_answers
        if not answers:
            return

        page = self.page

        # Ashby renders custom questions as labeled form groups
        # Try to match label text to screening_answers keys
        labels = page.query_selector_all("label")
        for label in labels:
            try:
                label_text = label.inner_text().strip().lower()
            except Exception as e:
                logger.debug("Ashby: failed to read label text: %s", e)
                continue

            # Match against screening_answers
            for key, value in answers.items():
                if not value:
                    continue
                key_lower = key.replace("_", " ").lower()
                if key_lower in label_text or label_text in key_lower:
                    label_for = label.get_attribute("for")
                    if label_for:
                        inp = page.query_selector(f"#{label_for}")
                        if inp and inp.is_visible() and not inp.input_value():
                            tag = inp.evaluate("el => el.tagName.toLowerCase()")
                            if tag == "select":
                                inp.select_option(label=value)
                            elif tag == "textarea":
                                inp.fill(value)
                            else:
                                self._human_type(inp, value)
                            self._random_pause(0.3, 0.6)
                    break
