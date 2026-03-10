# Changelog

All notable changes to AutoApply are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed
- **Multi-provider LLM API**: Replaced Claude Code CLI integration with direct HTTP API calls to Anthropic, OpenAI, Google Gemini, and DeepSeek. Configure your preferred provider and API key in Settings → AI Provider. (FR-031 through FR-036)
- **Electron-only distribution**: Removed browser mode (`--no-browser` flag, auto-browser-open). AutoApply now launches exclusively as an Electron desktop app.
- **AI status field**: `claude_code_available` renamed to `ai_available` across all API responses.
- **Privacy model**: AI document generation now sends prompts to your configured cloud LLM provider. No data is sent if no API key is configured.

### Added
- **Job description storage**: Every job that passes the filter has its full description saved as a styled HTML file in `~/.autoapply/profile/job_descriptions/`. Accessible via "View Job Description" button in the application detail modal, and via `GET /api/applications/:id/description`. Useful for interview prep after applying. (FR-075)
- **AI Provider settings**: New Settings section to select LLM provider (Anthropic, OpenAI, Google, DeepSeek), enter API key, and optionally override the default model.
- **API key validation endpoint** (`POST /api/ai/validate`): Test your API key before saving.
- **Default models per provider**: Anthropic → `claude-sonnet-4-20250514`, OpenAI → `gpt-4o`, Google → `gemini-2.0-flash`, DeepSeek → `deepseek-chat`.

### Fixed
- **Port conflict crash**: `run.py` now auto-detects a free port (5000-5010) instead of crashing with `WinError 10048` when port 5000 is already in use.

## [1.8.0] - 2026-03-10

Workday & Ashby ATS Support + Application Answers UI.

### Added
- **Workday applier** (`bot/apply/workday.py`): Multi-step form automation for Workday ATS (`*.myworkdayjobs.com`). Handles Apply button, account sign-in, My Information (name, phone, address, country/state dropdowns), My Experience (resume upload), Application Questions (cover letter, screening answers), Voluntary Disclosures (EEO), Self-Identification, and final submission. Uses `data-automation-id` selectors throughout. (FR-070)
- **Ashby applier** (`bot/apply/ashby.py`): Single-page form automation for Ashby ATS (`jobs.ashbyhq.com`, used by OpenAI, YC startups). Fills name, email, phone, LinkedIn, portfolio, location, uploads resume, fills cover letter, and answers custom questions via label matching. (FR-071)
- **ATS pipeline registration**: Workday and Ashby appliers registered in `APPLIERS` dict. Jobs with `myworkdayjobs.com` or `ashbyhq.com` URLs are automatically routed to the correct applier. (FR-072)
- **Application Answers UI** (Settings): New "Application Answers" section between Job Preferences and Platform Login. Collects work authorization, visa sponsorship, years of experience, desired salary, willingness to relocate, earliest start date. Collapsible EEO section for gender, ethnicity, veteran status, disability status. (FR-073)
- **Application Answers UI** (Wizard): Collapsible "Application Answers (recommended)" section in the Profile step with the 6 core screening fields. (FR-073)
- **Screening answers persistence**: `loadSettings()` and `saveSettings()` now read/write `screening_answers` dict. `wizardFinish()` collects wizard screening answers. All data stored in `profile.screening_answers` in `config.json`. (FR-073)
- **Ashby ATS fingerprint**: Added `ashbyhq.com` to `ATS_FINGERPRINTS` in `core/filter.py`. (FR-072)

### Changed
- `bot/bot.py` APPLIERS dict expanded from 4 to 6 entries (added Workday, Ashby).
- `core/filter.py` ATS_FINGERPRINTS expanded from 8 to 9 entries (added `ashbyhq.com`).

### Security
- Workday and Ashby appliers use same human-like interaction delays as existing appliers. (NFR-024)
- CAPTCHA detection on both Workday and Ashby forms. (NFR-025)
- Workday dropdown interaction uses `aria-haspopup="listbox"` pattern, avoiding fragile CSS selectors. (NFR-028)
- EEO data stored locally in `config.json` only — never transmitted to external services. (NFR-020)

## [1.7.2] - 2026-03-10

