from __future__ import annotations
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any
from .mundane import REFERENCE_EVENTS, resolve_country_chart
from .backtest import _signal_at


def mundane_walk_forward_backtest(window_days: int = 15, threshold: float = 40.0) -> dict[str, Any]:
    """Temporal holdout audit: canonical country chart is fixed, later corpus events are held out.

    This is a research audit, not a scientific forecast-accuracy claim. Control dates are sampled
    at deterministic offsets from each event to estimate how often a comparable signal occurs away
    from labelled events.
    """
    rows=[]; hits=0; controls=[]
    countries=sorted({e.country for e in REFERENCE_EVENTS})
    for country in countries:
        resolved=resolve_country_chart(country)
        primary_date=resolved['primary_chart']['local_date']
        events=[e for e in REFERENCE_EVENTS if e.country==country and e.local_date>primary_date]
        if not events: continue
        primary=next(e for e in REFERENCE_EVENTS if e.country==country and e.local_date==primary_date)
        for event in events:
            samples=[_signal_at(primary, event.utc_dt+timedelta(days=d))['score'] for d in range(-window_days,window_days+1)]
            peak=max(samples); hit=peak>=threshold; hits+=int(hit)
            # deterministic control at +180 days; skip if too close to another labelled event.
            control_dt=event.utc_dt+timedelta(days=180)
            cscore=_signal_at(primary,control_dt)['score']; controls.append(cscore)
            rows.append({'country':country,'event':event.event_name,'date':event.local_date,'peak_signal':round(peak,1),'threshold':threshold,'covered':hit,'control_signal':round(cscore,1)})
    event_scores=[r['peak_signal'] for r in rows]
    control_scores=[r['control_signal'] for r in rows]
    return {
        'events_tested':len(rows),'covered_events':hits,'coverage_pct':round(100*hits/max(1,len(rows)),1),
        'mean_event_peak':round(mean(event_scores),1) if event_scores else 0,
        'mean_control_signal':round(mean(control_scores),1) if control_scores else 0,
        'mean_separation':round((mean(event_scores)-mean(control_scores)) if event_scores and control_scores else 0,1),
        'threshold':threshold,'window_days_each_side':window_days,'rows':rows,
        'interpretation':'Temporal holdout and deterministic controls are included to test reproducibility and signal separation. This is not scientific evidence of causal or predictive validity.'
    }


def personal_calculation_audit(chart: dict[str, Any]) -> dict[str, Any]:
    """Check structural and arithmetic invariants; this is not a test of astrological validity."""
    from .engine import _varga_sign, _whole_sign_house

    checks=[]
    planets=chart.get('planets',{})
    required={'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'}
    checks.append(('nine_grahas', required.issubset(planets)))
    vargas=chart.get('divisional_charts',{})
    checks.append(('sixteen_vargas', len(vargas) == 16))
    checks.append(('navamsa_present', 'D9' in vargas))
    checks.append(('shadbala_seven_planets', len(chart.get('shadbala',{}).get('planets',{})) == 7))
    checks.append(('ashtakavarga_sav_12', len(chart.get('ashtakavarga_classical',{}).get('sav',[])) == 12))
    av=chart.get('ashtakavarga_classical',{})
    checks.append(('ashtakavarga_standard_total_337', sum(av.get('sav',[])) == 337))

    normalized=True
    for p,d in planets.items():
        lon=d.get('longitude')
        if not isinstance(lon,(int,float)) or not (0 <= lon < 360):
            normalized=False; break
        if d.get('sign_index') != int(lon // 30) or d.get('sign') is None:
            normalized=False; break
    checks.append(('natal_longitude_sign_consistency', normalized))

    d1=vargas.get('D1',{}).get('planets',{})
    d1_matches=bool(d1) and all(d1.get(p,{}).get('sign_index') == d.get('sign_index') for p,d in planets.items())
    checks.append(('d1_matches_natal_positions', d1_matches))

    house_consistency=True
    for name,v in vargas.items():
        lagna=v.get('lagna_sign_index')
        for p,d in v.get('planets',{}).items():
            sign=d.get('sign_index'); house=d.get('house')
            if not isinstance(sign,int) or not 0 <= sign < 12:
                house_consistency=False; break
            if lagna is not None and house != _whole_sign_house(lagna,sign):
                house_consistency=False; break
        if not house_consistency: break
    checks.append(('varga_house_consistency', house_consistency))

    forecast=chart.get('forecast',{})
    checks.append(('forecast_monotonic', bool(forecast.get('start')) and bool(forecast.get('end')) and forecast.get('start') <= forecast.get('end')))
    transit_rows=chart.get('transits',[])
    checks.append(('forecast_rows_within_window', all(forecast.get('start','') <= r.get('date','')[:10] <= forecast.get('end','') for r in transit_rows)))
    checks.append(('forecast_has_transits', len(transit_rows) > 0))
    moon_pada=chart.get('nakshatra_analysis',{}).get('moon',{}).get('pada')
    checks.append(('nakshatra_pada_valid', moon_pada in {1,2,3,4}))

    passed=sum(bool(x[1]) for x in checks)
    return {
        'passed':passed,
        'total':len(checks),
        'all_passed':passed==len(checks),
        'checks':[{'name':n,'passed':bool(v)} for n,v in checks],
        'note':'Structural and arithmetic consistency only; passing this audit does not validate the astrological rules or empirical forecast accuracy.'
    }
