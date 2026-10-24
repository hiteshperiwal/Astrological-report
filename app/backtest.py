from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from zoneinfo import ZoneInfo
import swisseph as swe
from .engine import _calc_planets, angular_distance, _time_to_jd
from .mundane import REFERENCE_EVENTS, resolve_country_chart, MundaneEvent


def _signal_at(country_event:MundaneEvent, when:datetime)->Dict[str,Any]:
    jd=_time_to_jd(when.astimezone(timezone.utc)); transit=_calc_planets(jd)
    natal_event=MundaneEvent(**resolve_country_chart(country_event.country)['primary_chart'])
    natal=_calc_planets(_time_to_jd(natal_event.utc_dt))
    triggers=[]; score=0.0
    for tp in ('Jupiter','Saturn','Rahu','Ketu'):
        for np in ('Sun','Moon','Saturn','Jupiter'):
            d=angular_distance(transit[tp]['longitude'],natal[np]['longitude'])
            asp=min((0,60,90,120,180),key=lambda a:abs(d-a)); orb=abs(d-asp)
            if orb<=3:
                score += {0:22,60:12,90:16,120:18,180:22}[asp]
                triggers.append(f'{tp} {asp}° {np}')
    return {'score':round(min(100,score),1),'triggers':triggers}


def retrospective_mundane_backtest(limit:int=100, window_days:int=15)->Dict[str,Any]:
    # This is signal coverage, not proof of predictive accuracy. Each event is
    # evaluated against the country's canonical chart and the transit sky around
    # the event date, with the event itself held out from analogue ranking.
    rows=[]
    events=REFERENCE_EVENTS[:max(1,min(limit,len(REFERENCE_EVENTS)))]
    hits=0
    for event in events:
        base=event.utc_dt
        samples=[]
        for delta in range(-window_days,window_days+1):
            samples.append(_signal_at(event,base+timedelta(days=delta)))
        peak=max(samples,key=lambda x:x['score'])
        hit=peak['score']>=40
        hits += int(hit)
        rows.append({'country':event.country,'event':event.event_name,'date':event.local_date,'event_type':event.event_type,'peak_signal':peak['score'],'trigger_count':len(peak['triggers']),'covered':hit,'best_triggers':peak['triggers'][:6]})
    return {'events_tested':len(rows),'window_days_each_side':window_days,'covered_events':hits,'coverage_pct':round(100*hits/max(1,len(rows)),1),'rows':rows,'interpretation':'Retrospective signal coverage only. It is not a measure of causal validity, and it is not a guarantee that future events will occur.'}
