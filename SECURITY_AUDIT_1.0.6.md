# Jyotish Lab 1.0.6 — Security, reliability and UI audit

**Audit date:** 2026-10-21  
**Scope:** FastAPI routes and request schemas, filesystem/subprocess/network operations, logs and error handling, browser rendering/event handlers, forecast resource limits, package/deployment configuration, and interactive smoke tests.

## Executive result

The application had several security and reliability weaknesses appropriate to fix before further use: an unauthenticated endpoint could run the world-event synchronization subprocess; birth details were written to terminal logs; there was no request-body size ceiling; some analysis horizons and backtest parameters allowed excessive work; the UI permitted inline event handlers and its mundane PDF button referenced a missing function; and browser clipboard access could raise unhandled errors. These have been addressed in this build.

This remains a **single-user research application, not a production multi-user service**. It has no account authentication, authorization model for personal charts, or distributed rate limiter. Do not expose it directly to the public internet without the deployment controls listed below.

## Findings and changes

| Area | Finding before patch | Change in 1.0.6 | Status |
|---|---|---|---|
| Administrative endpoint | `POST /api/mundane/world-events/sync` launched a Python subprocess with no authentication. | Endpoint is disabled unless `WORLD_EVENTS_SYNC_TOKEN` is configured; supplied token is checked with constant-time comparison; no subprocess output is returned to clients. UI prompts for token. | Fixed |
| Privacy/logging | Personal calculation and engine logs included name, date/time of birth, birthplace and location coordinates; place searches could be logged. | Sensitive fields are redacted in application phase logs; engine logs no longer print birth details; HTTP logs contain path/status/duration only. | Fixed for application logs |
| Response hardening | No consistent security headers or Content Security Policy. | Added CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and conservative cache headers. | Fixed |
| Inline event handlers | HTML and generated result markup used `onclick` attributes, which require a weaker CSP. | Replaced inline HTML event handlers with delegated `data-action` / `data-*` dispatch and removed duplicate subtab wiring. `script-src 'self'` is now viable. | Fixed |
| Request size | No body-size cap, including requests without a trustworthy `Content-Length`. | ASGI middleware buffers at most 1 MB and rejects larger request bodies with HTTP 413. | Fixed |
| Unbounded inputs | Library analysis accepted a generic dictionary and directly cast caller-controlled forecast parameters; personal and mundane forecast periods had overly broad unit-specific limits; backtest query bounds were loose. | Added strict Pydantic schemas, extra-field rejection, unit-aware horizon/date-range limits, chat question/history bounds, library search bounds, and bounded backtest query parameters. | Fixed |
| Geocoder | Query length and response size were not bounded; failure messages exposed exception details. | Query limited to 120 characters, URL query encoded, response capped at 512 KB, timeout retained, errors sanitized. Non-preset place searches are sent to Nominatim/OpenStreetMap and should not contain sensitive addresses. | Fixed |
| AI provider transport | Configured AI provider URLs could use non-TLS HTTP and provider errors were returned verbatim; response reads were unbounded. | Remote AI URLs must use HTTPS; HTTP is allowed only for localhost development. Provider response capped at 2 MB and errors sanitized. | Fixed |
| PDF text parsing | User-provided name/place and optional external AI text were inserted into ReportLab `Paragraph` markup without escaping. | Added XML escaping for dynamic Paragraph text, including the chart header, AI output and dynamic interpretation fields. | Fixed |
| Health endpoint | Public health response included internal chat-cache statistics. | Health now returns status, engine and version only. | Fixed |
| Frontend redundancy/reliability | Library and leader selectors could issue redundant initial requests; search fired for every keystroke; clipboard failures could become unhandled promise errors. | Shared initial library promise, debounced/abortable search, one subtab click handler, safe clipboard fallback/error UI. | Fixed |
| Mundane PDF export | UI action was wired to `downloadMundanePdf()` but the function was missing. | Implemented guarded PDF export with response handling, download and URL cleanup. | Fixed |
| Error details | Several generic exception paths returned exception class/message to the caller. | Generic 5xx messages are returned; detailed trace remains server-side. Expected validation errors remain readable. | Fixed for generic failure paths |

