from __future__ import annotations

import os
import socket
import sys
from pathlib import Path


def _find_free_port(start: int = 5000, end: int = 5010) -> int:
    """Try binding to ports in range [start, end]. Return first available."""
    for port in range(start, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(
        f"All ports {start}-{end} are in use. "
        f"Set AUTOAPPLY_PORT to a free port or close other applications."
    )


def main() -> None:
    env_port = os.environ.get("AUTOAPPLY_PORT")
    if env_port:
        port = int(env_port)
    else:
        port = _find_free_port()

    from config.settings import get_data_dir

    data_dir = get_data_dir()
    (data_dir / "profile" / "experiences").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "jobs").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "resumes").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "cover_letters").mkdir(parents=True, exist_ok=True)
    (data_dir / "profile" / "job_descriptions").mkdir(parents=True, exist_ok=True)
    (data_dir / "browser_profile").mkdir(parents=True, exist_ok=True)
    (data_dir / "backups").mkdir(parents=True, exist_ok=True)

    readme_path = data_dir / "profile" / "experiences" / "README.txt"
    if not readme_path.exists():
        readme_path.write_text(
            "HOW TO USE THIS FOLDER\n"
            "=====================\n\n"
            "Add .txt files describing your work experience, skills, and achievements.\n"
            "Write in plain language — the AI will read these to generate tailored\n"
            "resumes and cover letters for each job application.\n\n"
            "Tips:\n"
            "- One file per job/role works well, but any organization is fine\n"
            "- Include specific achievements with numbers where possible\n"
            "- Mention technologies, tools, and methodologies you've used\n"
            "- Describe projects you've led or contributed to\n"
            "- Include education, certifications, and relevant training\n\n"
            "Example files:\n"
            "  senior_engineer_acme.txt\n"
            "  skills_and_tools.txt\n"
            "  education.txt\n"
            "  projects_and_achievements.txt\n",
            encoding="utf-8",
        )

    from app import app, socketio

    print(f"AutoApply starting at http://localhost:{port}")
    socketio.run(app, host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
