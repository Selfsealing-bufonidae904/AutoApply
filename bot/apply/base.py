"""Base classes for job application automation.

Implements: FR-046 (applier abstraction).
"""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config.settings import UserProfile
    from core.filter import ScoredJob


@dataclass
class ApplyResult:
    """Result of an application attempt."""

    success: bool
    error_message: str | None = None
    captcha_detected: bool = False
    manual_required: bool = False


class BaseApplier(ABC):
    """Abstract base for platform-specific job appliers."""

    def __init__(self, page) -> None:
        self.page = page

    @abstractmethod
    def apply(
        self,
        job: "ScoredJob",
        resume_pdf_path: Path | None,
        cover_letter_text: str,
        profile: "UserProfile",
    ) -> ApplyResult:
        """Submit a job application.

        Args:
            job: The scored job to apply to.
            resume_pdf_path: Path to the tailored resume PDF.
            cover_letter_text: Cover letter text to paste.
            profile: User profile with personal info.

        Returns:
            ApplyResult indicating success or failure.
        """
        ...

    def _human_type(self, locator, text: str) -> None:
        """Type text character by character with human-like delays."""
        for char in text:
            locator.type(char)
            time.sleep(random.uniform(0.03, 0.08))

    def _random_pause(self, min_s: float = 0.5, max_s: float = 2.0) -> None:
        """Sleep for a random duration to mimic human behavior."""
        time.sleep(random.uniform(min_s, max_s))

    def _detect_captcha(self) -> bool:
        """Check if a CAPTCHA challenge is present on the page."""
        captcha_indicators = [
            "iframe[src*='captcha']",
            "iframe[src*='recaptcha']",
            "#captcha",
            ".g-recaptcha",
            "[data-sitekey]",
        ]
        for selector in captcha_indicators:
            if self.page.query_selector(selector):
                return True
        return False