### Added
- **Apply Manually button**: Review card now includes an "Apply Manually" button that opens the job URL in your browser and saves the application as `manual_required`, letting you apply yourself while the bot continues to the next job.
- `POST /api/bot/review/manual` endpoint for manual submit review decision.
- 2 new tests for manual review endpoint. Tests: 292 total.

## [1.7.1] - 2026-03-10

Bugfixes for platform login and Claude Code detection. *(Note: Claude Code CLI was replaced by multi-provider LLM API in a later release.)*

### Fixed
- **Claude Code detection on Windows**: `check_claude_code_available()` now returns full path from `shutil.which()` instead of bare command name. *(Superseded: Claude Code CLI replaced by LLM API in [Unreleased].)*
- **Platform login browser**: Wizard login buttons (LinkedIn, Indeed) now functional — calls new backend endpoints to open a headed Playwright browser for login. Previously showed placeholder alerts.

### Added
- **Login API endpoints**: `POST /api/login/open`, `POST /api/login/close`, `GET /api/login/status` — open/close a headed browser for platform login with persistent session.
- **Settings: Platform Login section**: Log into LinkedIn or Indeed from the Settings tab (not just during the wizard).
- **Login tests**: 10 new tests covering all login endpoints (validation, domain restriction, open/close/status).
- Tests increased from 280 to 290.

## [1.7.0] - 2026-03-10

Application Detail View — click into any application to see full details, timeline, and notes.

### Added
- **Application detail endpoint** (`GET /api/applications/:id`): Returns full application data including all 17 fields. (FR-065)
- **Application events endpoint** (`GET /api/applications/:id/events`): Returns feed events matching the application's job title and company, providing an activity timeline. (FR-066)
- **Application detail modal**: Click any row in the Applications table to open a detail modal with all fields, editable status/notes, activity timeline, and action links (view posting, download resume, view cover letter). (FR-065)
- **Database**: `get_feed_events_for_job()` method for querying events by job title and company.

### Changed
- `PATCH /api/applications/:id` now supports partial updates — notes-only updates no longer require `status` field. Returns 404 for non-existent applications. (FR-067)
- Application table rows are clickable with hover highlight.
- Status dropdown in table now includes Error and Manual Required options.
- Field name compatibility: table rendering uses both `job_title`/`applied_at` (backend) and `title`/`applied_date` (legacy) field names.
- Tests increased from 265 to 280 (15 new: 3 detail endpoint + 3 events endpoint + 5 PATCH partial + 4 database method).

### Security
- Detail and events endpoints validate application existence before returning data — returns 404 for unknown IDs. (NFR-028)

## [1.6.0] - 2026-03-10

Scheduling & Daily Planner — time-based bot automation.

### Added
- **Schedule configuration** (`config/settings.py`): `ScheduleConfig` model with `enabled`, `days_of_week`, `start_time`, `end_time` fields. Nested in `BotConfig.schedule`. (FR-060)
- **Scheduler engine** (`core/scheduler.py`): Background thread checks every 60 seconds whether the bot should be running based on configured days and time window. Supports overnight windows (e.g., 22:00-06:00). (FR-061, FR-062)
- **Schedule API endpoints**: `GET /api/bot/schedule` and `PUT /api/bot/schedule` with validation for day names and HH:MM time format. (FR-063)
- **Dashboard schedule UI**: Toggle, day-of-week checkboxes, and start/end time pickers in Settings panel. Active badge shows when schedule is enabled. (FR-064)
- **Auto-start on boot**: Scheduler starts automatically on app launch if schedule is enabled in config. (FR-061)

### Changed
- `bot_start()` reuses shared `_scheduler_start_bot()` to avoid duplicating bot thread logic.
- `bot_status` response now includes `schedule_enabled` field.
- Tests increased from 240 to 265 (25 new: 11 time window + 8 scheduler logic + 6 API).

### Security
- Schedule API validates day names against allowlist and time format against 0-23:0-59 range — rejects invalid input with 400. (NFR-028)
- Scheduler only stops bots it auto-started — manually started bots are never interrupted by the scheduler. (NFR-029)

## [1.5.0] - 2026-03-10

