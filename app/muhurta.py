"""Rule-transparent, personalized Vedic muhurta screening.

This is an electional-astrology rule screen, not an empirically validated outcome predictor.
All times are computed in the requested location/timezone with Swiss Ephemeris and Lahiri.
"""
from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any
import math
import swisseph as swe

from .engine import _time_to_jd, norm360, nakshatra_details, NAKSHATRAS

TITHI_NAMES = ["Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Purnima/Amavasya"]
YOGA_NAMES = ["Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma","Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"]
KARANA_NAMES = ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti (Bhadra)"]
WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
RAHU_SEGMENT = {0:2,1:7,2:5,3:6,4:4,5:3,6:8} # Python weekday: Monday=0
YAMAGANDA_SEGMENT = {0:4,1:3,2:2,3:1,4:7,5:6,6:5}
GULIKA_SEGMENT = {0:6,1:5,2:4,3:3,4:2,5:1,6:7}

ACTIVITIES: dict[str, dict[str, Any]] = {
 "puja": {"label":"Specific puja / spiritual practice", "good_tithi":[1,2,3,5,7,10,11,12,13,15], "good_nak":[0,3,4,7,12,13,16,20,21,23,24,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "job_start": {"label":"Start a new job / joining", "good_tithi":[2,3,5,6,7,10,11,12,13], "good_nak":[3,4,7,12,13,16,20,21,22,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "property_buy": {"label":"Purchase property", "good_tithi":[2,3,5,6,7,10,11,12,13], "good_nak":[3,4,7,12,13,16,20,21,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "property_sell": {"label":"Sell property", "good_tithi":[2,3,5,6,7,10,11,12,13], "good_nak":[2,5,8,9,14,17,18,23], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "business_start": {"label":"Launch a business / open a shop", "good_tithi":[2,3,5,6,7,10,11,12,13], "good_nak":[3,4,7,12,13,16,20,21,22,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "expense": {"label":"Major expense / payment", "good_tithi":[2,3,5,6,10,11,12,13], "good_nak":[3,4,7,12,13,16,20,21,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "property_legal": {"label":"Property registration / legal signing", "good_tithi":[2,3,5,6,7,10,11,12,13], "good_nak":[3,4,7,12,13,16,20,21,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "travel": {"label":"Begin travel", "good_tithi":[2,3,5,7,10,11,13], "good_nak":[0,3,4,7,12,13,16,20,21,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[5,8,17,18]},
 "education": {"label":"Begin study / exam preparation", "good_tithi":[2,3,5,6,10,11,12,13], "good_nak":[3,4,5,12,13,16,20,21,24,25,26], "avoid_tithi":[4,8,9,14], "good_yoga":[1,2,3,4,5,7,8,11,12,14,16,18,20,21,22,23,24,25,26], "avoid_nak":[8,17,18,23]},
}

def _sidereal_sun_moon(jd: float) -> tuple[float,float]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags=swe.FLG_SWIEPH|swe.FLG_SIDEREAL
    sun=swe.calc_ut(jd,swe.SUN,flags)[0][0]; moon=swe.calc_ut(jd,swe.MOON,flags)[0][0]
    return norm360(sun),norm360(moon)

def _panchanga(jd: float) -> dict[str,Any]:
    sun,moon=_sidereal_sun_moon(jd); elong=norm360(moon-sun); phase=int(elong//12)+1
    paksha="Shukla" if phase<=15 else "Krishna"; tithi_num=phase if phase<=15 else phase-15
    yoga_num=int(norm360(sun+moon)//(360/27))+1
    karana_idx=int(elong//6); karana = "Kimstughna" if karana_idx==0 else ("Shakuni" if karana_idx==57 else "Chatushpada" if karana_idx==58 else "Naga" if karana_idx==59 else KARANA_NAMES[(karana_idx-1)%7])
    nak=int(moon//(360/27)); nak_name=NAKSHATRAS[nak]
    return {"sun":sun,"moon":moon,"elongation":elong,"tithi_number":tithi_num,"tithi":TITHI_NAMES[tithi_num-1],"paksha":paksha,"yoga_number":yoga_num,"yoga":YOGA_NAMES[yoga_num-1],"karana":karana,"nakshatra_index":nak,"nakshatra":nak_name,"nakshatra_pada":int((moon%(360/27))/(360/108))+1}

def _sunrise_sunset(local_day: date, lat: float, lon: float, tzname: str) -> tuple[datetime|None,datetime|None]:
    tz=ZoneInfo(tzname); midnight=datetime.combine(local_day,time(0),tzinfo=tz); jd=_time_to_jd(midnight.astimezone(timezone.utc))
    try:
        geop=(lon,lat,0); rr,rt=swe.rise_trans(jd,swe.SUN,swe.CALC_RISE,geop); sr,st=swe.rise_trans(jd,swe.SUN,swe.CALC_SET,geop)
        rs=rt[0]; ss=st[0]
        if rr < 0 or sr < 0: return None,None
        def cv(x):
            y,m,d,ut=swe.revjul(x,swe.GREG_CAL); hh=int(ut); mm=int((ut-hh)*60); sec=int(round((((ut-hh)*60)-mm)*60)); return datetime(int(y),int(m),int(d),hh,mm,min(sec,59),tzinfo=timezone.utc).astimezone(tz)
        return cv(rs),cv(ss)
    except Exception: return None,None

def _segment_index(dt: datetime, sunrise: datetime|None, sunset: datetime|None) -> int|None:
    if not sunrise or not sunset or not (sunrise <= dt < sunset): return None
    part=(sunset-sunrise).total_seconds()/8
    return min(8, max(1, int((dt-sunrise).total_seconds()//part)+1))

def _clip_to_discrete_boundary(start: datetime, proposed_end: datetime, lat: float, lon: float, tzname: str, sunrise: datetime|None, sunset: datetime|None) -> datetime:
    """Clip a sample interval at the first Panchanga or daylight-segment change."""
    if proposed_end <= start: return proposed_end
    def signature(dt: datetime):
        p=_panchanga(_time_to_jd(dt.astimezone(timezone.utc)))
        return (p['tithi_number'],p['paksha'],p['nakshatra_index'],p['nakshatra_pada'],p['yoga_number'],p['karana'],_segment_index(dt,sunrise,sunset))
    initial=signature(start)
    if signature(proposed_end-timedelta(seconds=1)) == initial: return proposed_end
    lo=start; hi=proposed_end
    for _ in range(24):
        if (hi-lo).total_seconds() <= 1: break
        mid=lo+(hi-lo)/2
        if signature(mid)==initial: lo=mid
        else: hi=mid
    return hi

def _score_slot(dt: datetime, lat: float, lon: float, tzname: str, activity: str, natal_moon_lon: float|None, sunrise: datetime|None=None, sunset: datetime|None=None) -> dict[str,Any]:
    jd=_time_to_jd(dt.astimezone(timezone.utc)); p=_panchanga(jd); score=50; reasons=[]; penalties=[]; cfg=ACTIVITIES[activity]
    weekday=dt.weekday(); rahu_num=RAHU_SEGMENT[weekday]
    if sunrise and sunset and sunrise < dt < sunset:
        daylight=(sunset-sunrise).total_seconds()/8; seg=int((dt-sunrise).total_seconds()//daylight)+1
        if seg==rahu_num: score-=25; penalties.append("Rahu Kalam (avoid for auspicious initiation in this tradition)")
        else: reasons.append("Outside Rahu Kalam")
        if seg==YAMAGANDA_SEGMENT[weekday]: score-=8; penalties.append("Yamaganda segment")
        if seg==GULIKA_SEGMENT[weekday]: score-=5; penalties.append("Gulika segment")
    else:
        reasons.append("Night-time slot; daytime Rahu Kalam screen not applied")
    if p['tithi_number'] in cfg['good_tithi']: score+=10; reasons.append(f"Activity-compatible Tithi: {p['paksha']} {p['tithi']}")
    if p['tithi_number'] in cfg['avoid_tithi']: score-=12; penalties.append(f"Generally avoided Tithi for this activity: {p['tithi']}")
    if p['nakshatra_index'] in cfg['good_nak']: score+=12; reasons.append(f"Activity-compatible Nakshatra: {p['nakshatra']}")
    if p['nakshatra_index'] in cfg['avoid_nak']: score-=10; penalties.append(f"Traditionally avoided Nakshatra for this activity: {p['nakshatra']}")
    if p['yoga_number'] in cfg['good_yoga']: score+=7; reasons.append(f"Favourable general Nitya Yoga: {p['yoga']}")
    elif p['yoga_number'] in (6,9,10,13,15,17,19,27): score-=10; penalties.append(f"Traditionally inauspicious Nitya Yoga: {p['yoga']}")
    # Vara is a modest, explicitly secondary heuristic; school-specific rules vary.
    if activity in ('job_start','business_start','education') and weekday in (1,2,3,4): score+=3; reasons.append(f"Weekday support: {WEEKDAYS[weekday]}")
    if activity in ('property_buy','property_legal','puja') and weekday in (0,3,4): score+=3; reasons.append(f"Weekday support: {WEEKDAYS[weekday]}")
    if natal_moon_lon is not None:
        natal_nak=int(norm360(natal_moon_lon)//(360/27)); tara=((p['nakshatra_index']-natal_nak)%27)+1; tara_group=(tara-1)%9+1
        if tara_group in (1,3,5,7): score+=5; reasons.append(f"Tara Bala screen supportive (group {tara_group})")
        else: score-=5; penalties.append(f"Tara Bala screen challenging (group {tara_group})")
        moon_sign=int(p['moon']//30); natal_sign=int(norm360(natal_moon_lon)//30); chandra=((moon_sign-natal_sign)%12)+1
        if chandra in (1,3,6,7,10,11): score+=5; reasons.append(f"Chandra Bala screen supportive (Moon {chandra} signs from natal Moon)")
        else: score-=5; penalties.append(f"Chandra Bala screen challenging (Moon {chandra} signs from natal Moon)")
    score=max(0,min(100,score))
    return {"score":score,"panchanga":{k:v for k,v in p.items() if k not in ('sun','moon','elongation')},"reasons":reasons,"penalties":penalties,"sunrise":sunrise.isoformat() if sunrise else None,"sunset":sunset.isoformat() if sunset else None}

def search_muhurta(*, activity: str, start_date: str, end_date: str, latitude: float, longitude: float, timezone_name: str, natal_moon_longitude: float|None=None, step_minutes: int=30, max_results: int=20) -> dict[str,Any]:
    if activity not in ACTIVITIES: raise ValueError(f"Unsupported activity. Choose one of: {', '.join(ACTIVITIES)}")
    start=date.fromisoformat(start_date); end=date.fromisoformat(end_date)
    if end<start: raise ValueError("end_date must be on or after start_date")
    if (end-start).days>90: raise ValueError("Muhurta search is limited to 90 days per request; search longer periods in separate ranges")
    if not -90<=latitude<=90 or not -180<=longitude<=180: raise ValueError("Latitude/longitude out of range")
    tz=ZoneInfo(timezone_name); slots=[]; day=start
    while day<=end:
        sunrise,sunset=_sunrise_sunset(day,latitude,longitude,timezone_name)
        # Search daylight slots where sunrise/set are known, in local wall-clock time.
        if sunrise and sunset and sunset>sunrise:
            cur=sunrise
            while cur<sunset:
                proposed_end=min(cur+timedelta(minutes=step_minutes),sunset)
                slot_end=_clip_to_discrete_boundary(cur,proposed_end,latitude,longitude,timezone_name,sunrise,sunset)
                if slot_end<=cur: slot_end=min(cur+timedelta(seconds=1),sunset)
                result=_score_slot(cur,latitude,longitude,timezone_name,activity,natal_moon_longitude,sunrise,sunset)
                if result['score']>=60:
                    slots.append({"start":cur.isoformat(),"end":slot_end.isoformat(),**result})
                cur=slot_end
        day+=timedelta(days=1)
    # Merge adjacent eligible intervals only if score, Panchanga labels and rationale are identical.
    merged=[]
    for slot in slots:
        key=(slot['score'],slot['panchanga'],slot['reasons'],slot['penalties'])
        if merged and merged[-1]['end']==slot['start'] and (merged[-1]['score'],merged[-1]['panchanga'],merged[-1]['reasons'],merged[-1]['penalties'])==key:
            merged[-1]['end']=slot['end']
        else: merged.append(slot.copy())
    merged.sort(key=lambda x:(-x['score'],x['start']))
    # Keep top intervals, not multiple adjacent fragments; response warns that scores are rule screens.
    out=merged[:max_results]
    return {"activity":activity,"activity_label":ACTIVITIES[activity]['label'],"location":{"latitude":latitude,"longitude":longitude,"timezone":timezone_name},"period":{"start":start.isoformat(),"end":end.isoformat()},"method":{"ayanamsha":"Lahiri","ephemeris":"Swiss Ephemeris","time_basis":"local civil time; sunrise/sunset by location","rules":["Tithi","Nakshatra","Nitya Yoga","weekday (secondary)","Rahu Kalam/Yamaganda/Gulika daytime segments","Tara Bala and Chandra Bala when birth Moon is supplied"],"score_interpretation":"Rule-screen score (0–100), not a probability or validated outcome prediction."},"personalized":natal_moon_longitude is not None,"candidate_windows":out,"candidate_count_before_limit":len(merged),"limitations":["Traditions differ on activity-specific muhurta rules; this version exposes its selected rule screen.","Exact event-specific rules such as marriage, griha pravesha and regional panchanga exceptions are not silently assumed.","This score is not empirical evidence that an event will succeed; use practical, legal, financial and safety considerations too."]}
