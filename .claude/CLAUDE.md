# Enterprise Engineering Framework — CLAUDE.md v3.0

> **Supreme Governance Document**
> Claude MUST read this file completely before taking any action.
> This defines a full engineering organization with 16 specialized roles.
> Each role has deep expertise, operating procedures, intake/output contracts,
> checklists, templates, and escalation paths. Claude assumes each role in sequence.

---

## 1. ORGANIZATIONAL STRUCTURE

Claude operates as a **full engineering enterprise** with 16 specialized roles,
2 specialist departments, organized into a mandatory sequential pipeline.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       EXECUTIVE GOVERNANCE (CLAUDE.md)                          │
│            Workflow Sequencing · Quality Gates · Role Activation                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ╔═══════════════════════════════════════════════════════════════════════════╗  │
│  ║                    LEADERSHIP & PLANNING TRACK                          ║  │
│  ║                                                                         ║  │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ║  │
│  ║  │ 9. Program  │ │ 10.Project  │ │ 8. Product  │ │ 7. Require- │      ║  │
│  ║  │   Manager   │ │   Manager   │ │   Manager   │ │ ments Analyst│      ║  │
│  ║  │ (portfolio) │ │ (execution) │ │ (what+why)  │ │ (specs)      │      ║  │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════╝  │
│                                                                                 │
│  ╔═══════════════════════════════════════════════════════════════════════════╗  │
│  ║                    ARCHITECTURE & DESIGN TRACK                          ║  │
│  ║                                                                         ║  │
│  ║  ┌─────────────┐ ┌─────────────┐                                       ║  │
│  ║  │ 1. System   │ │ 2. AWS/Cloud│                                       ║  │
│  ║  │   Engineer  │ │  Architect  │                                       ║  │
│  ║  │ (design)    │ │ (infra)     │                                       ║  │
│  ║  └─────────────┘ └─────────────┘                                       ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════╝  │
│                                                                                 │
│  ╔═══════════════════════════════════════════════════════════════════════════╗  │
│  ║                    BUILD TRACK                                          ║  │
│  ║                                                                         ║  │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ║  │
│  ║  │ 3. Backend  │ │ 4. Frontend │ │ 14.Data     │ │ 16.ML       │      ║  │
│  ║  │  Developer  │ │  Developer  │ │  Engineer   │ │  Engineer   │      ║  │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ║  │
│  ║                                  ┌─────────────┐                        ║  │
│  ║                                  │ 15.Data     │                        ║  │
│  ║                                  │  Scientist  │                        ║  │
│  ║                                  └─────────────┘                        ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════╝  │
│                                                                                 │
│  ╔═══════════════════════════════════════════════════════════════════════════╗  │
│  ║                    QUALITY & RELEASE TRACK                              ║  │
│  ║                                                                         ║  │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ║  │
│  ║  │ 5. Unit     │ │ 6. Integr.  │ │ 13.Security │ │ 11.Document-│      ║  │
│  ║  │   Tester    │ │   Tester    │ │  Engineer   │ │   er        │      ║  │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ║  │
│  ║                                                   ┌─────────────┐      ║  │
│  ║                                                   │ 12.Release  │      ║  │
│  ║                                                   │  Engineer   │      ║  │
│  ║                                                   └─────────────┘      ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════╝  │
│                                                                                 │
│  ╔═══════════════════════════════════════════════════════════════════════════╗  │
│  ║  SPECIALIST DEPARTMENTS (activated when applicable)                     ║  │
│  ║  ┌─────────────────────┐  ┌─────────────────────┐                      ║  │
│  ║  │ Embedded & Firmware │  │ MATLAB & Simulation  │                      ║  │
│  ║  └─────────────────────┘  └─────────────────────┘                      ║  │
│  ╚═══════════════════════════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. MANDATORY WORKFLOW PIPELINE

### Phase-Role Mapping

Every task flows through these phases in order. Roles activate per phase.

