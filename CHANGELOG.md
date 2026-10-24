# Changelog

## 1.0.2 — Custom forecast windows and deeper political/personal synthesis
- Added optional exact start/end date ranges for both country mundane forecasts and personal forecasts.
- Added public uprising, government collapse, abrupt leadership removal and constitutional-crisis event classes.
- Added three-layer event interpretations and removed exact duplicate corpus rows without deleting unique combinations.

# Jyotish Lab 1.0.0 — historical mundane validation

- Reworked retrospective mundane testing into a chronological development/holdout replay.
- Forecasts are issued from historical anchors with a fixed 365-day horizon and annual anchor cadence for the India/Israel validation fixtures.
- Threshold selection is performed only on the development period and frozen for the blind holdout.
- Predictions are collapsed to one prediction per event class per forecast year and actual events are one-to-one matched, preventing overlapping windows from inflating hit counts.
- Added cached as-of-date historical signatures so replay does not repeatedly recompute the same event charts.
- Added `scripts_run_validation.py` and `data/mundane_backtest_report.json` as internal regression artifacts. No India/Israel UI controls were added.
- The validation report deliberately does not claim 80% accuracy where the blind holdout does not support it.

## 1.0.3 — Country + leader synthesis
- Added optional selected or custom leader birth data to country forecasts.
- Leader timing uses the same custom forecast period as the country chart.
- National and leader charts remain separate evidence layers; date overlaps are shown as concordance signals without an uncalibrated combined probability.
- Unknown birth times are labelled and use noon only as a reference time.
- Added personal chat handling for court/litigation and sibling/sister/brother questions with appropriate chart-layer limitations.
- Added `LEADER_COUNTRY_SYNTHESIS_AND_DEPLOYMENT.md` with methodology, data-quality policy, validation and deployment steps.

## 1.0.4 — adversarial audit and calculation transparency
- Corrected even-sign D30 Trimshamsha boundaries (5°/10°/18°/25°/30°).
- Fixed Sunapha/Anapha false positives when the Sun was the only planet in the relevant sign from the Moon.
- Added real calendar-date, 24-hour time, timezone and custom-window validation to request schemas.
- Passed personal custom forecast dates through the deterministic chat chart cache and included them in its cache key.
- Clarified that Shadbala component totals and Ashtakavarga reductions are screening approximations where the implementation is not canonical.
- Added `AUDIT_AND_ASTROLOGICAL_CORRECTNESS_1.0.4.md` with research sources, confirmed fixes, limitations and a prioritized correctness backlog.

## 1.0.5 — Calculation validation and personalized Muhurta
- Added activity-specific personalized Muhurta search for puja, job joining, property purchase/sale, business opening, major expense/payment, property registration/legal signing, travel, and education.
- Added location-aware local sunrise/sunset, Lahiri Panchanga, Tithi, Nakshatra/Pada, Nitya Yoga, Karana, weekday Rahu Kalam/Yamaganda/Gulika screens, and optional natal Moon Tara Bala/Chandra Bala.
- Added API endpoint `/api/muhurta/search`, UI controls for activity/date range/location, explainable reasons/conflicts, 90-day range limit, and explicit rule-score limitations.
- Added exploratory Muhurta tests and documentation for reference validation, deployment, and known gaps.
- Shadbala and Ashtakavarga limitations remain explicitly documented rather than being represented as complete canonical calculations.

- Corrected a major Ashtakavarga bug: the target sign was held fixed across all twelve BAV output signs; now the target sign varies correctly, standard BAV totals sum to 337, and graha-wise shodhana/pinda are exposed.
- Updated the full Mundane validation report after the chronological blind replay: Israel holdout precision 33.3% (3 hits/9 predictions); India holdout precision 5.0% (1 hit/20 predictions). Neither reaches the requested 80% precision target.


## 1.0.6 — Security audit, hardening and UI reliability
- Added a 1 MB request-body cap, security response headers and a restrictive CSP; removed inline HTML event handlers and moved action dispatch to one delegated handler.
- Disabled world-event sync unless a server-side `WORLD_EVENTS_SYNC_TOKEN` is configured; compare tokens in constant time and stopped returning subprocess output to clients.
- Redacted birth and location details from application/engine logs, removed internal cache metrics from public health output, and replaced internal exception details with generic API errors.
- Added bounded library/chat/backtest inputs and forecast horizon/date-range validation; constrained geocoder query/response sizes.
- Required HTTPS for remote AI provider endpoints, allowed plain HTTP only for localhost development, capped provider responses and sanitized provider errors.
- Escaped dynamic text before ReportLab Paragraph parsing to prevent user/AI-provided strings from being interpreted as PDF markup.
- Removed duplicate tab click wiring, shared the initial reference-library fetch, debounced/aborted library search requests, and implemented the previously missing mundane PDF export handler.
- Added security and UI wiring regression tests.
