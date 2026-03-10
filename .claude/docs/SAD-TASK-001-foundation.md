# System Architecture Document

**Document ID**: SAD-TASK-001-foundation
**Version**: 1.0
**Date**: 2026-03-09
**Status**: approved
**Author**: Claude (System Engineer)
**SRS Reference**: SRS-TASK-001-foundation

---

## 1. Executive Summary

AutoApply Phase 1 establishes a three-layer local application: a Flask+SocketIO web server (presentation), configuration and bot state management (service), and SQLite+filesystem persistence (infrastructure). The architecture prioritizes simplicity — single-process, no external services, pathlib everywhere — while providing clean extension points for future phases.

## 2. Architecture Overview

See full document in conversation context. Key components:
- Flask App (app.py) — Presentation Layer
- BotState (bot/state.py) — Service Layer
- AppConfig (config/settings.py) — Service Layer
- Database (db/database.py) — Infrastructure Layer
- SPA Dashboard (templates/index.html) — Presentation Layer

## 3. ADRs

- ADR-001: Single-process Flask + background thread (threading over multiprocess/asyncio)
- ADR-002: SQLite with direct sqlite3 (no ORM)
- ADR-003: Gevent async mode for Flask-SocketIO
- ADR-004: Inline CSS/JS in single HTML template

## 4. Critical Gap

NFR-007 (Path Traversal Protection): Must add filename validation to experience file API endpoints.

## 5. Traceability

28/28 requirements mapped (18 FRs + 10 NFRs = 100% coverage).
