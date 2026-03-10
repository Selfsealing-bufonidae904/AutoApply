# Setup & Installation

## What You Need

- **Python 3.11 or newer** — [Download from python.org](https://python.org/downloads/)
- **Node.js 18+** — Only needed for the desktop app ([Download](https://nodejs.org))
- **Claude Code CLI** (optional) — For AI-generated resumes and cover letters ([Install guide](https://docs.anthropic.com/en/docs/claude-code))

Without Claude Code, AutoApply still works — it just uses generic templates instead of tailored documents.

## Install and Run

### Option A: Browser Mode (simplest)

```bash
# Set up Python
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

python setup.py

# Install Playwright's Chromium browser (required for job searching/applying)
playwright install chromium

# Start
python run.py
```

Your browser opens to `http://localhost:5000`.

### Option B: Desktop App

```bash
# Set up Python (same as above)
python -m venv venv
venv\Scripts\activate        # or source venv/bin/activate
python setup.py

# Install Playwright's Chromium browser (required for job searching/applying)
playwright install chromium

# Set up and launch the desktop app
cd electron
npm install
npm start
```

A native app window opens with the dashboard.

## First Launch: Setup Wizard

On first launch, a wizard walks you through 7 steps:

1. **Personal Info** — Name, email, phone, location, bio
2. **Online Presence** — LinkedIn URL, portfolio URL (both optional)
3. **Job Preferences** — Job titles you're targeting, preferred locations, remote preference
4. **Filters** — Minimum salary, keywords to include or exclude
5. **Experience Level** — Mid, senior, staff, etc.
6. **Bot Settings** — Which platforms to scan, daily limit, timing
7. **Blacklist** — Companies you want to skip

Everything is editable later in the Settings tab.

## Log Into Your Job Platforms

This step is important. AutoApply uses a real browser to search and apply, so it needs your login sessions.

1. Start the bot once (hit the **Start** button)
2. A browser window opens in the background
3. Go to LinkedIn and/or Indeed and log in normally
4. Stop the bot

Your login sessions are saved. You won't need to log in again — AutoApply reuses the saved session on future runs.

## Next Steps

1. **[Write your experience files](experience-files.md)** — This is how AutoApply learns about your background to generate tailored resumes
2. **Review your settings** — Make sure job titles and locations match what you want
3. **Start the bot** — Hit Start on the dashboard and watch the activity feed
