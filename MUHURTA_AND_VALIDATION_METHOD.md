# Jyotish Lab 1.0.5 — calculation validation and personalized Muhurta

## Scope

This release implements a personalized, date-range-based electional timing screen and extends the calculation-validation harness. It does **not** claim that astrological readings have scientifically demonstrated predictive accuracy. “Precision” here means numerical/timezone correctness, deterministic behavior, explicit rule provenance, and agreement with a declared tradition/reference where a fixture exists.

## Research basis and conventions

- Swiss Ephemeris programmer documentation: https://www.astro.com/swisseph/swephprg.htm
- Swiss Ephemeris sidereal/ayanamsha documentation: https://www.astro.com/swisseph/swisseph.htm
- PyJHora reference project and test notes: https://github.com/naturalstupid/PyJHora
- PyJHora Ashtakavarga implementation notes: https://github.com/naturalstupid/PyJHora/blob/main/src/jhora/horoscope/chart/ashtakavarga.py
- Shadbala components and unit conventions overview: https://parasara.net/calculators/shadbala
- Birth-time provenance / Rodden Rating: https://www.astro.com/astro-databank/Help:RR

These references serve different purposes. Swiss Ephemeris validates astronomical positions/time handling; PyJHora is a useful independent Jyotish reference implementation whose method settings must be matched; astrological tradition sources document rule conventions, not empirical proof that forecasts cause or reliably predict outcomes.

## Calculation validation strategy

1. Keep Lahiri sidereal mode explicit before sidereal calculations; do not depend on Swiss Ephemeris' default ayanamsha.
2. Use timezone-aware local civil time and convert to UTC before Julian-day calculation.
3. Validate real Gregorian dates, 24-hour times, IANA timezone names, coordinate ranges, and ordered/limited search intervals.
4. Preserve the established D9 regression fixture (2001-02-06 17:57 Asia/Kolkata; Capricorn D9 ascendant and Saturn in Capricorn / D9 house 1).
5. Exercise divisional-chart boundary cases immediately below/on/above boundaries; D30 uses unequal classical bands and sign-parity-specific mapping.
6. Check yoga exclusion logic and custom-date propagation/caching.
7. Muhurta smoke tests check local sunrise/set date, 8-fold weekday segment tables, valid Panchanga ranges, deterministic output, optional natal-Moon personalization, and range/activity validation.
8. Forecast backtests must be chronological, avoid future-event leakage, use one-to-one event matching, and report precision, recall, false positives and coverage separately. Do not optimize on the blind holdout or represent event-corpus coverage as predictive accuracy.

## Personalized Muhurta feature

Endpoint: `POST /api/muhurta/search`

Supported activity profiles: puja/spiritual practice, job joining, property purchase, property sale, business opening, major expense/payment, property registration/legal signing, travel start, and beginning study/exam preparation.

Request fields: `activity`, `start_date`, `end_date`, `latitude`, `longitude`, `timezone`; optional `natal_dob`, `natal_tob`, and `natal_timezone` enable Tara Bala and Chandra Bala screens. The search period is limited to 90 days. The current UI defaults to Kolkata and allows coordinates/timezone to be edited; users must choose the actual event location.

Each candidate includes local start/end, score, Tithi/Paksha, Nakshatra/Pada, Nitya Yoga, Karana, sunrise/sunset, supporting rules and conflicts. Daylight Rahu Kalam, Yamaganda and Gulika segments are screened using weekday-specific eight-part tables. The displayed score is a weighted heuristic score from an explicit rule screen, **not a probability** and not a universal classical ranking. Regional panchanga conventions and activity-specific rules differ; the app avoids claiming a universal muhurta.

Personalization currently uses the natal Moon longitude for Tara Bala and Chandra Bala. It does not yet calculate a complete event-specific Muhurta Lagna, full Panchaka, regional Masa/Amanta-Purnimanta constraints, Abhijit/Madhyahna exceptions, or all tradition-specific do's/don'ts. The interface names these limitations rather than implying they were calculated.

## Shadbala and Ashtakavarga status

Shadbala remains explicitly labelled as a simplified six-component screening estimate, not canonical Shadbala. A canonical replacement requires the full component set (including Sthana subcomponents, complete Kala components, motion/war conventions, and Drik Bala rules) and pinned examples for a declared school/source. A partial rewrite would be more dangerous than a visible limitation.

Ashtakavarga BAV/SAV now uses the contributor-to-target-sign relationship correctly (the prior code incorrectly held the target sign fixed across the twelve output signs). Graha-wise Trikona Shodhana, Ekadhipatya Shodhana and per-graha Shodhya Pinda are now implemented with explicit BPHS/PVR-style assumptions and a standard 337-SAV-total invariant. This is a substantial correction, but the exact Pinda values still need to be compared against a pinned published chart fixture under the same occupied-sign rules and Virgo rasimana multiplier before calling every output canonical.

## Run and deploy

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Before production deployment:

1. Back up the current application and data folder.
2. Deploy to staging and run the full test suite, `/health`, `/api/personal/analyze`, `/api/muhurta/search`, and `/api/mundane/analyze` smoke tests.
3. Check that app/static version labels agree with the server version.
4. Run the D9 regression fixture and independent ephemeris comparison for several dates, latitudes, timezones, and dates near midnight.
5. Validate local sunrise/set against a trusted panchanga for the chosen city and selected ayanamsha.
6. Review candidate muhurta output manually for each activity profile before real ceremonial use.
7. Promote only if all staging checks pass; retain the previous ZIP for rollback.

## Known limitations

- A high muhurta score does not mean an event will succeed.
- The present rule weights are transparent engineering choices, not learned or statistically calibrated parameters.
- No guarantee is made for legal, financial, health or safety outcomes; those require domain expertise and practical constraints.
- The complete test suite is necessary for release acceptance; targeted tests alone are insufficient.
