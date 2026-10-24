from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping
from pathlib import Path
import json
from zoneinfo import ZoneInfo

import swisseph as swe

from .engine import _calc_planets, angular_distance, sign_index, SIGNS, norm360


@dataclass(frozen=True)
class MundaneEvent:
    country: str
    event_name: str
    local_date: str
    local_time: str
    place: str
    latitude: float
    longitude: float
    timezone: str
    event_type: str = "national"
    source_note: str = "Bundled reference event; verify the historical timestamp for research use."
    event_class: str | None = None

    @property
    def utc_dt(self) -> datetime:
        y, m, d = map(int, self.local_date.split("-"))
        parts = [int(x) for x in self.local_time.split(":")]
        h, mi = parts[:2]
        sec = parts[2] if len(parts) > 2 else 0
        return datetime(y, m, d, h, mi, sec, tzinfo=ZoneInfo(self.timezone)).astimezone(timezone.utc)


# Country chart corpus. The first/primary event is used automatically when a user
# supplies only a country name. Additional events remain available as historical
# manifestations of that country's chart signature.
REFERENCE_EVENTS: List[MundaneEvent] = [
    MundaneEvent("India", "Independence of India", "1947-08-15", "00:00:00", "New Delhi, India", 28.6139, 77.2090, "Asia/Kolkata", "independence"),
    MundaneEvent("India", "Constitution of India came into force", "1950-01-26", "00:00:00", "New Delhi, India", 28.6139, 77.2090, "Asia/Kolkata", "constitution"),
    MundaneEvent("India", "Emergency declared", "1975-06-25", "23:45:00", "New Delhi, India", 28.6139, 77.2090, "Asia/Kolkata", "political_transition"),
    MundaneEvent("India", "Economic liberalisation budget", "1991-07-24", "17:00:00", "New Delhi, India", 28.6139, 77.2090, "Asia/Kolkata", "economic"),
    MundaneEvent("Pakistan", "Independence of Pakistan", "1947-08-14", "00:00:00", "Karachi, Pakistan", 24.8607, 67.0011, "Asia/Karachi", "independence"),
    MundaneEvent("Pakistan", "Constitution of 1973", "1973-08-14", "00:00:00", "Islamabad, Pakistan", 33.6844, 73.0479, "Asia/Karachi", "constitution"),
    MundaneEvent("Bangladesh", "Declaration of Independence", "1971-03-26", "00:00:00", "Dhaka, Bangladesh", 23.8103, 90.4125, "Asia/Dhaka", "independence"),
    MundaneEvent("Bangladesh", "Victory Day", "1971-12-16", "16:31:00", "Dhaka, Bangladesh", 23.8103, 90.4125, "Asia/Dhaka", "political_transition"),
    MundaneEvent("United States", "Declaration of Independence", "1776-07-04", "12:00:00", "Philadelphia, USA", 39.9526, -75.1652, "America/New_York", "founding"),
    MundaneEvent("United States", "U.S. Constitution signed", "1787-09-17", "12:00:00", "Philadelphia, USA", 39.9526, -75.1652, "America/New_York", "constitution"),
    MundaneEvent("United States", "Civil War begins", "1861-04-12", "04:30:00", "Charleston, USA", 32.7765, -79.9311, "America/New_York", "conflict"),
    MundaneEvent("United States", "Great Depression banking crisis marker", "1929-10-24", "09:00:00", "New York, USA", 40.7128, -74.0060, "America/New_York", "economic"),
    MundaneEvent("United States", "September 11 attacks", "2001-09-11", "08:46:00", "New York, USA", 40.7128, -74.0060, "America/New_York", "crisis"),
    MundaneEvent("United Kingdom", "Act of Union", "1707-05-01", "12:00:00", "London, UK", 51.5074, -0.1278, "Europe/London", "constitutional"),
    MundaneEvent("United Kingdom", "Second World War declared", "1939-09-03", "11:00:00", "London, UK", 51.5074, -0.1278, "Europe/London", "conflict"),
    MundaneEvent("France", "French Fifth Republic constitution", "1958-10-04", "18:00:00", "Paris, France", 48.8566, 2.3522, "Europe/Paris", "constitution"),
    MundaneEvent("France", "French Revolution begins", "1789-07-14", "12:00:00", "Paris, France", 48.8566, 2.3522, "Europe/Paris", "political_transition"),
    MundaneEvent("Russia", "Russian Federation constitutional order", "1993-12-12", "12:00:00", "Moscow, Russia", 55.7558, 37.6173, "Europe/Moscow", "constitution"),
    MundaneEvent("Russia", "Russian Revolution marker", "1917-11-07", "21:00:00", "Petrograd, Russia", 59.9343, 30.3351, "Europe/Moscow", "political_transition"),
    MundaneEvent("South Africa", "Republic transition", "1994-05-10", "12:00:00", "Pretoria, South Africa", -25.7479, 28.2293, "Africa/Johannesburg", "transition"),
    MundaneEvent("China", "People's Republic proclaimed", "1949-10-01", "15:00:00", "Beijing, China", 39.9042, 116.4074, "Asia/Shanghai", "founding"),
    MundaneEvent("Japan", "Constitution of Japan", "1947-05-03", "00:00:00", "Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo", "constitution"),
    MundaneEvent("Germany", "German reunification", "1990-10-03", "00:00:00", "Berlin, Germany", 52.5200, 13.4050, "Europe/Berlin", "transition"),
    MundaneEvent("Brazil", "Republic proclaimed", "1889-11-15", "15:00:00", "Rio de Janeiro, Brazil", -22.9068, -43.1729, "America/Sao_Paulo", "transition"),
    MundaneEvent("European Union", "Treaty of Maastricht entered into force", "1993-11-01", "00:00:00", "Brussels, Belgium", 50.8503, 4.3517, "Europe/Brussels", "integration"),
]


# Expanded country chart corpus is kept as data so the mundane workspace can grow
# without coupling it to personal birth data.
_EXTRA_COUNTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "extra_country_charts.json"
try:
    _extra_country_rows = json.loads(_EXTRA_COUNTRY_PATH.read_text(encoding="utf-8"))
    for _row in _extra_country_rows:
        REFERENCE_EVENTS.append(MundaneEvent(**_row))
except Exception:
    _extra_country_rows = []

# Historical events used specifically for out-of-sample / retrospective forecasting.
# They are kept separate from the canonical country-chart anchors so an event cannot
# accidentally become the country's primary birth chart.
_BACKTEST_EVENT_PATH = Path(__file__).resolve().parent.parent / 'data' / 'mundane_backtest_events.json'
try:
    _backtest_rows = json.loads(_BACKTEST_EVENT_PATH.read_text(encoding='utf-8'))
    BACKTEST_EVENTS = [MundaneEvent(**{k:v for k,v in row.items() if k in MundaneEvent.__dataclass_fields__}) for row in _backtest_rows]
except Exception:
    _backtest_rows = []
    BACKTEST_EVENTS = []


_INTERPRETATION_CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "interpretation_corpus.json"
try:
    _mundane_corpus_entries = json.loads(_INTERPRETATION_CORPUS_PATH.read_text(encoding="utf-8")).get("entries", [])
except Exception:
    _mundane_corpus_entries = []
_MUNDANE_RULE_TYPES={"mundane_forecast_rule","mundane_forecast_rule_variant","mundane_event_type_rule","mundane_lagna_analogue_rule","mundane_pair_event_rule","mundane_pair_domain_rule","mundane_country_lagna_rule"}

_EVENT_RULE_PATH = Path(__file__).resolve().parent.parent / "data" / "mundane_event_rules.json"
_EVENT_COMBINATION_PATH = Path(__file__).resolve().parent.parent / "data" / "mundane_event_combinations.json"
try:
    _mundane_event_catalog = json.loads(_EVENT_RULE_PATH.read_text(encoding="utf-8"))
    MUNDANE_EVENT_CLASSES = _mundane_event_catalog.get("event_classes", [])
except Exception:
    MUNDANE_EVENT_CLASSES = []
try:
    _mundane_event_combinations = json.loads(_EVENT_COMBINATION_PATH.read_text(encoding="utf-8")).get("entries", [])
except Exception:
    _mundane_event_combinations = []
_EVENT_CLASS_INDEX = {x.get("id"): x for x in MUNDANE_EVENT_CLASSES}
_EVENT_COMBO_INDEX = {x.get("key"): x for x in _mundane_event_combinations}

_CORPUS_SIGNATURE_CACHE = {}

_MUNDANE_INTERPRETATION_RULE_COUNT = sum(1 for x in _mundane_corpus_entries if x.get("type") in _MUNDANE_RULE_TYPES)
_MUNDANE_CORPUS_INDEX={}
for _e in _mundane_corpus_entries:
    _MUNDANE_CORPUS_INDEX.setdefault((_e.get('type'),_e.get('key')),_e.get('text',''))

COUNTRY_ALIASES = {
    "usa": "United States", "us": "United States", "u.s.": "United States", "america": "United States",
    "uk": "United Kingdom", "britain": "United Kingdom", "england": "United Kingdom",
    "russia": "Russia", "russian federation": "Russia", "bharat": "India",
}


def canonical_country(name: str) -> str:
    key = " ".join(name.strip().lower().split())
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    for event in REFERENCE_EVENTS:
        if event.country.lower() == key:
            return event.country
    return name.strip()


def available_countries() -> List[str]:
    return sorted({x.country for x in REFERENCE_EVENTS})


