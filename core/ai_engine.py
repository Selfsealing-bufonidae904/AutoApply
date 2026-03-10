"""Claude Code AI Engine — generates tailored resumes and cover letters.

Invokes Claude Code CLI via subprocess (--print flag) for non-interactive
document generation. Falls back to static templates when Claude Code is
unavailable.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# On Windows, fall back to claude.cmd if claude is not in PATH
def _find_claude_cmd() -> str:
    """Find the Claude Code CLI command, preferring the exact path."""
    path = shutil.which("claude")
    if path:
        return path
    path = shutil.which("claude.cmd")
    if path:
        return path
    return "claude"

CLAUDE_CMD = _find_claude_cmd()

RESUME_PROMPT = """
You are an expert resume writer. Create a tailored, ATS-optimised resume for this specific job.

Instructions:
- Read ALL experience files below carefully
- Select only experiences and skills most relevant to THIS job
- Quantify achievements wherever numbers appear in the raw notes
- Use strong action verbs
- Keep content to one page worth of text
- Do NOT invent or exaggerate anything not present in the experience files

Output format — Markdown only, no preamble, no explanation:

# [Full Name]
[email] | [phone] | [location] | [linkedin if provided] | [portfolio if provided]

## Summary
2-3 sentences tailored specifically to this role and company.

## Experience
### [Job Title] — [Company] ([Start Year] - [End Year or Present])
- Achievement bullet using numbers where available
- Achievement bullet
...

## Skills
Comma-separated, relevant skills only.

## Education
[Degree] — [Institution] ([Year])

Omit any section for which there is no information.

---
EXPERIENCE FILES:
{experience_files_content}

---
JOB DESCRIPTION:
{job_description}

---
APPLICANT:
Name: {full_name}
Email: {email}
Phone: {phone}
Location: {location}
LinkedIn: {linkedin_url}
Portfolio: {portfolio_url}
"""

COVER_LETTER_PROMPT = """
You are an expert career coach. Write a cover letter for this job application.

Instructions:
- 3 paragraphs, professional but not stiff
- Reference specific details from the job description
- Use relevant experiences from the experience files
- Do NOT use filler phrases like "I am excited to apply" or "I am a perfect fit"
- Do NOT repeat the resume — add context and personality
- Match tone to the company culture inferred from the job description
- Output ONLY the cover letter body — no date, no address, no salutation header, no sign-off

---
EXPERIENCE FILES:
{experience_files_content}

---
JOB DESCRIPTION:
{job_description}

---
APPLICANT:
Name: {full_name}
Bio / tone preference: {bio}
"""


def check_claude_code_available() -> bool:
    """Check if Claude Code CLI is installed and responsive.

    Runs ``claude --version`` with a 10-second timeout.
    Returns True if the command exits with code 0, False otherwise.
    """
    try:
        result = subprocess.run(
            [CLAUDE_CMD, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def invoke_claude_code(prompt: str, timeout_seconds: int = 120) -> str:
    """Run Claude Code non-interactively via --print flag.

    Args:
        prompt: Full prompt text to send to Claude Code.
        timeout_seconds: Maximum wait time (default 120s).

    Returns:
        Stripped stdout from Claude Code.

    Raises:
        RuntimeError: If Claude Code is not found, returns non-zero, or times out.
    """
    try:
        result = subprocess.run(
            [CLAUDE_CMD, "--print", prompt],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"Claude Code CLI not found: '{CLAUDE_CMD}'. "
            "Install from https://docs.anthropic.com/en/docs/claude-code"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Claude Code timed out after {timeout_seconds}s. "
            "Try again or increase timeout."
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude Code failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    return result.stdout.strip()


def read_all_experience_files(experience_dir: Path) -> str:
    """Read all .txt files from experience directory, excluding README.txt.

    Files are sorted alphabetically and concatenated with section separators.

    Args:
        experience_dir: Path to directory containing .txt files.

    Returns:
        Concatenated content string, or empty string if no files found.
    """
    if not experience_dir.exists():
        return ""

    parts: list[str] = []
    for f in sorted(experience_dir.glob("*.txt")):
        if f.name.lower() == "readme.txt":
            continue
        try:
            content = f.read_text(encoding="utf-8")
            parts.append(f"=== {f.name} ===\n{content}")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning("Skipping unreadable experience file %s: %s", f.name, e)

    return "\n\n".join(parts)


def generate_documents(
    job,
    profile,
    experience_dir: Path,
    output_dir_resumes: Path,
    output_dir_cover_letters: Path,
) -> tuple[Path, Path]:
    """Generate tailored resume and cover letter for a job application.

    Reads experience files, calls Claude Code twice (resume + cover letter),
    saves outputs to disk, and returns paths.

    Args:
        job: Object with ``.id`` (str), ``.raw.company`` (str),
             ``.raw.description`` (str).
        profile: UserProfile with full_name, email, phone, location,
                 linkedin_url, portfolio_url, bio.
        experience_dir: Path to experience .txt files.
        output_dir_resumes: Where to save resume .md and .pdf files.
        output_dir_cover_letters: Where to save cover letter .txt files.

    Returns:
        Tuple of (resume_pdf_path, cover_letter_txt_path).

    Raises:
        RuntimeError: If Claude Code invocation fails.
    """
    from core.resume_renderer import render_resume_to_pdf

    experience_content = read_all_experience_files(experience_dir)

    safe_company = job.raw.company.replace(" ", "-").lower()
    date_str = datetime.now().strftime("%Y-%m-%d")
    base_name = f"{job.id}_{safe_company}_{date_str}"

    # Ensure output directories exist
    output_dir_resumes.mkdir(parents=True, exist_ok=True)
    output_dir_cover_letters.mkdir(parents=True, exist_ok=True)

    # Generate resume via Claude Code
    resume_md_text = invoke_claude_code(RESUME_PROMPT.format(
        experience_files_content=experience_content,
        job_description=job.raw.description,
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone_full,
        location=profile.location,
        linkedin_url=profile.linkedin_url or "N/A",
        portfolio_url=profile.portfolio_url or "N/A",
    ))

    # Generate cover letter via Claude Code
    cover_letter_text = invoke_claude_code(COVER_LETTER_PROMPT.format(
        experience_files_content=experience_content,
        job_description=job.raw.description,
        full_name=profile.full_name,
        bio=profile.bio,
    ))

    # Save resume Markdown + PDF
    resume_md_path = output_dir_resumes / f"{base_name}.md"
    resume_pdf_path = output_dir_resumes / f"{base_name}.pdf"
    resume_md_path.write_text(resume_md_text, encoding="utf-8")
    render_resume_to_pdf(resume_md_text, resume_pdf_path)

    # Save cover letter
    cl_path = output_dir_cover_letters / f"{base_name}.txt"
    cl_path.write_text(cover_letter_text, encoding="utf-8")

    return resume_pdf_path, cl_path
