from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo
import math
import swisseph as swe

from .engine import (
    _calc_planets, _time_to_jd, angular_distance, norm360, sign_index, deg_in_sign,
    SIGNS, PLANETS, EXALTATIONS, MULATRIKONA, OWN_SIGNS, _whole_sign_house,
)

SCHOOL_PROFILES = {
    "parashari": {
        "label": "Parashari synthesis",
        "timing": ["Vimshottari", "transits", "Ashtakavarga"],
        "notes": "Primary whole-sign Vedic framework with classical graha drishti and Varga emphasis.",
    },
    "jaimini": {
        "label": "Jaimini synthesis",
        "timing": ["Chara Dasha", "Chara Karakas", "Arudha", "Jaimini rashi drishti"],
        "notes": "Jaimini-oriented layer; several Jaimini techniques have school-specific variants.",
    },
    "tajaka": {
        "label": "Tajaka / Varshaphala",
        "timing": ["Solar return", "Muntha", "Annual Dasha", "Sahams"],
        "notes": "Annual-chart layer for year-specific questions. Exact Tajaka rules can vary by tradition.",
    },
    "synthesis": {
        "label": "Multi-school synthesis",
        "timing": ["Vimshottari", "Chara Dasha", "Tajaka", "Transits", "Ashtakavarga"],
        "notes": "Presents independent signals side by side rather than collapsing schools into one score.",
    },
}

# Classical natural bala values commonly expressed in shashtiamsas.
NAISARGIKA = {"Sun": 60.00, "Moon": 51.43, "Mars": 17.14, "Mercury": 25.71,
              "Jupiter": 34.29, "Venus": 42.86, "Saturn": 8.57}
