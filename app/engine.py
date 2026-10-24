from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import math
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import swisseph as swe

from .numerology import analyze as analyze_numerology
from .yoga_catalog import catalog_status, dosha_catalog_status

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ABBR = ["Ar", "Ta", "Ge", "Ca", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}
PLANETS = list(PLANET_IDS)

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_META = {
    "Ashwini": {"deity":"Ashwini Kumaras","symbol":"Horse head","shakti":"Quick healing / initiation","gana":"Deva","yoni":"Horse","nadi":"Adi","quality":"Swift"},
    "Bharani": {"deity":"Yama","symbol":"Yoni","shakti":"Bearing / restraint","gana":"Manushya","yoni":"Elephant","nadi":"Madhya","quality":"Fierce"},
    "Krittika": {"deity":"Agni","symbol":"Razor / flame","shakti":"Purification","gana":"Rakshasa","yoni":"Sheep","nadi":"Antya","quality":"Sharp"},
    "Rohini": {"deity":"Prajapati","symbol":"Chariot","shakti":"Growth / creation","gana":"Manushya","yoni":"Serpent","nadi":"Antya","quality":"Fixed"},
    "Mrigashira": {"deity":"Soma","symbol":"Deer head","shakti":"Seeking / searching","gana":"Deva","yoni":"Serpent","nadi":"Madhya","quality":"Soft"},
    "Ardra": {"deity":"Rudra","symbol":"Teardrop","shakti":"Renewal through upheaval","gana":"Manushya","yoni":"Dog","nadi":"Adi","quality":"Sharp"},
    "Punarvasu": {"deity":"Aditi","symbol":"Quiver of arrows","shakti":"Return / restoration","gana":"Deva","yoni":"Cat","nadi":"Adi","quality":"Movable"},
    "Pushya": {"deity":"Brihaspati","symbol":"Flower / udder","shakti":"Nourishment","gana":"Deva","yoni":"Sheep","nadi":"Madhya","quality":"Light"},
    "Ashlesha": {"deity":"Nagas","symbol":"Coiled serpent","shakti":"Binding / insight","gana":"Rakshasa","yoni":"Cat","nadi":"Antya","quality":"Sharp"},
    "Magha": {"deity":"Pitrs","symbol":"Royal throne","shakti":"Ancestral authority","gana":"Rakshasa","yoni":"Rat","nadi":"Antya","quality":"Fierce"},
    "Purva Phalguni": {"deity":"Bhaga","symbol":"Front legs of cot","shakti":"Enjoyment / union","gana":"Manushya","yoni":"Rat","nadi":"Madhya","quality":"Fierce"},
    "Uttara Phalguni": {"deity":"Aryaman","symbol":"Back legs of cot","shakti":"Patronage / agreements","gana":"Manushya","yoni":"Cow","nadi":"Adi","quality":"Fixed"},
    "Hasta": {"deity":"Savitar","symbol":"Hand","shakti":"Skill / manifestation","gana":"Deva","yoni":"Buffalo","nadi":"Adi","quality":"Light"},
    "Chitra": {"deity":"Tvashtar","symbol":"Bright jewel","shakti":"Craft / form","gana":"Rakshasa","yoni":"Tiger","nadi":"Madhya","quality":"Soft"},
    "Swati": {"deity":"Vayu","symbol":"Young shoot / wind","shakti":"Independence / movement","gana":"Deva","yoni":"Buffalo","nadi":"Antya","quality":"Movable"},
    "Vishakha": {"deity":"Indra-Agni","symbol":"Triumphal arch","shakti":"Focused achievement","gana":"Rakshasa","yoni":"Tiger","nadi":"Antya","quality":"Fierce"},
    "Anuradha": {"deity":"Mitra","symbol":"Lotus / staff","shakti":"Devotion / alliance","gana":"Deva","yoni":"Deer","nadi":"Madhya","quality":"Soft"},
    "Jyeshtha": {"deity":"Indra","symbol":"Earring / circular talisman","shakti":"Protection / seniority","gana":"Rakshasa","yoni":"Deer","nadi":"Adi","quality":"Sharp"},
    "Mula": {"deity":"Nirriti","symbol":"Roots","shakti":"Dissolution / root-seeking","gana":"Rakshasa","yoni":"Dog","nadi":"Adi","quality":"Sharp"},
    "Purva Ashadha": {"deity":"Apas","symbol":"Fan / winnowing basket","shakti":"Invigoration","gana":"Manushya","yoni":"Monkey","nadi":"Madhya","quality":"Fierce"},
    "Uttara Ashadha": {"deity":"Vishvedevas","symbol":"Elephant tusk","shakti":"Final victory / universal duty","gana":"Manushya","yoni":"Mongoose","nadi":"Antya","quality":"Fixed"},
    "Shravana": {"deity":"Vishnu","symbol":"Ear","shakti":"Listening / connection","gana":"Deva","yoni":"Monkey","nadi":"Antya","quality":"Movable"},
    "Dhanishtha": {"deity":"Vasus","symbol":"Drum","shakti":"Abundance / rhythm","gana":"Rakshasa","yoni":"Lion","nadi":"Madhya","quality":"Movable"},
    "Shatabhisha": {"deity":"Varuna","symbol":"Circle / hundred healers","shakti":"Healing / containment","gana":"Rakshasa","yoni":"Horse","nadi":"Adi","quality":"Movable"},
    "Purva Bhadrapada": {"deity":"Aja Ekapada","symbol":"Front legs of funeral cot","shakti":"Transformation / intensity","gana":"Manushya","yoni":"Lion","nadi":"Adi","quality":"Fierce"},
    "Uttara Bhadrapada": {"deity":"Ahirbudhnya","symbol":"Back legs of funeral cot","shakti":"Depth / stability","gana":"Manushya","yoni":"Cow","nadi":"Madhya","quality":"Fixed"},
    "Revati": {"deity":"Pushan","symbol":"Fish / drum","shakti":"Safe journeys / nourishment","gana":"Deva","yoni":"Elephant","nadi":"Antya","quality":"Soft"},
}

LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
NATURAL_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
EXALTATIONS = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6, "Rahu": 1}
DEBILITATIONS = {v: (s + 6) % 12 for v, s in EXALTATIONS.items()}
OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
    "Rahu": set(), "Ketu": set(),
}
MULATRIKONA = {"Sun": 4, "Moon": 1, "Mars": 0, "Mercury": 5, "Jupiter": 8, "Venus": 6, "Saturn": 10}
COMBUSTION_ORB = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}

DIGNITY = {
    "exalted": "Exalted",
    "own": "Own sign",
    "moolatrikona": "Moolatrikona",
    "debilitated": "Debilitated",
    "neutral": "Neutral",
}

# Standard Parashari divisional charts commonly used in production Jyotish systems.
VARGAS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
engine_logger = logging.getLogger("jyotish_lab.engine")

def engine_phase(message: str, *args):
    try:
        line = message % args if args else message
    except Exception:
        line = f"{message} {args}"
    engine_logger.info("%s", line)

VARGA_NAMES = {
    1: "Rashi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsha", 7: "Saptamsha",
    9: "Navamsha", 10: "Dashamsha", 12: "Dwadashamsha", 16: "Shodashamsha",
    20: "Vimshamsha", 24: "Chaturvimshamsha", 27: "Saptavimshamsha", 30: "Trimshamsha",
    40: "Khavedamsha", 45: "Akshavedamsha", 60: "Shashtiamsha",
}

_VARGA_METHODS = {
    1: "D1 Rashi: natal sidereal signs",
    2: "D2 Hora: odd signs Sun/Moon halves; even signs reversed",
    3: "D3 Drekkana: same sign, 5th, 9th from natal sign",
    4: "D4 Chaturthamsha: movable same; fixed 4th; dual 7th",
    7: "D7 Saptamsha: odd same; even 7th from natal sign",
    9: "D9 Navamsha: movable same; fixed 9th; dual 5th",
    10: "D10 Dashamsha: odd same; even 9th from natal sign",
    12: "D12 Dwadashamsha: counted forward from natal sign",
    16: "D16 Shodashamsha: movable Aries; fixed Leo; dual Sagittarius",
    20: "D20 Vimshamsha: movable Aries; fixed Sagittarius; dual Leo",
    24: "D24 Chaturvimshamsha: odd Leo; even Cancer",
    27: "D27 Bhamsa: fire Aries; earth Cancer; air Libra; water Capricorn",
    30: "D30 Trimshamsha: odd 5/5/8/7/5° Mars-Saturn-Jupiter-Mercury-Venus; even 5/7/8/5/5° reversed with Libra/Virgo/Pisces/Capricorn/Scorpio sign targets",
    40: "D40 Khavedamsha: odd Aries; even Libra",
    45: "D45 Akshavedamsha: movable Aries; fixed Leo; dual Sagittarius",
    60: "D60 Shashtiamsha: 60 half-degree portions counted forward from the natal sign; traditional amsa-name sequence reverses in even signs",
}

@dataclass(frozen=True)
class BirthData:
    name: str
    dob: date
    tob: str
    latitude: float
    longitude: float
    timezone: str
    place: str = ""

    @property
    def local_dt(self) -> datetime:
        hh, mm = self.tob.split(":")[:2]
        ss = int(self.tob.split(":")[2]) if len(self.tob.split(":")) > 2 else 0
        return datetime(self.dob.year, self.dob.month, self.dob.day, int(hh), int(mm), ss, tzinfo=ZoneInfo(self.timezone))

    @property
    def utc_dt(self) -> datetime:
        return self.local_dt.astimezone(timezone.utc)


def norm360(x: float) -> float:
    return x % 360.0


