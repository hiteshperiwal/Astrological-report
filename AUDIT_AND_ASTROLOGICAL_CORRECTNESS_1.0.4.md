# Jyotish Lab 1.0.4 — adversarial audit and astrological correctness report

## Scope and method

This audit reviewed the 1.0.3 project archive, source code, existing tests, calculation formulas, event/interpretation corpora, custom-period API paths and UI request wiring. It combines deterministic unit/regression tests, adversarial schema inputs, boundary tests and a manual traditional-method review. It is not a claim that astrological interpretation has been scientifically validated.

## Bugs found and corrected in this build

1. **D30 (Trimshamsha) even-sign boundary mapping.** The Cancer/Taurus/etc. even-sign bands used 5°, 12°, 20°, 25°, 30° instead of the commonly used Parashari 5°, 10°, 18°, 25°, 30° thresholds. This changed placements for portions of the 5°–25° range. The boundaries are corrected and now have tests immediately below/at each transition.
2. **False-positive Sunapha/Anapha Yoga.** The detector could treat the Sun alone in the 2nd/12th sign from the Moon as satisfying a yoga whose rule excludes the Sun. The detector now checks for at least one qualifying non-Sun graha after exclusion.
3. **Impossible dates and clock times accepted by request schemas.** `2001-02-30` and `25:99` passed regex-only validation. Calendar dates and 24-hour times are now parsed and rejected when invalid.
4. **Reversed custom date windows accepted at the API boundary.** Personal and mundane request models now reject reversed ranges and incomplete start/end pairs. Same-day windows are allowed (the forecast engine uses the full local day).
5. **Personal chat silently ignored custom forecast dates.** The cached chart builder omitted `forecast_start_date`/`forecast_end_date`, and its cache key therefore did not distinguish custom periods. Both values are now passed to the calculation and included in the cache key.
6. **Slow corpus fallback lookup and repeated counting.** Missing corpus keys previously scanned the full 135k-key index repeatedly, and rule counts were recomputed over the full corpus for each narrative. A prefix index and cached type counts now avoid those repeated full scans.
7. **Misleading strength labels.** The Shadbala calculation is a simplified six-component screening estimate, not a full canonical Shadbala implementation. Its method/note now disclose this. The Ashtakavarga BAV/SAV contributor tables remain available, but the sign-level shodhana/pinda reduction is explicitly labelled provisional rather than a canonical graha-wise shodhana result.

## Adversarial tests added

- Invalid calendar date and impossible time.
- Reversed and invalid custom forecast windows.
- Same-day country forecast window.
- Incomplete custom-leader payload.
- D30 threshold edges at 5°, 10°, 18° and 25°.
- Sunapha/Anapha exclusion of the Sun.
- Personal chat chart-cache propagation of custom dates.

Targeted run at build time: **21 passed** across adversarial validation, UI sections, custom forecast windows and country/leader synthesis.

## Astrological/technical correctness findings

### Astronomical layer

