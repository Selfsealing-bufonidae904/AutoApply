"""SQLite database layer for application storage and analytics.

Implements: FR-004 (SQLite database), FR-005 (application storage),
            FR-006 (analytics queries).
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from db.models import Application, FeedEvent

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary TEXT,
    apply_url TEXT NOT NULL,
    match_score INTEGER NOT NULL,
    resume_path TEXT,
    cover_letter_path TEXT,
    cover_letter_text TEXT,
    description_path TEXT,
    status TEXT NOT NULL DEFAULT 'applied',
    error_message TEXT,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dedup ON applications(external_id, platform);
CREATE INDEX IF NOT EXISTS idx_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applied_at ON applications(applied_at);

CREATE TABLE IF NOT EXISTS feed_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    job_title TEXT,
    company TEXT,
    platform TEXT,
    message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def close(self) -> None:
        """Close database resources. No-op for per-operation connections."""
        pass

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            self._migrate(conn)

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Apply incremental schema migrations for existing databases."""
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(applications)").fetchall()
        }
        if "description_path" not in columns:
            conn.execute("ALTER TABLE applications ADD COLUMN description_path TEXT")

    def save_application(
        self,
        external_id: str,
        platform: str,
        job_title: str,
        company: str,
        location: str | None,
        salary: str | None,
        apply_url: str,
        match_score: int,
        resume_path: str | None,
        cover_letter_path: str | None,
        cover_letter_text: str | None,
        status: str,
        error_message: str | None,
        description_path: str | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO applications (
                    external_id, platform, job_title, company, location, salary,
                    apply_url, match_score, resume_path, cover_letter_path,
                    cover_letter_text, description_path, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    external_id, platform, job_title, company, location, salary,
                    apply_url, match_score, resume_path, cover_letter_path,
                    cover_letter_text, description_path, status, error_message,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def update_status(self, application_id: int, status: str, notes: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE applications
                SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, notes, application_id),
            )

    def get_all_applications(
        self,
        status: str | None = None,
        platform: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Application]:
        query = "SELECT * FROM applications WHERE 1=1"
        params: list = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        if search:
            query += " AND (job_title LIKE ? OR company LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY applied_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Application(**dict(row)) for row in rows]

    def get_application(self, application_id: int) -> Application | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
            if row is None:
                return None
            return Application(**dict(row))

    def exists(self, external_id: str, platform: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM applications WHERE external_id = ? AND platform = ?",
                (external_id, platform),
            ).fetchone()
            return row is not None

    def export_csv(self, path: Path) -> None:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM applications ORDER BY applied_at DESC").fetchall()
            if not rows:
                return
            headers = rows[0].keys()
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(tuple(row))

    def save_feed_event(
        self,
        event_type: str,
        job_title: str | None = None,
        company: str | None = None,
        platform: str | None = None,
        message: str | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO feed_events (event_type, job_title, company, platform, message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, job_title, company, platform, message),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_feed_events_for_job(
        self, job_title: str, company: str, limit: int = 50,
    ) -> list[FeedEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM feed_events WHERE job_title = ? AND company = ? ORDER BY created_at DESC, id DESC LIMIT ?",
                (job_title, company, limit),
            ).fetchall()
            return [FeedEvent(**dict(row)) for row in rows]

    def get_feed_events(self, limit: int = 100) -> list[FeedEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM feed_events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [FeedEvent(**dict(row)) for row in rows]

    def get_analytics_summary(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

            by_status_rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
            ).fetchall()
            by_status = {row["status"]: row["count"] for row in by_status_rows}

            by_platform_rows = conn.execute(
                "SELECT platform, COUNT(*) as count FROM applications GROUP BY platform"
            ).fetchall()
            by_platform = {row["platform"]: row["count"] for row in by_platform_rows}

            return {
                "total": total,
                "by_status": by_status,
                "by_platform": by_platform,
            }

    def get_daily_analytics(self, days: int = 30) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DATE(applied_at) as date, COUNT(*) as count
                FROM applications
                WHERE applied_at >= DATE('now', ?)
                GROUP BY DATE(applied_at)
                ORDER BY date
                """,
                (f"-{days} days",),
            ).fetchall()
            return [{"date": row["date"], "count": row["count"]} for row in rows]