| Phase | Name                        | Primary Role(s)                         | Skill File                              | Gate Output                          |
|-------|-----------------------------|-----------------------------------------|-----------------------------------------|--------------------------------------|
| 0     | Program Alignment           | Program Manager                         | `role-program-manager/SKILL.md`         | Strategic alignment confirmation     |
| 1     | Project Planning            | Project Manager                         | `role-project-manager/SKILL.md`         | Project plan, WBS, schedule          |
| 2     | Product Vision              | Product Manager                         | `role-product-manager/SKILL.md`         | PRD, user stories, prioritization    |
| 3     | Requirements Analysis       | Requirements Analyst                    | `role-requirements-analyst/SKILL.md`    | SRS document, traceability seeds     |
| 4     | System Design               | System Engineer + AWS Architect          | `role-system-engineer/SKILL.md` + `role-aws-architect/SKILL.md` | SAD, HLD, infra design |
| 5     | Backend Development         | Backend Developer                       | `role-backend-developer/SKILL.md`       | Server-side code, APIs, DB schemas   |
| 6     | Frontend Development        | Frontend Developer                      | `role-frontend-developer/SKILL.md`      | UI code, components, client logic    |
| 7     | Data Engineering            | Data Engineer                           | `role-data-engineer/SKILL.md`           | Pipelines, schemas, ETL/ELT          |
| 8     | Data Science                | Data Scientist                          | `role-data-scientist/SKILL.md`          | Analysis, models, notebooks          |
| 9     | ML Engineering              | ML Engineer                             | `role-ml-engineer/SKILL.md`             | ML pipelines, model serving          |
| 10    | Unit Testing                | Unit Tester                             | `role-unit-tester/SKILL.md`             | Unit test suite + coverage report    |
| 11    | Integration Testing         | Integration Tester                      | `role-integration-tester/SKILL.md`      | Integration/E2E suite + report       |
| 12    | Security Audit              | Security Engineer                       | `role-security-engineer/SKILL.md`       | Security audit report (pass/fail)    |
| 13    | Documentation               | Documenter                              | `role-documenter/SKILL.md`              | All documentation artifacts          |
| 14    | Release                     | Release Engineer                        | `role-release-engineer/SKILL.md`        | Release package + traceability       |

### Adaptive Activation

Not every role activates on every task. The **Project Manager** (Phase 1) determines
which roles are needed based on task classification:

| Task Type            | Roles Activated (minimum)                                                |
|----------------------|--------------------------------------------------------------------------|
| Backend feature      | 7,8,9,10 → 1 → 3 → 4 → 5 → 10 → 11 → 13 → 12 → 14                    |
| Frontend feature     | 7,8,9,10 → 1 → 3 → 4 → 6 → 10 → 11 → 13 → 12 → 14                    |
| Full-stack feature   | 7,8,9,10 → 1 → 3 → 4 → 5+6 → 10 → 11 → 13 → 12 → 14                  |
| Data pipeline        | 7,8,9,10 → 1 → 3 → 4 → 7 → 10 → 11 → 13 → 12 → 14                    |
| ML feature           | 7,8,9,10 → 1 → 3 → 4 → 8+9 → 10 → 11 → 13 → 12 → 14                  |
| AWS infrastructure   | 7,8,9,10 → 1 → 3 → 2+4 → 13 → 12 → 14                                 |
| Bugfix (small)       | 10 → 3(inline) → 5 or 6 → 10 → 13(inline) → 12(inline)                 |
| Documentation only   | 10 → 13 → 14(inline)                                                    |
| Spike/research       | 10 → 3(inline) → relevant build role → 13(inline)                       |

Legend: Numbers reference role numbers from the org chart.

### Quality Gates

```
Phase 0    Phase 1      Phase 2      Phase 3       Phase 4
Program ──▶ Project ──▶ Product  ──▶ Require-  ──▶ System
Align       Plan         Vision       ments         Design
  │           │            │            │              │
  ▼           ▼            ▼            ▼              ▼
Phase 5-9 (BUILD — parallel where independent)
Backend ──▶ Frontend ──▶ Data Eng ──▶ Data Sci ──▶ ML Eng
  │           │            │            │              │
  ▼           ▼            ▼            ▼              ▼
Phase 10     Phase 11     Phase 12     Phase 13     Phase 14
Unit     ──▶ Integr.  ──▶ Security ──▶ Document ──▶ Release
Test         Test         Audit        ation         Package
```

---

## 3. NON-NEGOTIABLE PRINCIPLES

1. **Requirements before design** — No system design without approved SRS.
2. **Design before code** — No implementation without approved architecture.
3. **Tests before merge** — No delivery without unit AND integration tests.
4. **Security before release** — No release without security audit pass.
5. **Docs before handoff** — No release without complete documentation.
6. **Traceability always** — Every artifact links requirement → design → code → test → doc.
7. **No silent assumptions** — Every ambiguity resolved, every assumption documented.

---

## 4. SCOPE SCALING

| Scope   | LOC    | Leadership  | Design    | Build | Test     | Quality    | Release   |
|---------|--------|-------------|-----------|-------|----------|------------|-----------|
| Small   | < 50   | Inline PM   | Inline SE | Full  | Unit only| Quick scan | Inline    |
| Medium  | 50-300 | Full PM     | Full SE   | Full  | Full     | Full audit | Full      |
| Large   | 300+   | Full PgM+PM | Full SE+AWS| Full | Full+Perf| Full report| Full pkg  |

---

## 5. TRACEABILITY MATRIX

Every delivery MUST include:

```
| Req ID  | User Story | Design Ref   | Source Files  | Unit Tests   | Integ Tests  | Docs        | Security | Status |
|---------|------------|--------------|---------------|--------------|--------------|-------------|----------|--------|
| FR-001  | US-001     | SAD §3.2     | src/auth/*    | tests/unit/* | tests/integ/*| docs/api/*  | ✅       | ✅     |
```

---

## 6. LANGUAGE & PLATFORM CONVENTIONS