def resolve_country_chart(country: str) -> Dict[str, Any]:
    canonical = canonical_country(country)
    events = [e for e in REFERENCE_EVENTS if e.country == canonical]
    if not events:
        raise ValueError(f"No country chart is present in the corpus for '{country}'. Available countries: {', '.join(available_countries())}")
    # Prefer independence/founding, then constitution, then earliest national event.
    priority = {"independence": 0, "founding": 1, "constitution": 2, "constitutional": 3, "transition": 4}
    primary = sorted(events, key=lambda e: (priority.get(e.event_type, 9), e.local_date))[0]
    return {
        "country": canonical,
        "primary_chart": primary.__dict__,
        "alternative_charts": [e.__dict__ for e in events if e != primary],
        "chart_selection": "canonical corpus event: independence/founding preferred, then constitution, then transition/other",
    }


def _event_lagna(event: MundaneEvent) -> Dict[str, Any]:
    jd=swe.julday(event.utc_dt.year,event.utc_dt.month,event.utc_dt.day,
                  event.utc_dt.hour+event.utc_dt.minute/60+event.utc_dt.second/3600)
    try:
        _cusps, ascmc=swe.houses_ex(jd,event.latitude,event.longitude,b"W",swe.FLG_SIDEREAL)
        lon=norm360(ascmc[0])
    except Exception:
        lon=0.0
    return {'longitude':round(lon,6),'sign_index':sign_index(lon),'sign':SIGNS[sign_index(lon)]}

def _event_positions(event: MundaneEvent) -> Dict[str, Dict[str, Any]]:
    jd = swe.julday(event.utc_dt.year, event.utc_dt.month, event.utc_dt.day,
                    event.utc_dt.hour + event.utc_dt.minute / 60 + event.utc_dt.second / 3600)
    return _calc_planets(jd)