ATS Portal Support — Greenhouse and Lever application automation.

### Added
- **Greenhouse applier** (`bot/apply/greenhouse.py`): Form-filling automation for Greenhouse ATS — personal info (first/last name, email, phone, LinkedIn), resume upload, cover letter, and form submission. (FR-057)
- **Lever applier** (`bot/apply/lever.py`): Form-filling automation for Lever ATS — personal info (name, email, phone, LinkedIn, portfolio), resume upload, cover letter, and form submission with automatic `/apply` URL append. (FR-058)
- **ATS pipeline registration**: Greenhouse and Lever appliers registered in `APPLIERS` dict — jobs with `greenhouse.io` or `lever.co` URLs are now automatically routed to the correct applier. (FR-059)

### Changed
- `bot/bot.py` APPLIERS dict expanded from 2 to 4 entries (LinkedIn, Indeed, Greenhouse, Lever).
- Tests increased from 221 to 240 (19 new: 6 Greenhouse + 9 Lever + 4 pipeline registration).

### Security
- Greenhouse and Lever appliers use same human-like interaction delays as existing appliers. (NFR-024)
- CAPTCHA detection on both Greenhouse and Lever forms. (NFR-025)
- Form error detection prevents silent failures. (NFR-028)

## [1.4.0] - 2026-03-09

Dashboard Polish & Review Mode — user visibility and override control over the application process.

### Added
- **Application mode selector**: Dropdown in bot control bar with three modes — Full Auto, Review, Watch. (FR-053)
- **Review mode**: Bot pauses before each submission, emits REVIEW event with job details and generated cover letter for user preview. (FR-053)
- **Review card UI**: Preview card in dashboard with editable cover letter textarea and Approve / Edit / Skip buttons. (FR-053)
- **Review API endpoints**: `POST /api/bot/review/approve`, `/skip`, `/edit` for user decisions. Returns 409 if no review is pending. (FR-053)
- **Bot review gate**: `wait_for_review_decision()` blocks bot thread using `threading.Event` until user responds or bot is stopped. (FR-053)
- **Watch mode**: Launches Chromium in headed (visible) mode when selected. (FR-054)
- **Analytics charts**: Chart.js integration with daily line chart, status donut chart, and platform bar chart. (FR-055)
- **Cover letter modal**: View cover letter for past applications via dedicated modal. (FR-056)
- **REVIEW/SKIPPED feed badges**: Purple and gray badge styling for new event types. (FR-053)

### Changed
- `BotConfig.apply_mode` replaces `watch_mode` boolean — values: `"full_auto"` | `"review"` | `"watch"`. `watch_mode` kept for backward compatibility but deprecated. (FR-053)
- `BotState.get_status_dict()` now includes `awaiting_review` field. (FR-053)
- `BrowserManager` uses `apply_mode` instead of `watch_mode` for headed/headless decision. (FR-054)
- Tests increased from 205 to 221 (7 new API review tests + 9 new state review tests).

### Security
- Review endpoints return 409 when no review is pending — prevents duplicate decisions. (NFR-028)
- Review edit endpoint validates required `cover_letter` field — returns 400 if missing. (NFR-028)

## [1.3.1] - 2026-03-09

Dashboard Live Feed — real-time activity feed with history persistence.

### Added
- **Feed history API** (`GET /api/feed`): Returns recent feed events from the database with configurable `limit` parameter. Feed now persists across page refreshes. (FR-051)
- **Feed counter badge**: Shows event count `(N)` next to "Activity Feed" heading.
- **Clear button**: Clears the feed display (events remain in database).
- **CAPTCHA badge style**: Feed items with type `CAPTCHA` now display with red badge styling.
- **Message display**: Feed items show the backend `message` field as a secondary line when it adds context.
- **Application filter statuses**: Added "Error" and "Manual Required" options to the Applications tab status dropdown.

### Fixed
- **Feed field name mismatch**: `addFeedItem` now reads `evt.job_title` matching backend payload (was reading `evt.title`). Feed items were showing blank titles.
- **Stats not syncing from server**: `handleBotStatus` now reads flat fields (`jobs_found_today`, `applied_today`, `errors_today`) from the backend. Stats were stuck at zero on reconnect.
- **CAPTCHA errors not counted**: CAPTCHA events now increment the error counter in dashboard stats.

