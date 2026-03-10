# AutoApply

Automated job application bot that runs on your computer. It searches LinkedIn and Indeed, generates tailored resumes and cover letters using AI, and submits applications for you.

Everything runs locally — your data never leaves your machine.

## Quick Start

**You need**: Python 3.11+ and optionally [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) for AI-generated resumes.

```bash
# 1. Set up Python
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
python setup.py

# 2. Install Playwright's browser (needed for job searching/applying)
playwright install chromium

# 3. Run
python run.py
```

Your browser opens to the dashboard at `http://localhost:5000`. A setup wizard walks you through configuration on first launch.

**Want the desktop app instead?** See [Setup & Installation](docs/guides/setup.md).

## What It Does

1. **Searches** LinkedIn and Indeed for jobs matching your criteria
2. **Scores** each job (0-100) based on title, salary, location, and keywords
3. **Generates** a tailored resume and cover letter for each match (using Claude Code)
4. **Applies** automatically — fills out forms, uploads documents, submits
5. **Tracks** every application in a dashboard you can filter, search, and export

## Documentation

| Guide | Description |
|-------|-------------|
| [Setup & Installation](docs/guides/setup.md) | Install, first launch, and login |
| [How the Bot Works](docs/guides/how-the-bot-works.md) | The full pipeline — searching, scoring, applying |
| [Writing Experience Files](docs/guides/experience-files.md) | How to describe your background for better resumes |
| [How AI Generation Works](docs/guides/ai-generation.md) | What happens when AutoApply creates your documents |
| [Configuration](docs/guides/configuration.md) | All settings explained |
| [Troubleshooting](docs/guides/troubleshooting.md) | Common problems and fixes |
| [API Reference](docs/api/endpoints.md) | REST API for developers |
| [Changelog](CHANGELOG.md) | Version history |

## Your Data

All data stays on your machine at `~/.autoapply/`:

```
~/.autoapply/
├── config.json           # Your settings
├── autoapply.db          # Application history
├── profile/
│   ├── experiences/      # Your background (.txt files)
│   ├── resumes/          # Generated resumes (PDF)
│   └── cover_letters/    # Generated cover letters
└── browser_profile/      # Saved login sessions
```

## License

Proprietary. All rights reserved.
