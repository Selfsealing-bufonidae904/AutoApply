# Release Engineering Patterns

## CI/CD Pipeline Stages
```
Lint → Build → Unit Test → Integration Test → Security Scan → Package → Deploy Staging → Deploy Prod
```

## Semantic Versioning (semver)
```
MAJOR.MINOR.PATCH — e.g., 2.1.3
MAJOR: breaking changes (incompatible API)
MINOR: new features (backward compatible)
PATCH: bug fixes (backward compatible)
Pre-release: 2.1.3-beta.1
```

## Conventional Commits
```
feat(auth): add JWT refresh endpoint       → bumps MINOR
fix(cart): correct tax calculation          → bumps PATCH
feat(api)!: remove deprecated v1 endpoints → bumps MAJOR (! = breaking)
docs(readme): update quick start
chore(deps): bump lodash to 4.17.21
test(order): add edge case for empty cart
ci(pipeline): add security scan stage
perf(query): optimize user search index
```

## Deployment Strategies
| Strategy | Zero-Downtime | Rollback Speed | Risk | Complexity |
|----------|:---:|:---:|:---:|:---:|
| Big Bang | ❌ | Slow | High | Low |
| Rolling | ✅ | Medium | Medium | Medium |
| Blue/Green | ✅ | Fast (switch) | Low | Medium |
| Canary | ✅ | Fast (route) | Very Low | High |
| Feature Flags | ✅ | Instant (toggle) | Very Low | High |

## Dockerfile Best Practices
```dockerfile
# 1. Specific version (never :latest)
FROM node:20.11-alpine AS builder
# 2. Dependencies first (cache layer)
COPY package*.json ./
RUN npm ci --production
# 3. Source code (changes most)
COPY . .
RUN npm run build
# 4. Minimal runtime image
FROM node:20.11-alpine
RUN adduser -D appuser
USER appuser
COPY --from=builder /app/dist /app
HEALTHCHECK --interval=30s CMD wget -q --spider http://localhost:3000/health
ENTRYPOINT ["node", "/app/index.js"]
```

## Rollback Decision Matrix
| Signal | Auto-Rollback | Manual Decision |
|--------|:---:|:---:|
| Health check fails | ✅ | |
| Error rate > 5% | ✅ | |
| Error rate 1-5% | | ✅ |
| Latency > 2× baseline | | ✅ |
| Business metric drop | | ✅ |
| Single user report | | ✅ |
