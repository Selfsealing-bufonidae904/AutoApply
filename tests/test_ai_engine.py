"""Unit tests for core.ai_engine module.

Tests cover: Claude Code availability check, CLI invocation, experience file
reading, and document generation orchestration.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.ai_engine import (
    check_claude_code_available,
    invoke_claude_code,
    read_all_experience_files,
    generate_documents,
)


# ===================================================================
# FR-031 — Claude Code Availability Check
# ===================================================================


class TestCheckClaudeCodeAvailable:
    """FR-031: Detect whether Claude Code CLI is installed."""

    # Validates AC-031-1
    def test_available_when_version_succeeds(self, monkeypatch):
        """AC-031-1: claude --version exits 0 -> True."""
        result = subprocess.CompletedProcess(args=[], returncode=0, stdout="1.0.0\n")
        monkeypatch.setattr(
            "core.ai_engine.subprocess.run",
            lambda *a, **kw: result,
        )
        assert check_claude_code_available() is True

    # Validates AC-031-2
    def test_unavailable_when_not_found(self, monkeypatch):
        """AC-031-2: FileNotFoundError -> False."""
        def raise_fnf(*a, **kw):
            raise FileNotFoundError("claude not found")
        monkeypatch.setattr("core.ai_engine.subprocess.run", raise_fnf)
        assert check_claude_code_available() is False

    # Validates AC-031-3
    def test_unavailable_when_timeout(self, monkeypatch):
        """AC-031-3: TimeoutExpired -> False."""
        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired(cmd="claude", timeout=10)
        monkeypatch.setattr("core.ai_engine.subprocess.run", raise_timeout)
        assert check_claude_code_available() is False

    # Validates AC-031-N1
    def test_unavailable_when_nonzero_exit(self, monkeypatch):
        """AC-031-N1: Non-zero exit code -> False."""
        result = subprocess.CompletedProcess(args=[], returncode=1, stderr="error")
        monkeypatch.setattr(
            "core.ai_engine.subprocess.run",
            lambda *a, **kw: result,
        )
        assert check_claude_code_available() is False


# ===================================================================
# FR-032 — Claude Code Invocation
# ===================================================================


class TestInvokeClaudeCode:
    """FR-032: Invoke Claude Code CLI non-interactively."""

    # Validates AC-032-1
    def test_returns_stdout_on_success(self, monkeypatch):
        """AC-032-1: Successful invocation returns stripped stdout."""
        result = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="  Generated resume text\n  ",
            stderr="",
        )
        monkeypatch.setattr("core.ai_engine.subprocess.run", lambda *a, **kw: result)
        output = invoke_claude_code("test prompt")
        assert output == "Generated resume text"

    # Validates AC-032-2
    def test_raises_on_nonzero_exit(self, monkeypatch):
        """AC-032-2: Non-zero exit -> RuntimeError with exit code and stderr."""
        result = subprocess.CompletedProcess(
            args=[], returncode=1,
            stdout="",
            stderr="Something went wrong",
        )
        monkeypatch.setattr("core.ai_engine.subprocess.run", lambda *a, **kw: result)
        with pytest.raises(RuntimeError, match="exit 1"):
            invoke_claude_code("test prompt")

    # Validates AC-032-3
    def test_raises_on_timeout(self, monkeypatch):
        """AC-032-3: Timeout -> RuntimeError."""
        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired(cmd="claude", timeout=120)
        monkeypatch.setattr("core.ai_engine.subprocess.run", raise_timeout)
        with pytest.raises(RuntimeError, match="timed out"):
            invoke_claude_code("test prompt", timeout_seconds=120)

    # Validates AC-032-N1
    def test_raises_on_not_found(self, monkeypatch):
        """AC-032-N1: Command not found -> RuntimeError (not FileNotFoundError)."""
        def raise_fnf(*a, **kw):
            raise FileNotFoundError("No such file")
        monkeypatch.setattr("core.ai_engine.subprocess.run", raise_fnf)
        with pytest.raises(RuntimeError, match="not found"):
            invoke_claude_code("test prompt")

    # Validates AC-032-N2
    def test_empty_prompt_still_invokes(self, monkeypatch):
        """AC-032-N2: Empty prompt is passed through without pre-validation."""
        captured_args = {}

        def mock_run(*args, **kwargs):
            captured_args["args"] = args[0] if args else kwargs.get("args")
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="ok")

        monkeypatch.setattr("core.ai_engine.subprocess.run", mock_run)
        result = invoke_claude_code("")
        assert result == "ok"
        assert captured_args["args"][2] == ""  # prompt is the 3rd arg

    def test_uses_list_form_subprocess(self, monkeypatch):
        """NFR-022: subprocess.run uses list form, not shell=True."""
        captured_kwargs = {}

        def mock_run(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="ok")

        monkeypatch.setattr("core.ai_engine.subprocess.run", mock_run)
        invoke_claude_code("test")
        assert "shell" not in captured_kwargs or captured_kwargs["shell"] is False


# ===================================================================
# FR-033 — Read Experience Files
# ===================================================================


class TestReadAllExperienceFiles:
    """FR-033: Read and concatenate experience .txt files."""

    # Validates AC-033-1
    def test_reads_and_concatenates_files(self, tmp_path):
        """AC-033-1: Multiple files concatenated with section separators."""
        (tmp_path / "skills.txt").write_text("Python, Flask", encoding="utf-8")
        (tmp_path / "work_history.txt").write_text("5 years at Acme", encoding="utf-8")

        result = read_all_experience_files(tmp_path)
        assert "=== skills.txt ===" in result
        assert "Python, Flask" in result
        assert "=== work_history.txt ===" in result
        assert "5 years at Acme" in result

    # Validates AC-033-2
    def test_excludes_readme(self, tmp_path):
        """AC-033-2: README.txt is excluded."""
        (tmp_path / "README.txt").write_text("Instructions", encoding="utf-8")
        (tmp_path / "skills.txt").write_text("Python", encoding="utf-8")

        result = read_all_experience_files(tmp_path)
        assert "README.txt" not in result
        assert "Instructions" not in result
        assert "skills.txt" in result

    # Validates AC-033-3
    def test_empty_directory_returns_empty(self, tmp_path):
        """AC-033-3: No txt files -> empty string."""
        result = read_all_experience_files(tmp_path)
        assert result == ""

    def test_only_readme_returns_empty(self, tmp_path):
        """AC-033-3: Only README.txt -> empty string."""
        (tmp_path / "README.txt").write_text("Instructions", encoding="utf-8")
        result = read_all_experience_files(tmp_path)
        assert result == ""

    # Validates AC-033-N1
    def test_nonexistent_directory_returns_empty(self, tmp_path):
        """AC-033-N1: Non-existent directory -> empty string."""
        result = read_all_experience_files(tmp_path / "nonexistent")
        assert result == ""

    # Validates AC-033-N2
    def test_skips_unreadable_files(self, tmp_path):
        """AC-033-N2: Unreadable file skipped, others still read."""
        (tmp_path / "good.txt").write_text("Good content", encoding="utf-8")
        # Write bytes that aren't valid UTF-8
        (tmp_path / "bad.txt").write_bytes(b"\x80\x81\x82")

        result = read_all_experience_files(tmp_path)
        assert "Good content" in result
        assert "bad.txt" not in result

    def test_files_sorted_alphabetically(self, tmp_path):
        """Files are sorted alphabetically by filename."""
        (tmp_path / "z_last.txt").write_text("Last", encoding="utf-8")
        (tmp_path / "a_first.txt").write_text("First", encoding="utf-8")

        result = read_all_experience_files(tmp_path)
        idx_first = result.index("a_first.txt")
        idx_last = result.index("z_last.txt")
        assert idx_first < idx_last


# ===================================================================
# FR-036 — Document Generation Orchestration
# ===================================================================


class TestGenerateDocuments:
    """FR-036: Full document generation flow."""

    @pytest.fixture()
    def mock_env(self, tmp_path, monkeypatch):
        """Set up mock environment for generate_documents tests."""
        exp_dir = tmp_path / "experiences"
        exp_dir.mkdir()
        (exp_dir / "skills.txt").write_text("Python, Flask, AI", encoding="utf-8")

        res_dir = tmp_path / "resumes"
        cl_dir = tmp_path / "cover_letters"

        job = SimpleNamespace(
            id="test-uuid-123",
            raw=SimpleNamespace(
                company="Acme Corp",
                description="Senior Python developer needed",
            ),
        )

        profile = SimpleNamespace(
            full_name="John Doe",
            email="john@example.com",
            phone_full="+1555-1234",
            location="New York, NY",
            linkedin_url="https://linkedin.com/in/johndoe",
            portfolio_url=None,
            bio="Experienced engineer",
        )

        call_count = {"n": 0}

        def mock_invoke(prompt, timeout_seconds=120):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return "# John Doe\njohn@example.com\n\n## Summary\nExperienced engineer."
            return "I bring 5 years of Python experience to this role."

        monkeypatch.setattr("core.ai_engine.invoke_claude_code", mock_invoke)

        return {
            "job": job,
            "profile": profile,
            "exp_dir": exp_dir,
            "res_dir": res_dir,
            "cl_dir": cl_dir,
            "call_count": call_count,
        }

    # Validates AC-036-1
    def test_returns_existing_file_paths(self, mock_env):
        """AC-036-1: Returns tuple of paths that exist on disk."""
        pdf_path, cl_path = generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )
        assert pdf_path.exists()
        assert cl_path.exists()

    # Validates AC-036-2
    def test_creates_three_files(self, mock_env):
        """AC-036-2: Creates .md, .pdf, and .txt files."""
        pdf_path, cl_path = generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )

        assert pdf_path.suffix == ".pdf"
        assert cl_path.suffix == ".txt"

        # Also check .md was created
        md_path = pdf_path.with_suffix(".md")
        assert md_path.exists()

    # Validates AC-036-3
    def test_company_name_in_filename(self, mock_env):
        """AC-036-3: Company name has spaces replaced with hyphens, lowercased."""
        pdf_path, _ = generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )
        assert "acme-corp" in pdf_path.name

    def test_calls_claude_code_twice(self, mock_env):
        """Claude Code is invoked exactly twice (resume + cover letter)."""
        generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )
        assert mock_env["call_count"]["n"] == 2

    # Validates AC-036-N1
    def test_raises_on_claude_failure(self, mock_env, monkeypatch):
        """AC-036-N1: Claude Code failure raises RuntimeError."""
        def fail_invoke(prompt, timeout_seconds=120):
            raise RuntimeError("Claude Code failed")

        monkeypatch.setattr("core.ai_engine.invoke_claude_code", fail_invoke)

        with pytest.raises(RuntimeError):
            generate_documents(
                mock_env["job"],
                mock_env["profile"],
                mock_env["exp_dir"],
                mock_env["res_dir"],
                mock_env["cl_dir"],
            )

    def test_creates_output_directories(self, mock_env):
        """Output directories are created if they don't exist."""
        assert not mock_env["res_dir"].exists()
        assert not mock_env["cl_dir"].exists()

        generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )

        assert mock_env["res_dir"].exists()
        assert mock_env["cl_dir"].exists()

    def test_cover_letter_content_saved(self, mock_env):
        """Cover letter text is correctly saved to .txt file."""
        _, cl_path = generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )
        content = cl_path.read_text(encoding="utf-8")
        assert "5 years of Python experience" in content

    def test_resume_markdown_saved(self, mock_env):
        """Resume Markdown is saved to .md file."""
        pdf_path, _ = generate_documents(
            mock_env["job"],
            mock_env["profile"],
            mock_env["exp_dir"],
            mock_env["res_dir"],
            mock_env["cl_dir"],
        )
        md_path = pdf_path.with_suffix(".md")
        content = md_path.read_text(encoding="utf-8")
        assert "# John Doe" in content