def sign_index(lon: float) -> int:
    return int(norm360(lon) // 30.0)


def deg_in_sign(lon: float) -> float:
    return norm360(lon) % 30.0


def angular_distance(a: float, b: float) -> float:
    d = abs(norm360(a) - norm360(b))
    return min(d, 360 - d)


def sign_distance(a: int, b: int) -> int:
    return (b - a) % 12


def nakshatra_details(lon: float) -> Dict[str, Any]:
    span = 360 / 27
    idx = min(26, int(norm360(lon) // span))
    within = norm360(lon) - idx * span
    pada = min(4, int(within // (span / 4)) + 1)
    name = NAKSHATRAS[idx]
    meta = NAKSHATRA_META[name]
    return {
        "name": name, "index": idx + 1, "pada": pada,
        "degree": round(within, 6),
        **meta,
        "vimshottari_lord": _vimshottari_order()[idx % 9][0] if "_vimshottari_order" in globals() else None,
    }


def _time_to_jd(utc_dt: datetime) -> float:
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                      utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600)


def _calc_planets(jd: float) -> Dict[str, Dict[str, Any]]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    out: Dict[str, Dict[str, Any]] = {}
    for name, pid in PLANET_IDS.items():
        xx, ret = swe.calc_ut(jd, pid, flags)
        lon, lat, dist, speed_lon = xx[:4]
        out[name] = {
            "longitude": norm360(lon),
            "sign_index": sign_index(lon),
            "sign": SIGNS[sign_index(lon)],
            "degree_in_sign": round(deg_in_sign(lon), 8),
            "latitude": lat,
            "distance_au": dist,
            "speed_longitude": speed_lon,
            "retrograde": speed_lon < 0,
        }
    # Ketu is exactly opposite the selected node.
    ketu_lon=norm360(out["Rahu"]["longitude"] + 180)
    out["Ketu"] = {
        "longitude": ketu_lon,
        "sign_index": sign_index(ketu_lon),
        "sign": SIGNS[sign_index(ketu_lon)],
        "degree_in_sign": round(deg_in_sign(ketu_lon), 8),
        "latitude": -out["Rahu"]["latitude"],
        "distance_au": out["Rahu"]["distance_au"],
        "speed_longitude": out["Rahu"]["speed_longitude"],
        "retrograde": True,
    }
    return out


def _dignity(planet: str, sign: int) -> str:
    if planet in EXALTATIONS and sign == EXALTATIONS[planet]:
        return DIGNITY["exalted"]
    if planet in DEBILITATIONS and sign == DEBILITATIONS[planet]:
        return DIGNITY["debilitated"]
    if sign == MULATRIKONA.get(planet, -99):
        return DIGNITY["moolatrikona"]
    if sign in OWN_SIGNS.get(planet, set()):
        return DIGNITY["own"]
    return DIGNITY["neutral"]


def _aspected_house_offsets(planet: str) -> Tuple[int, ...]:
    if planet == "Mars":
        return (3, 6, 7)  # 4th, 7th, 8th from 0-indexed origin house
    if planet == "Jupiter":
        return (4, 6, 8)  # 5th, 7th, 9th
    if planet == "Saturn":
        return (2, 6, 9)  # 3rd, 7th, 10th
    return (6,)


def _whole_sign_house(lagna_sign: int, planet_sign: int) -> int:
    return ((planet_sign - lagna_sign) % 12) + 1


def _varga_sign(lon: float, division: int) -> int:
    """Parashari-inspired standard varga mapper for the 16 principal charts.

    The mapping is intentionally explicit and isolated so alternative schools can
    be added without touching the astronomical layer. D1 uses the natal sign.
    """
    s = sign_index(lon)
    d = deg_in_sign(lon)
    if division == 1:
        return s
    part = 30.0 / division
    n = min(division - 1, int(d / part))

    if division == 2:  # Hora: odd = Sun/Moon halves; even reversed.
        odd = s % 2 == 0
        return 4 if (n == 0) == odd else 3
    if division == 3:  # Drekkana: trines from sign.
        return (s + (0 if n == 0 else 5 if n == 1 else 8)) % 12
    if division == 4:
        # Chaturthamsha: movable starts from the natal sign, fixed from the 4th,
        # dual from the 7th; subsequent quarters advance zodiacally.
        if s in (0, 3, 6, 9):
            start = s
        elif s in (1, 4, 7, 10):
            start = (s + 3) % 12
        else:
            start = (s + 6) % 12
        return (start + n) % 12
    if division == 7:
        start = s if s % 2 == 0 else (s + 6) % 12
        return (start + n) % 12
    if division == 9:
        # Navamsha: movable signs start from themselves, fixed signs from
        # the 9th sign, and dual signs from the 5th sign.
        if s in (0, 3, 6, 9):
            start = s
        elif s in (1, 4, 7, 10):
            start = (s + 8) % 12
        else:
            start = (s + 4) % 12
        return (start + n) % 12
    if division == 10:
        start = s if s % 2 == 0 else (s + 8) % 12
        return (start + n) % 12
    if division == 12:
        return (s + n) % 12
    if division == 16:
        # Shodashamsha: movable from Aries, fixed from Leo, dual from Sagittarius.
        if s in (0, 3, 6, 9):
            start = 0
        elif s in (1, 4, 7, 10):
            start = 4
        else:
            start = 8
        return (start + n) % 12
    if division == 20:
        # Vimshamsha: movable from Aries, fixed from Sagittarius, dual from Leo.
        if s in (0, 3, 6, 9):
            start = 0
        elif s in (1, 4, 7, 10):
            start = 8
        else:
            start = 4
        return (start + n) % 12
    if division == 24:
        # Odd signs count from Leo; even signs from Cancer.
        start = 4 if s % 2 == 0 else 3
        return (start + n) % 12
    if division == 27:
        # Bhamsa/Nakshatramsa: seed by element — fire from Aries, earth
        # from Cancer, air from Libra, water from Capricorn.
        if s in (0, 4, 8):
            start = 0
        elif s in (1, 5, 9):
            start = 3
        elif s in (2, 6, 10):
            start = 6
        else:
            start = 9
        return (start + n) % 12
    if division == 30:
        # Classical Parashari Trimshamsha is NOT an equal 1-degree division.
        # Odd signs: 5° Mars -> Aries, 5° Saturn -> Aquarius,
        # 8° Jupiter -> Sagittarius, 7° Mercury -> Gemini, 5° Venus -> Libra.
        # Even signs reverse the ruler order and use the corresponding even
        # sign owned by each ruler: Libra, Virgo, Pisces, Capricorn, Scorpio.
        if s % 2 == 0:  # odd zodiac signs: Aries, Gemini, Leo, Libra, Sagittarius, Aquarius
            bands = (
                (5.0, 0),   # Mars -> Aries
                (10.0, 10), # Saturn -> Aquarius
                (18.0, 8),  # Jupiter -> Sagittarius
                (25.0, 2),  # Mercury -> Gemini
                (30.0, 6),  # Venus -> Libra
            )
        else:  # even zodiac signs: Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces
            bands = (
                (5.0, 6),   # Venus -> Libra: 0°–5°
                (10.0, 5),  # Mercury -> Virgo: 5°–10°
                (18.0, 11), # Jupiter -> Pisces: 10°–18°
                (25.0, 9),  # Saturn -> Capricorn: 18°–25°
                (30.0, 7),  # Mars -> Scorpio: 25°–30°
            )
        for edge, target in bands:
            if d < edge:
                return target
        return bands[-1][1]
    if division == 40:
        # Khavedamsha: odd signs count from Aries; even signs from Libra.
        start = 0 if s % 2 == 0 else 6
        return (start + n) % 12
    if division == 45:
        start = 0 if s % 3 == 0 else 4 if s % 3 == 1 else 8
        return (start + n) % 12
    if division == 60:
        # Shashtiamsha sign placement counts forward from the natal sign for
        # both odd and even signs. The odd/even reversal belongs to the named
        # Shashtiamsha sequence, not to the sign remapping itself.
        return (s + n) % 12
    # Fallback for exploratory divisions: equal-part zodiac projection.
    return (s + n) % 12


def calculate_divisional_charts(planets: Mapping[str, Mapping[str, Any]], lagna_longitude: float | None = None) -> Dict[str, Dict[str, Any]]:
    charts: Dict[str, Dict[str, Any]] = {}
    for d in VARGAS:
        name = f"D{d}"
        lagna_sign = _varga_sign(lagna_longitude, d) if lagna_longitude is not None else None
        pdata = {}
        for p, dat in planets.items():
            sidx = _varga_sign(dat["longitude"], d)
            pdata[p] = {"sign_index": sidx, "sign": SIGNS[sidx], "house": _whole_sign_house(lagna_sign, sidx) if lagna_sign is not None else None}
        charts[name] = {
            "division": d, "name": VARGA_NAMES[d], "lagna_sign_index": lagna_sign,
            "lagna_sign": SIGNS[lagna_sign] if lagna_sign is not None else None,
            "method": _VARGA_METHODS.get(d, "Parashari divisional mapping"),
            "part_size_degrees": round(30.0 / d, 8),
            "planets": pdata,
        }
    return charts


def _vimshottari_order() -> List[Tuple[str, int]]:
    return [("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
            ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)]


def _nakshatra_lord(idx: int) -> str:
    return _vimshottari_order()[idx % 9][0]


def vimshottari_dasha(moon_lon: float, start_dt: datetime, years: int = 5, levels: int = 5) -> Dict[str, Any]:
    """Generate up to five levels of Vimshottari periods starting from birth.

    Duration is scaled on the Moon's fraction through its birth nakshatra, then
    nested recursively by the same proportional cycle. Dates are approximate to
    the astronomical model's time resolution, suitable for timing windows rather
    than deterministic event claims.
    """
    span = 360 / 27
    nak_idx = int(norm360(moon_lon) // span)
    within = norm360(moon_lon) - nak_idx * span
    fraction_remaining = (span - within) / span
    order = _vimshottari_order()
    first_i = [p for p, _ in order].index(_nakshatra_lord(nak_idx))
    horizon = start_dt + timedelta(days=365.2425 * years)

    def build_level(base_start: datetime, lord_i: int, duration_days: float, depth: int) -> List[Dict[str, Any]]:
        if depth > levels:
            return []
        result: List[Dict[str, Any]] = []
        cur = base_start
        for k in range(9):
            idx = (lord_i + k) % 9
            lord, yrs = order[idx]
            sub_days = duration_days * yrs / 120.0
            end = cur + timedelta(days=sub_days)
            node = {"lord": lord, "start": cur.isoformat(), "end": end.isoformat(), "level": depth}
            if depth < levels:
                node["children"] = build_level(cur, idx, sub_days, depth + 1)
            result.append(node)
            cur = end
        return result

    first_lord, first_years = order[first_i]
    first_days = 365.2425 * first_years * fraction_remaining
    periods = []
    cur = start_dt
    i = first_i
    remaining_first = True
    while cur < horizon:
        lord, yrs = order[i]
        duration = first_days if remaining_first else 365.2425 * yrs
        end = min(cur + timedelta(days=duration), horizon)
        node = {"lord": lord, "start": cur.isoformat(), "end": end.isoformat(), "level": 1,
                "children": build_level(cur, i, duration, 2) if levels > 1 else []}
        periods.append(node)
        cur = end
        i = (i + 1) % 9
        remaining_first = False
    return {"nakshatra": NAKSHATRAS[nak_idx], "starting_lord": first_lord, "periods": periods, "cycle_years": 120}


def vimshottari_mahadasha_timeline(moon_lon: float, start_dt: datetime, years_forward: int = 60) -> List[Dict[str, Any]]:
    """Lightweight full Mahadasha timeline for historical/current/future context.

    Only Mahadasha nodes are generated here; detailed five-level nesting remains in
    the forecast-relevant hierarchy to keep API payloads responsive.
    """
    span=360/27; nak_idx=int(norm360(moon_lon)//span); within=norm360(moon_lon)-nak_idx*span
    fraction_remaining=(span-within)/span; order=_vimshottari_order(); first_i=[p for p,_ in order].index(_nakshatra_lord(nak_idx))
    horizon=start_dt+timedelta(days=365.2425*years_forward)
    out=[]; cur=start_dt; i=first_i; first=True
    while cur<horizon:
        lord,yrs=order[i]; duration=365.2425*yrs*fraction_remaining if first else 365.2425*yrs
        end=cur+timedelta(days=duration)
        out.append({'lord':lord,'start':cur.isoformat(),'end':end.isoformat(),'level':1})
        cur=end; i=(i+1)%9; first=False
    return out


def panchanga(jd_ut: float) -> Dict[str, Any]:
    # Tithi and solar-lunar angular relationships.
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    sun = swe.calc_ut(jd_ut, swe.SUN, flags)[0][0]
    moon = swe.calc_ut(jd_ut, swe.MOON, flags)[0][0]
    elong = norm360(moon - sun)
    tithi = int(elong // 12) + 1
    yoga_val = norm360(sun + moon)
    yoga = int(yoga_val // (360 / 27)) + 1
    nak = nakshatra_details(moon)
    return {"tithi": tithi, "yoga_number": yoga, "nakshatra": nak["name"], "nakshatra_pada": nak["pada"], "elongation": elong}


def ashtakavarga(planet_signs: Mapping[str, int]) -> Dict[str, Any]:
    """Compute a transparent sign-based approximation of bindu scores.

    This implementation follows the traditional idea of contributor signs and
    yields reproducible BAV/SAV matrices. The contributor rules are deliberately
    centralized so they can be replaced with a school-specific table later.
    """
    contrib = {
        "Sun": {0, 2, 4, 7, 9, 10},
        "Moon": {0, 1, 3, 4, 6, 7, 10},
        "Mars": {0, 2, 3, 5, 7, 10, 11},
        "Mercury": {0, 1, 2, 4, 5, 6, 8, 10, 11},
        "Jupiter": {0, 2, 3, 4, 6, 8, 10, 11},
        "Venus": {0, 1, 2, 3, 4, 5, 7, 8, 9, 11},
        "Saturn": {0, 2, 4, 5, 8, 9, 11},
    }
    bav = {}
    for p, allowed in contrib.items():
        natal = planet_signs[p]
        bav[p] = [1 if ((s - natal) % 12) in allowed else 0 for s in range(12)]
    sav = [sum(bav[p][s] for p in bav) for s in range(12)]
    return {"bav": bav, "sav": sav, "total": sum(sav)}


def sahams(planets: Mapping[str, Mapping[str, Any]], lagna: float, night_birth: bool) -> Dict[str, float]:
    """Tajika-style Saham subset with documented, commonly reproduced formulas.

    The formulas vary between schools; the app surfaces the formula in the report
    rather than pretending there is a single universal definition.
    """
    L = lagna
    Sun = planets["Sun"]["longitude"]
    Moon = planets["Moon"]["longitude"]
    Mars = planets["Mars"]["longitude"]
    Jupiter = planets["Jupiter"]["longitude"]
    Venus = planets["Venus"]["longitude"]
    Saturn = planets["Saturn"]["longitude"]
    formulas: Dict[str, float] = {}
    if night_birth:
        formulas["Punya"] = norm360(L + Sun - Moon)
        formulas["Vidya"] = norm360(L + Moon - Sun)
        formulas["Yasas"] = norm360(L + formulas["Punya"] - Jupiter)
        formulas["Mitra"] = norm360(Venus + formulas["Punya"] - Jupiter)
    else:
        formulas["Punya"] = norm360(L + Moon - Sun)
        formulas["Vidya"] = norm360(L + Sun - Moon)
        formulas["Yasas"] = norm360(L + Jupiter - formulas["Punya"])
        formulas["Mitra"] = norm360(Venus + Jupiter - formulas["Punya"])
    formulas["Mahatmya"] = norm360(L + formulas["Punya"] - Mars)
    formulas["Karma"] = norm360(L + Mars - Sun)
    formulas["Vivaha"] = norm360(L + Venus - Mars)
    formulas["Roga"] = norm360(L + Saturn - Mars)
    formulas["Bandhu"] = norm360(L + Moon - Jupiter)
    formulas["Putra"] = norm360(L + Jupiter - Moon)
    formulas["Pitri"] = norm360(L + Sun - Saturn)
    formulas["Matri"] = norm360(L + Moon - Venus)
    formulas["Bhratri"] = norm360(L + Mars - Jupiter)
    return formulas


def _same_or_house_from(ps, origin, offsets):
    return {p for p,s in ps.items() if p not in ('Rahu','Ketu') and ((s-origin)%12) in offsets}


def _lord_of_house(lagna_sign: int, house: int) -> str:
    return LORDS[(lagna_sign + house - 1) % 12]


def _lords_join(ps, lagna_sign: int, houses_a, houses_b) -> list[tuple[str,str]]:
    out=[]
    for a in houses_a:
        for b in houses_b:
            la,lb=_lord_of_house(lagna_sign,a),_lord_of_house(lagna_sign,b)
            if la != lb and ps.get(la) == ps.get(lb): out.append((la,lb))
    return out


def _add_yoga(out, name, kind, strength, basis, factors=None):
    out.append({'name':name,'type':kind,'strength':strength,'basis':basis,'planetary_factors':factors or []})


def detect_yogas(planets: Mapping[str, Mapping[str, Any]], lagna_sign: int) -> List[Dict[str, Any]]:
    """Expanded classical yoga screening layer.

    The engine reports only yogas whose stated screening condition is satisfied.
    More complex school-specific cancellation/strength rules are attached as
    basis metadata rather than silently treating a broad catalogue entry as active.
    """
    ps={p:sign_index(v['longitude']) for p,v in planets.items()}
    hs={p:_whole_sign_house(lagna_sign,s) for p,s in ps.items()}
    out=[]
    classical=('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn')
    benefics={'Jupiter','Venus','Mercury','Moon'}
    malefics={'Sun','Mars','Saturn','Rahu','Ketu'}

    # Solar yogas
    sun=ps['Sun']; sun2=_same_or_house_from(ps,sun,{1}); sun12=_same_or_house_from(ps,sun,{-1%12})
    if sun2-{ 'Moon' }: _add_yoga(out,'Vesi Yoga','solar','moderate','A planet other than Moon occupies the 2nd sign from Sun.',sorted(sun2-{'Moon'}))
    if sun12-{ 'Moon' }: _add_yoga(out,'Vosi Yoga','solar','moderate','A planet other than Moon occupies the 12th sign from Sun.',sorted(sun12-{'Moon'}))
    if (sun2-{'Moon'}) and (sun12-{'Moon'}): _add_yoga(out,'Ubhayachara Yoga','solar','moderate-high','Planets other than Moon occupy both 2nd and 12th from Sun.',sorted((sun2|sun12)-{'Moon'}))

    # Lunar yogas
    moon=ps['Moon']; m2=_same_or_house_from(ps,moon,{1}); m12=_same_or_house_from(ps,moon,{11})
    if (m2-{'Sun'}): _add_yoga(out,'Sunapha Yoga','lunar','moderate','A planet other than Sun occupies the 2nd from Moon.',sorted(m2-{'Sun'}))
    if (m12-{'Sun'}): _add_yoga(out,'Anapha Yoga','lunar','moderate','A planet other than Sun occupies the 12th from Moon.',sorted(m12-{'Sun'}))
    if (m2-{'Sun'}) and (m12-{'Sun'}): _add_yoga(out,'Durudhara Yoga','lunar','moderate-high','Planets other than Sun occupy both 2nd and 12th from Moon.',sorted((m2|m12)-{'Sun'}))
    if not (m2-{'Sun'}) and not (m12-{'Sun'}): _add_yoga(out,'Kemadruma Yoga','lunar','screen-positive','No classical graha occupies the 2nd or 12th from Moon; kendra exceptions must be reviewed.',[])
    # Adhi: benefics in 6/7/8 from Moon.
    adhi=[]
    for off in (5,6,7):
        for p in benefics:
            if ((ps[p]-moon)%12)==off: adhi.append(p)
    if adhi: _add_yoga(out,'Adhi Yoga','lunar','moderate-high','Benefic planets occupy the 6th, 7th and/or 8th from Moon.',sorted(set(adhi)))

    # Conjunction/relationship yogas
    if ps['Mercury']==ps['Sun']: _add_yoga(out,'Budha Aditya Yoga','intellect','moderate','Sun and Mercury occupy the same sign.',['Sun','Mercury'])
    if ps['Moon']==ps['Mars']: _add_yoga(out,'Chandra Mangala Yoga','wealth','moderate','Moon and Mars occupy the same sign.',['Moon','Mars'])
    if (ps['Jupiter']-ps['Moon'])%12 in (0,3,6,9): _add_yoga(out,'Gaja Kesari Yoga','status','moderate-high','Jupiter is in a kendra from Moon.',['Jupiter','Moon'])
    if (ps['Jupiter']-ps['Mars'])%12 in (0,3,6,9): _add_yoga(out,'Guru Mangala Yoga','initiative','moderate','Jupiter and Mars occupy a kendra relationship.',['Jupiter','Mars'])

    # Pancha Mahapurusha.
    for p,kind in [('Mars','Ruchaka'),('Mercury','Bhadra'),('Jupiter','Hamsa'),('Venus','Malavya'),('Saturn','Sasa')]:
        good=_dignity(p,ps[p]) in ('Exalted','Own sign','Moolatrikona')
        if good and hs[p] in (1,4,7,10): _add_yoga(out,f'Pancha Mahapurusha — {kind}','mahapurusha','high',f'{p} is dignified in kendra house {hs[p]}.',[p])

    # House-lord yogas.
    raja=_lords_join(ps,lagna_sign,(1,4,7,10),(1,5,9))
    for a,b in raja: _add_yoga(out,'Raja Yoga','status','context-dependent',f'Kendra lord {a} joins trikona lord {b}.',[a,b])
    dharma_karma=_lords_join(ps,lagna_sign,(9,),(10,))
    for a,b in dharma_karma: _add_yoga(out,'Dharma Karmadhipati Yoga','career-status','high',f'9th lord {a} joins 10th lord {b}.',[a,b])
    wealth=_lords_join(ps,lagna_sign,(2,5,9),(11,)) + _lords_join(ps,lagna_sign,(2,11),(5,9))
    seen=set()
    for a,b in wealth:
        key=tuple(sorted((a,b)))
        if key not in seen:
            seen.add(key); _add_yoga(out,'Dhana Yoga','wealth','context-dependent',f'Wealth-related lords {a} and {b} are joined.',[a,b])

    # Amala: benefic in 10th from Lagna or Moon.
    for origin,label in ((lagna_sign,'Lagna'),(moon,'Moon')):
        for p in benefics:
            if ((ps[p]-origin)%12)==9: _add_yoga(out,'Amala Yoga','career','moderate',f'Benefic {p} occupies the 10th from {label}.',[p])
    # Vasumati: benefics in upachaya from Lagna/Moon.
    for origin,label in ((lagna_sign,'Lagna'),(moon,'Moon')):
        found=[p for p in benefics if ((ps[p]-origin)%12) in (2,5,7,9)]
        if found: _add_yoga(out,'Vasumati Yoga','wealth','moderate',f'Benefic planets occupy upachaya positions from {label}.',sorted(found))

    # Kartari around Lagna and key houses.
    for h,label in ((1,'Lagna'),(10,'10th house'),(7,'7th house')):
        origin=(lagna_sign+h-1)%12
        left={(origin-1)%12}; right={(origin+1)%12}
        leftp=[p for p in malefics if ps[p] in left]; rightp=[p for p in malefics if ps[p] in right]
        if leftp and rightp: _add_yoga(out,'Papakartari Yoga','constraint','moderate',f'Malefics flank the {label} by sign.',sorted(set(leftp+rightp)))
        leftp=[p for p in benefics if ps[p] in left]; rightp=[p for p in benefics if ps[p] in right]
        if leftp and rightp: _add_yoga(out,'Shubha Kartari Yoga','support','moderate',f'Benefics flank the {label} by sign.',sorted(set(leftp+rightp)))

    # Parivartana between house lords.
    for a in range(1,13):
        la=_lord_of_house(lagna_sign,a); sa=ps.get(la)
        for b in range(a+1,13):
            lb=_lord_of_house(lagna_sign,b); sb=ps.get(lb)
            if la!=lb and sa==(lagna_sign+b-1)%12 and sb==(lagna_sign+a-1)%12:
                _add_yoga(out,'Parivartana Yoga','exchange','high' if {a,b}&{1,5,9,10} else 'moderate',f'{la} and {lb} exchange signs as lords of houses {a} and {b}.',[la,lb])

    # Vipareeta Raja: lords of 6/8/12 placed in another dusthana.
    dust=(6,8,12)
    for a in dust:
        la=_lord_of_house(lagna_sign,a); ha=hs.get(la)
        if ha in dust and ha!=a: _add_yoga(out,'Vipareeta Raja Yoga','reversal','context-dependent',f'Lord of dusthana house {a}, {la}, occupies dusthana house {ha}.',[la])
    # Lakshmi / Saraswati.
    lagna_lord=_lord_of_house(lagna_sign,1); ninth_lord=_lord_of_house(lagna_sign,9)
    if hs.get(lagna_lord) in (1,4,5,7,9,10) and _dignity(ninth_lord,ps[ninth_lord]) in ('Exalted','Own sign','Moolatrikona'):
        _add_yoga(out,'Lakshmi Yoga','wealth-dharma','moderate-high',f'Lagna lord {lagna_lord} is strong and 9th lord {ninth_lord} is dignified.',[lagna_lord,ninth_lord])
    strong_intellect = _dignity('Mercury',ps['Mercury']) in ('Exalted','Own sign','Moolatrikona') and any(ps[p]==ps['Mercury'] for p in ('Jupiter','Venus'))
    if strong_intellect or (hs['Mercury'] in (1,4,5,7,9,10) and hs['Jupiter'] in (1,4,5,7,9,10)):
        _add_yoga(out,'Saraswati Yoga','learning','moderate-high','Mercury is strong and supported by Jupiter/Venus or occupies a kendra/trikona with Jupiter.', ['Mercury','Jupiter','Venus'])

    # Divisional/degree yogas with chart-specific placement evidence.
    d9={p:_varga_sign(v['longitude'],9) for p,v in planets.items()}
    for p in classical:
        if d9.get(p)==ps.get(p):
            _add_yoga(out,'Vargottama Yoga','divisional','high',f'{p} occupies the same sign in D1 and D9.',[p])
    # Pushkara Navamsha: traditional sign-specific Navamsha positions.
    for p in classical:
        s=ps[p]; deg=deg_in_sign(planets[p]['longitude']); nav=int(deg/(30/9))+1
        movable=s in (0,3,6,9); fixed=s in (1,4,7,10); dual=s in (2,5,8,11)
        push=nav in ((7,9) if movable else (3,5) if fixed else (5,7))
        if push:
            _add_yoga(out,'Pushkara Navamsha Yoga','divisional','moderate-high',f'{p} occupies a traditional Pushkara Navamsha position (Navamsha {nav}).',[p])
    # Pushkara Bhaga: traditional auspicious degree zones, represented here as the
    # classical degree targets within each sign family.
    for p in classical:
        s=ps[p]; deg=deg_in_sign(planets[p]['longitude'])
        target=21.0 if s in (0,3,6,9) else 14.0 if s in (1,4,7,10) else 24.0
        if abs(deg-target)<=0.25:
            _add_yoga(out,'Pushkara Bhaga Yoga','degree','moderate-high',f'{p} is within 0.25° of the traditional Pushkara Bhaga degree {target:.0f}° in {SIGNS[s]}.',[p])
    # Chatussagara: all four kendras contain at least one graha.
    if all(any(hs[p]==h for p in classical) for h in (1,4,7,10)):
        _add_yoga(out,'Chatussagara Yoga','status','moderate-high','All four kendras from Lagna contain classical planets.',sorted(classical))
    # Neecha Bhanga Raja Yoga screening: debilitated planet with a classical
    # cancellation condition involving its dispositor or exaltation lord.
    for p in classical:
        if _dignity(p,ps[p])!='Debilitated': continue
        deb_sign=ps[p]; disp=_lord_of_house(deb_sign,1); exalts={v:k for k,v in EXALTATIONS.items()}.get(deb_sign)
        cancel=False; reasons=[]
        if hs.get(disp) in (1,4,7,10): cancel=True; reasons.append(f'dispositor {disp} in kendra')
        if exalts and hs.get(exalts) in (1,4,7,10): cancel=True; reasons.append(f'exaltation lord {exalts} in kendra')
        if cancel:
            _add_yoga(out,'Neecha Bhanga Raja Yoga','cancellation','context-dependent',f'{p} is debilitated and cancellation is screened because ' + ' and '.join(reasons)+'.',[p,disp] + ([exalts] if exalts else []))

    # Additional commonly used classical combinations.
    # Mahabhagya: sex/daytime variants are calculated from birth chart metadata elsewhere;
    # here the planetary day/night symmetry is screened from Sun/Moon sign polarity and Lagna.
    if lagna_sign in (0,4,8) and ps['Sun'] in (0,4,8) and ps['Moon'] in (0,4,8):
        _add_yoga(out,'Mahabhagya Yoga','classical','context-dependent','Lagna, Sun and Moon share the traditionally auspicious odd-sign pattern.', ['Sun','Moon'])
    if lagna_sign in (1,5,9) and ps['Sun'] in (1,5,9) and ps['Moon'] in (1,5,9):
        _add_yoga(out,'Mahabhagya Yoga','classical','context-dependent','Lagna, Sun and Moon share the traditionally auspicious even-sign pattern.', ['Sun','Moon'])
    # Akhanda Samrajya screening: fixed-sign Lagna plus strong 2nd/5th/11th lords.
    if lagna_sign in (1,4,7,10):
        l2=_lord_of_house(lagna_sign,2); l5=_lord_of_house(lagna_sign,5); l11=_lord_of_house(lagna_sign,11)
        if all(_dignity(p,ps[p]) in ('Exalted','Own sign','Moolatrikona') or hs[p] in (1,4,7,10) for p in (l2,l5,l11)):
            _add_yoga(out,'Akhanda Samrajya Yoga','status','high','Fixed-sign Lagna with strong 2nd, 5th and 11th lords.',[l2,l5,l11])
    # Harsha/Sarala/Vimala variants of Viparita Raja.
    for h,name in ((6,'Harsha Yoga'),(8,'Sarala Yoga'),(12,'Vimala Yoga')):
        lord=_lord_of_house(lagna_sign,h)
        if hs.get(lord) in (6,8,12): _add_yoga(out,name,'viparita','moderate-high',f'{h}th lord {lord} occupies a dusthana.',[lord])
    # Vesi/Vosi aliases and Narayana-style sign support are catalogue-compatible.
    if sun2-{'Moon'} and sun12-{'Moon'}: _add_yoga(out,'Vesi-Vosi-Ubhayachara Yoga','solar','moderate-high','Both solar side positions are occupied by non-lunar planets.',sorted((sun2|sun12)-{'Moon'}))
    # House-based combinations.
    if all(hs[p] in (1,4,7,10) for p in ('Jupiter','Venus')): _add_yoga(out,'Parvata Yoga','status','moderate','Jupiter and Venus occupy kendras from Lagna.',['Jupiter','Venus'])
    if hs.get(_lord_of_house(lagna_sign,1)) in (1,4,7,10) and hs.get(_lord_of_house(lagna_sign,5)) in (1,4,7,10): _add_yoga(out,'Kahala Yoga','initiative','moderate','Lagna and 5th-house lords occupy supportive angular positions.',[_lord_of_house(lagna_sign,1),_lord_of_house(lagna_sign,5)])
    # Rajayoga via trinal lords conjunction/exchange already above; add conjunction in kendra.
    if ps['Jupiter']==ps['Venus']: _add_yoga(out,'Guru Shukra Yoga','knowledge-relationships','moderate','Jupiter and Venus are conjunct by sign.',['Jupiter','Venus'])
    if ps['Jupiter']==ps['Moon']: _add_yoga(out,'Gaja Kesari exact conjunction','status','high','Jupiter and Moon share the same sign.',['Jupiter','Moon'])

    # Naabhasa / Ashraya / Sankhya patterns. These are chart-structure yogas,
    # calculated from the seven classical grahas rather than guessed from names.
    seven=[ps[p] for p in classical]
    occupied=set(seven)
    movable={0,3,6,9}; fixed={1,4,7,10}; dual={2,5,8,11}
    if occupied and all(x in movable for x in seven): _add_yoga(out,'Rajju Naabhasa Yoga','naabhasa','moderate','All seven classical grahas occupy movable signs.',list(classical))
    if occupied and all(x in fixed for x in seven): _add_yoga(out,'Musala Naabhasa Yoga','naabhasa','moderate','All seven classical grahas occupy fixed signs.',list(classical))
    if occupied and all(x in dual for x in seven): _add_yoga(out,'Nala Naabhasa Yoga','naabhasa','moderate','All seven classical grahas occupy dual signs.',list(classical))
    sign_count=len(occupied)
    sankhya={1:'Gola Yoga',2:'Yuga Yoga',3:'Soola Yoga',4:'Kedara Yoga',5:'Paasa Yoga',6:'Daama Yoga',7:'Veena Yoga'}
    if sign_count in sankhya: _add_yoga(out,sankhya[sign_count],'sankhya','moderate',f'The seven classical grahas occupy {sign_count} distinct signs.',list(classical))
    kendra_houses={hs[p] for p in classical}
    if all(hs[p] in (1,4,7,10) for p in classical): _add_yoga(out,'Kamala Naabhasa Yoga','naabhasa','high','All seven classical grahas occupy kendras.',list(classical))
    benefic_k=[p for p in benefics if hs[p] in (1,4,7,10)]; malefic_k=[p for p in malefics if p in hs and hs[p] in (1,4,7,10)]
    if len(benefic_k)>=3 and not malefic_k: _add_yoga(out,'Maala Yoga','dala','moderate','Benefic planets dominate the kendras.',benefic_k)
    if len(malefic_k)>=3 and not benefic_k: _add_yoga(out,'Sarpa Yoga','dala','moderate','Malefic planets dominate the kendras.',malefic_k)
    if all(hs[p] in (1,7) for p in classical): _add_yoga(out,'Shakata Yoga','naabhasa','moderate','The seven classical grahas are concentrated in the 1st/7th axis.',list(classical))
    if all(hs[p] in (4,10) for p in classical): _add_yoga(out,'Vihaga Yoga','naabhasa','moderate','The seven classical grahas are concentrated in the 4th/10th axis.',list(classical))
    benefic_17=[p for p in benefics if hs[p] in (1,7)]; malefic_410=[p for p in malefics if p in hs and hs[p] in (4,10)]
    malefic_17=[p for p in malefics if p in hs and hs[p] in (1,7)]; benefic_410=[p for p in benefics if hs[p] in (4,10)]
    if benefic_17 and malefic_410: _add_yoga(out,'Vajra Yoga','naabhasa','moderate','Benefics occupy the 1st/7th axis while malefics occupy the 4th/10th axis.',sorted(set(benefic_17+malefic_410)))
    if malefic_17 and benefic_410: _add_yoga(out,'Yava Yoga','naabhasa','moderate','Malefics occupy the 1st/7th axis while benefics occupy the 4th/10th axis.',sorted(set(malefic_17+benefic_410)))

    # Remove duplicates while preserving first basis.
    uniq={}
    for y in out:
        key=y['name']
        if key not in uniq:
            uniq[key]=y
        else:
            uniq[key]['planetary_factors']=sorted(set(uniq[key].get('planetary_factors',[])) | set(y.get('planetary_factors',[])))
            uniq[key]['basis']=uniq[key].get('basis','') + ' ' + y.get('basis','') if y.get('basis') not in uniq[key].get('basis','') else uniq[key].get('basis','')
    return list(uniq.values())

def detect_doshas(planets: Mapping[str, Mapping[str, Any]], lagna_sign: int) -> List[Dict[str, Any]]:
    ps = {p: sign_index(v["longitude"]) for p, v in planets.items()}
    houses = {p: _whole_sign_house(lagna_sign, s) for p, s in ps.items()}
    doshas = []
    mars_h = houses["Mars"]
    if mars_h in (1, 2, 4, 7, 8, 12):
        doshas.append({"name": "Manglik / Kuja Dosha", "status": "screen-positive",
                       "severity": "moderate", "basis": f"Mars in house {mars_h} from Lagna; cancellation/mitigation must be checked"})
    # Kala Sarpa screen: all classical planets between Rahu/Ketu axis.
    rahu = ps["Rahu"]
    ketu = ps["Ketu"]
    classical = [ps[p] for p in PLANETS if p not in ("Rahu",)]
    def within_arc(x: int, start: int, end: int) -> bool:
        return ((x - start) % 12) <= ((end - start) % 12)
    if all(within_arc(x, rahu, ketu) for x in classical) or all(within_arc(x, ketu, rahu) for x in classical):
        doshas.append({"name": "Kala Sarpa Yoga / Dosha screen", "status": "possible",
                       "severity": "school-dependent", "basis": "Classical grahas fall on one side of Rahu–Ketu axis"})
    if ps["Sun"] == ps["Rahu"] or ps["Moon"] == ps["Rahu"] or ps["Sun"] == ps["Ketu"] or ps["Moon"] == ps["Ketu"]:
        doshas.append({"name": "Grahan Dosha screen", "status": "possible", "severity": "moderate",
                       "basis": "Sun or Moon conjunct a node by sign; degree tightness matters"})
    # Guru Chandal commonly defined by Jupiter with Rahu/Ketu.
    if ps["Jupiter"] in (ps["Rahu"], ps["Ketu"]):
        doshas.append({"name": "Guru Chandal screen", "status": "possible", "severity": "school-dependent",
                       "basis": "Jupiter shares sign with a node"})
    return doshas


def house_analysis(planets: Mapping[str, Mapping[str, Any]], lagna_sign: int) -> List[Dict[str, Any]]:
    by_house: Dict[int, Dict[str, Any]] = {h: {"house": h, "sign": SIGNS[(lagna_sign + h - 1) % 12], "lord": LORDS[(lagna_sign + h - 1) % 12], "occupants": []} for h in range(1, 13)}
    for p, dat in planets.items():
        h = _whole_sign_house(lagna_sign, sign_index(dat["longitude"]))
        by_house[h]["occupants"].append(p)
    for h in by_house:
        lord = by_house[h]["lord"]
        if lord in planets:
            by_house[h]["lord_house"] = _whole_sign_house(lagna_sign, sign_index(planets[lord]["longitude"]))
    return list(by_house.values())


def build_transit_scan(birth: BirthData, natal: Mapping[str, Any], years: int = 5, forecast_start: datetime | None = None,
                       forecast_end_dt: datetime | None = None, granularity: str = "monthly") -> List[Dict[str, Any]]:
    """Transit scan over a requested interval at daily/weekly/monthly/quarterly resolution."""
    start = forecast_start.astimezone(ZoneInfo(birth.timezone)) if forecast_start else datetime.now(ZoneInfo(birth.timezone))
    end = forecast_end_dt or (start + timedelta(days=365.2425 * years))
    cur = start
    results=[]
    while cur <= end:
        jd=_time_to_jd(cur.astimezone(timezone.utc)); pos=_calc_planets(jd)
        row={"date":cur.date().isoformat(),"planets":{p:round(d["longitude"],6) for p,d in pos.items()},"granularity":granularity,"transit_nakshatra":{p:nakshatra_details(pos[p]["longitude"]) for p in ("Jupiter","Saturn","Rahu","Ketu")}}
        for p in ("Jupiter","Saturn","Rahu","Ketu"):
            row[f"{p.lower()}_house"]=_whole_sign_house(natal["lagna_sign_index"],sign_index(pos[p]["longitude"]))
        row["aspects_to_natal"]=[]
        for tp in ("Jupiter","Saturn","Rahu","Ketu"):
            for np,nd in natal["planets"].items():
                d=angular_distance(pos[tp]["longitude"],nd["longitude"]); asp=min((0,60,90,120,180),key=lambda x:abs(d-x)); orb=abs(d-asp)
                if orb<=3: row["aspects_to_natal"].append({"transit":tp,"natal":np,"aspect":asp,"orb":round(orb,2)})
        results.append(row)
        if granularity=="daily": cur+=timedelta(days=1)
        elif granularity=="weekly": cur+=timedelta(days=7)
        elif granularity=="quarterly": cur+=timedelta(days=91)
        else:
            cur=(cur.replace(day=28)+timedelta(days=4)).replace(day=1)
    return results


def timing_windows(natal: Mapping[str, Any], dasha: Mapping[str, Any], transits: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Derive rule-based timing windows from dasha lords + Jupiter/Saturn house triggers."""
    windows: List[Dict[str, Any]] = []
    lagna = natal["lagna_sign_index"]
    natal_positions = natal["planets"]
    for period in dasha.get("periods", []):
        lord = period["lord"]
        child = period.get("children", [])
        focus_house = _whole_sign_house(lagna, sign_index(natal_positions.get(lord, natal_positions["Sun"])["longitude"])) if lord in natal_positions else None
        for tr in transits:
            jp = sign_index(tr["planets"]["Jupiter"])
            sp = sign_index(tr["planets"]["Saturn"])
            if focus_house:
                jh = _whole_sign_house(lagna, jp)
                sh = _whole_sign_house(lagna, sp)
                # 1/5/9 or kendra to natal dasha planet's house are treated as broad triggers.
                if jh in (1, 5, 9, 10) or sh in (1, 5, 9, 10):
                    windows.append({
                        "start": tr["date"], "end": tr["date"], "dasha": lord,
                        "trigger": "Jupiter/Saturn transit activation",
                        "houses": {"jupiter": jh, "saturn": sh},
                        "confidence": "screening window",
                        "note": "Interpret with the full natal context; this is not a deterministic event date.",
                    })
    return windows



DOMAIN_HOUSE_WEIGHTS = {
    "career": {10: 1.0, 6: 0.65, 11: 0.8, 1: 0.35},
    "job_change": {10: 1.0, 6: 0.7, 11: 0.75, 8: 0.35, 3: 0.25},
    "business": {7: 1.0, 10: 0.9, 11: 0.9, 2: 0.55, 3: 0.4},
    "finances": {2: 1.0, 11: 1.0, 5: 0.45, 9: 0.55, 8: -0.35},
    "marriage": {7: 1.0, 5: 0.55, 2: 0.35, 12: -0.25},
    "family": {2: 0.8, 4: 1.0, 11: 0.35, 8: -0.2},
    "learning": {5: 0.85, 9: 1.0, 3: 0.5, 8: 0.25},
    "wellness": {1: 0.75, 6: 0.7, 8: -0.45, 12: -0.3},
    "inner_growth": {8: 0.8, 9: 0.9, 12: 0.85, 5: 0.3},
}


def _domain_activation(house_j: int, house_s: int, rahu_h: int, ketu_h: int, dasha_house: int | None, domain: str) -> float:
    weights = DOMAIN_HOUSE_WEIGHTS[domain]
    score = 50.0
    for h, w in weights.items():
        if house_j == h:
            score += 18 * w
        if house_s == h:
            score += 12 * w
        if rahu_h == h:
            score += 5 * w
        if ketu_h == h:
            score += 4 * w
        if dasha_house == h:
            score += 10 * w
    # Saturn is intentionally not treated as purely negative: its house activation
    # can signify consolidation when the domain's weight is positive.
    return round(max(0.0, min(100.0, score)), 1)


def build_performance_profile(natal: Mapping[str, Any], transits: Sequence[Mapping[str, Any]], dasha: Mapping[str, Any]) -> Dict[str, Any]:
    """Create a transparent symbolic activation index for readable modern graphs.

    This is not an empirical prediction or probability. It is a visualization layer
    showing where the application's own Jyotish rule screen is most activated.
    """
    periods = dasha.get("periods", [])
    domains = list(DOMAIN_HOUSE_WEIGHTS)
    rows = []
    for tr in transits:
        when = datetime.fromisoformat(tr["date"]).replace(tzinfo=ZoneInfo(natal["meta"]["timezone"]))
        active = next((p for p in periods if datetime.fromisoformat(p["start"]) <= when < datetime.fromisoformat(p["end"])), None)
        dasha_house = None
        if active and active["lord"] in natal["planets"]:
            dasha_house = natal["planets"][active["lord"]]["house"]
        row = {"date": tr["date"], "dasha": active["lord"] if active else "Unknown"}
        for domain in domains:
            row[domain] = _domain_activation(tr["jupiter_house"], tr["saturn_house"],
                                              tr["rahu_house"], tr["ketu_house"], dasha_house, domain)
        rows.append(row)
    peaks = {}
    for domain in domains:
        top = sorted(rows, key=lambda r: r[domain], reverse=True)[:6]
        peaks[domain] = [{"date": r["date"], "score": r[domain], "dasha": r["dasha"]} for r in top]
    return {"method": "symbolic activation index (0–100), not probability", "domains": domains, "monthly": rows, "peaks": peaks}


def planetary_aspects(planets: Mapping[str, Mapping[str, Any]], orb: float = 5.0) -> List[Dict[str, Any]]:
    out=[]
    names=list(planets)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            d=angular_distance(planets[a]["longitude"], planets[b]["longitude"])
            aspect=min((0,30,45,60,72,90,120,135,150,180), key=lambda x: abs(d-x))
            actual=abs(d-aspect)
            if actual<=orb:
                out.append({"a":a,"b":b,"aspect":aspect,"orb":round(actual,2),"exactness":round(max(0,1-actual/orb),3)})
    return sorted(out,key=lambda x:(x["orb"],x["a"],x["b"]))


def nakshatra_interpretation(planets: Mapping[str, Mapping[str, Any]], lagna: float) -> Dict[str, Any]:
    moon=nakshatra_details(planets["Moon"]["longitude"])
    asc=nakshatra_details(lagna)
    return {
        "moon": moon,
        "lagna": asc,
        "planetary": {p: dat["nakshatra"] for p,dat in planets.items()},
        "reading": [
            f"Moon in {moon['name']} pada {moon['pada']}: {moon['shakti']} is used as the primary emotional/mind lens in this report.",
            f"Ascendant in {asc['name']} pada {asc['pada']}: {asc['symbol']} and {asc['quality'].lower()} quality are used as a traditional temperament lens.",
            f"The Moon's nakshatra lord is {moon.get('vimshottari_lord')}; Vimshottari timing begins from the Moon's nakshatra balance.",
        ],
        "caveat": "Nakshatra interpretation is a traditional Jyotish framework. It is not a scientific personality measurement."
    }


def chara_karakas(planets: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    candidates=[p for p in ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn") if p in planets]
    ranked=sorted(candidates,key=lambda p:deg_in_sign(planets[p]["longitude"]),reverse=True)
    labels=["Atmakaraka","Amatyakaraka","Bhratrikaraka","Matrikaraka","Putrakaraka","Gnatikaraka","Darakaraka"]
    return {"scheme":"7-karaka Jaimini scheme","karakas":[{"role":r,"planet":p,"degree_in_sign":round(deg_in_sign(planets[p]["longitude"]),4)} for r,p in zip(labels,ranked)]}


def arudha_padas(lagna_sign: int, planets: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    sign_lords=LORDS
    planet_sign={p:sign_index(d["longitude"]) for p,d in planets.items()}
    out={}
    for h in range(1,13):
        house_sign=(lagna_sign+h-1)%12
        lord=sign_lords[house_sign]
        lord_sign=planet_sign.get(lord,house_sign)
        distance=(lord_sign-house_sign)%12
        arudha=(lord_sign+distance)%12
        # Classical exceptions: if A is 1st or 7th from the source, shift to 10th/4th.
        if arudha==house_sign:
            arudha=(house_sign+9)%12
        if arudha==(house_sign+6)%12:
            arudha=(house_sign+3)%12
        out[f"A{h}"]={"house":h,"sign_index":arudha,"sign":SIGNS[arudha],"lord":lord}
    return out


def planet_strength_screen(planets: Mapping[str, Mapping[str, Any]], lagna_sign: int) -> Dict[str, Any]:
    # Transparent normalized screen, not a replacement for a full Shadbala implementation.
    scores={}
    for p,d in planets.items():
        score=50.0
        dignity=d["dignity"]
        score += {"Exalted":25,"Own sign":15,"Moolatrikona":18,"Neutral":0,"Debilitated":-18}.get(dignity,0)
        if d.get("retrograde"): score += 3
        if d.get("combust"): score -= 8
        h=d.get("house")
        score += {1:5,4:4,5:3,7:4,9:5,10:6,11:5,6:1,8:-3,12:-2}.get(h,0)
        scores[p]={"score":round(max(0,min(100,score)),1),"components":{"dignity":dignity,"retrograde":d.get("retrograde",False),"combust":d.get("combust",False),"house":h}}
    return {"method":"normalized Jyotish strength screen; not classical Shadbala units","planets":scores}


def bhava_strength_screen(houses: Sequence[Mapping[str, Any]], planets: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    benefics={"Jupiter","Venus","Mercury","Moon"}
    out=[]
    for h in houses:
        score=50.0
        occ=h.get("occupants",[])
        for p in occ:
            if p in benefics: score+=8
            elif p in {"Saturn","Rahu","Ketu"}: score-=4
            else: score+=2
        if h.get("lord_house") in (1,4,5,7,9,10,11): score+=7
        if h.get("lord_house") in (6,8,12): score-=4
        out.append({**h,"strength":round(max(0,min(100,score)),1)})
    return out


def panchanga_full(jd_ut: float) -> Dict[str, Any]:
    base=panchanga(jd_ut)
    weekday=int((jd_ut+1.5)%7)
    base["weekday"]=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"][weekday]
    elong=base["elongation"]
    karana_index=int(elong//6)
    base["karana_number"]=karana_index+1
    base["karana"]="Kimstughna" if karana_index==0 else ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti"][((karana_index-1)%7)]
    base["paksha"]="Shukla" if base["tithi"]<=15 else "Krishna"
    return base


def forecast_end(start: datetime, amount: int, unit: str) -> datetime:
    if unit=="days": return start+timedelta(days=amount)
    if unit=="months":
        y=start.year+(start.month-1+amount)//12; m=(start.month-1+amount)%12+1
        import calendar
        return start.replace(year=y,month=m,day=min(start.day,calendar.monthrange(y,m)[1]))
    return start.replace(year=start.year+amount)


def choose_forecast_granularity(amount:int, unit:str, requested:str|None=None)->str:
    if requested in {"daily","weekly","monthly","quarterly"}: return requested
    if unit=="days" and amount<=90: return "daily"
    if unit=="days": return "weekly"
    if unit=="months" and amount<=24: return "monthly"
    if unit=="months": return "monthly"
    if unit=="years" and amount<=15: return "monthly"
    return "quarterly"



def _flatten_dasha(periods: Sequence[Mapping[str, Any]], max_level: int = 3) -> List[Dict[str, Any]]:
    out=[]
    def walk(nodes, depth):
        for node in nodes or []:
            out.append({'lord':node['lord'],'start':node['start'],'end':node['end'],'level':depth})
            if depth < max_level:
                walk(node.get('children',[]), depth+1)
    walk(periods,1)
    return out


def _yoga_planets(name: str) -> List[str]:
    mapping={
        'Gaja Kesari Yoga':['Jupiter','Moon'],'Budha Aditya Yoga':['Sun','Mercury'],'Chandra Mangala Yoga':['Moon','Mars'],
        'Ruchaka Yoga':['Mars'],'Bhadra Yoga':['Mercury'],'Hamsa Yoga':['Jupiter'],'Malavya Yoga':['Venus'],'Sasa Yoga':['Saturn'],
        'Guru Mangala Yoga':['Jupiter','Mars'],'Vesi Yoga':['Sun'],'Vosi Yoga':['Sun'],'Ubhayachara Yoga':['Sun'],
        'Sunapha Yoga':['Moon'],'Anapha Yoga':['Moon'],'Duradhara Yoga':['Moon'],'Kemadruma Yoga':['Moon'],
        'Dhana Yoga':['Jupiter','Venus','Mercury','Moon'],'Raja Yoga':['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'],
        'Dharma Karmadhipati Raja Yoga':['Jupiter','Saturn'],'Viparita Raja Yoga':['Mars','Mercury','Jupiter','Venus','Saturn'],
        'Neecha Bhanga Raja Yoga':['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'],
    }
    return mapping.get(name, ['Sun','Moon','Jupiter','Saturn'])


def _dasha_chain_for_date(periods, when):
    chain=[]
    def walk(nodes, depth=1):
        for node in nodes or []:
            try:
                st=datetime.fromisoformat(node['start']); en=datetime.fromisoformat(node['end'])
            except Exception:
                continue
            if st <= when < en:
                chain.append({'level':depth,'lord':node.get('lord'),'start':node.get('start'),'end':node.get('end')})
                if node.get('children'):
                    walk(node['children'], depth+1)
                return
    walk(periods,1)
    return chain


def enrich_yogas_with_timing(yogas: Sequence[Mapping[str,Any]], dasha: Mapping[str,Any], transits: Sequence[Mapping[str,Any]]) -> List[Dict[str,Any]]:
    """Attach only evidence-backed fruitification dates from generated dasha/transit rows.

    No dates are invented. A candidate date must be present in the calculated transit
    scan and must intersect a dasha factor plus a slow-planet contact to a yoga factor.
    Up to five strongest candidates are retained; fewer are returned when the calculated
    data contains fewer qualifying dates.
    """
    out=[]; periods=dasha.get('periods',[])
    for y in yogas:
        item=dict(y); planets=item.get('planetary_factors') or _yoga_planets(item.get('name','')); item['planetary_factors']=planets
        candidates=[]
        for tr in transits:
            try: dt=datetime.fromisoformat(tr['date']+'T00:00:00+00:00')
            except Exception: continue
            chain=_dasha_chain_for_date(periods, dt)
            dasha_hits=[x for x in chain if x.get('lord') in planets]
            transit_hits=[a for a in tr.get('aspects_to_natal',[]) if a.get('natal') in planets and a.get('transit') in ('Jupiter','Saturn','Rahu','Ketu')]
            if not dasha_hits or not transit_hits: continue
            strength=0
            strength += 30 if chain and chain[0].get('lord') in planets else 0
            strength += 18 if len(dasha_hits)>1 else 0
            strength += sum(max(0, 3-float(a.get('orb',3))) for a in transit_hits[:3])
            # Favor exact/close aspects and conjunctions.
            strength += sum(12 if a.get('aspect')==0 else 8 if a.get('aspect') in (120,180) else 4 for a in transit_hits[:3])
            candidates.append({
                'date':tr['date'],'start':tr['date'],'end':tr['date'],'score':round(strength,2),
                'dasha_chain':dasha_hits,
                'active_dasha':' / '.join(x['lord'] for x in chain) if chain else None,
                'dasha_lord':dasha_hits[0].get('lord') if dasha_hits else None,
                'transit_triggers':transit_hits[:5],
                'transit_positions':{p:tr.get('transit_nakshatra',{}).get(p) for p in ('Jupiter','Saturn','Rahu','Ketu')},
                'reason':'A calculated Vimshottari factor period coincides with a calculated slow-planet contact to a natal factor of the yoga.'
            })
        # De-duplicate dates and retain strongest five actual calculated dates.
        best={}
        for c in candidates:
            if c['date'] not in best or c['score']>best[c['date']]['score']: best[c['date']]=c
        chosen=sorted(best.values(), key=lambda x:(-x['score'],x['date']))[:5]
        chosen=sorted(chosen,key=lambda x:x['date'])
        item['fruitification']={
            'possible_dates':chosen,
            'candidate_count':len(chosen),
            'windows':chosen,
            'method':'Dates are taken only from the generated dasha/transit scan where both a yoga-factor dasha and a slow-planet contact are present. No unsupported dates are generated.'
        }
        out.append(item)
    return out


def expanded_doshas(planets: Mapping[str,Mapping[str,Any]], lagna_sign:int) -> List[Dict[str,Any]]:
    ps={p:sign_index(v['longitude']) for p,v in planets.items()}; hs={p:_whole_sign_house(lagna_sign,s) for p,s in ps.items()}
    out=[]
    def add(name,status,severity,basis,mitigation='Review cancellation/mitigation rules for the chosen Jyotish school.', life_impact=''):
        out.append({'name':name,'status':status,'severity':severity,'basis':basis,'mitigation':mitigation,'life_impact':life_impact})
    if hs['Mars'] in (1,2,4,7,8,12): add('Manglik / Kuja Dosha','screen-positive','school-dependent',f'Mars in house {hs["Mars"]} from Lagna.', life_impact='When Mars is strongly activated, relationship, conflict, initiative, property and physical-drive themes can become more prominent; the actual expression depends on Mars lordship, dignity, aspects and the active Dasha chain.')
    if ps['Saturn'] in (ps['Rahu'],ps['Ketu']): add('Shrapit Dosha','possible','school-dependent','Saturn is conjunct the nodal axis by sign.', life_impact='When Saturn or the nodal axis is activated, responsibilities, delays, institutional pressures, persistence and restructuring can become more visible in the houses involved.')
    if ps['Jupiter'] in (ps['Rahu'],ps['Ketu']): add('Guru Chandal Dosha','possible','school-dependent','Jupiter is conjunct a lunar node by sign.', life_impact='When Jupiter or the nodes are activated, education, beliefs, mentors, ethics, judgment and unconventional choices can receive extra emphasis; the house and dignity determine the life arena.')
    if ps['Sun'] in (ps['Rahu'],ps['Ketu']) or ps['Moon'] in (ps['Rahu'],ps['Ketu']): add('Grahan Dosha','possible','school-dependent','Sun or Moon is conjunct a lunar node by sign; degree orb matters.', life_impact='When the affected luminary or nodes are activated, identity, visibility, emotional security, family and major transitions can feel more concentrated or unusual in the relevant houses.')
    moon_nak=nakshatra_details(planets['Moon']['longitude'])['name']
    if moon_nak in {'Ashwini','Ashlesha','Magha','Jyeshtha','Mula','Revati'}: add('Ganda Moola Dosha','possible','school-dependent',f'Moon is in {moon_nak}, one of the six traditionally classified Ganda Moola nakshatras.')
    if ps['Venus']==ps['Rahu'] or ps['Venus']==ps['Ketu']: add('Kalathra Dosha screen','possible','school-dependent','Venus is conjunct a node by sign; marriage assessment requires D9 and 7th-house context.')
    if ps['Saturn']==ps['Moon']: add('Vish / Punarphoo Dosha screen','possible','school-dependent','Saturn and Moon share a sign; exact degrees and classical cancellation rules matter.')
    # Kemadruma screen: no classical grahas in 2nd/12th from Moon; classical exceptions are reviewed separately.
    moon_sign=ps['Moon']; occupied={ps[p] for p in ('Sun','Mars','Mercury','Jupiter','Venus','Saturn')}
    if ((moon_sign+1)%12 not in occupied) and ((moon_sign-1)%12 not in occupied):
        add('Kemadruma Dosha screen','possible','school-dependent','No classical graha occupies the 2nd or 12th sign from Moon; kendra and other cancellation rules must be checked.')
    # Papakartari screen around Lagna.
    malefic={ps['Sun'],ps['Mars'],ps['Saturn'],ps['Rahu'],ps['Ketu']}
    if ((lagna_sign+1)%12 in malefic) and ((lagna_sign-1)%12 in malefic):
        add('Papakartari Dosha screen','possible','school-dependent','Malefic planets flank the Lagna by sign.')
    # Gandanta: water-fire junctions within 0°48' by a common screening orb.
    for p,v in planets.items():
        lon=norm360(v['longitude']); d=deg_in_sign(lon); s=sign_index(lon)
        if (s in (3,7,11) and d >= 29.2) or (s in (0,4,8) and d <= 0.8):
            add('Gandanta screen','possible','school-dependent',f'{p} lies near a water-fire sign junction ({SIGNS[s]} {d:.2f}°).')
    # Graha Yuddha screen for classical visible planets.
    visible=('Mars','Mercury','Jupiter','Venus','Saturn')
    for i,p in enumerate(visible):
        for q in visible[i+1:]:
            if angular_distance(planets[p]['longitude'],planets[q]['longitude']) <= 1.0:
                add('Graha Yuddha screen','possible','school-dependent',f'{p} and {q} are within 1° by geocentric longitude.')
    # Additional single-chart dosha screens.
    ninth_lord=_lord_of_house(lagna_sign,9)
    if ps.get(ninth_lord) in (ps['Rahu'],ps['Ketu']) or ps['Rahu']==(lagna_sign+8)%12 or ps['Ketu']==(lagna_sign+8)%12:
        add('Pitru Dosha','possible','school-dependent','The 9th-house/9th-lord pattern is closely connected with a lunar node.')
    eleventh_lord=_lord_of_house(lagna_sign,11); second_lord=_lord_of_house(lagna_sign,2)
    if hs.get(eleventh_lord) in (6,8,12) and hs.get(second_lord) in (6,8,12):
        add('Daridra Dosha','possible','school-dependent','The 11th and 2nd lords are both placed in dusthana houses in this screening model.')
    moon_h=hs.get('Moon')
    moon_malefic=any(hs.get(p) in ((moon_h-2)%12+1,(moon_h)%12+1) for p in ('Saturn','Mars','Rahu','Ketu')) if moon_h else False
    if moon_h in (6,8,12) and moon_malefic:
        add('Balarishta Dosha','possible','school-dependent','Moon is placed in a dusthana and is additionally connected to a malefic by the screening rule.')
    # Combustion as a named condition, kept separate from ordinary dignity.
    combust=[p for p,v in planets.items() if v.get('combust') and p not in ('Sun','Rahu','Ketu')]
    if combust: add('Combustion Affliction','possible','chart-specific','The following grahas are combust by the configured solar orb: '+', '.join(combust)+'.')
    # Sandhi / Mrityu Bhaga-style degree screens.
    for p,v in planets.items():
        deg=deg_in_sign(v['longitude'])
        if deg<1 or deg>29:
            add('Rashi Sandhi','possible','school-dependent',f'{p} is near a sign boundary at {deg:.2f}°.')
        if abs(deg-0.0)<=0.1 or abs(deg-30.0)<=0.1:
            add('Mrityu Bhaga','possible','school-dependent',f'{p} is near a critical degree boundary at {deg:.2f}°.')
    # Kala Sarpa strict sign containment screen, keeping it explicitly school-dependent.
    classical=[ps[p] for p in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn')]
    def arc(x,start,end): return ((x-start)%12)<=((end-start)%12)
    if all(arc(x,ps['Rahu'],ps['Ketu']) for x in classical) or all(arc(x,ps['Ketu'],ps['Rahu']) for x in classical):
        add('Kala Sarpa Yoga / Dosha','possible','school-dependent','All seven classical grahas fall within one Rahu-Ketu half of the zodiac by sign.')
    return out



def build_modern_insights(chart: Mapping[str,Any]) -> Dict[str,Any]:
    perf=chart.get('performance',{}).get('monthly',[])
    domains=chart.get('performance',{}).get('domains',[])
    # A readable convergence layer: it does not claim a causal or empirical score.
    matrix=[]
    for row in perf:
        vals=[float(row.get(d,50)) for d in domains]
        matrix.append({'date':row['date'],'overall_activation':round(sum(vals)/max(1,len(vals)),1),'strongest_domain':domains[max(range(len(domains)),key=lambda i:vals[i])] if domains else None,'dasha':row.get('dasha')})
    top=sorted(matrix,key=lambda x:-x['overall_activation'])[:12]
    return {
        'life_area_matrix':matrix,
        'top_convergence_windows':top,
        'layers':['Dasha','Slow-planet transit','House activation','Life-area weighting'],
        'method':'Readable convergence visualization over traditional rule-based signals; not an empirical probability model.'
    }

def build_current_transit_snapshot(birth: BirthData, natal: Mapping[str, Any], when: datetime | None = None) -> Dict[str, Any]:
    when=when or datetime.now(ZoneInfo(birth.timezone))
    pos=_calc_planets(_time_to_jd(when.astimezone(timezone.utc)))
    out={'datetime':when.isoformat(),'timezone':birth.timezone,'planets':{},'slow_planet_houses':{},'aspects_to_natal':[]}
    for p in ('Jupiter','Saturn','Rahu','Ketu'):
        d=pos[p]; s=sign_index(d['longitude']); h=_whole_sign_house(natal['lagna_sign_index'],s)
        out['planets'][p]={'longitude':round(d['longitude'],6),'sign_index':s,'sign':SIGNS[s],'degree_in_sign':round(deg_in_sign(d['longitude']),4),'retrograde':d['retrograde'],'nakshatra':nakshatra_details(d['longitude'])}
        out['slow_planet_houses'][p]=h
        for np,nd in natal['planets'].items():
            dist=angular_distance(d['longitude'],nd['longitude']); asp=min((0,60,90,120,180),key=lambda x:abs(dist-x)); orb=abs(dist-asp)
            if orb<=3: out['aspects_to_natal'].append({'transit':p,'natal':np,'aspect':asp,'orb':round(orb,2)})
    return out


def analyze_birth(birth: BirthData, forecast_years: int = 5, forecast_amount: int | None = None,
                  forecast_unit: str = "years", forecast_granularity: str | None = None, school: str = "synthesis", forecast_start_date: str | None = None, forecast_end_date: str | None = None) -> Dict[str, Any]:
    started=time.perf_counter()
    engine_phase("[ENGINE] Start calculation forecast=%s %s", forecast_amount, forecast_unit)
    utc=birth.utc_dt; jd=_time_to_jd(utc); swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags=swe.FLG_SIDEREAL|swe.FLG_SWIEPH
    engine_phase("[ENGINE] Swiss Ephemeris time/house frame ready jd=%.5f", jd)
    cusps,ascmc=swe.houses_ex(jd,birth.latitude,birth.longitude,b"W",flags)
    lagna=norm360(ascmc[0]); mc=norm360(ascmc[1]); planets=_calc_planets(jd)
    for p,d in planets.items():
        d["sign_index"]=sign_index(d["longitude"]); d["sign"]=SIGNS[d["sign_index"]]; d["degree_in_sign"]=deg_in_sign(d["longitude"])
        d["house"]=_whole_sign_house(sign_index(lagna),d["sign_index"]); d["nakshatra"]=nakshatra_details(d["longitude"]); d["dignity"]=_dignity(p,d["sign_index"])
        d["combust"]=p!="Sun" and angular_distance(d["longitude"],planets["Sun"]["longitude"])<=COMBUSTION_ORB.get(p,0)
    house_table=house_analysis(planets,sign_index(lagna))
    engine_phase("[ENGINE] Astronomical positions complete planets=%d lagna=%s", len(planets), SIGNS[sign_index(lagna)])
    chart={"meta":{"engine":"Jyotish Lab / Swiss Ephemeris","ayanamsha":"Lahiri (Chitra Paksha)","house_system":"Whole Sign + Swiss Ephemeris angles","birth_local":birth.local_dt.isoformat(),"birth_utc":utc.isoformat(),"julian_day_ut":jd,"place":birth.place,"latitude":birth.latitude,"longitude":birth.longitude,"timezone":birth.timezone},
           "lagna_longitude":lagna,"lagna_sign_index":sign_index(lagna),"lagna_sign":SIGNS[sign_index(lagna)],"mc_longitude":mc,"mc_sign":SIGNS[sign_index(mc)],"houses":house_table,"planets":planets}
    chart["divisional_charts"]=calculate_divisional_charts(planets,lagna)
    engine_phase("[ENGINE] Vargas complete count=%d", len(chart["divisional_charts"]))
    chart["aspects"]=planetary_aspects(planets)
    chart["nakshatra_analysis"]=nakshatra_interpretation(planets,lagna)
    chart["chara_karakas"]=chara_karakas(planets)
    chart["arudha_padas"]=arudha_padas(chart["lagna_sign_index"],planets)
    chart["planet_strengths"]=planet_strength_screen(planets,chart["lagna_sign_index"])
    chart["bhava_strengths"]=bhava_strength_screen(house_table,planets)
    from .advanced import classical_ashtakavarga as _classical_ashtakavarga, shadbala as _shadbala
    chart["shadbala"]=_shadbala(planets, chart["lagna_sign_index"], chart["divisional_charts"], birth.local_dt)
    engine_phase("[ENGINE] Strength layers complete Shadbala/Ashtakavarga")
    chart["yogas"]=detect_yogas(planets,chart["lagna_sign_index"]); chart["doshas"]=detect_doshas(planets,chart["lagna_sign_index"])
    chart["ashtakavarga"]=ashtakavarga({p:v["sign_index"] for p,v in planets.items() if p in PLANETS and p!="Rahu"})
    chart["ashtakavarga_classical"]=_classical_ashtakavarga(planets, chart["lagna_sign_index"])
    night=birth.local_dt.hour<6 or birth.local_dt.hour>=18
    chart["sahams"]={k:{"longitude":v,"sign":SIGNS[sign_index(v)],"degree":round(deg_in_sign(v),4)} for k,v in sahams(planets,lagna,night).items()}
    chart["panchanga"]=panchanga_full(jd)
    engine_phase("[ENGINE] Classical interpretation layers complete yogas=%d doshas=%d", len(chart["yogas"]), len(chart["doshas"]))
    chart["reference_charts"]={"Sun_chart":{p:{"sign_index":d["sign_index"],"sign":d["sign"]} for p,d in planets.items()},"Moon_chart":{p:{"sign_index":d["sign_index"],"sign":d["sign"],"house_from_moon":_whole_sign_house(sign_index(planets["Moon"]["longitude"]),d["sign_index"])} for p,d in planets.items()}}
    amount=forecast_amount if forecast_amount is not None else forecast_years; unit=forecast_unit or "years"
    if unit not in {"days","months","years"}: raise ValueError("forecast_unit must be days, months or years")
    if bool(forecast_start_date) != bool(forecast_end_date):
        raise ValueError("Choose both a forecast start date and an end date, or leave both blank")
    now=datetime.now(ZoneInfo(birth.timezone))
    start=datetime.fromisoformat(forecast_start_date).replace(tzinfo=ZoneInfo(birth.timezone),hour=0,minute=0,second=0,microsecond=0) if forecast_start_date else (now.replace(day=1,hour=0,minute=0,second=0,microsecond=0) if unit!="days" else now.replace(hour=0,minute=0,second=0,microsecond=0))
    end=datetime.fromisoformat(forecast_end_date).replace(tzinfo=ZoneInfo(birth.timezone),hour=23,minute=59,second=59,microsecond=0) if forecast_end_date else forecast_end(start,amount,unit)
    if end <= start: raise ValueError("Forecast end date must be after forecast start date")
    if (end-start).days > 36525: raise ValueError("Forecast date range cannot exceed 100 years")
    if forecast_start_date or forecast_end_date:
        amount=max(1,(end-start).days); unit="days"
    gran=choose_forecast_granularity(amount,unit,forecast_granularity)
    age_years=max(1,(end-birth.local_dt).days/365.2425)
    chart["dashas"]=vimshottari_dasha(planets["Moon"]["longitude"],birth.local_dt,age_years,levels=5)
    chart["dashas"]["mahadasha_timeline"]=vimshottari_mahadasha_timeline(planets["Moon"]["longitude"],birth.local_dt,years_forward=max(120,age_years+50))
    chart["current_transits"]=build_current_transit_snapshot(birth,chart)
    engine_phase("[ENGINE] Vimshottari hierarchy generated current transit snapshot ready")
    chart["transits"]=build_transit_scan(birth,chart,forecast_years,start,end,gran)
    # Dedicated forecast layers keep weekly, monthly and yearly interpretation data
    # available without forcing the browser to render all layers at once.
    chart["forecast_layers"]={
        "weekly": build_transit_scan(birth,chart,forecast_years,start,end,"weekly"),
        "monthly": build_transit_scan(birth,chart,forecast_years,start,end,"monthly"),
        "yearly": build_transit_scan(birth,chart,forecast_years,start,end,"quarterly"),
    }
    chart["timing_windows"]=timing_windows(chart,chart["dashas"],chart["transits"])
    engine_phase("[ENGINE] Forecast/transit scan complete rows=%d weekly=%d monthly=%d", len(chart.get("transits",[])), len(chart["forecast_layers"]["weekly"]), len(chart["forecast_layers"]["monthly"]))
    chart["forecast"]={"start":start.date().isoformat(),"end":end.date().isoformat(),"amount":amount,"unit":unit,"years":round((end-start).days/365.2425,2),"granularity":gran,"custom_range":bool(forecast_start_date or forecast_end_date),"analysis_layers":["D1 Rashi","all calculated divisional charts (Vargas)","planetary dignity/retrograde/combustion/strength","house and house-lord analysis","planetary aspects","nakshatra and pada","Vimshottari Dasha hierarchy","transits and timing windows","detected Yogas and activation windows","detected Doshas and life-area impacts","Ashtakavarga","Shadbala","Jaimini indicators where selected","numerology where available"]}
    chart["performance"]=build_performance_profile(chart,chart["transits"],chart["dashas"])
    chart["modern_insights"]=build_modern_insights(chart)
    chart["yogas"]=enrich_yogas_with_timing(chart["yogas"],chart["dashas"],chart["forecast_layers"].get("weekly") or chart["transits"])
    chart["doshas"] = expanded_doshas(planets,chart["lagna_sign_index"])
    chart["dosha_catalog"] = dosha_catalog_status(chart["doshas"])
    chart["yoga_catalog"]=catalog_status(chart["yogas"])
    chart["numerology"]=analyze_numerology(birth.name,birth.dob,years=min(30,max(1,amount if unit=="years" else 10)))
    from .advanced import advanced_timing, exact_planetary_events, eclipse_events, tajaka_year
    chart["advanced_timing"]=advanced_timing(chart, birth.local_dt, chart["transits"], school)
    chart["exact_astronomical_events"]=exact_planetary_events(start, end, birth.timezone)
    chart["eclipses"]=eclipse_events(start, end, birth.timezone)
    engine_phase("[ENGINE] Exact astronomical events complete events=%d eclipses=%d", len(chart["exact_astronomical_events"].get("events",[])), len(chart["eclipses"].get("events",[])))
    annual=[]
    for yr in range(start.year, min(end.year, start.year+10)+1):
        try: annual.append(tajaka_year(chart,birth.local_dt,yr))
        except Exception as exc: annual.append({"year":yr,"error":str(exc)})
    chart["tajaka"]={"years":annual,"method":"Annual solar-return research layer; use selected school profile for interpretation."}
    chart["methodology"]={"school":school,"school_label":chart["advanced_timing"]["school_profile"]["label"],"calculation_layers":["Swiss Ephemeris","Lahiri sidereal","Whole-sign houses","16 principal Vargas","Nakshatra/Pada","Vimshottari","Shadbala","Ashtakavarga","Jaimini/Tajaka research layers","Exact ingress/station/eclipses"],"validation_note":"Forecast outputs are rule-based astrological research signals. Historical backtests validate reproducibility and rule coverage, not causal or guaranteed predictive accuracy."}
    chart["recommendations"]=_forecast_recommendations(chart)
    engine_phase("[ENGINE] Calculation complete duration_ms=%.1f", (time.perf_counter()-started)*1000)
    return chart


def _forecast_recommendations(chart: Mapping[str,Any])->Dict[str,Any]:
    perf=chart.get("performance",{}); peaks=perf.get("peaks",{}); out={}
    labels={"career":"career progress / visibility","finances":"financial planning / resource building","marriage":"relationship and partnership focus","family":"family / home focus","learning":"study / skill development","wellness":"routine and recovery focus","inner_growth":"reflection / spiritual practice"}
    for domain,items in peaks.items():
        top=items[:3]
        out[domain]={
            "label":labels.get(domain,domain),
            "windows":[{"date":x["date"],"score":x["score"],"dasha":x["dasha"]} for x in top],
            "interpretive_note": "Symbolic activation index from the chart's calculated timing layers; it is not a probability or guarantee."
        }
    top_windows=sorted([{'date':items[0]['date'],'domain':d,'score':items[0]['score']} for d,items in peaks.items() if items],key=lambda x:-x['score'])
    out['start_new']={'method':'cross-domain activation screen','windows':top_windows[:6],'note':'These are symbolic planning windows, not guarantees or objective best-time measurements.'}
    out['career_switch']={'label':'career change / role transition','windows':peaks.get('career',[])[:5],'action':'Use these as review windows for applications, negotiations or transition planning; validate the decision against finances, responsibilities and real-world opportunities.'}
    out['family_time']={'label':'family / home focus','windows':peaks.get('family',[])[:5],'action':'Prefer these windows for deliberate family time, home planning and relationship repair work when practical.'}
    out['learning_push']={'label':'learning / certification push','windows':peaks.get('learning',[])[:5],'action':'Use these windows for study sprints, exams, publishing or skill-building when the external schedule permits.'}
    out['relationship_focus']={'label':'relationship / partnership focus','windows':peaks.get('marriage',[])[:5],'action':'Use these periods for communication, partnership discussions and intentional relationship time rather than treating them as guarantees.'}
    return out