## Controls and test coverage

- **102 automated tests passed** with `pytest -q`.
- `python -m py_compile app/*.py scripts/*.py scripts_run_validation.py` passed.
- `node --check static/app.js` passed.
- Live in-process API smoke checks passed for the home page, health, static JavaScript, library, preset geocoder, world-event status, advanced reference endpoints, personalized Muhurta, personal analysis, and PDF generation.
- Security regression checks cover response headers, sync-token denial, body-size enforcement, schema bounds, HTTPS-only remote AI endpoints, public health minimization and inline-handler removal.
- Browser DOM interaction smoke test ran in Chromium with representative live engine output fixtures and mocked network transport: workspace navigation, birth-time picker open/close/apply, demo load, personal analysis render, all 15 personal tabs, AI build/copy/download, chat, personal PDF, Muhurta search, country render, country presets, custom-leader toggle, both historical date-range buttons, mundane backtest, mundane PDF, sync prompt, reference profile selection/category filter, location autocomplete selection and clear-place control. **No page errors or console errors remained.**
- Direct Chromium navigation to the local Uvicorn URL was blocked by this environment's browser policy (`ERR_BLOCKED_BY_ADMINISTRATOR`), so the DOM interaction test used `page.set_content`; API integration was tested separately through FastAPI `TestClient`.
- `pip check` reports a pre-existing shared-environment conflict: `moviepy 2.2.1` requires `pillow<12`, while the shared environment has `pillow 12.3.0`. Neither package is a direct dependency of this app's declared runtime requirements. A CVE database scanner (`pip-audit`) was not installed in the environment, so this audit does **not** certify all third-party dependency versions as vulnerability-free.

## Residual risks / deployment gate

1. **No user authentication or tenant isolation.** Anyone who can reach the app can submit chart requests and view generated responses from their own request; the app does not store a chart database, but it also has no account boundary. Add authentication and authorization before hosting for multiple users.
2. **No built-in distributed rate limiting.** CPU-heavy astrology and backtest routes should be rate-limited at the reverse proxy or API gateway. In-memory rate limiting would not be reliable across workers/replicas.
3. **TLS is a deployment responsibility.** Terminate HTTPS at a trusted reverse proxy; never send the sync token or AI API key over a public plain-HTTP connection. HSTS should be configured at the HTTPS proxy after verifying the deployment domain.
4. **AI privacy boundary.** If AI credentials are configured, the app sends its generated interpretation payload—including chart-derived data—to the configured AI provider. Use a provider approved for the data you enter. AI is optional and is not called if no key is configured.
5. **Secret handling.** Keep `.env` private and out of source control. Use a secret manager in hosted deployments. Use a long random `WORLD_EVENTS_SYNC_TOKEN`; leave it unset when web-triggered sync is unnecessary.
6. **Reverse-proxy limits.** Configure proxy request-size and timeout limits too; app-level limits do not replace perimeter controls.
7. **Dependency freshness.** Run `pip-audit`/OSV or the hosting platform's dependency scanner in CI and review updates on a regular schedule.
8. **No formal penetration test.** This is source-level hardening plus regression/smoke testing, not a third-party penetration test.

## Recommended production proxy controls

- TLS-only ingress; redirect HTTP to HTTPS.
- Authentication in front of all routes (and authorization for admin sync).
- Per-IP and, where applicable, per-account rate limits for `/api/personal/*`, `/api/mundane/*`, `/api/muhurta/search`, and backtest endpoints.
- Request body limit at or below 1 MB, bounded upstream timeouts and concurrency limits.
- Redact request bodies and query strings in proxy logs; do not log birth details or AI prompts.
- Keep `APP_ENV=production` to disable `/api/docs` and `/openapi.json` in a public deployment.
- Store AI and admin tokens in the deployment secret manager, not in image layers or committed files.

## Reproduction commands

```bash
python -m py_compile app/*.py scripts/*.py scripts_run_validation.py
node --check static/app.js
pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

World-event sync stays disabled until the server environment includes `WORLD_EVENTS_SYNC_TOKEN`. The `.env.example` documents the optional setting.
