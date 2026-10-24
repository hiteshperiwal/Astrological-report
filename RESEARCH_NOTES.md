# Research & verification notes

This project separates **astronomical calculation** from **astrological interpretation**.

## Verified technical backbone

### Swiss Ephemeris / pyswisseph

The astronomical layer uses Swiss Ephemeris through `pyswisseph`. The upstream project documents long-term ephemerides and describes precision in comparison with Astronomical Almanac standards. The upstream license notice is a dual-license model: AGPL-3.0 or the Swiss Ephemeris Professional License. `pyswisseph` itself adopts AGPL-3.0 and points back to the Swiss Ephemeris license for the underlying library.

Source references:

- https://github.com/aloistr/swisseph/blob/master/LICENSE
- https://github.com/astrorigin/pyswisseph/blob/master/README.rst
- https://github.com/astrorigin/pyswisseph/blob/master/docs/introduction.rst

### Sidereal / house computations

Swiss Ephemeris exposes house calculations and sidereal house conversion. This project explicitly sets Lahiri ayanamsha and then performs Jyotish whole-sign house analysis from the computed sidereal ascendant.

Source references:

- https://github.com/aloistr/swisseph/blob/master/swehouse.c
- https://github.com/astrorigin/pyswisseph/blob/master/docs/programmers_manual/house_cusp_calculation.rst

## Feature coverage cross-check

Contemporary open-source Jyotish projects were used as feature checklists, not as code dependencies:

- `vedic-calc` lists D1–D60 coverage, Vimsottari dasha, Sahams, yogas/doshas, Ashtakavarga, Panchanga, Jaimini, Tajaka, KP and other modules.
  - https://github.com/atolat/vedic-calc
- `dashaflow` lists Lahiri sidereal calculations, D2–D60, 5-level Vimshottari, Shadbala, Ashtakavarga, Jaimini and yoga families.
  - https://github.com/adarshj322/dashaflow
- `PyJHora` documents broad Jyotish coverage including Sahams, divisional charts, doshas, yogas and transit/Tajaka modules.
  - https://github.com/naturalstupid/PyJHora

## Sahams

Saham formulas are known to vary by school. The current engine includes a transparent subset and surfaces that the formulas are school-dependent rather than treating them as universal.

A checked reference example for Punya, Vidya, Yasas, Mitra and related Sahams is the PyJHora transit Saham documentation:

- https://github.com/naturalstupid/PyJHora/blob/main/src/jhora/horoscope/transit/README.md

## What is deliberately not claimed

1. The app does not claim astrology is scientifically validated.
2. A computed transit/dasha window is not an objective event prediction.
3. Dosha and yoga detection can differ across classical schools and software implementations.
4. The current release is not a full implementation of every Jaimini, Tajaka, KP, Nadi, Ashtakoota and specialty chart calculation.
5. The current Ashtakavarga layer is a reproducible screening matrix, not a claim of universal canonical scoring.
6. D30/D40/D45/D60 and other specialized varga conventions can differ; the code isolates these mappings for replacement with a chosen school-specific table.

## Validation performed in this build

- Python compilation: passed.
- Engine tests: 4/4 passed.
- Live FastAPI health endpoint: passed.
- Live `/api/analyze` smoke test: passed for a Kolkata example; returned D1/D9 data, 16 divisional charts and five-year timing output.


## 1.0.4 audit update

The adversarial audit corrected even-sign D30 boundaries, Sunapha/Anapha exclusion logic, request-date/time validation, and personal-chat custom-date cache propagation. It also relabelled the current Shadbala and Ashtakavarga reduction outputs as approximations where their formulas are not canonical. See `AUDIT_AND_ASTROLOGICAL_CORRECTNESS_1.0.4.md` for the full correctness findings, research sources and prioritized backlog.
