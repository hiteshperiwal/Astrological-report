# Jyotish Lab 1.0.6 — Security & UI Reliability Build

A local Vedic astrology research and reporting workspace built around Swiss Ephemeris.

## Two independent products in one application

### Personal Astrology

The personal workspace accepts an individual's birth details and produces:

- D1 / Rashi Kundali
- Chandra Lagna and Surya Lagna reference charts
- 16 principal Parashari Vargas with visible charts, including D9 Navamsa and D10 Dashamsha
- Graha matrix: sign, house, degree, dignity, retrograde, combustion
- Planetary aspects
- 27 Nakshatra metadata and interpretation, including Moon Nakshatra and Pada
- Panchanga snapshot: weekday, tithi/paksha, nakshatra, yoga and karana
- Vimshottari Dasha hierarchy through five levels
- Yoga and Dosha screening
- Normalized planet/bhava strength screens
- Jaimini Chara Karakas
- Arudha Padas
- Ashtakavarga matrix
- Sahams
- Dynamic forecasts in days, months or years
- Selectable Parashari, Jaimini, Tajaka/Varshaphala or multi-school synthesis layers
- Shadbala-inspired six-component screening estimate (component formulas are simplified and explicitly labelled approximate)
- BAV/SAV contributor tables with Prastara, graha-wise Trikona and Ekadhipatya Shodhana, per-graha Shodhya Pinda using explicit BPHS/PVR-style assumptions
- Alternative timing systems: Chara, Ashtottari, Yogini, Narayana and Kalachakra research layers
- Tajaka solar returns, Muntha and annual year-lord screens
- Exact planetary ingress/station calendar and Swiss Ephemeris eclipse calendar
- Daily, weekly, monthly or quarterly forecast sampling
- Life-area activation graphs and planning windows
- Detailed PDF with Kundalis, varga atlas, Nakshatra, Dashas, strengths and timing

### Mundane Astrology

The country chart remains the primary collective chart. Optionally, a user can select a saved national leader or enter custom leader birth details; the app evaluates the leader chart separately over the same custom date range and displays date-level corroboration without inventing a combined probability.

The application resolves the country's chart from its national-event corpus and performs:

- Canonical country chart selection
- Alternative national charts
- Country planetary signature
- Same-country historical analogues
- Worldwide historical analogues
- Near-term and long-term transit scans
- Exact ingress, retrograde-station and eclipse calendars
- Expanded dated national/world event corpus with source-quality caveats and date-only/noon proxies identified
- Temporal walk-forward holdout audit with deterministic control dates
- Explicit political event classes including public uprising, leadership transition, government fall and constitutional crisis
- Stock-market and commodity-direction event classes (not empirically validated financial forecasts)
- Dynamic country activation graphs
- Historical-event comparisons attached to future windows

Historical similarity is presented as an astrological research pattern, not causal evidence or a guaranteed event forecast.

### Reference Library

A separate public-figure reference library is included for chart verification. Profiles distinguish verified birth date/place from uncertain birth time. If no reliably verified public birth time is stored, the software uses 12:00 local only as a clearly labelled reference chart rather than pretending it is a timed Kundali.

## Backend diagnostics and privacy

The backend logs request paths, processing stages, counts and durations. Birth name/date/time, birthplace, coordinates, place-search text and chat questions are redacted from application logs. Do not enable verbose request-body logging at a reverse proxy. Unexpected exceptions are recorded server-side while generic 5xx messages are returned to clients.

## Run locally

```bash
python -m venv .venv
.venv\\Scripts\\Activate.ps1       # Windows PowerShell
# source .venv/bin/activate          # macOS/Linux
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

API docs (development only): `http://127.0.0.1:8000/api/docs`. Set `APP_ENV=production` to disable the interactive docs and OpenAPI schema endpoints.

## Methodology and audit boundary

Astronomical positions use Swiss Ephemeris with Lahiri/Chitra Paksha sidereal settings. Whole-sign houses are used for the main interpretive house framework. Some traditional systems have school-specific variants. Shadbala remains a simplified six-component screening estimate; Ashtakavarga reductions use documented BPHS/PVR-style assumptions and still require pinned independent fixture comparisons; the yoga detector is a rule-screening catalogue, not an exhaustive classical adjudicator.

See `RESEARCH_NOTES.md`, `AUDIT_AND_ASTROLOGICAL_CORRECTNESS_1.0.4.md`, `MUHURTA_AND_VALIDATION_METHOD.md` and `REFERENCE_VALIDATION_MANIFEST.json` for source references, corrected calculation logic, known limitations, the prioritized validation backlog and deployment gate. The test suite validates implementation invariants and reproducibility; it does not prove astrological predictive validity.

This software is interpretive astrology, not scientific prediction, medical diagnosis, financial advice, or a guarantee of future events.

## Jyotish Lab 0.8.7 — research-grade depth release

