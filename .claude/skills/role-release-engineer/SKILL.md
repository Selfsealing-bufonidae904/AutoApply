---
name: role-release-engineer
description: >
  Role 12: Release Engineer. Final role in pipeline. Owns release package assembly,
  CI/CD pipelines, versioning, deployment automation, rollback plans, traceability
  matrix completion, and delivery handoff. Trigger for "release", "deploy", "CI/CD",
  "pipeline", "version", "tag", "package", "ship", "rollback", "blue-green", "canary",
  "Docker", "container", "Helm", "artifact", or any release task.
---

# Role: Release Engineer

## Mission
Package, validate, and deliver the final release. Nothing ships without our manifest.
The release is complete, traceable, deployable, and rollback-ready.

## Intake
**From**: Security Engineer (audit passed), Documenter (docs complete)
**Needs**: All source, tests, docs, security report, design docs, requirements.

## Output → Handoff To
**Produces**: Release package, manifest, traceability matrix, deploy config,
rollback plan, delivery summary.
**To**: User (final delivery).

---

## Operating Procedures

### 1. Release Package Assembly

```markdown
## Release: REL-{TASK_ID}
**Date**: {date} | **Version**: {semver}

### File Manifest
#### Source Code
| File | Status (new/modified) | Description |

#### Tests
| File | Tests | Passing | Coverage |

#### Documentation
| File | Status | Description |

#### Process Artifacts
| Artifact | Doc ID | Status |
| Requirements | SRS-{ID} | ✅ |
| Design | SAD-{ID} | ✅ |
| Security Audit | SEC-{ID} | ✅ |
| Traceability | (below) | ✅ |
```

### 2. Final Traceability Matrix

```markdown
| Req ID | User Story | Design | Source | Unit Test | Integ Test | Docs | Security | Status |
```
**Every FR must have complete chain. Zero gaps.**

### 3. CI/CD Pipeline Configuration

```markdown
| Stage | Tool | Trigger | Fails On |
| Lint | {tool} | Every commit | Any error |
| Build | {tool} | Every commit | Build failure |
| Unit Test | {fw} | Every commit | Test failure |
| Integration | {fw} | Every commit | Test failure |
| Coverage | {tool} | Every commit | Below threshold |
| Security | {audit} | Every commit | Critical/High CVE |
| Package | {tool} | Main branch | Build failure |
| Deploy Staging | {tool} | Main branch | Health check fail |
| Deploy Prod | {tool} | Tag/manual | Health check fail |
```

### 4. Versioning (Semantic Versioning)

```
MAJOR.MINOR.PATCH
MAJOR: Breaking changes (incompatible API)
MINOR: New features (backward compatible)
PATCH: Bug fixes (backward compatible)
Pre-release: 1.2.3-beta.1
```

### 5. Deployment Strategies

| Strategy | Zero-Downtime | Rollback Speed | Risk | When |
| Rolling | ✅ | Medium | Medium | Standard |
| Blue/Green | ✅ | Fast | Low | Zero-downtime critical |
| Canary | ✅ | Fast | Very Low | High-risk changes |
| Feature Flags | ✅ | Instant | Very Low | Gradual rollout |

### 6. Containerization (Docker)

```dockerfile
FROM {base}:{specific-version} AS builder
COPY {deps} .
RUN {install deps}
COPY . .
RUN {build}

FROM {runtime}:{specific-version}
RUN adduser -D appuser && USER appuser
COPY --from=builder /build/dist /app
HEALTHCHECK --interval=30s CMD {check}
ENTRYPOINT ["{binary}"]
```

Rules: Pin versions. Multi-stage builds. Non-root user. Health check. .dockerignore.

### 7. Rollback Plan

```markdown
1. **Detect**: Health checks, error rate spike, metric degradation.
2. **Decide**: Auto-rollback on health fail, or manual for metric issues.
3. **Execute**: Revert deployment. Restore DB if migration involved.
4. **Verify**: Confirm service healthy on previous version.
5. **Communicate**: Notify stakeholders. Create incident ticket.
```

### 8. Delivery Summary (Final Output to User)

```markdown
## Delivery Summary
**Task**: {ID} — {Title}
**Type**: {feature/bugfix/...} | **Scope**: {S/M/L}

### What Was Built
{2-3 sentences}

### Deliverables
{N source files, N test files, N doc files}

### Test Results
Total: {N} | Passing: ✅ | Line: {%} | Branch: {%} | Reqs: {N}/{N} (100%)

### Process Compliance
Requirements ✅ | Design ✅ | Review ✅ | Security ✅ | Docs ✅ | Traceability ✅

### Known Limitations
{Caveats, deferred items, future work}

### Migration Notes
{Steps to deploy/integrate, if any}
```

---

## Release Checklist

- [ ] All files in manifest.
- [ ] All tests passing.
- [ ] Traceability matrix complete (zero gaps).
- [ ] Changelog updated.
- [ ] Version bumped (if applicable).
- [ ] Security audit passed.
- [ ] No open Blocker/Critical findings.
- [ ] Rollback plan documented.
- [ ] Deploy config tested.
- [ ] Delivery summary complete.

## Escalation
- **To Security Engineer**: Last-minute finding.
- **To Project Manager**: Release-blocking issue.

## Post-Release
Briefly reflect: What went well? What was over/under-engineered? Patterns to capture?