- Swiss Ephemeris is used for sidereal planetary positions with Lahiri ayanamsha; whole-sign houses are then calculated from the sidereal ascendant. This is a coherent declared convention, but house systems/ayanamsha choices must remain explicit because other software may use different settings. See the [Swiss Ephemeris programmer documentation](https://www.astro.com/swisseph/swephprg.htm).
- D1/D9 regression fixture remains: 6 Feb 2001, 17:57 IST, supplied coordinates 28.8777942 N / 74.0633619 E, Lahiri; Saturn is in Capricorn in D9, with Capricorn D9 Lagna and Saturn in D9 house 1.
- Unknown or rounded birth times remain a major source of uncertainty for Lagna, houses and Vargas. Astro-Databank describes source-based Rodden ratings and cautions that a rating is about provenance/reliability, not an absolute guarantee. See [Rodden rating guidance](https://www.astro.com/astro-databank/Help:RR).

### Traditional interpretation layer

- **Vimshottari Dasha:** recursive subperiod sequence starts from the parent lord; it is a coherent implementation of the 120-year cycle, but exact day counts depend on year-length convention and date/time handling. It should be cross-checked against a named reference implementation before claiming universal parity.
- **Vargas:** the app calculates 16 named charts, but not every divisional mapping is universally agreed across schools. D30 was corrected here; D40/D45/D60 and several higher Vargas still require cross-validation against a named, versioned reference dataset. D60 is especially sensitive to birth-time uncertainty.
- **Yogas/Doshas:** the detector is a rule-screening catalogue, not an exhaustive classical adjudicator. Many yogas need cancellation rules, benefic/malefic condition, combustion/war/strength, house-lord context and school-specific exceptions. A detected name should be interpreted as “screen-positive” unless all required conditions are implemented. The audit fixed one known exclusion error but does not certify every yoga definition.
- **Shadbala:** the six headings are present, but the components are approximations. The UI/report now disclose that fact rather than implying canonical strength scoring.
- **Ashtakavarga:** the seven BAV contributor tables are present. The separate legacy `ashtakavarga` output is an approximation, and the reduction/pinda path in `classical_ashtakavarga` is not yet a fully canonical graha-wise implementation. Do not present the reduction results as reference-equivalent until cross-validated.
- **Day/night dependent calculations:** some day/night choices use clock hour (before 06:00 or from 18:00) instead of computed local sunrise/sunset. This is not adequate for high-latitude or seasonally extreme cases; sunrise/sunset should be used in a future calculation-layer update.
- **Planetary aspects and combustion:** aspect/orb rules are simplified and fixed-orb; classical schools can differ. Combustion is not a universal binary switch and can depend on planet, motion and school conventions.
- **Jaimini/Tajaka/specialty layers:** the UI can offer multi-school synthesis, but this is not equivalent to a complete implementation of all Chara Dasha, Argalā, Jaimini aspects, Tajaka annual techniques, Prashna, KP sublords, Nadi, Sahams and other specialist methods.

### Interpretation corpus

- `interpretation_corpus.json` has 135,303 materialized entries (~82.7 MB). Runtime metadata multiplies this by 720 and can therefore display 97,418,160 virtualized combinations; the older test only asserted a lower bound of 853,200. Neither figure represents independently researched or astrologically validated rules. Many entries are controlled paraphrases over a finite rule skeleton, and exact-text deduplication does not remove semantic near-duplicates.
- `mundane_event_combinations.json` has 34,996 entries, but only 58 distinct text templates and repeated combinations per event class. The combinatorial count must not be described as that many independently sourced interpretations.
- Historical event rows frequently include date-only/noon proxies, as documented in `app/mundane.py`. Such records can support broad slow-planet analogue exploration, but they are not precise event charts and can inflate apparent matches when event definitions or windows are broad.

## Remaining priority backlog

### P0 — before calling the app astrologically reference-accurate

1. Cross-check planetary positions, Ascendant, D1, all 16 Vargas, Vimshottari MD/AD/PD, Shadbala and Ashtakavarga against a pinned reference dataset from a named software/version under the same Lahiri and calculation conventions.
2. Implement complete canonical Shadbala subcomponents or rename all dependent outputs as approximate screening metrics consistently in UI/PDF/API.
3. Implement BAV-wise Trikona Shodhana, Ekadhipatya Shodhana and pinda calculations against a verified worked example/reference, with tests for exceptions.
4. Compute sunrise/sunset for day/night-sensitive calculations and add DST/historical timezone regression cases.
5. Build a yoga rule registry with sources, prerequisites, exclusions, cancellation rules, school tags and confidence labels; test every rule with positive and negative fixtures.
6. Audit all divisional mapping boundaries (D2/D3/D4/D7/D9/D10/D12/D16/D20/D24/D27/D30/D40/D45/D60), including exact boundary values and random positions against a reference implementation.

### P1 — forecast quality and data governance

1. Evaluate event forecasts on a pre-registered, chronological holdout with one-to-one event matching, base-rate controls, precision, recall, false-positive rate, lead-time and abstention metrics. Keep the threshold frozen on blind data.
2. Add source URL, source date, birth-data reliability grade, event-time precision and uncertainty metadata to every reference profile/event. Quarantine uncertain times from Lagna/Varga validation.
3. Distinguish a *calculated astronomical event* (eclipse/ingress) from an *astrological interpretation* and from a *real-world event forecast* in API and UI.
4. Do not describe market, conflict, leadership, legal or health event classes as verified predictions absent independent prospective evidence.
5. Replace broad catch-and-continue paths with structured warnings where they can silently omit sections; add payload-size and latency tests for long horizons and large corpora.

### P2 — completeness

- Add school-specific configurations for Parashari, Jaimini, Tajaka/Varshaphala and optional KP rather than presenting a single blended engine as complete coverage.
- Add full Chara Dasha variants, Argalā, Jaimini aspects, annual-chart yogas, Sahams and relevant dasha systems only with reference fixtures.
- Add reproducible chart snapshots with engine version, ephemeris version, timezone database version, ayanamsha, house convention and calculation settings.
- Add randomized/property-based tests for longitude normalization, sign/house consistency, period ordering, input bounds, serialization and output determinism. Hypothesis is an appropriate tool for this; see [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/).

## Empirical calibration boundary

Astronomical calculations can be checked against ephemerides and other software. Astrological meanings and predictions require a different kind of evaluation. Controlled tests have been published, including Carlson's 1985 double-blind study in *Nature* ([paper](https://www.nature.com/articles/318419a0)); that literature is contested, so it should be represented fairly, not treated as proof for or against every Jyotish method. This build validates code invariants and fixes identified rule bugs; it does **not** establish that astrological event forecasts are empirically reliable.

## Deployment gate

1. Install dependencies from `requirements.txt` in a clean environment.
2. Run `python -m py_compile app/*.py` and `node --check static/app.js`.
3. Run targeted tests: `pytest -q tests/test_adversarial_validation.py tests/test_ui_sections.py tests/test_custom_forecast_windows.py tests/test_leader_country_synthesis.py`.
4. Run the full suite with an explicit timeout and collect per-test durations; do not treat timeout as a pass.
5. Smoke-test `/api/health`, personal analyze/chat with and without custom ranges, country forecast with same-day/reversed ranges, leader chart overlay, PDF export, and D9 fixture.
6. Compare a fixed set of natal charts and boundary positions against the pinned reference calculator before production release.
7. Deploy to staging, preserve previous build and data files, validate logs and payload size, then promote. Roll back the archive if D1/D9/D30 or date-window smoke tests regress.

## Final test-run status

- Python compilation: passed.
- JavaScript syntax check: passed.
- Adversarial/schema/UI/custom-period/leader-synthesis targeted group: **20 passed**.
- Additional D9 regression, Varga assignment, long-horizon prediction, yoga interpretation and corpus regression group: passed in targeted runs (19-test group: **19 passed**).
- Full combined suite: reached **57 passing tests before the execution timeout**, without reporting an assertion failure. The combined process did not finish; this is not recorded as a full-suite pass. The remaining high-cost tests passed in targeted subsets, but a complete CI run in a less constrained environment is still a release gate.
- Live health endpoint smoke test: `/health` returns `status=ok` and version `1.0.4`.

## Current conclusion

This release fixes confirmed code defects and makes several approximation boundaries explicit. The most important remaining issue is not missing interpretation volume; it is reference-equivalent calculation coverage and blind empirical forecast evaluation. The next work should prioritize correctness fixtures and canonical subcomponent calculations rather than increasing the nominal number of corpus combinations.
