# Country + Leader Synthesis, Personal Scenario Coverage, and Deployment Plan

## What this release adds

- Optional country-leader overlay in the Mundane workspace. The national chart remains the primary collective chart; the leader chart is a separate corroboration/timing lens.
- Leader may be selected from the existing public-figure reference library or entered manually (name, date, time, birthplace, coordinates, timezone and time-quality label).
- If the selected leader has no reliable birth time, the app uses a labelled noon reference. It does not present that as a verified timed chart. House-based, Lagna-dependent and divisional conclusions are explicitly downgraded when time is unknown.
- Country forecast period is reused for the leader chart when the user selects a custom start/end range. The response reports date overlaps as research signals rather than inventing a single combined probability.
- Personal chat intent coverage includes court/litigation questions and sister/brother/sibling questions. These are framed as indirect indications in the native chart; an individual relative's own chart and real circumstances are distinct evidence.

## Methodological research notes

The implementation uses a layered, non-collapsing design:

1. **National chart:** canonical country/founding chart and its national-house framework.
2. **Leader natal chart:** a separate individual chart; it is not a proxy for the country or population.
3. **Timing:** the same user-defined forecast interval is applied to both chart engines where available.
4. **Concordance:** overlaps are listed with date, country event class and activation metadata. They are not called a validated probability, and no absence of overlap is treated as proof of weakness.
5. **Birth-data provenance:** selected profile source and time-status are displayed. If the time is unknown, noon is a computational reference only.
6. **Personal life domains:** career/business use existing D10 and 6th/10th/11th-house layers; spouse/relationship uses existing D9 and 7th-house layers; court/dispute questions direct the reader toward 6th/8th/9th/12th factors and D6/D30 when available; sibling questions use D3 and 3rd/11th-house factors where generated. No single placement or Yoga/Dosha is treated as sufficient by itself.

### Calibration rules

- Keep exact interpretation deduplication separate from genuine combinations. A rule's source, key and factor requirements must remain stable.
- Birth time confidence is a provenance field, not a score of astrological accuracy. Avoid precise Lagna/Varga claims where the time is not verified.
- Do not convert the leader's individual chart strength into a deterministic claim about government strength, policy competence, war result or public support.
- For future predictive validation, freeze event taxonomy and thresholds before the holdout. Report precision, recall, false-positive rate, class-level confusion matrix and the dates actually forecast. Do not tune on the blind holdout.
- Political/territorial/war event classes remain conditional astrological scenarios; they are not factual assertions or deterministic geopolitical forecasts.

## Data-quality policy

Public-figure profiles include `source` and `time_status`. For new profiles, capture source URL/title, access date, whether date and time are independently sourced, time-zone conversion, coordinates provenance, and a confidence class. Never fabricate a birth time. Unknown/approximate times should not be silently promoted to verified. For leader chart interpretation, report the uncertainty before discussing house or divisional-chart details.

## Deployment plan

### Local / staging

1. Back up the existing application directory and data folder.
2. Unzip this release into a fresh directory; do not overwrite a live directory in place.
3. Create a virtual environment and install `requirements.txt`.
4. Copy `.env.example` to `.env` only if needed; keep secrets outside source control.
5. Run `python -m compileall app`, `node --check static/app.js`, and `pytest -q`.
6. Start with `uvicorn app.main:app --host 127.0.0.1 --port 8000` and verify `/`, `/api/library`, and a country request without a leader, with a database leader, and with custom leader details.
7. Verify custom period start/end are identical in the country and leader overlay, and that unknown-time leaders are visibly labelled.

### Production

1. Deploy to a staging environment first and retain the prior ZIP as a rollback artifact.
2. Configure process supervision (systemd, Docker Compose, or platform equivalent), TLS termination, request-size/time limits and log rotation.
3. Keep profile provenance and user-entered birth data out of public logs. Do not expose raw custom details in analytics.
4. Smoke-test country-only mode, saved leader mode, custom leader mode, invalid/missing coordinates, invalid timezone, unknown time, and custom date window.
5. Promote only after full regression tests pass; monitor exceptions and slow calculations. Roll back to the previous release if the new endpoint causes repeated 4xx/5xx or unacceptable latency.
6. Schedule a separate historical blind-validation run before making any accuracy claims.

## Known limitations

- The leader overlay is a first calibrated integration layer, not a validated model of government effectiveness.
- The current concordance display is date-overlap based; it does not calculate an empirically trained joint probability.
- Some reference profiles have unknown birth times and are only suitable for date-based planetary context, not reliable house/Varga analysis.
- The full test suite must be run in the deployment environment; targeted syntax and regression checks are not equivalent to full acceptance testing.

## Research references

- Astro-Databank, “Help: RR” — definitions of Rodden data ratings and explicit warnings about unknown/uncertain birth times: https://www.astro.com/astro-databank/Help:RR
- Astro-Databank overview — birth data source notes and rating system: https://en.wikipedia.org/wiki/Astrodatabank
- National chart technique overview (practitioner source; useful for documenting the tradition, not evidence of predictive validity): https://kerykeion.net/content/learn-astrology/mundane-national-charts
- Mundane/national chart practice overview and founding-moment uncertainty (practitioner source): https://astroleg.com/the-astrology-of-nations-how-countries-reflect-cosmic-archetypes/

These references describe astrological practice and birth-data provenance. They do not establish that astrology can reliably predict political outcomes.