### Changed
- Tests increased from 202 to 205 (3 new feed endpoint tests).

## [1.3.0] - 2026-03-09

Bot Core — automated job searching, filtering, and application submission.

### Added
- **Job search engines** (`bot/search/`): LinkedIn and Indeed searchers using Playwright for real-time job discovery with pagination support. (FR-041, FR-042, FR-043)
- **Job scoring engine** (`core/filter.py`): 0-100 scoring system based on title match (0-35), salary (0-20), location (0-20), and keyword match (0-25) with hard disqualifiers for blacklisted companies, excluded keywords, and duplicates. (FR-044, FR-045)
- **ATS detection** (`core/filter.py`): URL-based fingerprinting for Greenhouse, Lever, Workday, Taleo, iCIMS, LinkedIn, and Indeed. (FR-045)
- **Browser manager** (`bot/browser.py`): Playwright persistent context at `~/.autoapply/browser_profile/` preserving login sessions across runs. (FR-047)
- **LinkedIn Easy Apply** (`bot/apply/linkedin.py`): Multi-step modal automation — form filling, resume upload, cover letter paste, submission with confirmation. (FR-048)
- **Indeed Quick Apply** (`bot/apply/indeed.py`): Multi-step form automation — name/email/phone fill, resume upload, external ATS redirect detection. (FR-049)
- **Main bot loop** (`bot/bot.py`): Search → filter → generate docs → apply → save pipeline with pause/stop support, daily limits, rate limiting, and search intervals. (FR-050)
- **Live feed events**: SocketIO events (FOUND, FILTERED, GENERATING, APPLYING, APPLIED, CAPTCHA, ERROR) with database persistence. (FR-051)
- **Bot thread integration** (`app.py`): Daemon thread spawning with duplicate prevention, config validation, and graceful stop with 10s join timeout. (FR-052)

### Changed
- `bot_start()` now validates config exists before spawning thread (returns 400 if missing). (FR-052)
- `bot_stop()` now joins thread with 10s timeout for clean shutdown. (FR-052)
- Tests increased from 77 to 202 (49 new: 35 filter + 14 bot base).

### Security
- CAPTCHA detection prevents automated bypass attempts — returns error to user. (NFR-025)
- Human-like interaction delays (30-80ms per keystroke, 0.5-2s pauses) to avoid detection. (NFR-024)
- Browser automation uses persistent context, no credential storage in code. (NFR-025)
- Thread-safe bot state with `threading.Lock` on all mutations. (NFR-027)

## [1.2.0] - 2026-03-09

Claude Code AI Engine — AI-powered resume and cover letter generation.

### Added
- **AI Engine** (`core/ai_engine.py`): Invokes Claude Code CLI to generate tailored resumes and cover letters for each job application. (FR-031 through FR-036)
- **Resume PDF Renderer** (`core/resume_renderer.py`): Converts Markdown resumes to ATS-safe PDFs using ReportLab — Helvetica only, single-column, no colors/tables. (FR-037)
- **Claude Code availability check**: Runtime detection via `claude --version` subprocess with 10s timeout. (FR-031)
- **Fallback templates**: When Claude Code is unavailable, falls back to static cover letter template and pre-uploaded resume PDF. (FR-038)
- **Dashboard warning banner**: Persistent warning when Claude Code is not detected, with link to install instructions. (FR-039)
- **Experience file reader**: Reads and concatenates all `.txt` files from experience directory with section separators. (FR-033)

### Changed
- `check_claude_code_available()` in `app.py` now delegates to `core.ai_engine` for real runtime check (previously only checked `shutil.which()`). (FR-040)
- Dashboard initialization reads `claude_code_available` from `/api/setup/status` and `/api/bot/status`. (FR-039)
- Tests increased from 46 to 77 (36 new tests for AI engine and PDF renderer).

### Security
- Claude Code invocation uses list-form `subprocess.run()` — no `shell=True`. (NFR-022)
- Prompts contain only non-secret profile fields (name, email, phone, location, URLs, bio). (NFR-020)

