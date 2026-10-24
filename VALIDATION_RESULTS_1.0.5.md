# Jyotish Lab 1.0.5 — validation results

## Automated checks

- `pytest -q --disable-warnings --maxfail=1`: **89 passed** (25.4 seconds in the final full run before packaging).
- `node --check static/app.js`: passed.
- `python -m py_compile app/*.py scripts/*.py scripts_run_validation.py`: passed.
- FastAPI `TestClient` smoke test: `/health` returns version `1.0.5`; personalized `/api/muhurta/search` returns 200 for a valid request and 422 for a period exceeding 90 days.
- Muhurta exploratory checks: Kolkata, London, New York and Sydney sunrise/set local dates; weekday Rahu Kalam/Yamaganda/Gulika tables; Panchanga label ranges; deterministic response; optional natal-Moon personalization; 90-day boundary; interval clipping at discrete Panchanga/daylight-segment transitions.
- Muhurta runtime probe: 1-day search ~0.01 s, 14-day ~0.11 s, 90-day ~0.71 s in this execution environment (indicative only).
- Chart regressions: established D9 fixture, all 16 principal Vargas, D30 unequal division boundaries, Vimshottari hierarchy, yoga logic, custom forecast ranges and mundane leader overlays.
- Ashtakavarga regression: BAV/SAV contributor table totals are now invariant at **337** for the selected standard seven-graha contributor tables; Trikona/Ekadhipatya reductions and per-graha Pinda arithmetic are tested.

## Historical mundane replay

The bundled strict chronological replay script completed using the frozen holdout split and did not reach the desired 80% precision target:

| Country / blind period | Threshold selected on development data | Blind predictions | Correct matches | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Israel, 2024–2026 | 60 | 9 | 3 | 33.3% | 42.9% | 37.5% |
| India, 1990–1999 | 95 | 20 | 1 | 5.0% | 20.0% | 8.0% |

Matched examples recorded by the report:
- Israel: 13 April 2024 Iran attack → `border_clash`.
- Israel: 17 September 2024 Hezbollah pager explosions → `terror_attack`.
- Israel: 8 June 2026 renewed Israel-Iran strikes → `border_clash`.
- India: 3 May 1999 Kargil War begins → `border_clash`.

These are exact-class matches to the bundled corpus, not evidence that the system would have communicated the precise event/date in a real forecast. The low precision, particularly for India, means the event-class engine is not calibrated for dependable operational prediction. The report must not be tuned after seeing holdout results and then still called blind.

## Findings and remaining gates

1. **Ashtakavarga**: corrected a material sign-loop defect; graha-wise reduction logic now uses explicit BPHS/PVR-style conventions. Independent pinned examples are still needed to confirm every Pinda result across schools.
2. **Shadbala**: remains a simplified screening estimate, not a canonical six-bala implementation. The UI and PDF explicitly disclose this.
3. **Muhurta**: calculations and rule screens are tested for numerical/timezone integrity. Activity-specific weighting is a documented tradition-based heuristic, not a statistically calibrated score. It omits some region- and lineage-specific requirements, and a qualified local Panchanga should be consulted for ceremonies with strict local rules.
4. **Predictive validity**: no forecast precision target is claimed. The current mundane blind results are below target; no tuning has been done to force 80%.
5. **Release acceptance**: the complete automated suite passed. Production rollout should still use the documented staging smoke tests, compare a sample of chart and Panchanga outputs against a pinned external reference under matching settings, and retain the prior ZIP for rollback.