This release separates Personal Astrology, Mundane Astrology, and the Reference Library into independent workspaces. Personal analysis adds a broad yoga catalogue with fruitification timing screens, expanded dosha screens, numerology, and black/white production UI. Mundane analysis adds a substantially expanded historical event corpus, country-chart resolution, same-country/worldwide analogue matching, near/long forecasts, a retrospective signal-coverage harness, and PDF export.

The astronomical layer uses Swiss Ephemeris sidereal Lahiri calculations. Swiss Ephemeris documents Lahiri as a supported sidereal mode and `swe_houses_ex()` for sidereal house calculations.

The breadth of the feature map is informed by established open-source Jyotish software such as PyJHora and related reference implementations, which document extensive divisional-chart, yoga, dosha, dasha, Ashtakavarga, strength, transit, Jaimini and Tajaka coverage. This project remains a separate implementation and does not claim that every classical school uses identical rules.

### Validation policy

The test suite verifies deterministic calculations, API behavior, PDF generation, and retrospective signal coverage. The interpretation engine is deliberately direct and reproducible: identical inputs produce identical rule output, and difficult signals are not randomized or hidden.


### Deterministic interpretation mode (0.9.0)

The interpretation layer uses a reproducible rule corpus and direct-result rendering. The expanded corpus contains 32,228 explicit combinations covering planetary placements, planet pairs, Dasha pairs, transit contacts, Vargas, Yoga/Dosha life impacts and mundane country forecast domains. Personal forecast rows expose 16 domains; mundane country rows expose 14 national domains. Corpus regeneration is available through `scripts/expand_interpretation_corpus.py`.


## Custom forecast windows (1.0.2)
Both Personal and Mundane workspaces accept an optional start/end date pair. When both dates are selected, the forecast is restricted to that interval; leave both blank to use the horizon controls. Consecutive mundane dates with identical complete outcomes are grouped into a date range. Mundane political event classes include internal unrest, public uprising, leadership transition/removal, government fall and constitutional crisis, with summary, mechanism and corroboration interpretation layers.

## Country + leader forecasts (v1.0.3)

The Mundane workspace can optionally include a leader from the public reference library or manually entered birth data. The country chart remains the primary collective chart; the leader chart is a separate timing lens. If birth time is unknown, a noon reference is clearly labelled and house/Varga conclusions are uncertain. Country and leader timing overlaps are presented as research signals, not a calibrated joint probability. See `LEADER_COUNTRY_SYNTHESIS_AND_DEPLOYMENT.md` for methodology, sources, validation boundaries, and the deployment checklist.


## Personalized Muhurta (1.0.5)

The Personal Astrology workspace includes a personalized Muhurta search for puja, job joining, property purchase/sale, business start, major expense/payment, property registration, travel and education. Set the actual location, timezone and date range (up to 90 days). Supplying birth date/time enables a natal-Moon Tara Bala/Chandra Bala screen. Scores are transparent rule-screen scores, not probabilities or empirically validated outcome forecasts. See `MUHURTA_AND_VALIDATION_METHOD.md` for conventions, validation strategy, deployment steps and limitations.


## Security and privacy (1.0.6)

- Response hardening headers include a restrictive Content Security Policy, frame denial, MIME sniffing protection, a referrer policy and disabled camera/microphone/geolocation permissions. HTML controls no longer use inline event-handler attributes.
- Request bodies are capped at 1 MB, including chunked bodies. Personal forecasts, custom date ranges, library analysis, chat history and historical backtests have explicit input bounds.
- The world-event sync endpoint is disabled unless `WORLD_EVENTS_SYNC_TOKEN` is configured. When enabled, the UI prompts for the token and sends it in `X-Admin-Token`; use HTTPS for any non-local deployment.
- Place searches for non-preset locations are sent to the public Nominatim/OpenStreetMap geocoder; avoid searching for sensitive personal addresses.
- AI interpretation is optional. When enabled, the generated chart interpretation payload is sent to the configured `AI_API_URL`; use only a provider you trust. Dynamic text is escaped before PDF markup parsing. Remote provider URLs must use HTTPS; plain HTTP is accepted only for localhost development. Provider error bodies are not exposed to users and responses are capped at 2 MB.
- There is no user-account/authentication or per-user data isolation in this single-user research application. Do not expose it directly to the public internet without adding authentication, TLS termination, reverse-proxy rate limits, secure secret management, and an appropriate data-retention policy. In-memory controls are not a substitute for multi-worker production rate limiting.
- Set `WORLD_EVENTS_SYNC_TOKEN` to a long random secret only if you intend to use the browser sync control. Leave it unset to disable that administrative action. `.env` is ignored by Git; never commit real API keys or sync tokens.

See `SECURITY_AUDIT_1.0.6.md` for findings, fixes, tests and residual deployment risks.
#   A s t r o l o g i c a l - r e p o r t  
 