## [1.1.0] - 2026-03-09

Electron desktop shell — standalone native app experience.

### Added
- **Electron desktop shell** (`electron/`): Native app window with system tray, splash screen, and single-instance lock. (FR-019, FR-022, FR-024, NFR-015)
- **Python backend lifecycle**: Electron spawns and manages Flask as a child process with health checks, crash restart, and graceful shutdown. (FR-020, FR-021, FR-023)
- **Health endpoint** (`GET /api/health`): Readiness probe for lifecycle management. (FR-025)
- **Shutdown endpoint** (`POST /api/shutdown`): Graceful server termination, localhost-only. (FR-026)
- **CLI flags**: `--no-browser` flag and `AUTOAPPLY_PORT` env var for Electron integration. (FR-027, FR-028)
- **Shared Chromium**: Playwright reuses Electron's bundled Chromium to save ~150MB. (FR-029, ADR-006)
- **Backend logging**: stdout/stderr captured to `~/.autoapply/backend.log` with rotation at 10MB. (FR-030)
- **Port auto-detection**: Finds available port if 5000 is occupied. (ADR-008)

### Changed
- `run.py` now uses `argparse` for CLI argument handling.
- Tests increased from 109 to 117 (new endpoint and CLI tests).

### Security
- `/api/shutdown` rejects non-localhost requests with 403. (FR-026)
- Electron renderer: `nodeIntegration: false`, `contextIsolation: true`. (NFR-016)
- `preload.js` only exposes `openExternal` (URL scheme validated) and `getVersion`. (NFR-016)

## [1.0.0] - 2026-03-09

Phase 1 Foundation — project setup, configuration, database, API, and dashboard.

### Added
- **Setup script** (`setup.py`): Automated environment setup with Python version check, dependency installation, Playwright Chromium installation, and data directory creation. (FR-001, FR-002)
- **Configuration system** (`config/settings.py`): Pydantic v2 models for `UserProfile`, `SearchCriteria`, `BotConfig`, and `AppConfig` with JSON persistence at `~/.autoapply/config.json`. (FR-003, FR-004, FR-005)
- **SQLite database** (`db/database.py`): `applications` and `feed_events` tables with parameterized queries, deduplication index, CSV export, and analytics queries. (FR-006, FR-007, FR-015, FR-016)
- **Database models** (`db/models.py`): Pydantic models for `Application` (17 fields) and `FeedEvent` (7 fields). (FR-006)
- **Bot state machine** (`bot/state.py`): Thread-safe `BotState` with `threading.Lock`, supporting start/pause/stop/resume transitions, daily counters, and uptime tracking. (FR-008, FR-009)
- **Flask web server** (`app.py`): 19 API endpoints covering bot control, applications CRUD, profile/experience file management, configuration, analytics, and setup status. (FR-010 through FR-018)
- **SPA dashboard** (`templates/index.html`): Single-page application with dark theme, 7-step setup wizard, bot controls, application list with filters, analytics charts, settings panel, and profile management. (FR-010, FR-011, FR-012, FR-013, FR-014)
- **WebSocket integration**: Flask-SocketIO with gevent async mode for real-time bot status updates. (FR-009)
- **Entry point** (`run.py`): Creates data directories, starts server on port 5000, auto-opens browser. (FR-001, FR-002)
- **Path traversal protection**: Allowlist filename regex on all experience file endpoints. (NFR-007)
- **Error handling**: Global exception handlers returning JSON (no stack trace leakage). (NFR-009)
- **Unit tests**: 101 tests across 4 test files with 96% code coverage. (NFR-005)
- **Integration tests**: 8 cross-component workflow tests. (NFR-005)
- **Security audit**: Full OWASP Top 10 review, all checks passed. (NFR-007, NFR-010)

### Security
- Parameterized SQL queries throughout — no string concatenation. (NFR-007)
- Filename validation with allowlist regex `^[a-zA-Z0-9_\- ]+\.txt$`. (NFR-007)
- Server binds to 127.0.0.1 only — no external network access. (NFR-007)
- JSON error responses — no internal details leaked. (NFR-009)
