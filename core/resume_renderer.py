"""Resume PDF renderer — converts Markdown to ATS-safe PDF via ReportLab.

Implements: FR-033 (PDF resume generation).

Supports a limited Markdown subset designed for resume formatting:
  # Name          → 18pt bold
  ## Section      → 12pt bold + thin rule
  ### Subsection  → 11pt bold
  - bullet        → em-dash prefix, indented
  **bold**        → bold span
  ---             → horizontal rule
  plain text      → 10pt body paragraph
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

# Font constants — Helvetica only for ATS compatibility
FONT_NORMAL = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# Size constants
SIZE_H1 = 18
SIZE_H2 = 12
SIZE_H3 = 11
SIZE_BODY = 10
SIZE_CONTACT = 10

# Layout constants
MARGIN = 0.75 * inch
LINE_SPACING = 1.3  # multiplier for line height
BULLET_INDENT = 0.25 * inch
PARAGRAPH_SPACING = 4  # points between paragraphs
SECTION_SPACING = 10  # points before section headers
RULE_THICKNESS = 0.5

# Bold pattern
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def render_resume_to_pdf(resume_md_text: str, resume_pdf_path: Path) -> None:
    """Convert Markdown resume text to an ATS-safe PDF.

    Args:
        resume_md_text: Markdown-formatted resume string.
        resume_pdf_path: Output path for the PDF file.
    """
    page_width, page_height = letter
    usable_width = page_width - 2 * MARGIN

    c = Canvas(str(resume_pdf_path), pagesize=letter)
    y = page_height - MARGIN  # current vertical position (top-down)

    def new_page() -> float:
        c.showPage()
        return float(page_height - MARGIN)

    def check_space(needed: float) -> float:
        nonlocal y
        if y - needed < MARGIN:
            y = new_page()
        return float(y)

    def draw_text(text: str, font: str, size: float, x: float, max_width: float) -> None:
        """Draw text with word wrapping and inline bold support."""
        nonlocal y
        line_height = size * LINE_SPACING

        # Split into lines that fit within max_width
        words = text.split()
        if not words:
            return

        lines: list[str] = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            # Approximate width (bold markers add some inaccuracy but acceptable)
            plain_test = BOLD_RE.sub(r"\1", test_line)
            c.setFont(font, size)
            if c.stringWidth(plain_test, font, size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        for line in lines:
            check_space(line_height)
            _draw_line_with_bold(c, line, font, size, x, y)
            y -= line_height

    def draw_rule() -> None:
        """Draw a thin horizontal rule."""
        nonlocal y
        check_space(RULE_THICKNESS + 4)
        y -= 2
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(RULE_THICKNESS)
        c.line(MARGIN, y, page_width - MARGIN, y)
        y -= 2

    lines = resume_md_text.split("\n")
    is_first_line = True

    for line in lines:
        stripped = line.strip()

        # Blank line → paragraph spacing
        if not stripped:
            y -= PARAGRAPH_SPACING
            continue

        # Horizontal rule
        if stripped == "---" or stripped == "***" or stripped == "___":
            draw_rule()
            continue

        # H1 — Name
        if stripped.startswith("# ") and not stripped.startswith("## "):
            heading = stripped[2:].strip()
            check_space(SIZE_H1 * LINE_SPACING + 4)
            if not is_first_line:
                y -= SECTION_SPACING
            c.setFont(FONT_BOLD, SIZE_H1)
            c.drawString(MARGIN, y, heading)
            y -= SIZE_H1 * LINE_SPACING
            is_first_line = False
            continue

        # H2 — Section header with rule
        if stripped.startswith("## ") and not stripped.startswith("### "):
            heading = stripped[3:].strip()
            check_space(SIZE_H2 * LINE_SPACING + SECTION_SPACING + RULE_THICKNESS + 4)
            y -= SECTION_SPACING
            c.setFont(FONT_BOLD, SIZE_H2)
            c.drawString(MARGIN, y, heading)
            y -= SIZE_H2 * LINE_SPACING
            # Thin rule under section header
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(RULE_THICKNESS)
            c.line(MARGIN, y + 2, page_width - MARGIN, y + 2)
            y -= 2
            continue

        # H3 — Subsection
        if stripped.startswith("### "):
            heading = stripped[4:].strip()
            check_space(SIZE_H3 * LINE_SPACING + 4)
            y -= 4
            c.setFont(FONT_BOLD, SIZE_H3)
            _draw_line_with_bold(c, heading, FONT_BOLD, SIZE_H3, MARGIN, y)
            y -= SIZE_H3 * LINE_SPACING
            continue

        # Bullet point
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].strip()
            check_space(SIZE_BODY * LINE_SPACING)
            # Em-dash prefix
            em_dash = "\u2014 "
            draw_text(
                em_dash + bullet_text,
                FONT_NORMAL,
                SIZE_BODY,
                MARGIN + BULLET_INDENT,
                usable_width - BULLET_INDENT,
            )
            continue

        # Body text (contact line or paragraph)
        draw_text(stripped, FONT_NORMAL, SIZE_BODY, MARGIN, usable_width)
        is_first_line = False

    c.save()


def _draw_line_with_bold(
    c: Canvas, text: str, base_font: str, size: float, x: float, y: float
) -> None:
    """Draw a single line with inline **bold** support."""
    parts = BOLD_RE.split(text)
    cursor_x = x

    # BOLD_RE.split alternates: [normal, bold_content, normal, bold_content, ...]
    for i, part in enumerate(parts):
        if not part:
            continue
        # Odd indices are the captured bold groups
        if i % 2 == 1:
            c.setFont(FONT_BOLD, size)
        else:
            c.setFont(base_font, size)

        c.drawString(cursor_x, y, part)
        cursor_x += c.stringWidth(part, FONT_BOLD if i % 2 == 1 else base_font, size)