SHADBALA_MIN_RUPAS = {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
                      "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}
DIG_STRONG = {"Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7}

# Standard BAV contributor table (BPHS-style 8 reference points).
BAV_TABLE = {
"Sun":{"Sun":[1,2,4,7,8,9,10,11],"Moon":[3,6,10,11],"Mars":[1,2,4,7,8,9,10,11],"Mercury":[3,5,6,9,10,11,12],"Jupiter":[5,6,9,11],"Venus":[6,7,12],"Saturn":[1,2,4,7,8,9,10,11],"Lagna":[3,4,6,10,11,12]},
"Moon":{"Sun":[3,6,7,8,10,11],"Moon":[1,3,6,7,10,11],"Mars":[2,3,5,6,9,10,11],"Mercury":[1,3,4,5,7,8,10,11],"Jupiter":[1,4,7,8,10,11,12],"Venus":[3,4,5,7,9,10,11],"Saturn":[3,5,6,11],"Lagna":[3,6,10,11]},
"Mars":{"Sun":[3,5,6,10,11],"Moon":[3,6,11],"Mars":[1,2,4,7,8,10,11],"Mercury":[3,5,6,11],"Jupiter":[6,10,11,12],"Venus":[6,8,11,12],"Saturn":[1,4,7,8,9,10,11],"Lagna":[1,3,6,10,11]},
"Mercury":{"Sun":[5,6,9,11,12],"Moon":[2,4,6,8,10,11],"Mars":[1,2,4,7,8,9,10,11],"Mercury":[1,3,5,6,9,10,11,12],"Jupiter":[6,8,11,12],"Venus":[1,2,3,4,5,8,9,11],"Saturn":[1,2,4,7,8,9,10,11],"Lagna":[1,2,4,6,8,10,11]},
"Jupiter":{"Sun":[1,2,3,4,7,8,9,10,11],"Moon":[2,5,7,9,11],"Mars":[1,2,4,7,8,10,11],"Mercury":[1,2,4,5,6,9,10,11],"Jupiter":[1,2,3,4,7,8,10,11],"Venus":[2,5,6,9,10,11],"Saturn":[3,5,6,12],"Lagna":[1,2,4,5,6,7,9,10,11]},
"Venus":{"Sun":[8,11,12],"Moon":[1,2,3,4,5,8,9,11,12],"Mars":[3,4,6,8,9,11,12],"Mercury":[3,5,6,9,11],"Jupiter":[5,8,9,10,11],"Venus":[1,2,3,4,5,8,9,10,11],"Saturn":[3,4,5,8,9,10,11],"Lagna":[1,2,3,4,5,8,9]},
"Saturn":{"Sun":[1,2,4,7,8,10,11],"Moon":[3,6,11],"Mars":[3,5,6,10,11,12],"Mercury":[6,8,9,10,11,12],"Jupiter":[5,6,11,12],"Venus":[6,11,12],"Saturn":[3,5,6,11],"Lagna":[1,3,4,6,10,11]},
}


def classical_ashtakavarga(planets: Mapping[str, Mapping[str, Any]], lagna_sign: int) -> Dict[str, Any]:
    signs = {p: sign_index(d["longitude"]) for p, d in planets.items()}
    refs = {p: signs[p] for p in ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn")}
    refs["Lagna"] = lagna_sign
    bav: dict[str, list[int]] = {}
    prastara: dict[str, list[list[int]]] = {}
    for planet, table in BAV_TABLE.items():
        row=[]; matrix=[]
        for s in range(12):
            contributions=[]
            bindu=0
            for ref, ref_sign in refs.items():
                house=((s-ref_sign)%12)+1
                yes=int(house in table[ref])
                contributions.append(yes); bindu+=yes
            row.append(bindu); matrix.append(contributions)
        bav[planet]=row; prastara[planet]=matrix
    sav=[sum(bav[p][s] for p in bav) for s in range(12)]
    # Graha-wise classical-style shodhana: operate on each planet's BAV row,
    # not on the aggregate SAV. The exact school conventions and rasimana
    # multiplier are recorded in the result.
    tri_sets=[(0,4,8),(1,5,9),(2,6,10),(3,7,11)]
    trikona_bav={}; ekadhipatya_bav={}; trikona_steps={}; eka_steps={}
    owner_pairs=[(0,7),(1,6),(2,5),(8,11),(9,10)]
    occupied=set(signs.values()) | {lagna_sign}
    rasi_multipliers=[7,10,8,4,10,6,7,8,9,5,11,12]  # BPHS/PVR-style set; Virgo=6
    graha_multipliers={"Sun":5,"Moon":5,"Mars":8,"Mercury":5,"Jupiter":10,"Venus":7,"Saturn":5}
    per_planet_pinda={}
    for planet,row in bav.items():
        reduced=row[:]; steps=[]
        for trio in tri_sets:
            vals=[reduced[i] for i in trio]
            # Common BPHS/PVR rule: if any sign has zero bindus, no trikona reduction.
            if 0 in vals: steps.append({"signs":[SIGNS[i] for i in trio],"action":"unchanged_zero_present"}); continue
            if vals[0]==vals[1]==vals[2]:
                for i in trio: reduced[i]=0
                steps.append({"signs":[SIGNS[i] for i in trio],"action":"all_zero_equal"})
            else:
                m=min(vals)
                for i in trio: reduced[i]-=m
                steps.append({"signs":[SIGNS[i] for i in trio],"action":"subtract_minimum","amount":m})
        trikona_bav[planet]=reduced
        trikona_steps[planet]=steps
        eka=reduced[:]; est=[]
        for a,b in owner_pairs:
            if eka[a]==0 or eka[b]==0 or (a in occupied and b in occupied):
                est.append({"signs":[SIGNS[a],SIGNS[b],],"action":"unchanged_zero_or_both_occupied"}); continue
            occ_a=a in occupied; occ_b=b in occupied
            if not occ_a and not occ_b:
                if eka[a]==eka[b]: eka[a]=eka[b]=0; action="both_empty_equal_zero"
                else: m=min(eka[a],eka[b]); eka[a]=eka[b]=m; action="both_empty_equalize_to_min"
            elif occ_a:
                if eka[b] <= eka[a]: eka[b]=0; action="empty_b_reduced_to_zero"
                else: eka[b]=eka[a]; action="empty_b_capped_to_occupied"
            else:
                if eka[a] <= eka[b]: eka[a]=0; action="empty_a_reduced_to_zero"
                else: eka[a]=eka[b]; action="empty_a_capped_to_occupied"
            est.append({"signs":[SIGNS[a],SIGNS[b]],"action":action})
        ekadhipatya_bav[planet]=eka; eka_steps[planet]=est
        rp=sum(eka[i]*rasi_multipliers[i] for i in range(12))
        gp=sum(graha_multipliers[ref]*eka[signs[ref]] for ref in graha_multipliers)
        per_planet_pinda[planet]={"rasi_pinda":rp,"graha_pinda":gp,"shodhya_pinda":rp+gp}
    return {"method":"Classical BAV/SAV contributor tables with graha-wise Trikona Shodhana, Ekadhipatya Shodhana and Shodhya Pinda; BPHS/PVR-style assumptions", 
            "bav":bav,"sav":sav,"prastara":prastara,
            "trikona_shodhana":{p:trikona_bav[p] for p in trikona_bav},
            "trikona_steps":trikona_steps,
            "ekadhipatya_shodhana":ekadhipatya_bav,"ekadhipatya_steps":eka_steps,
            "shodhya_pinda":{"rasi_pinda":sum(v['rasi_pinda'] for v in per_planet_pinda.values()),"reduced_pinda":sum(v['shodhya_pinda'] for v in per_planet_pinda.values()),"per_planet":per_planet_pinda},
            "conventions":{"rasimana_multipliers":rasi_multipliers,"grahamana_multipliers":graha_multipliers,"occupied_signs_for_ekadhipatya":[SIGNS[i] for i in sorted(occupied)],"school":"BPHS/PVR-style; source conventions differ, especially Virgo rasimana multiplier"},
            "validation":{"expected_sav_total":337,"actual_sav_total":sum(sav),"sav_total_pass":sum(sav)==337,"rahu_ketu_excluded_from_bav_contributors":True}}



def _saptavarga_score(planet: str, varga_signs: Mapping[str, Mapping[str, Any]]) -> float:
    score=0.0
    for key in ("D1","D2","D3","D7","D9","D12","D30"):
        sign=varga_signs.get(key,{}).get("planets",{}).get(planet,{}).get("sign_index")
        if sign is None: continue
        if sign==EXALTATIONS.get(planet): score += 30
        elif sign==MULATRIKONA.get(planet): score += 22.5
        elif sign in OWN_SIGNS.get(planet,set()): score += 15
        else: score += 3.75
    return score


def shadbala(planets: Mapping[str, Mapping[str, Any]], lagna_sign: int, vargas: Mapping[str, Mapping[str, Any]], birth_local: datetime) -> Dict[str, Any]:
    rows={}
    # Six-fold framework. The implementation is auditable and uses 60-virupa component units.
    for p in ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"):
        d=planets[p]; lon=d["longitude"]; house=_whole_sign_house(lagna_sign,sign_index(lon))
        ex=EXALTATIONS[p]; dist=angular_distance(lon, ex*0+({"Sun":10,"Moon":33,"Mars":298,"Mercury":165,"Jupiter":95,"Venus":357,"Saturn":200}[p]))
        uccha=max(0.0,60.0*(1-dist/180.0))
        sapt=_saptavarga_score(p,vargas)
        kendra={1:60,4:60,7:60,10:60,2:30,5:30,8:30,11:30}.get(house,15)
        sthana=uccha+sapt+kendra
        strong_house=DIG_STRONG[p]; diff=abs(house-strong_house); diff=min(diff,12-diff)
        dig=max(0.0,60.0*(1-diff/6.0))
        # Kala: day/night + waxing/waning approximation. Moon gets the strongest paksha contribution.
        day=birth_local.hour>=6 and birth_local.hour<18
        kala=30.0 + (15.0 if (p in ("Sun","Jupiter","Venus") and day) or (p in ("Moon","Mars","Saturn") and not day) else 0.0)
        if p=="Moon": kala += 15.0
        chesta=45.0 if d.get("retrograde") else 30.0
        if p in ("Sun","Moon"): chesta=30.0
        nais=NAISARGIKA[p]
        # Drik: signed sum of exact classical aspect relationships, capped.
        drik=0.0
        for q,qdat in planets.items():
            if q==p or q not in ("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"): continue
            dd=angular_distance(lon,qdat["longitude"])
            near=min((0,60,90,120,180),key=lambda x:abs(dd-x)); orb=abs(dd-near)
            if orb<=5:
                benefic=q in ("Jupiter","Venus") or (q=="Mercury" and not qdat.get("combust",False))
                drik += (10-orb*2) if benefic else -(10-orb*2)
        drik=max(-30,min(30,drik))
        total=sthana+dig+kala+chesta+nais+drik
        rupas=total/60
        pct=100*rupas/SHADBALA_MIN_RUPAS[p]
        ishta=math.sqrt(max(0,uccha*min(60,chesta)))
        kashta=math.sqrt(max(0,(60-uccha)*(60-min(60,chesta))))
        rows[p]={"sthana":round(sthana,2),"dig":round(dig,2),"kala":round(kala,2),"cheshta":round(chesta,2),"naisargika":round(nais,2),"drik":round(drik,2),"total_virupas":round(total,2),"rupas":round(rupas,2),"minimum_rupas":SHADBALA_MIN_RUPAS[p],"strength_pct":round(pct,1),"classification":"strong" if pct>=150 else "adequate" if pct>=100 else "below-minimum","ishta_phala":round(ishta,2),"kashta_phala":round(kashta,2)}
    return {"method":"Shadbala-inspired six-component screening estimate; not a complete canonical Shadbala calculation", "planets":rows,"units":"virupas / rupas (approximate component units)","note":"Rahu and Ketu are excluded. Sthana/Kala/Cheshta/Drik component formulas are simplified proxies; do not treat strength_pct or classification as a canonical Shadbala result. Full classical bala requires complete subcomponent calculations and chosen school conventions."}


def _jd_to_dt(jd: float, tz: str = "UTC") -> datetime:
    y,m,d,ut=swe.revjul(jd, swe.GREG_CAL)
    h=int(ut); mins=(ut-h)*60; mi=int(mins); sec=round((mins-mi)*60)
    if sec>=60: sec=0; mi+=1
    if mi>=60: mi=0; h+=1
    dt=datetime(int(y),int(m),int(d),h,mi,min(sec,59),tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(tz))


def _bisect_root(fn, lo: float, hi: float, iterations: int=32) -> float:
    flo=fn(lo); fhi=fn(hi)
    for _ in range(iterations):
        mid=(lo+hi)/2; fm=fn(mid)
        if abs(fm)<1e-7: return mid
        if flo*fm<=0: hi=mid; fhi=fm
        else: lo=mid; flo=fm
    return (lo+hi)/2


def exact_planetary_events(start: datetime, end: datetime, tz: str="UTC") -> Dict[str, Any]:
    """Find sign ingresses and retrograde stations by numerical refinement."""
    start=start.astimezone(timezone.utc); end=end.astimezone(timezone.utc)
    jd0=_time_to_jd(start); jd1=_time_to_jd(end)
    events=[]
    planets=["Mercury","Venus","Mars","Jupiter","Saturn","Rahu"]
    ids={p:{"Mercury":swe.MERCURY,"Venus":swe.VENUS,"Mars":swe.MARS,"Jupiter":swe.JUPITER,"Saturn":swe.SATURN,"Rahu":swe.MEAN_NODE}[p] for p in planets}
    step=1.0
    cur=jd0
    prev={}
    while cur<=jd1:
        for p in planets:
            xx=swe.calc_ut(cur,ids[p],swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED)[0]
            lon,speed=norm360(xx[0]),xx[3]
            s=sign_index(lon)
            if p in prev:
                pl,ps,p_speed=prev[p]
                if s!=ps:
                    # sign boundary root using shortest angular distance to target boundary
                    target=(s*30)%360
                    def f(j):
                        l=norm360(swe.calc_ut(j,ids[p],swe.FLG_SWIEPH|swe.FLG_SIDEREAL)[0][0])
                        return ((l-target+180)%360)-180
                    root=_bisect_root(f,cur-step,cur)
                    events.append({"type":"ingress","planet":p,"from_sign":SIGNS[ps],"to_sign":SIGNS[s],"datetime":_jd_to_dt(root,tz).isoformat()})
                if (speed<0 and prev[p][2]>=0) or (speed>=0 and prev[p][2]<0):
                    def sf(j):
                        return swe.calc_ut(j,ids[p],swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED)[0][3]
                    try:
                        root=_bisect_root(sf,cur-step,cur,iterations=40)
                    except Exception:
                        root=cur
                    events.append({"type":"station","planet":p,"station":"retrograde" if speed<0 else "direct","datetime":_jd_to_dt(root,tz).isoformat(),"speed_before":round(prev[p][2],6),"speed_after":round(speed,6)})
            prev[p]=(lon,s,speed)
        cur+=step
    return {"events":events,"method":"Daily ephemeris scan with numerical refinement around sign boundaries and speed sign changes.","precision_note":"Station times are refined to the local numerical root; ingress times are ephemeris-refined but should be checked against the selected ephemeris settings."}


def eclipse_events(start: datetime, end: datetime, tz: str="UTC") -> Dict[str, Any]:
    out=[]; cursor=_time_to_jd(start.astimezone(timezone.utc)); end_jd=_time_to_jd(end.astimezone(timezone.utc))
    while cursor<end_jd:
        flag,t=swe.sol_eclipse_when_glob(cursor,swe.FLG_SWIEPH,0,False); mx=t[0]
        if mx<=cursor or mx>end_jd: break
        out.append({"type":"solar_eclipse","maximum":_jd_to_dt(mx,tz).isoformat(),"flags":int(flag)})
        cursor=mx+1
    cursor=_time_to_jd(start.astimezone(timezone.utc))
    while cursor<end_jd:
        flag,t=swe.lun_eclipse_when(cursor,swe.FLG_SWIEPH,0,False); mx=t[0]
        if mx<=cursor or mx>end_jd: break
        out.append({"type":"lunar_eclipse","maximum":_jd_to_dt(mx,tz).isoformat(),"flags":int(flag)})
        cursor=mx+1
    return {"events":sorted(out,key=lambda x:x["maximum"]),"method":"Swiss Ephemeris global eclipse search.","note":"Global eclipse occurrence; local visibility requires a separate topocentric/local-visibility calculation."}


def _solar_return_jd(natal_sun: float, year: int) -> float:
    # Search around the birthday in UTC and refine the first Sun longitude crossing.
    approx=datetime(year,1,1,tzinfo=timezone.utc)
    start=_time_to_jd(approx); prev=start
    def angle(j):
        return ((norm360(swe.calc_ut(j,swe.SUN,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)[0][0])-natal_sun+180)%360)-180
    pv=angle(prev)
    for i in range(1,370):
        cur=start+i
        cv=angle(cur)
        if pv*cv<=0:
            return _bisect_root(angle,prev,cur)
        prev=cur; pv=cv
    return start


def tajaka_year(natal: Mapping[str, Any], birth: datetime, year: int) -> Dict[str, Any]:
    jd=_solar_return_jd(natal["planets"]["Sun"]["longitude"],year)
    dt=_jd_to_dt(jd,birth.tzinfo.key if getattr(birth.tzinfo,"key",None) else "UTC")
    pos=_calc_planets(jd); flags=swe.FLG_SWIEPH|swe.FLG_SIDEREAL
    cusps,ascmc=swe.houses_ex(jd,natal["meta"]["latitude"],natal["meta"]["longitude"],b"W",flags)
    asc=norm360(ascmc[0]); muntha=norm360(natal["lagna_longitude"]+30*((year-birth.year)%12))
    year_lord=list(("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"))[((year-birth.year)%7)]
    return {"year":year,"solar_return":dt.isoformat(),"lagna":asc,"lagna_sign":SIGNS[sign_index(asc)],"muntha":muntha,"muntha_sign":SIGNS[sign_index(muntha)],"year_lord":year_lord,"planets":{p:{"longitude":d["longitude"],"sign":SIGNS[sign_index(d["longitude"])]} for p,d in pos.items()},"sahams":{},"method":"Tajaka annual solar-return screen; Muntha/year-lord timing is school-dependent."}


def chara_dasha(lagna_sign: int, start: datetime, years: int=12) -> Dict[str, Any]:
    # Jaimini Chara Dasha is sign-based and has multiple direction rules. This implementation exposes a transparent 12-sign annual cycle.
    signs=list(range(12)); nodes=[]; cur=start
    for i in range(years):
        s=(lagna_sign+i)%12
        end=cur+timedelta(days=365.2425)
        nodes.append({"sign":SIGNS[s],"sign_index":s,"start":cur.isoformat(),"end":end.isoformat(),"years":1})
        cur=end
    return {"system":"Chara Dasha","periods":nodes,"method":"Jaimini sign-dasha research mode using one-year sign periods from Lagna; advanced direction/antardasha variants are selectable in future rule packs."}


def ashtottari_dasha(moon_lon: float, start: datetime, years: int=8) -> Dict[str, Any]:
    order=[("Sun",6), ("Moon",15), ("Mars",8), ("Mercury",17), ("Saturn",10), ("Jupiter",19), ("Rahu",12), ("Venus",21)]
    total=108; span=360/27; idx=int(moon_lon//span)%8; cur=start; out=[]
    for i in range(8):
        lord,dur=order[(idx+i)%8]; end=cur+timedelta(days=365.2425*dur)
        out.append({"lord":lord,"start":cur.isoformat(),"end":end.isoformat(),"years":dur}); cur=end
        if cur>=start+timedelta(days=365.2425*years): break
    return {"system":"Ashtottari Dasha","cycle_years":total,"periods":out,"applicability":"Conditional dasha; chart-school rules should be checked before using it as a primary timing system."}


def yogini_dasha(start: datetime, years:int=8) -> Dict[str, Any]:
    order=[("Mangala",1),("Pingala",2),("Dhanya",3),("Bhramari",4),("Bhadrika",5),("Ulka",6),("Siddha",7),("Sankata",8)]
    cur=start; out=[]
    for name,dur in order*4:
        end=cur+timedelta(days=365.2425*dur); out.append({"lord":name,"years":dur,"start":cur.isoformat(),"end":end.isoformat()}); cur=end
        if (cur-start).days>=365.2425*years: break
    return {"system":"Yogini Dasha","cycle_years":36,"periods":out}


def narayana_dasha(lagna_sign:int,start:datetime,years:int=12)->Dict[str,Any]:
    cur=start; out=[]
    for i in range(years):
        s=(lagna_sign+i)%12; end=cur+timedelta(days=365.2425); out.append({"sign":SIGNS[s],"sign_index":s,"start":cur.isoformat(),"end":end.isoformat(),"years":1}); cur=end
    return {"system":"Narayana Dasha","periods":out,"method":"Sign-based annual research mode; Narayana direction and exceptions vary by lineage."}


def kalachakra_dasha(moon_lon:float,start:datetime,years:int=8)->Dict[str,Any]:
    # The full Kalachakra mapping is highly lineage-specific; expose a deterministic research sequence keyed to Moon nakshatra.
    idx=int(moon_lon/(360/27)); base=[0,4,8,3,7,11,2,6,10,1,5,9]
    cur=start; out=[]
    for i in range(years):
        s=base[(idx+i)%12]; end=cur+timedelta(days=365.2425); out.append({"sign":SIGNS[s],"sign_index":s,"start":cur.isoformat(),"end":end.isoformat(),"years":1}); cur=end
    return {"system":"Kalachakra Dasha","periods":out,"method":"Research-mode sign sequence keyed to lunar nakshatra; full traditional gati/pada logic is lineage-specific."}


def sudarshana_chakra(natal: Mapping[str,Any], transits: Sequence[Mapping[str,Any]]) -> Dict[str,Any]:
    lag=natal["lagna_sign_index"]; moon=sign_index(natal["planets"]["Moon"]["longitude"]); sun=sign_index(natal["planets"]["Sun"]["longitude"])
    rows=[]
    for tr in transits:
        scores={"Lagna":0,"Moon":0,"Sun":0}
        for base,label in ((lag,"Lagna"),(moon,"Moon"),(sun,"Sun")):
            for p in ("Jupiter","Saturn"):
                h=_whole_sign_house(base,sign_index(tr["planets"][p]))
                if h in (1,5,9,10,11): scores[label]+=20
                elif h in (6,8,12): scores[label]-=10
        rows.append({"date":tr["date"],**scores,"composite":round(sum(scores.values())/3,1)})
    return {"method":"Sudarshana Chakra three-reference screen (Lagna, Moon, Sun)","rows":rows}


def advanced_timing(natal: Mapping[str,Any], birth: datetime, transits: Sequence[Mapping[str,Any]], school:str="synthesis") -> Dict[str,Any]:
    school=school if school in SCHOOL_PROFILES else "synthesis"
    start=datetime.fromisoformat(transits[0]["date"]).replace(tzinfo=birth.tzinfo) if transits else birth
    end=datetime.fromisoformat(transits[-1]["date"]).replace(tzinfo=birth.tzinfo) if transits else birth+timedelta(days=365)
    return {"school":school,"school_profile":SCHOOL_PROFILES[school],
            "chara_dasha":chara_dasha(natal["lagna_sign_index"],birth,max(12,((end-birth).days//365)+1)),
            "ashtottari":ashtottari_dasha(natal["planets"]["Moon"]["longitude"],birth,max(8,((end-birth).days//365)+1)),
            "yogini":yogini_dasha(birth,max(8,((end-birth).days//365)+1)),
            "narayana":narayana_dasha(natal["lagna_sign_index"],birth,max(12,((end-birth).days//365)+1)),
            "kalachakra":kalachakra_dasha(natal["planets"]["Moon"]["longitude"],birth,max(8,((end-birth).days//365)+1)),
            "sudarshana":sudarshana_chakra(natal,transits)}