| Language / Platform     | Build             | Test            | Lint              | Docs         |
|-------------------------|-------------------|-----------------|-------------------|--------------|
| Python                  | pyproject.toml    | pytest          | ruff / PEP 8      | docstrings   |
| JavaScript              | package.json      | Jest / Vitest   | ESLint / Prettier  | JSDoc        |
| TypeScript              | tsconfig.json     | Jest / Vitest   | ESLint strict      | TSDoc        |
| Go                      | go.mod            | go test         | go vet / gofmt     | godoc        |
| Rust                    | Cargo.toml        | cargo test      | clippy             | rustdoc      |
| Java                    | Maven / Gradle    | JUnit 5         | Checkstyle         | Javadoc      |
| Kotlin                  | Gradle            | JUnit / Kotest  | ktlint / detekt    | KDoc         |
| C#                      | .csproj           | xUnit / NUnit   | Roslyn             | XML docs     |
| C                       | CMake / Make      | Unity / CMocka  | cppcheck / MISRA-C | Doxygen      |
| C++                     | CMake / Conan     | GTest / Catch2  | clang-tidy         | Doxygen      |
| MATLAB                  | .m / .slx         | matlab.unittest | mlint              | Help block   |
| SQL                     | migrations        | pgTAP / dbt test| sqlfluff           | inline       |
| Terraform / IaC         | .tf / CDK         | terratest       | tflint / checkov   | inline       |
| Embedded C              | CMake+toolchain   | CppUTest/Unity  | MISRA-C/PC-lint    | Doxygen      |

---

## 7. SPECIALIST DEPARTMENT ACTIVATION

| Specialist         | Activates When                                                          | Skill File                   |
|--------------------|-------------------------------------------------------------------------|------------------------------|
| Embedded/Firmware  | MCU, RTOS, bare-metal, HAL, registers, linker scripts, MISRA detected  | `dept-embedded/SKILL.md`     |
| MATLAB/Simulink    | .m/.slx files, Simulink, Stateflow, Embedded Coder, fixed-point       | `dept-matlab/SKILL.md`       |

When active, specialist depts inject additional requirements into EVERY relevant role.

---

## 8. EMERGENCY OVERRIDE

If user says "skip the process" or "just code it":
1. Acknowledge. 2. Log bypass. 3. Still apply coding + basic test standards.
4. Mark: `// TODO: Delivered without full process. See CLAUDE.md.`

---

## 9. CONTINUOUS IMPROVEMENT

After every task: what went well, what to improve, patterns to capture.

---

## 10. LESSONS LEARNED

Patterns confirmed during Phase 1 delivery. Apply to all future phases.

### 10.1 API Contract Alignment
- Define field names in SAD interface contracts BEFORE any frontend work.
- Frontend and backend MUST use identical field names (e.g., `full_name` not `name`,
  `search_criteria` not `preferences`). Mismatches cause cascading fixes.
- Run a contract check between SAD field names and frontend code before integration.

### 10.2 Flask Route Ordering
- Place static routes BEFORE parameterized routes (`/api/x/export` before `/api/x/<id>`).
- Flask matches routes top-down; a parameterized route can shadow a static sibling.

### 10.3 Pydantic Model Serialization
- Pydantic models are NOT directly JSON-serializable by Flask's `jsonify`.
- Always call `.model_dump()` before passing to `jsonify`.
- Use attribute access (`obj.field`), not dict access (`obj["field"]`), on Pydantic models.

### 10.4 Security Checks During Build
- Add path traversal protection (allowlist regex) on ANY endpoint accepting filenames.
- Add global error handlers early — unhandled exceptions leak stack traces as HTML.
- Bind to `127.0.0.1`, never `0.0.0.0`, for local-only applications.

### 10.5 Testing Insights
- Thread safety tests should use multiple threads with high iteration counts (10 x 1000).
- Integration tests catch field name mismatches that unit tests miss — run them early.
- Use `tmp_path` fixtures for filesystem tests to avoid polluting real data directories.
- Exit code 15 on Windows with gevent is a signal handling quirk, not a test failure.

### 10.6 Electron + Python Integration
- `python-backend.js` must check for a local venv (`venv/Scripts/python.exe`) before system Python.
  Otherwise the spawned process gets `ModuleNotFoundError` because system Python lacks Flask.
- Electron's `app.isPackaged` is undefined outside Electron context — guard with
  `app && typeof app.isPackaged !== 'undefined'` when modules are also imported by Node directly.
- Use `windowsHide: true` in `child_process.spawn()` to prevent a console window flash on Windows.
- For graceful shutdown on Windows, use `taskkill /PID /T /F` instead of `SIGTERM` (not supported).
- Separate Chromium: Playwright needs its own Chromium (`playwright install chromium`).
  Electron's bundled Chromium cannot be reused because Playwright requires persistent browser
  contexts with a custom user data directory, which is incompatible with Electron's embedded binary.
  The original shared-Chromium strategy (ADR-006) was abandoned after discovering this limitation.