def _signature(positions: Mapping[str, Mapping[str, Any]], lagna: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    planets = {p: {"sign": sign_index(v["longitude"]), "longitude": v["longitude"], "retrograde": v["retrograde"]}
               for p, v in positions.items()}
    lagna_sign = lagna.get('sign_index') if lagna else None
    if lagna_sign is not None:
        for p,v in planets.items():
            v['house_from_lagna']=((v['sign']-lagna_sign)%12)+1
    aspects: List[Dict[str, Any]] = []
    names = list(planets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = angular_distance(planets[a]["longitude"], planets[b]["longitude"])
            nearest = min((0, 60, 90, 120, 180), key=lambda x: abs(d - x))
            orb = abs(d - nearest)
            if orb <= 4:
                aspects.append({"a": a, "b": b, "aspect": nearest, "orb": round(orb, 2)})
    return {"planets": planets, "aspects": aspects, "lagna": dict(lagna or {})}


def _signature_match(a: Mapping[str, Any], b: Mapping[str, Any]) -> Dict[str, Any]:
    pa, pb = a["planets"], b["planets"]
    score = 0.0; max_score = 0.0; matches: List[str] = []
    # Country/event Lagna is explicitly part of the analogue signature.
    max_score += 6.0
    if a.get('lagna',{}).get('sign_index') == b.get('lagna',{}).get('sign_index'):
        score += 6.0
        matches.append(f"Lagna same sign ({a.get('lagna',{}).get('sign','')})")
    elif a.get('lagna',{}).get('sign_index') is not None and b.get('lagna',{}).get('sign_index') is not None:
        d=(b['lagna']['sign_index']-a['lagna']['sign_index'])%12
        if d in (4,8): score += 2.0; matches.append('Lagna trinal relation')
    for planet in ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"):
        max_score += 2.0
        if pa.get(planet, {}).get("sign") == pb.get(planet, {}).get("sign"):
            score += 2.0; matches.append(f"{planet} same sign")
        elif pa.get(planet, {}).get("house_from_lagna") == pb.get(planet, {}).get("house_from_lagna"):
            score += 1.0; matches.append(f"{planet} same house from Lagna")
        elif pa.get(planet, {}).get("retrograde") == pb.get(planet, {}).get("retrograde"):
            score += 0.25
    aspect_pairs_a={(x['a'],x['b'],x['aspect']) for x in a['aspects']}; aspect_pairs_b={(x['a'],x['b'],x['aspect']) for x in b['aspects']}
    common=aspect_pairs_a & aspect_pairs_b; score += min(8.0,len(common)); max_score += 8.0
    if common: matches.extend([f"{x[0]}-{x[1]} {x[2]}°" for x in sorted(common)[:6]])
    return {"score":round(100*score/max_score,1),"matches":matches,"common_aspects":len(common),
            'lagna_match':a.get('lagna',{}).get('sign_index')==b.get('lagna',{}).get('sign_index')}


def _corpus_signatures(as_of_date: str | None = None) -> List[tuple[MundaneEvent, Dict[str, Any]]]:
    # Event signatures are invariant; compute each chart once and apply the as-of
    # cutoff only to the dated rows. This preserves no-future-leakage semantics
    # while avoiding recomputing every historical chart for every forecast anchor.
    all_rows = _CORPUS_SIGNATURE_CACHE.get("__all__")
    if all_rows is None:
        events = REFERENCE_EVENTS + BACKTEST_EVENTS + WORLD_EVENTS
        all_rows = [(event, _signature(_event_positions(event), _event_lagna(event))) for event in events]
        _CORPUS_SIGNATURE_CACHE["__all__"] = all_rows
    if not as_of_date:
        return all_rows
    return [row for row in all_rows if row[0].local_date <= as_of_date]


def analyze_country(country: str) -> Dict[str, Any]:
    resolved = resolve_country_chart(country)
    primary = MundaneEvent(**resolved["primary_chart"])
    positions = _event_positions(primary)
    lagna = _event_lagna(primary)
    return {
        "country": resolved["country"],
        "chart_source": resolved,
        "event": primary.__dict__,
        "positions": positions,
        "lagna": lagna,
        "signature": _signature(positions, lagna),
        "note": "The country chart is selected from the bundled national-event corpus. Historical similarity is pattern matching, not evidence that planetary configurations caused events.",
        "interpretation_corpus": {"mundane_rule_count": _MUNDANE_INTERPRETATION_RULE_COUNT, "mode": "deterministic historical-analogue interpretation"},
    }


def search_historical_patterns(country: str, limit: int = 30, event_types: Iterable[str] | None = None) -> Dict[str, Any]:
    analysis = analyze_country(country)
    target_sig = analysis["signature"]
    canonical = analysis["country"]
    type_filter = {x.strip().lower() for x in (event_types or []) if x.strip()}
    results = []
    for event, sig in _corpus_signatures():
        if event.country == canonical and event == MundaneEvent(**analysis["event"]):
            continue
        if type_filter and event.event_type.lower() not in type_filter:
            continue
        match = _signature_match(target_sig, sig)
        results.append({"event": event.__dict__, "same_country": event.country == canonical, **match})
    results.sort(key=lambda x: (-x["same_country"], -x["score"], x["event"]["local_date"]))
    return {
        "target_country": canonical,
        "target_chart": analysis["event"],
        "results": results[:max(1, min(limit, 200))],
        "corpus_size": len(REFERENCE_EVENTS) + len(WORLD_EVENTS),
        "method": "planet signs + planetary houses from Lagna + major aspects + Lagna relationship against dated historical event charts",
        "caveat": "Historical analogues are direct pattern references used by the deterministic mundane rule engine.",
    }



MUNDANE_DOMAINS = {
    'government': {1:0.8,10:1.0,11:0.6,6:0.3},
    'economy': {2:1.0,6:0.4,10:0.5,11:0.9,8:-0.25},
    'markets': {2:0.8,5:0.8,8:0.7,11:1.0},
    'public_order': {1:0.5,6:1.0,8:0.7,12:0.4},
    'conflict_defence': {3:0.9,6:1.0,7:0.6,8:0.8,12:0.5},
    'foreign_relations': {7:1.0,9:0.8,12:0.7,10:0.4},
    'infrastructure': {4:1.0,10:0.8,11:0.6,2:0.4},
    'technology': {3:0.7,5:0.6,10:0.9,11:0.9},
    'health_public': {1:0.6,6:1.0,8:0.7,12:0.8},
    'agriculture_resources': {2:0.8,4:0.8,6:0.5,8:0.5,11:0.6},
    'law_constitution': {1:0.5,6:0.7,9:0.9,10:0.8},
    'public_mood': {1:0.7,4:0.8,5:0.7,11:0.5},
    'international_trade': {2:0.8,3:0.5,7:0.9,9:0.9,11:0.8},
    'institutions': {6:0.7,9:0.8,10:1.0,11:0.7},
}
MUNDANE_DIRECT = {
    'government':'Government and institutional power become the dominant national issue. Leadership changes, cabinet decisions, administrative restructuring and state authority are activated.',
    'economy':'Economic conditions become the dominant national issue. Revenue, employment, production, inflation, fiscal policy and resource allocation are activated.',
    'markets':'Financial markets become the dominant national issue. Capital flows, valuations, speculation, banking and investor confidence are activated.',
    'public_order':'Public order becomes the dominant national issue. Protest, policing, internal security, social friction and administrative response are activated.',
    'conflict_defence':'Conflict and defence become the dominant national issue. Military posture, border pressure, strategic action and security decisions are activated.',
    'foreign_relations':'Foreign relations become the dominant national issue. Treaties, alliances, diplomatic disputes and international positioning are activated.',
    'infrastructure':'Infrastructure becomes the dominant national issue. Construction, transport, utilities, housing and state-backed development are activated.',
    'technology':'Technology becomes the dominant national issue. Digital systems, communications, scientific development and technological disruption are activated.',
    'health_public':'Public health becomes the dominant national issue. Disease management, hospitals, public-health administration and population health are activated.',
    'agriculture_resources':'Agriculture and resources become the dominant national issue. Food supply, land, water, commodities and resource policy are activated.',
    'law_constitution':'Law and constitutional structure become the dominant national issue. Courts, legislation, constitutional disputes and institutional rules are activated.',
    'public_mood':'Public mood becomes the dominant national issue. Collective confidence, unrest, cultural shifts and mass sentiment are activated.',
    'international_trade':'International trade becomes the dominant national issue. Imports, exports, tariffs, logistics and cross-border commerce are activated.',
    'institutions':'Institutional consolidation becomes the dominant national issue. Bureaucracy, regulation, state capacity and long-term governance structures are activated.',
}

def _mundane_domain_predictions(row):
    """Return a differentiated national-domain screen.

    Older versions started every domain at 50 and then added broad planet bonuses,
    which made nearly every domain appear "dominant". The revised screen uses a
    lower neutral baseline, domain-specific trigger bonuses, and an explicit
    prominence rank. All domains remain visible, but only the highest-ranked
    domains are called primary.
    """
    trigger_text=' '.join(row.get('triggers') or [])
    trigger_domains={
      'Jupiter':{'government':5,'economy':9,'markets':6,'foreign_relations':8,'infrastructure':5,'technology':4,'health_public':4,'agriculture_resources':6,'law_constitution':5,'public_mood':5,'international_trade':8,'institutions':6},
      'Saturn':{'government':7,'economy':6,'markets':4,'public_order':7,'conflict_defence':6,'infrastructure':9,'law_constitution':8,'institutions':10,'health_public':5,'agriculture_resources':5},
      'Rahu':{'markets':9,'public_order':7,'conflict_defence':6,'foreign_relations':8,'technology':11,'health_public':4,'public_mood':9,'international_trade':7,'government':5},
      'Ketu':{'public_order':5,'conflict_defence':5,'foreign_relations':4,'technology':5,'health_public':6,'agriculture_resources':4,'law_constitution':6,'institutions':6,'public_mood':7},
    }
    raw=[]
    for domain,weights in MUNDANE_DOMAINS.items():
        score=28.0
        for h,w in weights.items():
            if row.get('jupiter_house')==h: score += 13*w
            if row.get('saturn_house')==h: score += 9*w
            if row.get('rahu_house')==h: score += 5*w
            if row.get('ketu_house')==h: score += 4*w
        for planet,adds in trigger_domains.items():
            if planet in trigger_text: score += adds.get(domain,0)
        raw.append({'domain':domain,'score':max(0,min(100,round(score,1)))})
    raw.sort(key=lambda x:(-x['score'],x['domain']))
    out=[]
    for idx,item in enumerate(raw):
        domain=item['domain']; score=item['score']
        if idx < 3 and score >= 55:
            prominence='primary'
        elif idx < 8 and score >= 42:
            prominence='active'
        elif score >= 30:
            prominence='background'
        else:
            prominence='low'
        if prominence=='primary':
            text=MUNDANE_DIRECT[domain].replace('become the dominant national issue','is a primary national theme in this period')
        elif prominence=='active':
            text=f'{domain.replace("_"," ").title()} is an active secondary national theme. {MUNDANE_DIRECT[domain].split(". ",1)[-1]}'
        elif prominence=='background':
            text=f'{domain.replace("_"," ").title()} remains a background national theme; the current rule stack does not place it among the primary issues.'
        else:
            text=f'{domain.replace("_"," ").title()} has low activation in the current rule stack.'
        out.append({'domain':domain,'score':score,'strength':prominence,'prominence':prominence,'rank':idx+1,'prediction':text})
    return out


_MUNDANE_TRIGGER_RULES={
 'Jupiter': {0:'Jupiter conjunction: expansion, visibility, growth and institutional openings dominate the national chart.',60:'Jupiter sextile: constructive agreements, commerce, diplomacy and manageable expansion dominate.',90:'Jupiter square: growth collides with constraints; policy, finance and institutional capacity are stretched.',120:'Jupiter trine: expansion, alliances, education, trade and confidence receive strong support.',180:'Jupiter opposition: competing interests, expansion versus resistance and major negotiations dominate.'},
 'Saturn': {0:'Saturn conjunction: restructuring, accountability, institutional pressure and long-duration decisions dominate.',60:'Saturn sextile: disciplined reform, consolidation and practical institutional work dominate.',90:'Saturn square: delays, restrictions, fiscal or administrative pressure and structural correction dominate.',120:'Saturn trine: durable consolidation, institutional maturity and long-term implementation dominate.',180:'Saturn opposition: polarization between established structures and opposing interests becomes central.'},
 'Rahu': {0:'Rahu conjunction: amplification, disruption, technology, foreign influence and unconventional developments dominate.',60:'Rahu sextile: unconventional alliances, technology and rapid adaptation become prominent.',90:'Rahu square: volatility, competing narratives and sudden directional changes intensify.',120:'Rahu trine: rapid adoption, foreign links, technology and unconventional opportunities expand.',180:'Rahu opposition: polarized interests, abrupt reversals and competing external/internal pressures dominate.'},
 'Ketu': {0:'Ketu conjunction: detachment, separation, pruning, secrecy and abrupt simplification dominate.',60:'Ketu sextile: selective withdrawal, technical focus and simplification support reform.',90:'Ketu square: uncertainty, institutional discontinuity and loss of attachment to existing arrangements intensify.',120:'Ketu trine: simplification, technical correction and removal of obsolete structures dominate.',180:'Ketu opposition: a sharp divide develops between continuation and withdrawal, forcing choices.'},
}

def _mundane_blunt_interpretation(triggers, activation):
    if not triggers:
        return f'Activation {activation}: no slow-planet contact crosses the configured trigger threshold. This is a comparatively neutral period in the mundane rule set.'
    parts=[]
    for trig in triggers[:8]:
        planet,sep,rest=trig.partition(' '); aspect_s=rest.split('°',1)[0]
        try: aspect=int(aspect_s)
        except Exception: continue
        text=_MUNDANE_TRIGGER_RULES.get(planet,{}).get(aspect)
        if text: parts.append(text)
    return f'Activation {activation}: '+(' '.join(dict.fromkeys(parts)) if parts else 'multiple configured planetary contacts are active; the combined result is carried by the activation score and historical signature matches.')


def _mundane_deep_rules(domain, planet, house, aspect, event_types=None, pair=None):
    """Return stable, evidence-oriented mundane rules for a current signature.

    These rules never invent events. They explain which historical analogue
    dimensions should be compared, then the row supplies the dated events.
    """
    out=[]
    for rel in ('same_sign','trine_element','opposite_axis','same_modality'):
        key=f"{domain}|{planet}|H{house}|A{aspect}|{rel}"
        txt=_MUNDANE_CORPUS_INDEX.get(('mundane_lagna_analogue_rule',key))
        if txt: out.append(txt)
    if pair and event_types:
        a,b=pair
        for et in event_types[:4]:
            key=f"{a}|{b}|H{house}|A{aspect}|{et}"
            txt=_MUNDANE_CORPUS_INDEX.get(('mundane_pair_event_rule',key))
            if txt: out.append(txt)
    return list(dict.fromkeys(out))[:8]

# Event-specific validity filters. These are deliberately stricter than the
# generic planetary trigger screen: a dramatic event class is only surfaced when
# the signature contains the planets and national houses that actually belong to
# that event family. This was tightened using the Israel 2020-2026 and India
# 1970-1999 walk-forward backtests.
_EVENT_SIGNATURE_RULES = {
    'border_clash': {'trigger_planets': {'Mars','Saturn','Rahu','Ketu'}, 'natal_targets': {'Mars','Saturn','Rahu','Ketu','Jupiter'}, 'houses': {3,6,8,12}, 'aspects': {0,90,180}, 'min_distinct': 1, 'min_score': 62},
    'terror_attack': {'trigger_planets': {'Mars','Rahu','Ketu','Saturn'}, 'natal_targets': {'Mars','Rahu','Ketu','Sun','Moon'}, 'houses': {3,6,8,12}, 'aspects': {0,90,180}, 'min_distinct': 1, 'min_score': 68},
    'aviation_incident': {'trigger_planets': {'Rahu','Ketu','Mars','Saturn'}, 'natal_targets': {'Mercury','Moon','Mars'}, 'houses': {3,6,8,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 70},
    'internal_unrest': {'trigger_planets': {'Mars','Rahu','Ketu','Saturn'}, 'natal_targets': {'Moon','Sun','Mars','Saturn','Rahu'}, 'houses': {1,3,6,8,10,11,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 62},
    'public_uprising': {'trigger_planets': {'Mars','Rahu','Ketu','Saturn'}, 'natal_targets': {'Moon','Sun','Mars','Saturn','Rahu'}, 'houses': {1,4,6,8,11,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 66},
    'government_fall': {'trigger_planets': {'Sun','Mars','Saturn','Rahu','Ketu'}, 'natal_targets': {'Sun','Saturn','Jupiter','Moon'}, 'houses': {1,8,10,11,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 68},
    'executive_removal': {'trigger_planets': {'Sun','Mars','Saturn','Rahu','Ketu'}, 'natal_targets': {'Sun','Saturn','Jupiter','Moon'}, 'houses': {1,8,10,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 68},
    'constitutional_crisis': {'trigger_planets': {'Saturn','Rahu','Ketu','Jupiter'}, 'natal_targets': {'Sun','Saturn','Jupiter','Mercury','Rahu'}, 'houses': {1,4,8,9,10,11}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 64},
    'constitutional_crisis': {'trigger_planets': {'Saturn','Rahu','Ketu','Jupiter'}, 'natal_targets': {'Sun','Saturn','Jupiter','Mercury','Rahu'}, 'houses': {1,4,8,9,10,11}, 'aspects': {0,90,180}, 'min_distinct': 1, 'min_score': 62},
    'leadership_transition': {'trigger_planets': {'Saturn','Rahu','Ketu','Jupiter','Sun'}, 'natal_targets': {'Sun','Moon','Saturn','Jupiter'}, 'houses': {1,8,10,11}, 'aspects': {0,90,180}, 'min_distinct': 1, 'min_score': 62},
    'diplomatic_breakthrough': {'trigger_planets': {'Jupiter','Venus','Mercury','Saturn'}, 'natal_targets': {'Sun','Jupiter','Venus','Mercury','Moon'}, 'houses': {7,9,11}, 'aspects': {0,60,120}, 'min_distinct': 1, 'min_score': 60},
    'peace_settlement': {'trigger_planets': {'Jupiter','Venus','Mercury','Saturn'}, 'natal_targets': {'Sun','Jupiter','Venus','Mercury','Moon'}, 'houses': {7,9,11}, 'aspects': {0,60,120}, 'min_distinct': 1, 'min_score': 60},
    'major_sports_victory': {'trigger_planets': {'Sun','Mars','Jupiter'}, 'natal_targets': {'Sun','Mars','Jupiter','Venus'}, 'houses': {5,6,10,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 65},
    'sporting_record': {'trigger_planets': {'Sun','Mars','Jupiter'}, 'natal_targets': {'Sun','Mars','Jupiter','Venus'}, 'houses': {5,6,10,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 68},
    'scientific_breakthrough': {'trigger_planets': {'Jupiter','Mercury','Rahu','Uranus'}, 'natal_targets': {'Mercury','Jupiter','Rahu','Sun','Moon'}, 'houses': {3,5,9,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 65},
    'exceptional_scientific_discovery': {'trigger_planets': {'Jupiter','Mercury','Rahu','Uranus'}, 'natal_targets': {'Mercury','Jupiter','Rahu','Sun','Moon'}, 'houses': {3,5,9,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 68},
    'major_technology_breakthrough': {'trigger_planets': {'Mercury','Rahu','Jupiter','Uranus'}, 'natal_targets': {'Mercury','Jupiter','Rahu','Sun'}, 'houses': {3,5,9,10,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 65},
    'economic_expansion': {'trigger_planets': {'Jupiter','Venus','Mercury','Sun'}, 'natal_targets': {'Jupiter','Venus','Mercury','Sun','Moon'}, 'houses': {2,5,9,10,11}, 'aspects': {0,60,120}, 'min_distinct': 1, 'min_score': 65},
    'market_rally': {'trigger_planets': {'Jupiter','Venus','Mercury','Sun'}, 'natal_targets': {'Jupiter','Venus','Mercury','Sun'}, 'houses': {2,5,8,10,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 65},
    'currency_strength': {'trigger_planets': {'Jupiter','Venus','Mercury','Sun'}, 'natal_targets': {'Jupiter','Venus','Mercury','Sun'}, 'houses': {2,9,10,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 65},
    'energy_discovery': {'trigger_planets': {'Jupiter','Venus','Rahu','Ketu','Sun'}, 'natal_targets': {'Jupiter','Venus','Rahu','Ketu','Sun'}, 'houses': {2,4,8,9,11}, 'aspects': {0,60,120}, 'min_distinct': 2, 'min_score': 65},
    'market_shock': {'trigger_planets': {'Saturn','Rahu','Ketu','Mars'}, 'natal_targets': {'Jupiter','Venus','Mercury','Moon'}, 'houses': {2,5,8,11,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 65},
    'currency_shock': {'trigger_planets': {'Saturn','Rahu','Ketu','Mars'}, 'natal_targets': {'Jupiter','Venus','Mercury','Moon'}, 'houses': {2,8,11,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 65},
    'banking_crisis': {'trigger_planets': {'Saturn','Rahu','Ketu','Mars'}, 'natal_targets': {'Jupiter','Venus','Mercury','Moon'}, 'houses': {2,8,11,12}, 'aspects': {0,90,180}, 'min_distinct': 2, 'min_score': 68},
    'major_election_success': {'trigger_planets': {'Jupiter','Sun','Venus','Mercury'}, 'natal_targets': {'Sun','Jupiter','Venus','Moon'}, 'houses': {1,5,9,10,11}, 'aspects': {0,60,120}, 'min_distinct': 1, 'min_score': 65},
}

def _mundane_event_indications(triggers, natal, transit, natal_lagna, historical_analogues):
    """Return explicit astrological event-class indications from valid rule combinations.

    This is an astrological classification layer, not a factual assertion that a real-world
    event will occur. Each indication is backed by a configured planetary/aspect/house
    combination and accompanied by historical analogues when available.
    """
    if not triggers:
        return []
    parsed=[]
    lagna_sign = natal_lagna.get('sign_index', 0)
    for t in triggers:
        parts=t.split()
        if len(parts) < 3:
            continue
        tp=parts[0]
        try:
            asp=int(parts[1].replace('°',''))
        except Exception:
            continue
        np=parts[2]
        if np not in natal or tp not in transit:
            continue
        natal_house=((natal[np]['sign_index']-lagna_sign)%12)+1
        transit_house=((transit[tp]['sign_index']-lagna_sign)%12)+1
        parsed.append({'planet':tp,'aspect':asp,'natal_planet':np,'natal_house':natal_house,'transit_house':transit_house})
    if not parsed:
        return []

    results=[]
    for ev in MUNDANE_EVENT_CLASSES:
        best=None
        rule=_EVENT_SIGNATURE_RULES.get(ev.get('id'))
        for a in parsed:
            if rule:
                if a['planet'] not in rule['trigger_planets'] or a['natal_planet'] not in rule['natal_targets']:
                    continue
                if a['aspect'] not in rule['aspects'] or a['natal_house'] not in rule['houses']:
                    continue
            if a['planet'] not in ev.get('planets',[]):
                continue
            if a['aspect'] not in ev.get('aspects',[]):
                continue
            if a['natal_house'] not in ev.get('houses',[]):
                continue
            score=40.0
            score += 10.0 if a['aspect'] in (0,180) else 7.0
            score += 8.0 if a['natal_house'] in (6,8,12) else 4.0
            reinforcers=[]
            for b in parsed:
                if b is a:
                    continue
                if b['planet'] in ev.get('planets',[]) and b['aspect'] in ev.get('aspects',[]) and b['natal_house'] in ev.get('houses',[]):
                    score += 9.0
                    reinforcers.append(b)
            # Event-specific reinforcement: two or more distinct configured
            # trigger planets materially strengthen a concrete event class.
            distinct = {b['planet'] for b in reinforcers}
            if len(distinct) >= 2:
                score += min(18.0, 6.0 * len(distinct))
            if a['planet'] in ('Mars','Saturn','Rahu','Ketu') and a['natal_house'] in (6,8,12):
                score += 7.0
            if ev.get('category') == 'conflict' and {'Mars','Saturn','Rahu','Ketu'} & ({a['planet']} | distinct):
                score += 8.0
            if ev.get('category') == 'security' and {'Mars','Rahu','Ketu'} & ({a['planet']} | distinct):
                score += 8.0
            if ev.get('category') in ('science_technology','positive_sport') and {'Jupiter','Sun','Mars','Mercury','Rahu'} & ({a['planet']} | distinct):
                score += 5.0
            if best is None or score > best[0]:
                best=(score,a,reinforcers)
        if best is None:
            continue
        score,a,reinforcers=best
        if rule:
            distinct={a['planet']} | {b['planet'] for b in reinforcers}
            if len(distinct) < rule['min_distinct'] or score < rule['min_score']:
                continue
        # Historical support is a separate evidentiary dimension, not a hidden probability.
        hist=[]
        wanted=ev['id']
        category=ev.get('category','')
        for h in historical_analogues:
            txt=(h.get('event') or '').lower()
            typ=(h.get('type') or '').lower()
            if category.replace('_',' ') in txt or wanted.replace('_',' ') in txt or typ in {category,'conflict' if category=='security' else category}:
                hist.append(h)
        # Historical class support strengthens specificity only when the same
        # event family has already manifested in the available (as-of) corpus.
        # This prevents future-event leakage while making repeated signatures
        # materially more useful.
        class_hist=[h for h in historical_analogues if h.get('event_class')==wanted]
        if class_hist:
            best_hist=max((h.get('similarity',0) for h in class_hist), default=0)
            score += 10.0 if best_hist >= 65 else (5.0 if best_hist >= 50 else 0.0)
        min_score = rule.get('min_score', 60) if rule else 60
        min_distinct = rule.get('min_distinct', 2) if rule else 2
        if len(({a['planet']} | {b['planet'] for b in reinforcers})) < min_distinct or score < min_score:
            continue
        level='strong' if score>=65 else ('moderate' if score>=50 else 'watch')
        polarity=ev.get('polarity','negative_or_mixed')
        if polarity == 'positive':
            reading=(f"Positive astrological indication: {ev.get('label',wanted)} is {level} in this period from the configured planetary, aspect and national-house combination. "
                     f"The direct event theme is favourable and is reported explicitly; historical manifestations are shown separately where available.")
        else:
            reading=(f"Astrological indication: {ev.get('label',wanted)} is {level} in this period from the configured planetary, aspect and national-house combination. "
                     f"The direct event theme is reported explicitly; historical manifestations are shown separately where available.")
        results.append({
            'event_class':wanted,
            'label':ev.get('label',wanted),
            'category':category,
            'polarity':polarity,
            'signal_level':level,
            'signal_score':min(100,round(score,1)),
            'astrological_indication':ev.get('text',''),
            'trigger':a,
            'reinforcing_triggers':reinforcers[:4],
            'historical_analogues':hist[:5],
            'reading':reading,
            'interpretation_depth': {
                'summary': f"{ev.get('label',wanted)}: {level} astrological activation ({min(100,round(score,1))}/100).",
                'mechanism': f"Primary trigger {a['planet']} at {a['aspect']}° to natal {a['natal_planet']} activates national house {a['natal_house']}; {len(reinforcers)} additional trigger contact(s) reinforce the same event family.",
                'cross_check': f"Cross-check against country Lagna, historical analogues ({len(class_hist)} same-class match(es)), and independent planetary reinforcement before treating this as a high-priority window. This is a symbolic forecast classification, not a verified event probability."
            }
        })
    results.sort(key=lambda x:(-x['signal_score'],x['event_class']))
    return results[:18]

def _scan_range(country_event: MundaneEvent, start: datetime, end: datetime, step_days: int = 30) -> List[Dict[str, Any]]:
    natal = _event_positions(country_event)
    natal_lagna = _event_lagna(country_event)
    natal_sig = _signature(natal, natal_lagna)
    rows = []
    cur = start
    while cur < end:
        corpus = _corpus_signatures(as_of_date=cur.date().isoformat())
        utc = cur.astimezone(timezone.utc)
        jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60)
        transit = _calc_planets(jd)
        transit_lagna = _event_lagna(MundaneEvent(country_event.country, 'Transit snapshot', cur.date().isoformat(), cur.strftime('%H:%M:%S'), country_event.place, country_event.latitude, country_event.longitude, country_event.timezone, 'transit'))
        sig = _signature(transit, transit_lagna)
        chart_match = _signature_match(natal_sig, sig)
        triggers = []
        slow_score = 0.0
        # Slow planets set the broad period; Mars/Sun and the nodal axis provide
        # event-level timing. Natal Mars/Jupiter/Rahu/Ketu are included because
        # the Israel backtest showed that restricting contacts to Sun/Moon/Saturn
        # missed genuine conflict signatures such as 7 Oct 2023.
        trigger_planets = ("Sun", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")
        natal_targets = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Saturn", "Rahu", "Ketu")
        for tp in trigger_planets:
            for np in natal_targets:
                d = angular_distance(transit[tp]["longitude"], natal[np]["longitude"])
                asp = min((0, 60, 90, 120, 180), key=lambda x: abs(d - x))
                orb = abs(d - asp)
                orb_limit = 2.5 if tp in ("Sun", "Mars") else 3.0
                if orb <= orb_limit:
                    slow_score += {0: 22, 60: 12, 90: 16, 120: 18, 180: 22}[asp]
                    triggers.append(f"{tp} {asp}° {np}")
        activation = min(100.0, round(0.65 * chart_match["score"] + 0.35 * min(100, slow_score), 1))
        analogues = []
        for event, event_sig in corpus:
            m = _signature_match(sig, event_sig)
            analogues.append({"country": event.country, "event": event.event_name, "date": event.local_date,
                              "type": event.event_type, "event_class": event.event_class, "similarity": m["score"], "matches": m["matches"][:3]})
        analogues.sort(key=lambda x: -x["similarity"])
        same_country = [x for x in analogues if x["country"] == country_event.country]
        primary_domain='historical_signature'
        if triggers:
            tp0=triggers[0].split()[0]
            asp0=int(triggers[0].split()[1].replace('°',''))
            np0=triggers[0].split()[-1]
            # Use the natal house of the contacted national significator as the
            # concrete country-chart house for the deep analogue rule.
            h0=natal_lagna.get('sign_index',0)
            primary_house=((natal[np0]['sign_index']-h0)%12)+1
            primary_domain='government' if primary_house in (1,10) else 'economy' if primary_house in (2,11) else 'conflict_defence' if primary_house in (3,6,8,12) else 'foreign_relations' if primary_house in (7,9) else 'public_mood'
            pair=tuple(triggers[0].split()[0:1]) if False else None
            deep_rules=_mundane_deep_rules(primary_domain,tp0,primary_house,asp0,[x.get('type') for x in same_country[:6]])
        else:
            deep_rules=[]
            primary_house=None
        row={"date": cur.date().isoformat(), "activation": activation, "triggers": triggers,
             "country_chart_similarity": chart_match["score"],
             "global_historical_analogues": analogues[:10],
             "same_country_analogues": same_country[:6]}
        row["prediction_mode"]="astrological-event-classification"
        row["historical_analogue_summary"]= [f"{x['date']}: {x['country']} — {x['event']} ({x['type']})" for x in analogues[:8]]
        row["historical_evidence"]=same_country[:6] + analogues[:6]
        row["event_indications"]=_mundane_event_indications(triggers, natal, transit, natal_lagna, analogues)
        row["direct_prediction"]=(row["event_indications"][0]["reading"] if row["event_indications"] else
                                  "Astrological forecast signal: no specific event class crosses the configured combination threshold in this period.")
        row["deep_interpretation"]=deep_rules
        row["signal_level"]="high" if activation>=70 else ("moderate" if activation>=50 else "low")
        row["blunt_interpretation"]=_mundane_blunt_interpretation(triggers, activation)
        rows.append(row)
        cur += timedelta(days=step_days)
    return rows


def _event_class_predictions(forecast_rows: List[Dict[str, Any]], threshold: float = 60.0, top_k: int = 3) -> List[Dict[str, Any]]:
    """Collapse a historical forecast horizon to one prediction per event class."""
    preds = {}
    for fr in forecast_rows:
        for ind in fr.get('event_indications', []):
            score = float(ind.get('signal_score', 0))
            key = ind.get('event_class')
            if key and score >= threshold and (key not in preds or score > preds[key]['signal_score']):
                preds[key] = {
                    'event_class': key, 'label': ind.get('label', key), 'signal_score': score,
                    'signal_level': ind.get('signal_level'), 'forecast_date': fr.get('date')
                }
    return sorted(preds.values(), key=lambda x: (-x['signal_score'], x['event_class']))[:top_k]


def _match_predictions_to_actuals(predictions: List[Dict[str, Any]], actual_events: List[MundaneEvent]) -> Dict[str, Any]:
    """One-to-one exact-class matching so overlapping forecast windows cannot inflate hits."""
    remaining = list(actual_events)
    hits = []
    for pred in sorted(predictions, key=lambda x: -x['signal_score']):
        candidates = [e for e in remaining if e.event_class == pred['event_class']]
        if candidates:
            event = min(candidates, key=lambda e: e.local_date)
            remaining.remove(event)
            hits.append({'prediction': pred, 'actual': {'event': event.event_name, 'date': event.local_date, 'event_class': event.event_class}})
    return {'hits': hits, 'false_positives': [p for p in predictions if not any(h['prediction'] is p for h in hits)]}


def _run_backtest_segment(event: MundaneEvent, actual: List[MundaneEvent], start_date: str, end_date: str,
                          horizon_days: int, anchor_step_days: int, threshold: float, top_k: int) -> Dict[str, Any]:
    """Strict walk-forward replay for one contiguous time segment."""
    rows=[]
    anchor = datetime.fromisoformat(start_date).replace(tzinfo=ZoneInfo(event.timezone))
    end = datetime.fromisoformat(end_date).replace(tzinfo=ZoneInfo(event.timezone))
    while anchor <= end:
        horizon_end = min(anchor + timedelta(days=horizon_days), end + timedelta(days=1))
        forecast_rows = _scan_range(event, anchor, horizon_end, max(30, min(60, horizon_days)))
        preds = _event_class_predictions(forecast_rows, threshold, top_k)
        actual_window = [e for e in actual if anchor.date().isoformat() <= e.local_date < horizon_end.date().isoformat()]
        match = _match_predictions_to_actuals(preds, actual_window)
        rows.append({
            'anchor_date': anchor.date().isoformat(), 'horizon_end': horizon_end.date().isoformat(),
            'predicted_events': preds,
            'actual_events': [{'event':e.event_name,'date':e.local_date,'event_class':e.event_class} for e in actual_window],
            'hits': match['hits'],
            'false_positive_predictions': match['false_positives'],
            'missed_actual_events': [{'event':e.event_name,'date':e.local_date,'event_class':e.event_class}
                                     for e in actual_window if e.event_class not in {h['actual']['event_class'] for h in match['hits']}],
        })
        anchor += timedelta(days=anchor_step_days)
    predicted=sum(len(r['predicted_events']) for r in rows)
    actual_n=sum(len(r['actual_events']) for r in rows)
    hits=sum(len(r['hits']) for r in rows)
    precision=100*hits/max(1,predicted)
    recall=100*hits/max(1,actual_n)
    return {'rows':rows,'predicted':predicted,'actual':actual_n,'hits':hits,
            'precision_pct':round(precision,1),'recall_pct':round(recall,1),
            'f1_pct':round(2*precision*recall/max(0.001,precision+recall),1)}


def _tune_backtest_threshold(event: MundaneEvent, actual: List[MundaneEvent], start_date: str, end_date: str,
                             horizon_days: int, anchor_step_days: int, top_k: int = 3) -> Dict[str, Any]:
    """Choose threshold using development data only. Preference: precision >=80 with useful recall; otherwise max F1."""
    candidates=[]
    for threshold in (60,65,70,72,75,78,80,82,85,88,90,92,95):
        r=_run_backtest_segment(event,actual,start_date,end_date,horizon_days,anchor_step_days,threshold,top_k)
        candidates.append({'threshold':threshold, **{k:r[k] for k in ('predicted','actual','hits','precision_pct','recall_pct','f1_pct')}})
    qualifying=[x for x in candidates if x['precision_pct'] >= 80 and x['predicted'] > 0]
    if qualifying:
        chosen=max(qualifying,key=lambda x:(x['recall_pct'],x['f1_pct'],x['precision_pct']))
        criterion='highest recall among development thresholds reaching >=80% precision'
    else:
        chosen=max(candidates,key=lambda x:(x['f1_pct'],x['precision_pct'],x['recall_pct']))
        criterion='highest development F1 because no threshold reached 80% precision'
    return {'chosen':chosen,'candidates':candidates,'criterion':criterion}


def retrospective_event_forecast_backtest(country: str, start_date: str, end_date: str,
                                           horizon_days: int = 365, step_days: int = 90,
                                           development_end: str | None = None, holdout_start: str | None = None,
                                           threshold: float | None = None, top_k: int = 3) -> Dict[str, Any]:
    """Strict historical replay with development tuning and a blind chronological holdout.

    The forecast at anchor D only uses chart/transit information available at D. Actual
    events after D are never used to generate that forecast. Threshold selection is done
    on the development segment and then frozen for the holdout segment.
    """
    resolved=resolve_country_chart(country); event=MundaneEvent(**resolved['primary_chart'])
    actual=[e for e in BACKTEST_EVENTS if e.country==resolved['country'] and start_date <= e.local_date <= end_date]
    if not actual:
        return {'country':resolved['country'],'anchors_tested':0,'actual_events':0,'rows':[],
                'summary':'No documented backtest events in the selected range.'}
    # If no explicit split is supplied, use the first 60% of the date range for development.
    if development_end is None or holdout_start is None:
        a=datetime.fromisoformat(start_date); b=datetime.fromisoformat(end_date)
        split=a+(b-a)*0.6
        development_end=split.date().isoformat(); holdout_start=(split+timedelta(days=1)).date().isoformat()
    dev_actual=[e for e in actual if start_date <= e.local_date <= development_end]
    test_actual=[e for e in actual if holdout_start <= e.local_date <= end_date]
    if threshold is None:
        tuned=_tune_backtest_threshold(event,dev_actual,start_date,development_end,horizon_days,step_days,top_k)
        threshold=float(tuned['chosen']['threshold'])
    else:
        tuned={'chosen':{'threshold':threshold},'candidates':[],'criterion':'externally supplied/frozen threshold'}
    dev=_run_backtest_segment(event,dev_actual,start_date,development_end,horizon_days,step_days,threshold,top_k) if dev_actual else {'rows':[],'predicted':0,'actual':0,'hits':0,'precision_pct':0,'recall_pct':0,'f1_pct':0}
    test=_run_backtest_segment(event,test_actual,holdout_start,end_date,horizon_days,step_days,threshold,top_k) if test_actual else {'rows':[],'predicted':0,'actual':0,'hits':0,'precision_pct':0,'recall_pct':0,'f1_pct':0}
    return {
        'country':resolved['country'],'start_date':start_date,'end_date':end_date,'development_end':development_end,
        'holdout_start':holdout_start,'horizon_days':horizon_days,'step_days':step_days,'threshold':threshold,'top_k':top_k,
        'development':dev,'blind_holdout':test,'tuning':tuned,
        'anchors_tested':len(dev['rows'])+len(test['rows']),'actual_events_in_corpus':len(actual),
        'blind_holdout_precision_pct':test['precision_pct'],'blind_holdout_recall_pct':test['recall_pct'],
        'blind_holdout_f1_pct':test['f1_pct'],'meets_80_precision':test['precision_pct']>=80.0,
        'method':'Chronological train/tune/holdout replay. Threshold is selected only on the development period and frozen before the blind holdout. Predictions are one-per-class and actual events are one-to-one matched.',
        'interpretation':'The percentages measure agreement between this configured astrological classification engine and the bundled historical event corpus. They are not scientific proof of causation or general predictive accuracy.'
    }


def _add_period(start: datetime, amount: int, unit: str) -> datetime:
    if unit == "days": return start + timedelta(days=amount)
    if unit == "months":
        y=start.year+(start.month-1+amount)//12; m=(start.month-1+amount)%12+1
        import calendar
        return start.replace(year=y,month=m,day=min(start.day,calendar.monthrange(y,m)[1]))
    return start.replace(year=start.year+amount)


def _step_for(unit: str, amount: int) -> int:
    if unit == "days": return 1 if amount <= 60 else 7
    if unit == "months": return 30
    return 30 if amount <= 15 else 91


def scan_mundane_forecast(country: str, near_amount: int = 24, long_amount: int = 10,
                          near_unit: str = "months", long_unit: str = "years", **legacy) -> Dict[str, Any]:
    if "near_years" in legacy: near_amount, near_unit = int(legacy["near_years"]), "years"
    if "long_years" in legacy: long_amount, long_unit = int(legacy["long_years"]), "years"
    """Independent country forecast. No personal chart is involved."""
    resolved=resolve_country_chart(country); event=MundaneEvent(**resolved["primary_chart"])
    local_now=datetime.now(ZoneInfo(event.timezone)).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    period_start=legacy.get("period_start_date"); period_end=legacy.get("period_end_date")
    if bool(period_start) != bool(period_end): raise ValueError("Choose both a forecast start date and an end date, or leave both blank")
    if period_start and period_end:
        local_now=datetime.fromisoformat(str(period_start)).replace(tzinfo=ZoneInfo(event.timezone),hour=0,minute=0,second=0,microsecond=0)
        long_end=datetime.fromisoformat(str(period_end)).replace(tzinfo=ZoneInfo(event.timezone),hour=23,minute=59,second=59,microsecond=0)
        if long_end <= local_now: raise ValueError("Forecast end date must be after start date")
        if (long_end-local_now).days > 36525: raise ValueError("Forecast date range cannot exceed 100 years")
        days=(long_end-local_now).days
        step=1 if days<=60 else (7 if days<=365 else 30 if days<=3650 else 91)
        near_end=long_end
        near_rows=_scan_range(event,local_now,near_end,step)
        long_rows=[]
        near_amount=(days or 1); near_unit="days"; long_amount=0; long_unit="days"
    else:
        near_end=_add_period(local_now,near_amount,near_unit); long_end=_add_period(near_end,long_amount,long_unit)
        near_rows=_scan_range(event,local_now,near_end,_step_for(near_unit,near_amount))
        long_rows=_scan_range(event,near_end,long_end,_step_for(long_unit,long_amount))
    from .advanced import exact_planetary_events, eclipse_events
    exact=exact_planetary_events(local_now,long_end,event.timezone)
    eclipses=eclipse_events(local_now,long_end,event.timezone)
    combined=sorted(near_rows+long_rows,key=lambda x:(-x["activation"],x["date"]))
    return {"country":resolved["country"],"country_chart":event.__dict__,"start":local_now.date().isoformat(),"near_end":near_end.date().isoformat(),"long_end":long_end.date().isoformat(),
            "near_term":{"amount":near_amount,"unit":near_unit,"monthly":near_rows,"peaks":sorted(near_rows,key=lambda x:-x["activation"])[:12]},
            "long_term":{"amount":long_amount,"unit":long_unit,"monthly":long_rows,"peaks":sorted(long_rows,key=lambda x:-x["activation"])[:12]},
            "peaks":combined[:30],
            "exact_astronomical_events":exact,"eclipses":eclipses,
            "method":"Deterministic astrological event-classification engine: present/future signatures are evaluated against planetary/aspect/national-house combinations and compared with dated historical event charts, including country/event Lagna.",
            "prediction_mode":"astrological-event-classification",
            "event_class_count":len(MUNDANE_EVENT_CLASSES),
            "event_combination_rule_count":len(_mundane_event_combinations),
            "prediction_depth_layers":["summary","planet/aspect/national-house mechanism","historical analogue and corroboration cross-check"],
            "political_event_classes":["internal_unrest","public_uprising","leadership_transition","executive_removal","government_fall","constitutional_crisis"],
            "reading_style":"direct", "custom_period":bool(period_start and period_end), "requested_period":{"start":local_now.date().isoformat(),"end":long_end.date().isoformat()},
            "caveat":"Event indications are astrological forecast classifications, not verified factual statements about future events. Historical matches are displayed as evidence for interpretation."}


# Expanded date-oriented historical research corpus. Most entries below are date-only
# markers (12:00 local proxy) unless an event time is documented in the base corpus.
# They are useful for daily/slow-planet signature matching but should not be treated
# as precise timed event charts without archival time verification.
REFERENCE_EVENTS.extend([
    MundaneEvent('India','Sino-Indian War begins','1962-10-20','12:00:00','India',20.5937,78.9629,'Asia/Kolkata','conflict','Date-only historical marker; noon proxy for research matching.','border_clash'),
    MundaneEvent('India','Bangladesh Liberation War / India intervention','1971-12-03','12:00:00','India',20.5937,78.9629,'Asia/Kolkata','conflict','Date-only historical marker; noon proxy for research matching.','border_clash'),
    MundaneEvent('India','Pokhran-II nuclear tests','1998-05-11','12:00:00','Pokhran, India',27.095,71.752,'Asia/Kolkata','strategic','Date-only historical marker; noon proxy for research matching.'),
    MundaneEvent('India','Goods and Services Tax launched','2017-07-01','00:00:00','New Delhi, India',28.6139,77.2090,'Asia/Kolkata','economic','Midnight implementation marker; verify parliamentary/technical timing for precision.','economic_expansion'),
    MundaneEvent('India','COVID-19 national lockdown begins','2020-03-25','00:00:00','New Delhi, India',28.6139,77.2090,'Asia/Kolkata','crisis','Date/time of national restriction marker.'),
    MundaneEvent('Pakistan','First military coup','1958-10-07','12:00:00','Pakistan',30.3753,69.3451,'Asia/Karachi','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Pakistan','1971 war / secession crisis','1971-12-16','12:00:00','Pakistan',30.3753,69.3451,'Asia/Karachi','conflict','Date-only historical marker; noon proxy.'),
    MundaneEvent('Pakistan','Military coup of 1977','1977-07-05','12:00:00','Islamabad, Pakistan',33.6844,73.0479,'Asia/Karachi','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Pakistan','Military coup of 1999','1999-10-12','12:00:00','Islamabad, Pakistan',33.6844,73.0479,'Asia/Karachi','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Pakistan','No-confidence transition','2022-04-10','12:00:00','Islamabad, Pakistan',33.6844,73.0479,'Asia/Karachi','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Bangladesh','Assassination of Sheikh Mujibur Rahman','1975-08-15','12:00:00','Dhaka, Bangladesh',23.8103,90.4125,'Asia/Dhaka','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Bangladesh','Mass political transition','1990-12-06','12:00:00','Dhaka, Bangladesh',23.8103,90.4125,'Asia/Dhaka','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Bangladesh','Caretaker government crisis','2007-01-11','12:00:00','Dhaka, Bangladesh',23.8103,90.4125,'Asia/Dhaka','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('Bangladesh','Government transition','2024-08-05','12:00:00','Dhaka, Bangladesh',23.8103,90.4125,'Asia/Dhaka','political_transition','Date-only historical marker; noon proxy.'),
    MundaneEvent('United States','Pearl Harbor attack / US enters WWII','1941-12-07','07:48:00','Pearl Harbor, USA',21.3099,-157.8581,'Pacific/Honolulu','conflict','Historically documented local start time; verify archival conventions.'),
    MundaneEvent('United States','JFK assassination','1963-11-22','12:30:00','Dallas, USA',32.7767,-96.7970,'America/Chicago','political_crisis','Historically documented event time.'),
    MundaneEvent('United States','Apollo 11 Moon landing','1969-07-20','16:17:00','Moon / NASA mission','0','0','UTC','technology','Mission event; location is not terrestrial. Time marker retained for mundane research.'),
    MundaneEvent('United States','Nixon resignation','1974-08-09','12:00:00','Washington, USA',38.9072,-77.0369,'America/New_York','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('United States','2008 financial crisis marker','2008-09-15','12:00:00','New York, USA',40.7128,-74.0060,'America/New_York','economic','Date-only market crisis marker; noon proxy.'),
    MundaneEvent('United States','COVID-19 national emergency','2020-03-13','12:00:00','Washington, USA',38.9072,-77.0369,'America/New_York','crisis','Date-only national marker; noon proxy.'),
    MundaneEvent('United Kingdom','UK joins EEC','1973-01-01','00:00:00','London, UK',51.5074,-0.1278,'Europe/London','integration','Implementation date.'),
    MundaneEvent('United Kingdom','Brexit referendum','2016-06-23','12:00:00','London, UK',51.5074,-0.1278,'Europe/London','constitutional','Date-only national vote marker; noon proxy.'),
    MundaneEvent('United Kingdom','Brexit legal exit','2020-01-31','23:00:00','London, UK',51.5074,-0.1278,'Europe/London','constitutional','Exit time marker.'),
    MundaneEvent('France','May 1968 crisis marker','1968-05-13','12:00:00','Paris, France',48.8566,2.3522,'Europe/Paris','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('France','Mitterrand elected president','1981-05-10','12:00:00','Paris, France',48.8566,2.3522,'Europe/Paris','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('France','Euro referendum / Maastricht marker','1992-09-20','12:00:00','Paris, France',48.8566,2.3522,'Europe/Paris','integration','Date-only marker; noon proxy.'),
    MundaneEvent('Russia','Dissolution of Soviet Union','1991-12-26','12:00:00','Moscow, Russia',55.7558,37.6173,'Europe/Moscow','transition','Date-only marker; noon proxy.'),
    MundaneEvent('Russia','Russian financial crisis','1998-08-17','12:00:00','Moscow, Russia',55.7558,37.6173,'Europe/Moscow','economic','Date-only marker; noon proxy.'),
    MundaneEvent('Russia','Crimea annexation marker','2014-03-18','12:00:00','Moscow, Russia',55.7558,37.6173,'Europe/Moscow','geopolitical','Date-only marker; noon proxy.'),
    MundaneEvent('Russia','Invasion of Ukraine begins','2022-02-24','05:00:00','Moscow, Russia',55.7558,37.6173,'Europe/Moscow','conflict','Publicly reported launch-time marker; verify operational chronology for research use.'),
    MundaneEvent('China','Reform and opening begins','1978-12-18','12:00:00','Beijing, China',39.9042,116.4074,'Asia/Shanghai','economic','Date-only political-economic marker; noon proxy.'),
    MundaneEvent('China','1989 political crisis marker','1989-06-04','12:00:00','Beijing, China',39.9042,116.4074,'Asia/Shanghai','political_crisis','Date-only marker; noon proxy.'),
    MundaneEvent('China','China joins WTO','2001-12-11','00:00:00','Beijing, China',39.9042,116.4074,'Asia/Shanghai','economic','Accession date.'),
    MundaneEvent('China','COVID-19 outbreak global marker','2020-01-23','12:00:00','Wuhan, China',30.5928,114.3055,'Asia/Shanghai','crisis','Date-only marker; noon proxy.'),
    MundaneEvent('Japan','Asset bubble collapse marker','1991-03-01','12:00:00','Tokyo, Japan',35.6762,139.6503,'Asia/Tokyo','economic','Date-only economic marker; noon proxy.'),
    MundaneEvent('Japan','Tohoku earthquake and tsunami','2011-03-11','14:46:00','Japan',38.322,-142.369,'Asia/Tokyo','disaster','Earthquake epicenter coordinates are approximate; event time widely documented.'),
    MundaneEvent('Japan','COVID state of emergency marker','2020-04-07','12:00:00','Tokyo, Japan',35.6762,139.6503,'Asia/Tokyo','crisis','Date-only marker; noon proxy.'),
    MundaneEvent('Germany','Hitler appointed chancellor','1933-01-30','12:00:00','Berlin, Germany',52.5200,13.4050,'Europe/Berlin','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('Germany','Federal Republic founded','1949-05-23','12:00:00','Bonn, Germany',50.7374,7.0982,'Europe/Berlin','founding','Date-only marker; noon proxy.'),
    MundaneEvent('Germany','Berlin Wall falls','1989-11-09','18:53:00','Berlin, Germany',52.5200,13.4050,'Europe/Berlin','transition','Publicly reported press-conference timing marker; verify archival timestamp.'),
    MundaneEvent('Germany','Euro introduced as accounting currency','1999-01-01','00:00:00','Frankfurt, Germany',50.1109,8.6821,'Europe/Berlin','economic','Implementation date.'),
    MundaneEvent('South Africa','Nelson Mandela released','1990-02-11','15:00:00','Cape Town, South Africa',-33.9249,18.4241,'Africa/Johannesburg','political_transition','Publicly reported release-time marker.'),
    MundaneEvent('South Africa','First democratic election','1994-04-27','12:00:00','South Africa',-30.5595,22.9375,'Africa/Johannesburg','political_transition','Election date; noon proxy.'),
    MundaneEvent('Brazil','Military coup','1964-04-01','12:00:00','Brasilia, Brazil',-15.7939,-47.8828,'America/Sao_Paulo','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('Brazil','Constitution of Brazil','1988-10-05','12:00:00','Brasilia, Brazil',-15.7939,-47.8828,'America/Sao_Paulo','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Brazil','Impeachment of Dilma Rousseff','2016-08-31','12:00:00','Brasilia, Brazil',-15.7939,-47.8828,'America/Sao_Paulo','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('Brazil','2022 presidential election marker','2022-10-30','12:00:00','Brasilia, Brazil',-15.7939,-47.8828,'America/Sao_Paulo','political_transition','Election date; noon proxy.'),
    MundaneEvent('European Union','Lisbon Treaty enters into force','2009-12-01','00:00:00','Brussels, Belgium',50.8503,4.3517,'Europe/Brussels','integration','Implementation date.'),
    MundaneEvent('European Union','Euro currency launched','2002-01-01','00:00:00','Brussels, Belgium',50.8503,4.3517,'Europe/Brussels','economic','Currency implementation date.'),
])

# Additional source-oriented national charts and major manifestations. Date-only entries
# are intentionally marked as noon proxies so users can distinguish them from timed charts.
REFERENCE_EVENTS.extend([
    MundaneEvent('Canada','Canadian Confederation','1867-07-01','12:00:00','Ottawa, Canada',45.4215,-75.6972,'America/Toronto','founding','Date-only marker; noon proxy. Verify archival proclamation timing for timed research.'),
    MundaneEvent('Canada','Constitution Act 1982','1982-04-17','12:00:00','Ottawa, Canada',45.4215,-75.6972,'America/Toronto','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Australia','Federation of Australia','1901-01-01','00:00:00','Sydney, Australia',-33.8688,151.2093,'Australia/Sydney','founding','Federation implementation date.'),
    MundaneEvent('Australia','Constitution referendum marker','1999-11-06','12:00:00','Canberra, Australia',-35.2809,149.1300,'Australia/Sydney','constitutional','Date-only marker; noon proxy.'),
    MundaneEvent('New Zealand','Treaty of Waitangi marker','1840-02-06','12:00:00','Waitangi, New Zealand',-35.2647,174.0804,'Pacific/Auckland','founding','Historical signing date; timing conventions vary by local signing sequence.'),
    MundaneEvent('New Zealand','Dominion status','1907-09-26','12:00:00','Wellington, New Zealand',-41.2866,174.7756,'Pacific/Auckland','constitutional','Date-only marker; noon proxy.'),
    MundaneEvent('Italy','Kingdom of Italy proclaimed','1861-03-17','12:00:00','Turin, Italy',45.0703,7.6869,'Europe/Rome','founding','Date-only marker; noon proxy.'),
    MundaneEvent('Italy','Italian Republic referendum','1946-06-02','12:00:00','Rome, Italy',41.9028,12.4964,'Europe/Rome','transition','Date-only national vote marker; noon proxy.'),
    MundaneEvent('Spain','Spanish Constitution approved','1978-12-06','12:00:00','Madrid, Spain',40.4168,-3.7038,'Europe/Madrid','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Spain','Spanish transition marker','1975-11-20','12:00:00','Madrid, Spain',40.4168,-3.7038,'Europe/Madrid','political_transition','Date-only marker; noon proxy.'),
    MundaneEvent('Israel','Declaration of the State of Israel','1948-05-14','16:00:00','Tel Aviv, Israel',32.0853,34.7818,'Asia/Jerusalem','founding','Publicly documented declaration time; verify archival time standard.','leadership_transition'),
    MundaneEvent('Israel','Six-Day War begins','1967-06-05','08:00:00','Israel',31.0461,34.8516,'Asia/Jerusalem','conflict','Approximate operational start marker; verify archival convention.','border_clash'),
    MundaneEvent('Iran','Islamic Republic referendum','1979-04-01','12:00:00','Tehran, Iran',35.6892,51.3890,'Asia/Tehran','transition','Date-only referendum marker; noon proxy.'),
    MundaneEvent('Iran','Islamic Republic constitution','1979-12-03','12:00:00','Tehran, Iran',35.6892,51.3890,'Asia/Tehran','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Turkey','Republic of Turkey proclaimed','1923-10-29','12:00:00','Ankara, Turkey',39.9334,32.8597,'Europe/Istanbul','founding','Date-only marker; noon proxy.'),
    MundaneEvent('Turkey','Constitutional referendum marker','1982-11-07','12:00:00','Ankara, Turkey',39.9334,32.8597,'Europe/Istanbul','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Saudi Arabia','Kingdom of Saudi Arabia unified','1932-09-23','12:00:00','Riyadh, Saudi Arabia',24.7136,46.6753,'Asia/Riyadh','founding','Date-only unification marker; noon proxy.'),
    MundaneEvent('Saudi Arabia','Oil nationalization marker','1980-11-01','12:00:00','Riyadh, Saudi Arabia',24.7136,46.6753,'Asia/Riyadh','economic','Date-only corporate/state-control marker; noon proxy.'),
    MundaneEvent('Indonesia','Proclamation of Indonesian Independence','1945-08-17','10:00:00','Jakarta, Indonesia',-6.2088,106.8456,'Asia/Jakarta','independence','Commonly documented proclamation time; verify archival source for research-grade timing.'),
    MundaneEvent('Indonesia','Reformasi transition','1998-05-21','12:00:00','Jakarta, Indonesia',-6.2088,106.8456,'Asia/Jakarta','political_transition','Date-only transition marker; noon proxy.'),
    MundaneEvent('Mexico','Mexican War of Independence begins','1810-09-16','12:00:00','Dolores Hidalgo, Mexico',21.1561,-100.9324,'America/Mexico_City','independence','Date-only historical marker; noon proxy.'),
    MundaneEvent('Mexico','Constitution of 1917','1917-02-05','12:00:00','Queretaro, Mexico',20.5888,-100.3899,'America/Mexico_City','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Argentina','Declaration of Independence','1816-07-09','12:00:00','Tucuman, Argentina',-26.8083,-65.2176,'America/Argentina/Tucuman','independence','Date-only marker; noon proxy.'),
    MundaneEvent('Argentina','Constitution of Argentina','1853-05-01','12:00:00','Santa Fe, Argentina',-31.6333,-60.7000,'America/Argentina/Buenos_Aires','constitution','Date-only marker; noon proxy.'),
    MundaneEvent('Nigeria','Independence of Nigeria','1960-10-01','12:00:00','Lagos, Nigeria',6.5244,3.3792,'Africa/Lagos','independence','Date-only marker; noon proxy.'),
    MundaneEvent('Nigeria','Fourth Republic inauguration','1999-05-29','12:00:00','Abuja, Nigeria',9.0765,7.3986,'Africa/Lagos','transition','Date-only marker; noon proxy.'),
    MundaneEvent('Egypt','Egyptian Republic proclaimed','1953-06-18','12:00:00','Cairo, Egypt',30.0444,31.2357,'Africa/Cairo','transition','Date-only marker; noon proxy.'),
    MundaneEvent('Egypt','Egyptian Revolution 2011 marker','2011-01-25','12:00:00','Cairo, Egypt',30.0444,31.2357,'Africa/Cairo','political_transition','Date-only protest-wave marker; noon proxy.'),
    MundaneEvent('South Korea','Republic of Korea established','1948-08-15','12:00:00','Seoul, South Korea',37.5665,126.9780,'Asia/Seoul','founding','Date-only marker; noon proxy.'),
    MundaneEvent('South Korea','Asian financial crisis marker','1997-11-21','12:00:00','Seoul, South Korea',37.5665,126.9780,'Asia/Seoul','economic','Date-only market/IMF crisis marker; noon proxy.'),
    MundaneEvent('Ukraine','Independence of Ukraine','1991-08-24','12:00:00','Kyiv, Ukraine',50.4501,30.5234,'Europe/Kyiv','independence','Date-only marker; noon proxy.'),
    MundaneEvent('Ukraine','Orange Revolution marker','2004-11-22','12:00:00','Kyiv, Ukraine',50.4501,30.5234,'Europe/Kyiv','political_transition','Date-only protest marker; noon proxy.'),
])

# Extend common aliases after corpus expansion.
COUNTRY_ALIASES.update({
    'canada':'Canada','australia':'Australia','new zealand':'New Zealand','nz':'New Zealand',
    'italy':'Italy','spain':'Spain','israel':'Israel','iran':'Iran','turkey':'Turkey',
    'saudi arabia':'Saudi Arabia','indonesia':'Indonesia','mexico':'Mexico','argentina':'Argentina',
    'nigeria':'Nigeria','egypt':'Egypt','south korea':'South Korea','korea':'South Korea','ukraine':'Ukraine',
})


# World historical corpus: source-backed, date-oriented events. The bundled national
# corpus remains usable offline; this cache can be populated with 1,000+ events via
# scripts/sync_world_events.py from the public CC-BY-SA historical-events dataset.
_WORLD_EVENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "world_historical_events.json"
WORLD_EVENTS: List[MundaneEvent] = []
try:
    if _WORLD_EVENTS_PATH.exists():
        for _row in json.loads(_WORLD_EVENTS_PATH.read_text(encoding="utf-8")):
            WORLD_EVENTS.append(MundaneEvent(**_row))
except Exception:
    WORLD_EVENTS = []

def world_historical_events(limit: int = 1000) -> List[MundaneEvent]:
    return WORLD_EVENTS[:max(0, int(limit))]

def reload_world_events() -> int:
    global WORLD_EVENTS
    WORLD_EVENTS=[]
    try:
        if _WORLD_EVENTS_PATH.exists():
            for _row in json.loads(_WORLD_EVENTS_PATH.read_text(encoding="utf-8")):
                WORLD_EVENTS.append(MundaneEvent(**_row))
    except Exception:
        WORLD_EVENTS=[]
    return len(WORLD_EVENTS)

def world_event_status() -> Dict[str, Any]:
    return {
        "loaded": len(WORLD_EVENTS),
        "target": 1000,
        "ready": len(WORLD_EVENTS) >= 1000,
        "source": "snauhaus/historic_events (CC BY-SA 3.0; Wikimedia/Wikipedia-derived)",
        "cache": str(_WORLD_EVENTS_PATH),
    }
