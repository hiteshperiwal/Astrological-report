from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
import re

SIGN_TRAITS = {
    "Aries": "direct, initiative-driven, competitive, quick to act",
    "Taurus": "steady, comfort-seeking, persistent, materially grounded",
    "Gemini": "curious, verbal, adaptive, multi-track in attention",
    "Cancer": "protective, emotionally perceptive, family-oriented",
    "Leo": "expressive, proud, creative, leadership-oriented",
    "Virgo": "analytical, service-minded, precise, improvement-oriented",
    "Libra": "relational, diplomatic, aesthetic, balance-seeking",
    "Scorpio": "intense, private, investigative, transformative",
    "Sagittarius": "expansive, candid, philosophical, freedom-seeking",
    "Capricorn": "structured, strategic, disciplined, responsibility-oriented",
    "Aquarius": "independent, conceptual, systems-oriented, future-facing",
    "Pisces": "imaginative, empathic, porous, meaning-oriented",
}
PLANET_THEMES = {
    "Sun": "identity, confidence, authority, life direction",
    "Moon": "emotional processing, habits, belonging, inner security",
    "Mars": "drive, assertion, conflict style, execution",
    "Mercury": "thinking, communication, analysis, commerce",
    "Jupiter": "learning, growth, ethics, mentors, opportunity",
    "Venus": "relationships, aesthetics, pleasure, negotiation, money preferences",
    "Saturn": "discipline, delay, responsibility, boundaries, long-term results",
    "Rahu": "amplification, novelty, appetite, unconventional experiences",
    "Ketu": "detachment, specialization, discontinuity, introspection",
}
HOUSE_THEMES = {
    1: "identity, vitality, self-presentation",
    2: "wealth, savings, speech, family resources",
    3: "skills, writing, communication, courage, siblings",
    4: "home, mother, property, emotional foundations",
    5: "creativity, intelligence, children, romance, speculation",
    6: "work routines, service, competition, debt, health maintenance",
    7: "partnerships, marriage, contracts, public counterparties",
    8: "joint resources, inheritance, deep change, research, uncertainty",
    9: "higher learning, travel, dharma, mentors, fortune",
    10: "career, status, authority, public contribution",
    11: "income, networks, gains, community, long-term aspirations",
    12: "expenses, retreat, foreign residence, sleep, contemplation",
}


def _active(periods: List[Dict[str, Any]], when: datetime) -> str:
    for p in periods:
        if datetime.fromisoformat(p["start"]) <= when < datetime.fromisoformat(p["end"]):
            return p["lord"]
    return "Unknown"


def _planet_sentiment(p: Dict[str, Any]) -> str:
    dignity = p.get("dignity", "Neutral")
    if dignity in ("Exalted", "Own sign", "Moolatrikona"):
        return "stronger / more coherent"
    if dignity == "Debilitated":
        return "more effort-intensive and context-sensitive"
    return "moderately expressed"


def generate_narrative(chart: Dict[str, Any]) -> Dict[str, Any]:
    lagna = chart["lagna_sign"]
    planets = chart["planets"]
    moon = planets["Moon"]
    sun = planets["Sun"]
    rising_style = SIGN_TRAITS[lagna]
    moon_style = SIGN_TRAITS[moon["sign"]]

    personality = [
        f"The {lagna} ascendant frames the outward operating style as {rising_style}.",
        f"The Moon in {moon['sign']} adds an inner pattern that is {moon_style}; this is often where private motivations differ from public presentation.",
        f"The Sun in {sun['sign']} places identity emphasis on {SIGN_TRAITS[sun['sign']]}, while its house position ({sun['house']}) shows the life arena where recognition and agency are repeatedly negotiated.",
    ]
    for p in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        x = planets[p]
        personality.append(
            f"{p}: {x['sign']} / house {x['house']} / {x['nakshatra']['name']} pada {x['nakshatra']['pada']} — {PLANET_THEMES[p]}; the planet is {x['dignity'].lower()} and therefore expresses its themes as { _planet_sentiment(x) } in expression."
        )

    def house_focus(houses: List[int]) -> List[Dict[str, Any]]:
        return [h for h in chart["houses"] if h["house"] in houses]

    finances = house_focus([2, 5, 8, 9, 11])
    family = house_focus([2, 4])
    marriage = house_focus([7])
    career = house_focus([6, 10, 11])
    wellness = house_focus([1, 6, 8, 12])

    annual = []
    transits = chart.get("transits", [])
    years_seen = sorted({datetime.fromisoformat(r["date"]).year for r in transits})
    for target_year in years_seen:
        rows = [r for r in transits if r["date"].startswith(str(target_year))]
        if rows:
            j_signs = {r["planets"]["Jupiter"] // 30 for r in rows}
            s_signs = {r["planets"]["Saturn"] // 30 for r in rows}
            j_houses = sorted({_house_from_transit(chart, x, "Jupiter") for x in rows})
            s_houses = sorted({_house_from_transit(chart, x, "Saturn") for x in rows})
            annual.append({
                "year": target_year,
                "jupiter_houses": j_houses,
                "saturn_houses": s_houses,
                "focus": _annual_focus(j_houses, s_houses),
            })

    timing = chart.get("timing_windows", [])[:80]
    return {
        "opening": "This report synthesizes the computed sidereal chart, divisional charts, dashas and transit timing into direct Jyotish interpretations.",
        "personality": personality,
        "finances": _domain_summary("finances", finances, planets),
        "family": _domain_summary("family", family, planets),
        "marriage": _domain_summary("marriage", marriage, planets),
        "career": _domain_summary("career", career, planets),
        "wellness": _domain_summary("wellness", wellness, planets),
        "spiritual": _domain_summary("spiritual", house_focus([8, 9, 12]), planets),
        "annual": annual,
        "timing": timing,
        "yogas": chart.get("yogas", []),
        "doshas": chart.get("doshas", []),
        "interpretations": build_interpretation_library(chart),
    }


def _house_from_transit(chart: Dict[str, Any], row: Dict[str, Any], planet: str) -> int:
    s = int(row["planets"][planet] // 30) % 12
    return ((s - chart["lagna_sign_index"]) % 12) + 1


def _annual_focus(j_houses: List[int], s_houses: List[int]) -> List[str]:
    out: List[str] = []
    for h in sorted(set(j_houses + s_houses)):
        if h in HOUSE_THEMES:
            out.append(f"house {h}: {HOUSE_THEMES[h]}")
    return out[:5]


def _domain_summary(domain: str, houses: List[Dict[str, Any]], planets: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    relevant = []
    for h in houses:
        relevant.append({"house": h["house"], "sign": h["sign"], "lord": h["lord"], "occupants": h["occupants"], "lord_house": h.get("lord_house")})
    notes: List[str] = []
    if domain == "finances":
        notes.append("Read the 2nd and 11th houses for earning/savings and the 5th/8th for risk, speculation, shared resources and volatility.")
        if any(planets[p]["house"] in (2, 5, 9, 11) for p in ("Jupiter", "Venus") if p in planets):
            notes.append("Jupiter/Venus connect to wealth-oriented houses, which can support expansion, negotiation or resource attraction, depending on dignity and timing.")
    elif domain == "family":
        notes.append("The 2nd house describes the family/resource base; the 4th adds home, emotional anchoring and property themes.")
    elif domain == "marriage":
        notes.append("Marriage is read from the 7th house and lord, Venus, Moon, and especially the Navamsa (D9). The application flags patterns rather than declaring an inevitable outcome.")
    elif domain == "career":
        notes.append("The 10th/6th/11th combination is used for work, visible contribution and gains; D10 adds a secondary career lens.")
    elif domain == "wellness":
        notes.append("The 1st, 6th, 8th and 12th houses connect vitality, routines, recovery and transformation themes in the traditional reading.")
    elif domain == "spiritual":
        notes.append("The 8th/9th/12th houses are treated as a symbolic triad for transformation, dharma/learning and retreat/inner life.")
    return {"domain": domain, "houses": relevant, "notes": notes}



# ---------------------------------------------------------------------------
# Expanded Jyotish interpretation library
# ---------------------------------------------------------------------------
# This is deliberately rule-based and transparent. It is a traditional
# interpretive reference layer, not an empirical personality or outcome model.

_SIGN_INTERP = {
    "Aries":"initiative, independence, direct action and a preference for starting rather than waiting",
    "Taurus":"stability, resources, persistence, sensory grounding and a preference for durable results",
    "Gemini":"curiosity, communication, adaptability, learning and movement between multiple interests",
    "Cancer":"care, belonging, protection, memory, family orientation and sensitivity to environment",
    "Leo":"creative self-expression, visibility, leadership, pride and a need to make a meaningful contribution",
    "Virgo":"analysis, craft, service, refinement, systems and attention to practical detail",
    "Libra":"partnership, diplomacy, aesthetics, negotiation and the search for balance",
    "Scorpio":"depth, investigation, resilience, privacy, transformation and concentrated effort",
    "Sagittarius":"learning, exploration, ethics, teaching, optimism and expansion of horizons",
    "Capricorn":"structure, responsibility, strategy, endurance and long-term achievement",
    "Aquarius":"independence, systems thinking, networks, experimentation and future-oriented ideas",
    "Pisces":"imagination, compassion, symbolism, surrender, spirituality and porous boundaries",
}

_PLANET_INTERP = {
    "Sun":"identity, authority, confidence, visibility, purpose and relationship with leadership",
    "Moon":"mind, emotional processing, habits, belonging, memory, comfort and responsiveness",
    "Mars":"drive, courage, initiative, competition, physical effort and conflict style",
    "Mercury":"thinking, speech, writing, analysis, learning, commerce and negotiation",
    "Jupiter":"wisdom, teaching, mentors, ethics, faith, expansion and opportunity",
    "Venus":"relationships, attraction, art, comfort, agreements, pleasure and values",
    "Saturn":"discipline, duty, boundaries, delay, endurance, accountability and durable results",
    "Rahu":"novelty, amplification, unconventional appetite, ambition and fascination with unfamiliar territory",
    "Ketu":"detachment, specialization, introspection, discontinuity and a tendency to simplify or withdraw",
}

_HOUSE_INTERP = {
    1:"identity, body, temperament, self-direction and how life is approached",
    2:"speech, family resources, savings, food, values and accumulated wealth",
    3:"communication, courage, writing, skills, siblings, initiative and short journeys",
    4:"home, emotional foundations, mother, property, education and inner security",
    5:"creativity, intelligence, children, romance, learning, mantra and calculated risk",
    6:"work routines, service, competition, debts, obstacles, discipline and health maintenance",
    7:"partnership, marriage, contracts, clients, public counterparts and one-to-one exchange",
    8:"shared resources, inheritance, vulnerability, research, hidden processes and transformation",
    9:"dharma, higher learning, teachers, pilgrimage, long journeys, principles and worldview",
    10:"career, status, responsibility, authority, public contribution and visible achievement",
    11:"income, gains, networks, communities, fulfilment of aims and long-term aspirations",
    12:"expenses, retreat, foreign environments, sleep, release, contemplation and private life",
}

_NAKSHATRA_INTERP = {
    "Ashwini":"swift beginnings, healing, initiative and a preference for direct movement",
    "Bharani":"capacity, responsibility, endurance, boundaries and transformation through experience",
    "Krittika":"discernment, purification, decisiveness and the ability to separate what is useful from what is not",
    "Rohini":"growth, cultivation, beauty, attraction and the building of tangible value",
    "Mrigashira":"searching, curiosity, investigation and movement toward something not yet fully understood",
    "Ardra":"intensity, renewal, questioning, disruption and rebuilding after insight",
    "Punarvasu":"return, restoration, learning from cycles and finding a path back to essentials",
    "Pushya":"nourishment, teaching, responsibility, protection and steady development",
    "Ashlesha":"perception, strategy, psychological depth and sensitivity to hidden dynamics",
    "Magha":"ancestry, authority, legacy, dignity and connection with inherited responsibilities",
    "Purva Phalguni":"enjoyment, creativity, affection, rest, attraction and the desire to celebrate life",
    "Uttara Phalguni":"agreements, patronage, responsibility, friendship and durable cooperation",
    "Hasta":"skill, craft, organization, practical intelligence and the ability to make ideas tangible",
    "Chitra":"design, refinement, charisma, craftsmanship and the creation of visible form",
    "Swati":"independence, movement, adaptability, trade and learning through self-direction",
    "Vishakha":"focus, ambition, persistence and concentrated movement toward a chosen goal",
    "Anuradha":"devotion, friendship, alliance, discipline and growth through relationship",
    "Jyeshtha":"protection, seniority, responsibility, strategic awareness and management of complexity",
    "Mula":"root investigation, simplification, release and the search for underlying causes",
    "Purva Ashadha":"conviction, renewal, persuasion, courage and strengthening through repeated effort",
    "Uttara Ashadha":"principles, responsibility, lasting achievement and commitment to collective standards",
    "Shravana":"listening, learning, transmission of knowledge and connection through information",
    "Dhanishtha":"rhythm, resources, social coordination, achievement and timing",
    "Shatabhisha":"healing, research, privacy, systems and the ability to work with complex problems",
    "Purva Bhadrapada":"intensity, ideals, transformation and willingness to examine difficult subjects",
    "Uttara Bhadrapada":"depth, stability, patience, compassion and long-duration transformation",
    "Revati":"guidance, completion, safe transitions, nourishment and compassionate movement",
}

_DIGNITY_GUIDANCE = {
    "Exalted":"traditionally treated as a strengthened expression of the planet's significations, subject to house, lordship and timing",
    "Own sign":"traditionally associated with familiarity and relative stability in the planet's expression",
    "Moolatrikona":"traditionally treated as a strong functional expression of the planet's core significations",
    "Neutral":"interpreted primarily through house, lordship, association, aspects and timing",
    "Debilitated":"traditionally read as an area requiring integration, skill and contextual support rather than as a fixed negative outcome",
}

def _planet_house_sentence(planet, house, sign, dignity, motion='direct', combust='not combust'):
    contextual = _corpus_direct('planet_contextual', f'{planet}|{house}|{sign}|{dignity}|{motion}|{combust}') if '_CORPUS_INDEX' in globals() else ''
    base = f"{planet} in the {house}th house places { _PLANET_INTERP[planet] } into the life arena of { _HOUSE_INTERP[house] }. In {sign}, the expression is colored by {_SIGN_INTERP[sign]}. The planet is {dignity.lower()}; { _DIGNITY_GUIDANCE.get(dignity, '') }."
    return contextual or base

def _dasha_context(chart, before=2, after=3):
    """Return current + adjacent Mahadashas, with full nested sub-periods."""
    now=_datetime_from_iso(chart.get('current_transits',{}).get('datetime')) if chart.get('current_transits',{}).get('datetime') else datetime.now()
    timeline=chart.get('dashas',{}).get('mahadasha_timeline',[]) or []
    top=[]
    for p in timeline:
        try: st=_datetime_from_iso(p['start']); en=_datetime_from_iso(p['end'])
        except Exception: continue
        top.append((st,en,p))
    idx=next((i for i,(st,en,p) in enumerate(top) if st<=now<en),None)
    if idx is None and top:
        idx=min(range(len(top)),key=lambda i:abs((top[i][0]-now).total_seconds()))

    order=[('Ketu',7),('Venus',20),('Sun',6),('Moon',10),('Mars',7),('Rahu',18),('Jupiter',16),('Saturn',19),('Mercury',17)]
    order_map={p:i for i,(p,_) in enumerate(order)}
    level_names={1:'Mahadasha',2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'}

    def make_children(start_iso,end_iso,lord,depth):
        # Browser payload stays compact: selected Mahadashas include Antardasha and
        # Pratyantar rows; the active chain still exposes all five levels. The PDF
        # expands Sookshma and Prana directly from the selected Mahadasha timings.
        if depth>3 or lord not in order_map: return []
        st=_datetime_from_iso(start_iso); en=_datetime_from_iso(end_iso); total=(en-st).total_seconds()
        cur=st; out=[]
        # Every sub-period starts from the lord of its parent, not from Ketu.
        # Vimshottari is a cyclic sequence; the first Antardasha of Jupiter is
        # Jupiter, the first Antardasha of Saturn is Saturn, etc.
        parent_idx=order_map[lord]
        for k in range(9):
            child_lord,years=order[(parent_idx+k)%9]
            dur=total*years/120.0
            child_end=en if k==8 else cur+timedelta(seconds=dur)
            node={'level':depth,'level_name':level_names[depth],'lord':child_lord,'start':cur.isoformat(),'end':child_end.isoformat()}
            if depth<3: node['children']=make_children(node['start'],node['end'],child_lord,depth+1)
            out.append(node); cur=child_end
        return out

    def serialize_top(node):
        out={'level':1,'level_name':'Mahadasha','lord':node.get('lord'),'start':node.get('start'),'end':node.get('end')}
        out['children']=make_children(out['start'],out['end'],out['lord'],2)
        return out

    selected=[]
    if idx is not None:
        selected.extend(top[max(0,idx-before):idx]); selected.append(top[idx]); selected.extend(top[idx+1:idx+1+after])
    previous=[serialize_top(p) for _,_,p in top[max(0,(idx or 0)-before):(idx or 0)]] if idx is not None else []
    current=serialize_top(top[idx][2]) if idx is not None else None
    future=[serialize_top(p) for _,_,p in top[(idx+1 if idx is not None else 0):(idx+1 if idx is not None else 0)+after]]

    # Active chain is taken from the forecast hierarchy because it preserves the exact
    # engine-generated active sub-period boundaries for the requested forecast horizon.
    active=[]
    def walk(nodes,depth=1):
        for node in nodes or []:
            try: st=_datetime_from_iso(node['start']); en=_datetime_from_iso(node['end'])
            except Exception: continue
            if st<=now<en:
                active.append({'level':depth,'level_name':level_names.get(depth,f'Level {depth}'),'lord':node.get('lord'),'start':node.get('start'),'end':node.get('end')})
                if depth<5: walk(node.get('children',[]),depth+1)
                return
    walk(chart.get('dashas',{}).get('periods',[]),1)
    return {'previous_mahadashas':previous,'current_mahadasha':current,'next_mahadashas':future,
            'selected_mahadashas':previous+([current] if current else [])+future,'current_hierarchy':active,
            'selection_rule':'2 previous + current + 3 next Mahadashas; each selected Mahadasha includes Antardasha, Pratyantar, Sookshma and Prana sub-periods.'}


def _transit_interpretations(chart):
    snap=chart.get('current_transits',{})
    rows=[]
    themes={'Jupiter':'growth, learning, expansion, opportunity and support','Saturn':'structure, responsibility, consolidation, accountability and delayed-but-durable results','Rahu':'novelty, amplification, experimentation, appetite and unconventional developments','Ketu':'detachment, specialization, simplification, closure and inward focus'}
    for p,d in snap.get('planets',{}).items():
        h=snap.get('slow_planet_houses',{}).get(p)
        if h is None: continue
        nk=d.get('nakshatra') or {}
        rows.append({'planet':p,'sign':d.get('sign'),'house':h,'degree':d.get('degree_in_sign'),'retrograde':d.get('retrograde'),'nakshatra':nk.get('name'),'pada':nk.get('pada'),'interpretation':f'{p} is currently in {d.get("sign")} in house {h}, {nk.get("name","the current Nakshatra")} pada {nk.get("pada","—")}. This transit emphasizes {themes.get(p,"the planet’s core significations")} through the matters of house {h}. The transit Nakshatra and Pada refine how that emphasis is expressed; retrograde motion makes the theme more review-oriented when applicable.'})
    milestones=[]
    current_houses={p:snap.get('slow_planet_houses',{}).get(p) for p in ('Jupiter','Saturn','Rahu','Ketu')}
    current_date=(snap.get('datetime') or '')[:10]
    last_seen=dict(current_houses)
    for r in (chart.get('transits') or []):
        if not r.get('date') or r['date'][:10] < current_date: continue
        for p in ('Jupiter','Saturn','Rahu','Ketu'):
            h=r.get(f'{p.lower()}_house')
            if h is None: continue
            prev=last_seen.get(p)
            if prev is not None and prev != h:
                nk=(r.get('transit_nakshatra') or {}).get(p) or {}
                milestones.append({'date':r['date'],'planet':p,'from_house':prev,'to_house':h,'sign':(nk.get('name') or '—'),'nakshatra':nk.get('name'),'pada':nk.get('pada'),'interpretation':f'{p} changes emphasis from house {prev} to house {h}. The new house shifts attention toward {HOUSE_THEMES.get(h,"the new life area")}. At the transition point {p} is in {nk.get("name","the current Nakshatra")} pada {nk.get("pada","—")}, refining the style of the change.'})
            last_seen[p]=h
    seen=set(); unique=[]
    for x in milestones:
        k=(x['date'],x['planet'],x['to_house'])
        if k not in seen: seen.add(k); unique.append(x)
    return {'current':rows,'future_milestones':unique[:80], 'latest_aspects':snap.get('aspects_to_natal',[])}



DASHA_THEMES={
 'Sun':'identity, authority, visibility, leadership, father/mentor themes and decisive life direction',
 'Moon':'mind, habits, emotional security, home, family, nourishment and changing priorities',
 'Mars':'initiative, competition, courage, technical action, property, conflict resolution and physical drive',
 'Mercury':'learning, communication, analysis, commerce, contracts, technology, networking and adaptability',
 'Jupiter':'education, mentors, wisdom, expansion, finances, children, ethics, travel and opportunity',
 'Venus':'relationships, marriage, comfort, art, negotiation, vehicles, luxury and material enjoyment',
 'Saturn':'work, responsibility, discipline, delays, institutions, endurance, restructuring and long-term achievement',
 'Rahu':'unconventional ambition, foreign links, technology, appetite, experimentation and sudden shifts in priorities',
 'Ketu':'detachment, specialization, research, spiritual inquiry, simplification and completion of old patterns',
}
DOSHA_THEMES={
 'Manglik / Kuja Dosha':'Mars brings a sharper, more active tone to the houses it influences. In relationship analysis this can increase the need for direct communication, patience and constructive handling of conflict.',
 'Kala Sarpa Yoga / Dosha':'A concentrated nodal axis can make periods of life feel strongly polarized, with themes of urgency, fixation, release and major directional shifts becoming more noticeable.',
 'Grahan Dosha':'Node-Sun/Moon contact can make identity or emotional themes more intense, unusual or periodically obscured; the exact house and degree relationship determines where the emphasis appears.',
 'Guru Chandal Dosha':'Jupiter-node contact can make learning, belief, ethics, teachers and judgment more unconventional; the placement can produce independent thinking but also requires careful discrimination.',
 'Shrapit Dosha':'Saturn-node contact can combine pressure, persistence and unconventional circumstances, often pushing the person to rebuild structures rather than relying on established patterns.',
 'Ganda Moola Dosha':'Moon in a traditionally classified Ganda Moola Nakshatra emphasizes transitions, sensitivity to change and the need to establish stable rhythms around the Moon’s house and lordship.',
 'Kalathra Dosha screen':'Node-Venus contact can make relationship and agreement themes more unconventional or intense, requiring clarity around expectations and attachment.',
 'Vish / Punarphoo Dosha screen':'Saturn-Moon contact can bring a serious or delayed tone to emotional matters, increasing the importance of maturity, patience and stable routines.',
 'Kemadruma Dosha screen':'Reduced planetary support around the Moon can make self-generated emotional stability especially important; cancellation factors and the Moon’s dignity materially modify the reading.',
 'Papakartari Dosha screen':'Malefic enclosure concentrates pressure around the affected house or Lagna, often making discipline and deliberate choices more important until supportive factors activate.',
 'Gandanta screen':'A planet near a water-fire junction can mark a sensitive transition between modes of expression; the relevant house and dasha show where this becomes visible.',
 'Graha Yuddha screen':'Close planetary longitude can make the significations of the involved planets compete for expression, making their house lordships and dignity especially important.',
}

def _dasha_significance(chart, lord, level, start=None, end=None):
    p=chart.get('planets',{}).get(lord,{})
    h=p.get('house'); sign=p.get('sign'); n=p.get('nakshatra',{}) or {}
    house_theme=HOUSE_THEMES.get(int(h),'the occupied life area') if h else 'the relevant life area'
    level_phrase={1:'sets the broad life chapter',2:'selects the concrete area within that chapter',3:'narrows the active storyline',4:'concentrates the theme into a short phase',5:'acts as the finest timing layer'}.get(level,'refines timing')
    if not p: return f'{lord} {level_phrase}; the planet data is not available.'
    text=(f'{lord} {"Mahadasha" if level==1 else "Antardasha" if level==2 else "Pratyantar Dasha" if level==3 else "Sookshma Dasha" if level==4 else "Prana Dasha"} {level_phrase}. '
          f'Natal {lord} is in {sign}, house {h}, {n.get("name","—")} pada {n.get("pada","—")}. Its principal life themes are {DASHA_THEMES.get(lord,PLANET_THEMES.get(lord,lord))}. '
          f'Because it occupies house {h}, the period repeatedly activates {house_theme}; its sign and Nakshatra modify how those matters are pursued. '
          f'The period can change priorities, decisions and circumstances around these themes according to the other active dasha levels and transit support.')
    return {'lord':lord,'level':level,'level_name':{1:'Mahadasha',2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'}.get(level,'Dasha'),'start':start,'end':end,'text':text}

def _dasha_interpretations(chart):
    out=[]
    now=_datetime_from_iso(chart.get('current_transits',{}).get('datetime')) if chart.get('current_transits',{}).get('datetime') else datetime.now()
    # all periods intersecting the forecast plus the active chain, deduplicated
    seen=set()
    def walk(nodes,depth=1):
        for n in nodes or []:
            try: st=_datetime_from_iso(n['start']); en=_datetime_from_iso(n['end'])
            except Exception: continue
            if en < now and depth>1: continue
            if depth==1 or (st <= now <= en) or (en >= now and depth<=3):
                key=(depth,n.get('lord'),n.get('start'))
                if key not in seen:
                    seen.add(key); out.append(_dasha_significance(chart,n.get('lord'),depth,n.get('start'),n.get('end')))
            if depth<5 and (st <= now <= en): walk(n.get('children',[]),depth+1)
    walk(chart.get('dashas',{}).get('periods',[]),1)
    # add past/current/future Mahadashas explicitly
    timeline=chart.get('dashas',{}).get('mahadasha_timeline',[])
    for n in timeline:
        try: st=_datetime_from_iso(n['start']); en=_datetime_from_iso(n['end'])
        except Exception: continue
        if en >= now and len([x for x in out if x['level']==1])>=8: break
        if (1,n.get('lord'),n.get('start')) not in seen:
            out.append(_dasha_significance(chart,n.get('lord'),1,n.get('start'),n.get('end')))
            seen.add((1,n.get('lord'),n.get('start')))
    return out

def _dosha_interpretations(chart):
    out=[]
    for d in chart.get('doshas',[]):
        if d.get('status') not in ('screen-positive','present','possible'): continue
        name=d.get('name','')
        base=DOSHA_THEMES.get(name)
        if not base:
            base=DOSHA_THEMES.get(name.replace(' / Dosha','').replace(' screen','')+' screen')
        base=base or f'{name} is active in the chart according to the stated screening rule. Its effect is read through the affected planet, house, lordship, dignity and timing.'
        life=d.get('life_impact') or base
        impacts=[]
        for domain in ('relationship','career','money','family','health','education','spirituality','travel'):
            text=_corpus_direct('dosha_life_impact',f'{name}|{domain}')
            if text: impacts.append({'domain':domain,'text':text})
        direct=' '.join(x['text'] for x in impacts[:8])
        out.append({**d,'interpretation':f'{base} The specific chart basis is: {d.get("basis", "chart-specific condition detected")}. '+direct, 'life_impact':life, 'life_impact_by_domain':impacts})
    return out

def _gemstone_recommendations(chart):
    lagna=chart.get('lagna_sign_index',0); planets=chart.get('planets',{})
    house_lords={h:chart.get('houses',[{}])[h-1].get('lord') for h in range(1,13) if len(chart.get('houses',[]))>=h}
    candidates=[]
    for h,priority in ((1,100),(5,90),(9,95)):
        lord=house_lords.get(h); p=planets.get(lord,{})
        if not lord or not p: continue
        candidates.append((priority,lord,h,p))
    # Avoid recommending a stone simply because a planet is weak; prioritize benefic functional roles.
    stones={'Sun':('Ruby','Sun','identity, vitality and authority'), 'Moon':('Pearl','Moon','emotional steadiness and receptivity'), 'Mars':('Red Coral','Mars','initiative, courage and disciplined action'), 'Mercury':('Emerald','Mercury','learning, communication and analytical work'), 'Jupiter':('Yellow Sapphire','Jupiter','wisdom, teaching, expansion and guidance'), 'Venus':('Diamond / White Sapphire','Venus','relationships, aesthetics, negotiation and comfort'), 'Saturn':('Blue Sapphire','Saturn','discipline, structure and long-term responsibility'), 'Rahu':('Hessonite','Rahu','unconventional ambition and experimentation'), 'Ketu':("Cat's Eye",'Ketu','specialization, detachment and inward focus')}
    out=[]; used=set()
    for priority,lord,h,p in sorted(candidates,reverse=True):
        if lord in used or lord not in stones: continue
        stone,planet,focus=stones[lord]; used.add(lord)
        out.append({'planet':planet,'gemstone':stone,'priority':priority,'reason':f'{planet} rules house {h} for this Lagna and is therefore a primary chart significator. The gemstone is traditionally associated with strengthening that planet’s themes: {focus}. Natal placement: {p.get("sign")} house {p.get("house")}.','traditional_use':'Traditionally worn to strengthen the associated graha after considering its functional role, dignity and the complete chart.'})
    return out[:3]

def _prediction_answer(narrative, question):
    pred=narrative.get('predictions',{}) or {}
    rows=pred.get('predictions',[]) or []
    q=question.lower()
    requested=None
    if 'week' in q: requested='weekly'
    elif 'month' in q: requested='monthly'
    elif 'quarter' in q: requested='quarterly'
    elif 'year' in q or 'annual' in q: requested='yearly'
    if requested and requested != pred.get('granularity'):
        # The selected report horizon is authoritative; explain what is actually available.
        rows=rows[:8]
    else:
        rows=rows[:10]
    pieces=[f"The prediction section uses the selected {pred.get('granularity','forecast')} horizon and combines the calculated Vimshottari hierarchy, slow-planet transits, transit Nakshatra/Pada, Ashtakavarga, alternative Dashas, Sudarshana and exact astronomical events."]
    for r in rows:
        pieces.append(r.get('interpretation',''))
    return _unique_chat(pieces,12)

def _interpretation_chat(chart, narrative, question):
    q=_clean_chat_text(question).lower()
    i=narrative.get('interpretations',{}) if narrative else {}
    answers=[]
    # Explicit combined requests first.
    if 'yoga' in q and 'dosha' in q:
        answers.extend(_yoga_answer(chart,i,q,narrative))
        answers.extend(_dosha_answer(chart,i))
    elif 'yoga' in q:
        answers=_yoga_answer(chart,i,q,narrative)
    elif 'dosha' in q:
        answers=_dosha_answer(chart,i)
    elif any(k in q for k in ('dasha','mahadasha','antardasha','pratyantar','sookshma','sukshma','prana')):
        answers=_dasha_answer(chart,i,q)
    elif any(k in q for k in ('nakshatra','pada')):
        answers=_nakshatra_answer(chart,i)
    elif any(k in q for k in ('transit','jupiter','saturn','rahu','ketu')):
        answers=_transit_answer(i,q)
    elif any(k in q for k in ('gemstone','gem','stone','ruby','emerald','sapphire','coral','pearl','hessonite','cat\'s eye')):
        answers=[f"{x.get('gemstone')} for {x.get('planet')}: {x.get('reason')}" for x in i.get('gemstone_recommendations',[])[:6]]
    elif any(k in q for k in ('sister','brother','sibling','siblings')):
        # Sibling topics are assessed from the natal chart and D3 when available;
        # do not infer a relative's literal fate from the native's chart alone.
        answer=[]
        for div in ('D3','Drekkana'):
            answer += [x.get('text','') for x in i.get('divisional',[]) if x.get('division')==div]
        answer += [x.get('text','') for x in i.get('integrated_factor_interpretations',[]) if any(k in str(x).lower() for k in ('third house','sibling','mars','communication'))][:4]
        answer.append('This is an indirect indication through your chart, not a substitute for your sister’s or brother’s own chart and current circumstances. Stronger timing claims require D3, the 3rd/11th-house factors, relevant Dasha and transits to agree.')
    elif any(k in q for k in ('court','lawsuit','litigation','legal case','legal dispute','judge','custody')):
        answer=[]
        answer += [x.get('text','') for x in i.get('divisional',[]) if x.get('division') in ('D6','D30')]
        answer += [x.get('text','') for x in i.get('integrated_factor_interpretations',[]) if any(k in str(x).lower() for k in ('sixth house','eighth house','twelfth house','saturn','mars','legal','dispute'))][:5]
        answer += [f"{x.get('date')}: activation {x.get('score')}; Dasha {x.get('dasha')}." for x in narrative.get('timing_windows',[])[:4]]
        answer.append('Court outcomes cannot be determined from a single factor. Read the 6th, 8th, 9th and 12th houses, their lords, Dasha sequence and relevant Vargas together; treat this as a symbolic timing assessment, not legal advice.')
    elif any(k in q for k in ('d9','navamsa','marriage','wife','husband','relationship','partner')):
        d9=[x for x in i.get('divisional',[]) if x.get('division')=='D9']
        answers=[x.get('text','') for x in d9]
        if any(k in q for k in ('marriage','timing','when')):
            answers += [f"{x.get('date')}: activation {x.get('score')} — Dasha {x.get('dasha','')}" for x in narrative.get('marriage_timing',{}).get('windows',[])[:5]]
    elif any(k in q for k in ('career','profession','job','work')):
        answers=[f"{x.get('option')}: {x.get('reason')}" for x in narrative.get('career_options',[])[:6]]
        if any(k in q for k in ('change','switch','when','timing')):
            answers += [f"{x.get('date')}: activation {x.get('score')}; Dasha {x.get('dasha')}" for x in narrative.get('job_change_timing',{}).get('windows',[])[:5]]
        if 'd10' in q or 'dashamsha' in q:
            answers += [x.get('text','') for x in i.get('divisional',[]) if x.get('division')=='D10']
    elif 'business' in q or 'entrepreneur' in q:
        answers=[f"{x.get('date')}: activation {x.get('score')}; Dasha {x.get('dasha')}" for x in narrative.get('business_timing',{}).get('windows',[])[:7]]
        if 'd10' in q or 'dashamsha' in q:
            answers += [x.get('text','') for x in i.get('divisional',[]) if x.get('division')=='D10']
    elif any(k in q for k in ('week','weekly')):
        answers=[x.get('interpretation','') for x in narrative.get('forecast_interpretations',{}).get('weekly',[])[:8]]
    elif any(k in q for k in ('month','monthly')):
        answers=[x.get('interpretation','') for x in narrative.get('forecast_interpretations',{}).get('monthly',[])[:8]]
    elif any(k in q for k in ('year','yearly','annual')):
        answers=[x.get('interpretation','') for x in narrative.get('forecast_interpretations',{}).get('yearly',[])[:6]]
    else:
        answers=list(i.get('executive',[])[:2]) + [x.get('interpretation','') for x in i.get('integrated_factor_interpretations',[])[:4]]
    answers=_unique_chat(answers, 18)
    if not answers:
        answers=['No matching interpretation was found for that question in the generated chart data. Try asking about a specific Dasha, Varga, Yoga, Dosha, Nakshatra/Pada, transit, career, marriage, business or gemstone.']
    return '\n\n'.join(answers)

def build_interpretation_library(chart):
    planets=chart.get("planets",{})
    lagna=chart.get("lagna_sign","Unknown")
    out={"version":"0.9.8 interpretation library"}
    out["executive"]=[
        f"The ascendant is {lagna}. In traditional Jyotish, the ascendant is the primary framework for reading identity, vitality and the sequence of houses.",
        f"The Moon is in {planets.get('Moon',{}).get('sign','Unknown')}, placing mind and habit patterns within that sign's symbolic qualities.",
        f"The Sun is in {planets.get('Sun',{}).get('sign','Unknown')} in house {planets.get('Sun',{}).get('house','—')}, linking purpose and visibility to that life area.",
    ]
    out["lagna"]=[f"{s} rising is traditionally associated with {_SIGN_INTERP[s]}." for s in _SIGN_INTERP]
    out["planetary"]=[]
    for p,d in planets.items():
        h=int(d.get('house') or 1); sign=d.get('sign','Unknown'); dignity=d.get('dignity','Neutral')
        motion='retrograde' if d.get('retrograde') else 'direct'
        combust='combust' if d.get('combust') else 'not combust'
        out["planetary"].append({"planet":p,"sign":sign,"house":h,"text":_planet_house_sentence(p,h,sign,dignity,motion,combust),"motion":motion,"combust":combust})
    out["house_themes"]=[]
    for h in range(1,13):
        occ=[p for p,d in planets.items() if d.get('house')==h]
        sign=(chart.get('lagna_sign_index',0)+h-1)%12
        lord={0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}[sign]
        out["house_themes"].append({"house":h,"sign":list(_SIGN_INTERP)[sign],"lord":lord,"occupants":occ,"text":f"House {h} covers {_HOUSE_INTERP[h]}. Its sign is {list(_SIGN_INTERP)[sign]}, so {_SIGN_INTERP[list(_SIGN_INTERP)[sign]]}. Its traditional lord is {lord}." + (f" Occupants: {', '.join(occ)}." if occ else " No natal graha occupies this whole-sign house." )})
    out["planet_sign_matrix"]=[]
    for p,d in planets.items():
        sign=d.get('sign','Unknown')
        out["planet_sign_matrix"].append({"planet":p,"sign":sign,"text":f"{p} in {sign}: {_PLANET_INTERP[p]} are expressed through {_SIGN_INTERP.get(sign,'the sign symbolism')}."})
    out["nakshatra"]=[]
    for p,d in planets.items():
        n=d.get('nakshatra',{}); name=n.get('name','Unknown')
        out["nakshatra"].append({"planet":p,"name":name,"pada":n.get('pada'),'text':f"{p} in {name}, pada {n.get('pada','—')}: {_NAKSHATRA_INTERP.get(name,'traditional nakshatra themes are read through deity, shakti, lord and pada')}. The Vimshottari lord is {n.get('vimshottari_lord','—')}."})
    out["dignity"]=[{"planet":p,"dignity":d.get('dignity','Neutral'),"text":f"{p}: {d.get('dignity','Neutral')}. {_DIGNITY_GUIDANCE.get(d.get('dignity','Neutral'),'')}"} for p,d in planets.items()]
    # Generate a compact but large reference corpus: 9 planets x 12 houses + 9 planets x 12 signs + 27 nakshatras + 12 house themes.
    out["reference_corpus"]={
        "planet_house_rules":[{"planet":p,"house":h,"text":_planet_house_sentence(p,h,list(_SIGN_INTERP)[(chart.get('lagna_sign_index',0)+h-1)%12],"Neutral")} for p in _PLANET_INTERP for h in range(1,13)],
        "planet_sign_rules":[{"planet":p,"sign":s,"text":f"{p} in {s}: {_PLANET_INTERP[p]} are interpreted through {_SIGN_INTERP[s]}."} for p in _PLANET_INTERP for s in _SIGN_INTERP],
        "nakshatra_rules":[{"name":n,"text":f"{n}: {_NAKSHATRA_INTERP[n]}."} for n in _NAKSHATRA_INTERP],
        "house_rules":[{"house":h,"text":f"House {h}: {_HOUSE_INTERP[h]}."} for h in range(1,13)],
    }
    out["count"] = sum(len(v) for v in out["reference_corpus"].values()) + len(out["planetary"])+len(out["nakshatra"])
    return out


def flatten_report(chart: Dict[str, Any], narrative: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"JYOTISH LAB — PERSONALIZED ASTROLOGICAL REPORT")
    lines.append(f"Name: {chart['meta'].get('name', '') or 'Native'}")
    lines.append(f"Birth: {chart['meta']['birth_local']} | {chart['meta']['place']} | {chart['meta']['timezone']}")
    lines.append("")
    lines.append("EXECUTIVE INTERPRETATION")
    lines.extend([f"• {x}" for x in narrative["personality"][:6]])
    for key in ("finances", "family", "marriage", "career", "wellness", "spiritual"):
        lines.append("")
        lines.append(key.upper())
        for note in narrative[key]["notes"]:
            lines.append(f"• {note}")
    lines.append("")
    lines.append("YOGAS")
    for y in chart.get("yogas", []):
        lines.append(f"• {y['name']}: {y['basis']} | strength: {y['strength']}")
    lines.append("")
    lines.append("DOSHA SCREENS")
    for d in chart.get("doshas", []):
        lines.append(f"• {d['name']}: {d['status']} | severity: {d['severity']} | {d['basis']}")
    lines.append("")
    lines.append("FIVE-YEAR WINDOWS")
    for w in narrative.get("timing", [])[:40]:
        lines.append(f"• {w['start']} — dasha {w['dasha']} — {w['trigger']} — {w['confidence']}")
    lines.append("")
    lines.append("METHOD / LIMITATIONS")
    lines.append(narrative["opening"])
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# 0.7.8 expanded runtime interpretation system
# ---------------------------------------------------------------------------
import json as _json
from pathlib import Path as _Path

_CORPUS_PATH = _Path(__file__).resolve().parent.parent / 'data' / 'interpretation_corpus.json'
try:
    _RUNTIME_CORPUS = _json.loads(_CORPUS_PATH.read_text(encoding='utf-8')).get('entries', [])
    _CORPUS_INDEX = {}
    _CORPUS_PREFIX_INDEX = {}
    _CORPUS_COUNTS_BY_TYPE = {}
    for _entry in _RUNTIME_CORPUS:
        _kind, _key = _entry.get('type'), _entry.get('key')
        _CORPUS_INDEX.setdefault((_kind, _key), []).append(_entry)
        if isinstance(_key, str) and '|v' in _key:
            _base_key = _key.split('|v', 1)[0]
            _CORPUS_PREFIX_INDEX.setdefault((_kind, _base_key), []).append(_entry)
        _CORPUS_COUNTS_BY_TYPE[_kind] = _CORPUS_COUNTS_BY_TYPE.get(_kind, 0) + 1
except Exception:
    _RUNTIME_CORPUS = []
    _CORPUS_INDEX = {}
    _CORPUS_PREFIX_INDEX = {}
    _CORPUS_COUNTS_BY_TYPE = {}

_VARGA_PURPOSES = {
    'D1': 'overall life pattern, identity, vitality, houses and the main promise of the horoscope',
    'D2': 'wealth management, food, resources and material support',
    'D3': 'siblings, courage, skills, initiative and effort',
    'D4': 'property, home, fixed assets and inner security',
    'D7': 'children, creativity, lineage and nurturing',
    'D9': 'marriage, dharma, maturity and the deeper strength of planets',
    'D10': 'career, profession, authority, reputation and visible contribution',
    'D12': 'parents, ancestry and inherited family patterns',
    'D16': 'vehicles, comforts, luxuries and mobility',
    'D20': 'spiritual practice, devotion, mantra and inner discipline',
    'D24': 'education, scholarship, learning and mastery',
    'D27': 'resilience, strengths, weaknesses and subtle capacity',
    'D30': 'difficulties, vulnerabilities, conflict and corrective discipline',
    'D40': 'subtle inherited auspicious/inauspicious patterns',
    'D45': 'character, conduct, lineage and deeper dharmic qualities',
    'D60': 'fine-grained karmic patterning and subtle natal influences',
}

_PADA_TONE = {
    1: 'initiative and direct expression',
    2: 'stability, cultivation and practical development',
    3: 'communication, networking and mental movement',
    4: 'emotional depth, consolidation and inward integration',
}


_VIRTUAL_LENSES = [
    'Manifestation: the theme becomes visible through concrete decisions in this life area.',
    'Motivation: the result is shaped by what the person repeatedly tries to develop or understand here.',
    'Behavior: this combination describes the preferred way of approaching the house matters.',
    'Development: maturity comes from learning to use the planet well without overextending its difficult side.',
    'Timing: the theme becomes louder when the planet, its lord, dispositor or connected house is activated.',
    'Relationship effect: other people can become an important channel through which the placement manifests.',
    'Resource effect: the placement can influence how effort, money, time or attention are allocated.',
    'Decision effect: choices involving this house are colored by the planet and its sign.',
    'Visibility: the result becomes easier to notice when the planet is angular or strongly activated.',
    'Repetition: similar themes can recur until the underlying house matter is handled with greater skill.',
    'Strength: dignity, benefic support and constructive aspects can make the expression more available.',
    'Pressure: affliction, combustion or difficult lordship can make the same theme require more conscious management.',
    'Integration: the strongest reading combines this factor with the Moon, Lagna and relevant Vargas.',
    'House lord: the houses ruled by the planet provide additional channels for the result.',
    'Dispositor: the sign lord supplies a second layer of interpretation.',
    'Nakshatra: the Nakshatra lord adds a more specific motivational layer.',
    'Pada: the Pada refines the style in which the planet expresses its promise.',
    'Dasha: the Mahadasha makes the broad theme active while sub-periods specify its expression.',
    'Antardasha: a connected Antardasha can turn potential into a more concrete lived theme.',
    'Pratyantar: the Pratyantar narrows the timing toward shorter periods of heightened activity.',
    'Sookshma: the Sookshma layer concentrates the theme inside an already active sequence.',
    'Prana: the Prana layer provides the finest timing refinement in this hierarchy.',
    'Transit: a slow transit can bring the natal promise into a more visible period of activity.',
    'Jupiter transit: Jupiter expands the matters represented by the contacted factor.',
    'Saturn transit: Saturn structures, tests and consolidates the contacted matters.',
    'Rahu transit: Rahu can increase novelty, experimentation and unconventional developments.',
    'Ketu transit: Ketu can reduce attachment while increasing specialization or inward focus.',
    'Transit Nakshatra: the transit Nakshatra adds a qualitative tone to the timing.',
    'Transit Pada: the transit Pada gives a narrower stylistic refinement to the transit.',
    'Career lens: a connection with the 10th house or D10 can alter professional direction or visibility.',
    'Wealth lens: a connection with the 2nd or 11th can affect resources, gains and accumulation.',
    'Relationship lens: a connection with the 7th or D9 can influence partnership dynamics.',
    'Learning lens: a connection with the 5th or 9th can shape education, teaching and intellectual growth.',
    'Family lens: a connection with the 2nd or 4th can make family responsibilities more prominent.',
    'Home lens: a connection with the 4th can emphasize residence, property and emotional foundations.',
    'Creativity lens: a connection with the 5th can emphasize creative output, children or calculated risk.',
    'Service lens: a connection with the 6th can emphasize work routines, competition and problem-solving.',
    'Transformation lens: a connection with the 8th can emphasize research, shared resources and major transitions.',
    'Dharma lens: a connection with the 9th can emphasize teachers, travel, principles and worldview.',
    'Gains lens: a connection with the 11th can emphasize networks, income and long-term aims.',
    'Release lens: a connection with the 12th can emphasize closure, retreat, foreign environments or expenses.',
    'Action: the most useful expression is to convert the symbolic theme into an observable habit.',
    'Opportunity: constructive circumstances can appear when timing supports the natal promise.',
    'Challenge: the difficult side becomes more visible when the planet is weak and heavily afflicted.',
    'Consolidation: results improve when repeatable systems are built around the house matter.',
    'Choice: the placement describes themes; circumstances and decisions shape their concrete expression.',
    'Sequence: the result should be read as part of a chain rather than as an isolated placement.',
    'Synthesis: combine sign, house, lordship, dignity, Nakshatra, Dasha and transit before timing a result.',
    'Specificity: agreement among several layers makes the corresponding life area more prominent.',
    'Balance: use the planet’s natural qualities without allowing one theme to dominate the whole chart.',
    'Cycle: the theme can return in different forms as dasha and transit cycles repeat.',
    'Threshold: major changes become more noticeable when several timing layers converge.',
    'Context: the same planet can behave differently depending on lordship and dispositor.',
    'Evidence: this reading is tied to the supplied chart factors rather than a generic sign statement.',
    'Priority: simultaneous activation in D1 and the relevant Varga deserves closer attention.',
    'Resolution: Nakshatra, Pada and sub-period make a broad placement more specific.',
    'Practical reading: translate the symbolism into the connected career, relationship, financial or learning domain.',
    'Long view: Saturnian and 9th/10th/11th-house connections can matter across several years.',
    'Short view: Moon, Mars, Mercury and sub-period activation can make a theme noticeable sooner.',
]
_VIRTUAL_VARIANTS_PER_RULE=720

# Additional depth lenses: these are interpretive dimensions, not new chart facts.
# They only become meaningful when the referenced chart factor actually exists.
_DEPTH_AXES = {
    'Life expression': ['how the factor is likely to be experienced in daily life', 'how the factor can shape recurring choices', 'how the factor can alter priorities'],
    'Strength expression': ['how dignity and support can make the theme easier to access', 'how supportive placements can stabilize the theme', 'how the same promise can become more reliable with maturity'],
    'Challenge expression': ['where overextension of the planet can create friction', 'where the same symbolism can become excessive', 'where conscious pacing can reduce unnecessary friction'],
    'Timing expression': ['what becomes more visible when the planet is activated', 'how sub-periods can narrow the life area being emphasized', 'how slow transits can make a natal promise more concrete'],
    'Integration': ['how the placement should be read with its dispositor', 'how the placement changes when read with the Moon', 'how the placement changes when confirmed by the relevant Varga'],
    'Domain translation': ['career and contribution', 'relationships and agreements', 'money and resource management', 'learning and skill development', 'family and home', 'inner development and meaning'],
    'Sequence': ['the broad theme established by the Mahadasha', 'the concrete expression selected by the Antardasha', 'the shorter trigger represented by the Pratyantar', 'the fine timing represented by Sookshma and Prana'],
    'Transit synthesis': ['Jupiter can broaden the activated matter', 'Saturn can structure or test the activated matter', 'Rahu can intensify novelty around the activated matter', 'Ketu can simplify or detach from the activated matter'],
    'Varga synthesis': ['D1 shows the foundational life area', 'the relevant Varga shows the specialized field', 'D9 can refine maturity and planetary strength', 'D10 can refine professional expression'],
    'Practical translation': ['what to watch for when the factor is activated', 'what type of decision the period foregrounds', 'what kind of effort can make constructive use of the period'],
}

_EXTRA_DEPTH_LENSES=[]
for axis, phrases in _DEPTH_AXES.items():
    for phrase in phrases:
        _EXTRA_DEPTH_LENSES.append(f'{axis}: {phrase}.')
# Expand deterministically with cross-domain combinations until the variant pool is doubled.
for axis, phrases in _DEPTH_AXES.items():
    for other_axis, other_phrases in _DEPTH_AXES.items():
        if axis == other_axis:
            continue
        for phrase in phrases:
            for other in other_phrases[:2]:
                _EXTRA_DEPTH_LENSES.append(f'{axis} + {other_axis}: {phrase}; {other}.')
                if len(_EXTRA_DEPTH_LENSES) >= 180:
                    break
            if len(_EXTRA_DEPTH_LENSES) >= 180:
                break
        if len(_EXTRA_DEPTH_LENSES) >= 180:
            break
    if len(_EXTRA_DEPTH_LENSES) >= 180:
        break
# Only unique lenses are retained.
_EXTRA_DEPTH_LENSES=list(dict.fromkeys(_EXTRA_DEPTH_LENSES))
_VIRTUAL_LENSES=list(dict.fromkeys(_VIRTUAL_LENSES + _EXTRA_DEPTH_LENSES))

def _corpus_find(kind, key, variants=2):
    """Return stable physical corpus variants for a rule."""
    import hashlib
    matches=_CORPUS_INDEX.get((kind,key), [])
    if not matches:
        matches=_CORPUS_PREFIX_INDEX.get((kind,key), [])
    if not matches: return ''
    seed=int(hashlib.sha256(f'{kind}|{key}'.encode()).hexdigest()[:8],16)
    take=max(1,min(int(variants or 1),len(matches)))
    chosen=[matches[(seed+i)%len(matches)].get('text','').strip() for i in range(take)]
    if take < variants and _VIRTUAL_LENSES:
        chosen.append(_VIRTUAL_LENSES[seed % len(_VIRTUAL_LENSES)])
    return ' '.join(dict.fromkeys(x for x in chosen if x))


_COMBINATION_RULES={
 ('Sun','Saturn'):'authority meets restriction: status, leadership and institutional responsibility rise together; the result is pressure to prove competence and carry consequences.',
 ('Sun','Jupiter'):'authority meets expansion: leadership, recognition, education, counsel and influence reinforce each other.',
 ('Sun','Mars'):'authority meets force: initiative, competition, command and decisive action dominate the period.',
 ('Sun','Rahu'):'authority meets amplification: visibility, ambition, foreign and unconventional themes intensify.',
 ('Moon','Saturn'):'mind meets duty: emotional burdens, family responsibility, delays and disciplined routines become central.',
 ('Moon','Mars'):'mind meets action: rapid reactions, property or family activity, initiative and conflict resolution become prominent.',
 ('Moon','Jupiter'):'mind meets expansion: learning, family support, counsel, optimism and opportunity become prominent.',
 ('Moon','Rahu'):'mind meets amplification: restlessness, unusual desires and abrupt changes in emotional priorities intensify.',
 ('Mars','Saturn'):'force meets resistance: sustained effort, engineering, conflict, delays and restructuring become unavoidable work.',
 ('Mars','Jupiter'):'action meets expansion: enterprise, education and strategic execution reinforce each other.',
 ('Mars','Venus'):'drive meets attraction: relationships, money, creativity and negotiation become tightly linked.',
 ('Mercury','Jupiter'):'analysis meets wisdom: study, writing, teaching, commerce, law and strategy become linked.',
 ('Mercury','Saturn'):'analysis meets structure: documentation, contracts, technical work, compliance and methodical planning dominate.',
 ('Mercury','Rahu'):'analysis meets amplification: technology, media, unconventional information and rapid narrative shifts intensify.',
 ('Jupiter','Saturn'):'expansion meets consolidation: growth is forced through structure, accountability and long-term planning.',
 ('Jupiter','Rahu'):'expansion meets appetite: large ambitions, foreign links and unconventional beliefs intensify.',
 ('Venus','Saturn'):'relationships meet duty: commitments, contracts and financial discipline become prominent.',
 ('Venus','Rahu'):'relationships meet amplification: attraction, luxury, media, foreign links and financial appetite intensify.',
 ('Saturn','Rahu'):'restriction meets amplification: institutional pressure, restructuring, technology and unconventional solutions intensify.',
 ('Saturn','Ketu'):'structure meets detachment: endings, simplification, institutional pruning and withdrawal become prominent.',
 ('Rahu','Ketu'):'the nodal axis dominates: polarization, abrupt shifts, release, obsession and redirection become the defining themes.',
}

def _combination_interpretations(chart):
    planets=chart.get('planets',{}) or {}
    active=_dasha_context(chart).get('current_hierarchy') or []
    active_lords={x.get('lord') for x in active}
    rows=[]; names=list(planets)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            rule=_COMBINATION_RULES.get(tuple(sorted((a,b))))
            if not rule: continue
            pa,pb=planets[a],planets[b]
            active_now=bool(active_lords & {a,b})
            relation='conjunction by sign' if pa.get('sign')==pb.get('sign') else 'cross-planet combination'
            rows.append({'planets':[a,b],'relation':relation,'houses':sorted({pa.get('house'),pb.get('house')}-{None}),'active_now':active_now,
                'interpretation':f'{a} + {b}: {rule} Natal positions: {a} in {pa.get("sign")} house {pa.get("house")}; {b} in {pb.get("sign")} house {pb.get("house")}. '+
                ('This combination is active now because one of its planets is in the current Dasha chain.' if active_now else 'This combination is natal and becomes active when either planet is activated by Dasha or a material transit contact.')})
    return rows


def _dasha_chain_at(periods, when):
    chain=[]
    def walk(nodes, depth=1):
        for node in nodes or []:
            try:
                st=_datetime_from_iso(node['start']); en=_datetime_from_iso(node['end'])
            except Exception:
                continue
            if st <= when < en:
                chain.append({'level':depth,'lord':node.get('lord'),'start':node.get('start'),'end':node.get('end')})
                if node.get('children'):
                    walk(node['children'], depth+1)
                return True
        return False
    walk(periods,1)
    return chain


def _datetime_from_iso(value):
    from datetime import datetime as _dt
    return _dt.fromisoformat(value)


def _forecast_dates(chart, key):
    layers=chart.get('forecast_layers', {})
    rows=layers.get(key) or []
    if rows:
        return rows
    return chart.get('transits', [])


def _interpret_period_rows(chart, rows, period_name):
    out=[]
    planets=chart.get('planets', {})
    periods=chart.get('dashas',{}).get('periods',[])
    for r in rows:
        chain=_dasha_chain_at(periods, _datetime_from_iso(r['date']+'T00:00:00'+_tz_suffix(chart))) if r.get('date') else []
        dasha=' / '.join(x['lord'] for x in chain) if chain else '—'
        jh=r.get('jupiter_house'); sh=r.get('saturn_house'); rh=r.get('rahu_house'); kh=r.get('ketu_house')
        domain_scores={}
        for domain, weights in DOMAIN_HOUSE_WEIGHTS_LOCAL.items():
            score=50.0
            for h,w in weights.items():
                if jh==h: score += 18*w
                if sh==h: score += 12*w
                if rh==h: score += 5*w
                if kh==h: score += 4*w
                if chain and chain[0]['lord'] in planets and planets[chain[0]['lord']].get('house')==h: score += 10*w
            domain_scores[domain]=round(max(0,min(100,score)),1)
        top=sorted(domain_scores.items(),key=lambda x:x[1],reverse=True)[:3]
        labels=[d.replace('_',' ').title() for d,_ in top]
        focus=', '.join(labels)
        lead=chain[0]['lord'] if chain else 'the current timing layer'
        interpretation=(f'{period_name.title()} {r["date"]}: {focus} receives the strongest symbolic activation in this period. '
                       f'The active Vimshottari chain is {dasha or "not available"}. Jupiter is activating house {jh}, '
                       f'Saturn house {sh}, with the nodal axis across houses {rh} and {kh}. '
                       f'Use the {lead} significations together with the relevant houses when reading this period.')
        deep_rules=[]
        if len(chain)>=3:
            key=f"{chain[0]['lord']}|{chain[1]['lord']}|{chain[2]['lord']}"
            txt=_corpus_direct('dasha_triple',key)
            if txt: deep_rules.append(txt)
        for dom,_score in top:
            key=f"{dom}|{chain[0]['lord'] if chain else lead}|{jh or 1}|dasha_transit_overlap"
            txt=_corpus_direct('prediction_domain_timing',key)
            if txt: deep_rules.append(txt)
            vkey={'career':'D10','job_change':'D10','business':'D10','marriage':'D9','finances':'D2','learning':'D24','family':'D12'}.get(dom)
            if vkey:
                txt=_corpus_direct('domain_varga_confirmation',f"{dom}|{chain[0]['lord'] if chain else lead}|{jh or 1}|{vkey}")
                if txt: deep_rules.append(txt)
        unique_deep=list(dict.fromkeys(deep_rules))[:8]
        out.append({'date':r['date'],'period':period_name,'dasha':dasha,'scores':domain_scores,'focus':labels,'interpretation':interpretation,'deep_rules':unique_deep,
                    'interpretation_depth':{
                        'summary':f"{period_name.title()} {r['date']}: strongest focus is {focus}; leading Dasha chain: {dasha or 'not available'}.",
                        'mechanism':f"Jupiter house {jh}, Saturn house {sh}, Rahu house {rh}, Ketu house {kh}; leading activation scores: {', '.join(f'{label} {score}/100' for label,score in top)}. These are deterministic Jyotish activation indices, not empirical probabilities.",
                        'cross_confirmation':(' '.join(unique_deep[:4]) if unique_deep else f"Cross-check the Dasha chain {dasha or 'not available'} against the relevant natal houses, divisional chart and applicable Yoga/Dosha timing before treating this window as a high-priority interpretation.")
                    }})
    return out


def _tz_suffix(chart):
    from datetime import datetime as _dt
    try:
        # Dasha dates already carry offsets; forecast dates do not. Use a fixed +00:00
        # comparison only when the period cannot be localized. This fallback is replaced
        # by a UTC-normalized comparison below where needed.
        return '+00:00'
    except Exception:
        return '+00:00'

# Local weights mirror the engine domain screen and include business/job-change layers.
DOMAIN_HOUSE_WEIGHTS_LOCAL={
    'career':{10:1.0,6:0.65,11:0.8,1:0.35},
    'job_change':{10:1.0,6:0.7,11:0.75,8:0.35,3:0.25},
    'business':{7:1.0,10:0.9,11:0.9,2:0.55,3:0.4},
    'marriage':{7:1.0,5:0.55,2:0.35,12:-0.25},
    'finances':{2:1.0,11:1.0,5:0.45,9:0.55,8:-0.35},
    'learning':{5:0.85,9:1.0,3:0.5,8:0.25},
    'family':{2:0.8,4:1.0,11:0.35,8:-0.2},
}


def _career_options(chart):
    p=chart.get('planets',{}); tenth=next((x for x in chart.get('houses',[]) if x.get('house')==10),{})
    tenth_sign=tenth.get('sign','')
    occupants=tenth.get('occupants',[])
    signals=[]
    def add(label, reason, score): signals.append({'option':label,'reason':reason,'score':score})
    merc_h=p.get('Mercury',{}).get('house'); jup_h=p.get('Jupiter',{}).get('house'); ven_h=p.get('Venus',{}).get('house'); mars_h=p.get('Mars',{}).get('house'); sat_h=p.get('Saturn',{}).get('house')
    d10=chart.get('divisional_charts',{}).get('D10',{})
    d10_house10=[pl for pl,d in d10.get('planets',{}).items() if d.get('house')==10]
    d10_lagna=d10.get('lagna_sign','')
    if tenth_sign in ('Gemini','Virgo') or merc_h in (2,3,6,10,11): add('Analytics, software, data, consulting or communications','Mercury and the 10th-house pattern emphasize analysis, communication and systems.',90)
    if tenth_sign in ('Sagittarius','Pisces') or jup_h in (2,5,9,10,11): add('Teaching, law, advisory, finance, policy or knowledge work','Jupiter-linked career factors emphasize learning, guidance, judgment and expansion.',88)
    if tenth_sign in ('Taurus','Libra') or ven_h in (2,5,7,10,11): add('Finance, design, luxury, media, client relations or negotiation','Venus-linked factors emphasize value, aesthetics, agreements and resources.',86)
    if mars_h in (3,6,10,11) or tenth_sign in ('Aries','Scorpio'): add('Engineering, operations, technology, entrepreneurship or competitive fields','Mars-linked factors emphasize execution, technical effort and decisive action.',87)
    if sat_h in (6,10,11) or tenth_sign in ('Capricorn','Aquarius'): add('Operations, management, infrastructure, compliance or large organizations','Saturn-linked factors emphasize structure, endurance, systems and responsibility.',89)
    if d10_house10: add('Career roles connected to D10 10th-house planets', 'The Dashamsha places '+', '.join(d10_house10)+' in its 10th house; this directly colors professional expression in the career division.',92)
    if d10_lagna in ('Gemini','Virgo','Aquarius'): add('Technology, analytics, communications and systems work','The Dashamsha Lagna emphasizes a mental, networked or systems-oriented professional style.',88)
    if d10_lagna in ('Taurus','Libra','Pisces'): add('Finance, design, client-facing, advisory or relationship-based work','The Dashamsha Lagna emphasizes value, agreement, aesthetics or guidance in professional expression.',86)
    if d10_lagna in ('Aries','Scorpio','Capricorn'): add('Operations, engineering, leadership and execution-heavy work','The Dashamsha Lagna emphasizes initiative, technical execution, structure and responsibility.',87)
    if occupants: add('Roles connected to '+', '.join(occupants),'Planetary occupancy of the 10th house directly colors professional expression.',84)
    if not signals: add('Structured professional work with a clear specialization','The chart is read through the 10th lord, D10 and active dasha rather than through a single job title.',75)
    unique={x['option']:x for x in signals}
    return sorted(unique.values(),key=lambda x:x['score'],reverse=True)[:8]


def _timing_windows_by_domain(chart, domain, count=12):
    layers=chart.get('forecast_layers',{})
    rows=layers.get('monthly') or chart.get('transits',[])
    periods=chart.get('dashas',{}).get('periods',[])
    out=[]
    for r in rows:
        scores={}
        chain=_dasha_chain_at(periods, _datetime_from_iso(r['date']+'T00:00:00+00:00')) if r.get('date') else []
        for d,weights in DOMAIN_HOUSE_WEIGHTS_LOCAL.items():
            score=50.0
            for h,w in weights.items():
                if r.get('jupiter_house')==h: score+=18*w
                if r.get('saturn_house')==h: score+=12*w
                if r.get('rahu_house')==h: score+=5*w
                if r.get('ketu_house')==h: score+=4*w
                if chain and chain[0]['lord'] in chart.get('planets',{}) and chart['planets'][chain[0]['lord']].get('house')==h: score+=10*w
            scores[d]=round(max(0,min(100,score)),1)
        score=scores.get(domain,50)
        if domain=='marriage':
            d9=chart.get('divisional_charts',{}).get('D9',{})
            d9_seventh=[pl for pl,d in d9.get('planets',{}).items() if d.get('house')==7]
            if d9_seventh: score=min(100,score+5)
        if domain in ('career','job_change','business'):
            d10=chart.get('divisional_charts',{}).get('D10',{})
            d10_tenth=[pl for pl,d in d10.get('planets',{}).items() if d.get('house')==10]
            if d10_tenth: score=min(100,score+5)
        out.append({'date':r['date'],'score':round(score,1),'dasha':' / '.join(x['lord'] for x in chain) or '—','transit_houses':{'jupiter':r.get('jupiter_house'),'saturn':r.get('saturn_house')}})
    return sorted(out,key=lambda x:x['score'],reverse=True)[:count]


def _divisional_interpretations(chart):
    out=[]
    house_theme={1:'identity and vitality',2:'wealth and resources',3:'skills and initiative',4:'home and foundations',5:'creativity and children',6:'service and competition',7:'partnerships and public dealings',8:'transformation and shared resources',9:'dharma and higher learning',10:'career and public contribution',11:'gains and networks',12:'retreat, expenses and foreign environments'}
    for key,v in chart.get('divisional_charts',{}).items():
        purpose=_VARGA_PURPOSES.get(key, v.get('name','divisional chart'))
        lagna=v.get('lagna_sign','—')
        placements=[]
        for p,d in v.get('planets',{}).items():
            h=int(d.get('house') or 0); sg=d.get('sign','—')
            if h in (1,4,5,7,9,10,11) or p in ('Sun','Moon','Jupiter','Venus','Saturn'):
                placements.append((p,d))
        clauses=[]
        for p,d in placements[:7]:
            h=int(d.get('house') or 0); sg=d.get('sign','—')
            role=PLANET_THEMES.get(p,p)
            clauses.append(f'{p} in {sg}, house {h}, directs {role} into {house_theme.get(h,"the relevant life area")}')
        focus='; '.join(clauses) if clauses else 'the division has a distributed planetary pattern without a single dominant angular concentration'
        # Turn the Varga purpose into a direct reading rather than a generic instruction.
        if key=='D9': lead='Relationship choices, marriage patterns, dharma and the mature expression of the planets are emphasized.'
        elif key=='D10': lead='Professional direction, authority, reputation and the way work becomes visible are emphasized.'
        elif key=='D2': lead='Resource handling, earning style, savings and the material support structure receive the strongest attention.'
        elif key=='D7': lead='Children, creativity, continuity and nurturing expression are emphasized.'
        elif key=='D24': lead='Education, scholarship, learning style and mastery develop through the strongest placements in this division.'
        elif key=='D20': lead='Devotion, spiritual practice, mantra and inner discipline are emphasized by the occupied houses and planets.'
        elif key=='D12': lead='Parental, ancestral and inherited family themes are highlighted by the D12 pattern.'
        elif key=='D4': lead='Home, property, fixed assets and emotional foundations are colored by the D4 placements.'
        else: lead=f'The main {purpose} themes are carried by the Dasha-sensitive placements in this division.'
        text=(f'{key} {v.get("name","")} has {lagna} rising and concentrates on {purpose}. {lead} '
              f'In this chart, {focus}. The strongest result comes when a planet shown here is also active by Dasha or connected to a relevant transit; then the corresponding {key} theme becomes more concrete in lived circumstances.')
        out.append({'division':key,'name':v.get('name'), 'lagna':lagna,'purpose':purpose,'text':' '.join(text.split()),'planets':v.get('planets',{})})
    return out


def _pada_interpretations(chart):
    out=[]
    for p,d in chart.get('planets',{}).items():
        n=d.get('nakshatra',{}); name=n.get('name'); pada=n.get('pada')
        if not name or not pada: continue
        base=_corpus_find('nakshatra_pada',f'{name}|{pada}')
        out.append({'planet':p,'nakshatra':name,'pada':pada,'text':f'{p}: {base} The pada tone is {_PADA_TONE.get(int(pada),"specific refinement")}. Because this is {p} in this pada, apply the result to {PLANET_THEMES.get(p,p)}.'})
    return out


def _active_dasha_analysis(chart):
    start=chart.get('forecast',{}).get('start'); end=chart.get('forecast',{}).get('end')
    if not start or not end: return []
    from datetime import datetime as _dt
    st=_dt.fromisoformat(start+'T00:00:00+00:00'); en=_dt.fromisoformat(end+'T23:59:59+00:00')
    out=[]
    def walk(nodes,depth=1):
        for n in nodes or []:
            ns=_dt.fromisoformat(n['start']).astimezone(st.tzinfo); ne=_dt.fromisoformat(n['end']).astimezone(st.tzinfo)
            if ne<st or ns>en: continue
            item={'level':depth,'level_name':{1:'Mahadasha',2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'}.get(depth,f'Level {depth}'),'lord':n['lord'],'start':n['start'],'end':n['end']}
            out.append(item)
            if depth<5: walk(n.get('children',[]),depth+1)
    walk(chart.get('dashas',{}).get('periods',[]))
    return out


def _applicable_doshas(chart):
    return [d for d in chart.get('doshas',[]) if d.get('status') in ('screen-positive','present','possible')]



DASHA_THEMES={
 'Sun':'identity, authority, visibility, leadership, father/mentor themes and decisive life direction',
 'Moon':'mind, habits, emotional security, home, family, nourishment and changing priorities',
 'Mars':'initiative, competition, courage, technical action, property, conflict resolution and physical drive',
 'Mercury':'learning, communication, analysis, commerce, contracts, technology, networking and adaptability',
 'Jupiter':'education, mentors, wisdom, expansion, finances, children, ethics, travel and opportunity',
 'Venus':'relationships, marriage, comfort, art, negotiation, vehicles, luxury and material enjoyment',
 'Saturn':'work, responsibility, discipline, delays, institutions, endurance, restructuring and long-term achievement',
 'Rahu':'unconventional ambition, foreign links, technology, appetite, experimentation and sudden shifts in priorities',
 'Ketu':'detachment, specialization, research, spiritual inquiry, simplification and completion of old patterns',
}
DOSHA_THEMES={
 'Manglik / Kuja Dosha':'Mars brings a sharper, more active tone to the houses it influences. In relationship analysis this can increase the need for direct communication, patience and constructive handling of conflict.',
 'Kala Sarpa Yoga / Dosha':'A concentrated nodal axis can make periods of life feel strongly polarized, with themes of urgency, fixation, release and major directional shifts becoming more noticeable.',
 'Grahan Dosha':'Node-Sun/Moon contact can make identity or emotional themes more intense, unusual or periodically obscured; the exact house and degree relationship determines where the emphasis appears.',
 'Guru Chandal Dosha':'Jupiter-node contact can make learning, belief, ethics, teachers and judgment more unconventional; the placement can produce independent thinking but also requires careful discrimination.',
 'Shrapit Dosha':'Saturn-node contact can combine pressure, persistence and unconventional circumstances, often pushing the person to rebuild structures rather than relying on established patterns.',
 'Ganda Moola Dosha':'Moon in a traditionally classified Ganda Moola Nakshatra emphasizes transitions, sensitivity to change and the need to establish stable rhythms around the Moon’s house and lordship.',
 'Kalathra Dosha screen':'Node-Venus contact can make relationship and agreement themes more unconventional or intense, requiring clarity around expectations and attachment.',
 'Vish / Punarphoo Dosha screen':'Saturn-Moon contact can bring a serious or delayed tone to emotional matters, increasing the importance of maturity, patience and stable routines.',
 'Kemadruma Dosha screen':'Reduced planetary support around the Moon can make self-generated emotional stability especially important; cancellation factors and the Moon’s dignity materially modify the reading.',
 'Papakartari Dosha screen':'Malefic enclosure concentrates pressure around the affected house or Lagna, often making discipline and deliberate choices more important until supportive factors activate.',
 'Gandanta screen':'A planet near a water-fire junction can mark a sensitive transition between modes of expression; the relevant house and dasha show where this becomes visible.',
 'Graha Yuddha screen':'Close planetary longitude can make the significations of the involved planets compete for expression, making their house lordships and dignity especially important.',
}

def _dasha_significance(chart, lord, level, start=None, end=None):
    p=chart.get('planets',{}).get(lord,{})
    h=p.get('house'); sign=p.get('sign'); n=p.get('nakshatra',{}) or {}
    house_theme=HOUSE_THEMES.get(int(h),'the occupied life area') if h else 'the relevant life area'
    level_phrase={1:'sets the broad life chapter',2:'selects the concrete area within that chapter',3:'narrows the active storyline',4:'concentrates the theme into a short phase',5:'acts as the finest timing layer'}.get(level,'refines timing')
    if not p: return f'{lord} {level_phrase}; the planet data is not available.'
    text=(f'{lord} {"Mahadasha" if level==1 else "Antardasha" if level==2 else "Pratyantar Dasha" if level==3 else "Sookshma Dasha" if level==4 else "Prana Dasha"} {level_phrase}. '
          f'Natal {lord} is in {sign}, house {h}, {n.get("name","—")} pada {n.get("pada","—")}. Its principal life themes are {DASHA_THEMES.get(lord,PLANET_THEMES.get(lord,lord))}. '
          f'Because it occupies house {h}, the period repeatedly activates {house_theme}; its sign and Nakshatra modify how those matters are pursued. '
          f'The period can change priorities, decisions and circumstances around these themes according to the other active dasha levels and transit support.')
    return {'lord':lord,'level':level,'level_name':{1:'Mahadasha',2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'}.get(level,'Dasha'),'start':start,'end':end,'text':text}

def _dasha_interpretations(chart):
    out=[]
    now=_datetime_from_iso(chart.get('current_transits',{}).get('datetime')) if chart.get('current_transits',{}).get('datetime') else datetime.now()
    # all periods intersecting the forecast plus the active chain, deduplicated
    seen=set()
    def walk(nodes,depth=1):
        for n in nodes or []:
            try: st=_datetime_from_iso(n['start']); en=_datetime_from_iso(n['end'])
            except Exception: continue
            if en < now and depth>1: continue
            if depth==1 or (st <= now <= en) or (en >= now and depth<=3):
                key=(depth,n.get('lord'),n.get('start'))
                if key not in seen:
                    seen.add(key); out.append(_dasha_significance(chart,n.get('lord'),depth,n.get('start'),n.get('end')))
            if depth<5 and (st <= now <= en): walk(n.get('children',[]),depth+1)
    walk(chart.get('dashas',{}).get('periods',[]),1)
    # add past/current/future Mahadashas explicitly
    timeline=chart.get('dashas',{}).get('mahadasha_timeline',[])
    for n in timeline:
        try: st=_datetime_from_iso(n['start']); en=_datetime_from_iso(n['end'])
        except Exception: continue
        if en >= now and len([x for x in out if x['level']==1])>=8: break
        if (1,n.get('lord'),n.get('start')) not in seen:
            out.append(_dasha_significance(chart,n.get('lord'),1,n.get('start'),n.get('end')))
            seen.add((1,n.get('lord'),n.get('start')))
    return out

def _dosha_interpretations(chart):
    out=[]
    for d in chart.get('doshas',[]):
        if d.get('status') not in ('screen-positive','present','possible'): continue
        name=d.get('name','')
        base=DOSHA_THEMES.get(name)
        if not base:
            base=DOSHA_THEMES.get(name.replace(' / Dosha','').replace(' screen','')+' screen')
        base=base or f'{name} is active in the chart according to the stated screening rule. Its effect is read through the affected planet, house, lordship, dignity and timing.'
        life=d.get('life_impact') or base
        impacts=[]
        for domain in ('relationship','career','money','family','health','education','spirituality','travel'):
            text=_corpus_direct('dosha_life_impact',f'{name}|{domain}')
            if text: impacts.append({'domain':domain,'text':text})
        direct=' '.join(x['text'] for x in impacts[:8])
        out.append({**d,'interpretation':f'{base} The specific chart basis is: {d.get("basis", "chart-specific condition detected")}. '+direct, 'life_impact':life, 'life_impact_by_domain':impacts})
    return out

def _gemstone_recommendations(chart):
    lagna=chart.get('lagna_sign_index',0); planets=chart.get('planets',{})
    house_lords={h:chart.get('houses',[{}])[h-1].get('lord') for h in range(1,13) if len(chart.get('houses',[]))>=h}
    candidates=[]
    for h,priority in ((1,100),(5,90),(9,95)):
        lord=house_lords.get(h); p=planets.get(lord,{})
        if not lord or not p: continue
        candidates.append((priority,lord,h,p))
    # Avoid recommending a stone simply because a planet is weak; prioritize benefic functional roles.
    stones={'Sun':('Ruby','Sun','identity, vitality and authority'), 'Moon':('Pearl','Moon','emotional steadiness and receptivity'), 'Mars':('Red Coral','Mars','initiative, courage and disciplined action'), 'Mercury':('Emerald','Mercury','learning, communication and analytical work'), 'Jupiter':('Yellow Sapphire','Jupiter','wisdom, teaching, expansion and guidance'), 'Venus':('Diamond / White Sapphire','Venus','relationships, aesthetics, negotiation and comfort'), 'Saturn':('Blue Sapphire','Saturn','discipline, structure and long-term responsibility'), 'Rahu':('Hessonite','Rahu','unconventional ambition and experimentation'), 'Ketu':("Cat's Eye",'Ketu','specialization, detachment and inward focus')}
    out=[]; used=set()
    for priority,lord,h,p in sorted(candidates,reverse=True):
        if lord in used or lord not in stones: continue
        stone,planet,focus=stones[lord]; used.add(lord)
        out.append({'planet':planet,'gemstone':stone,'priority':priority,'reason':f'{planet} rules house {h} for this Lagna and is therefore a primary chart significator. The gemstone is traditionally associated with strengthening that planet’s themes: {focus}. Natal placement: {p.get("sign")} house {p.get("house")}.','traditional_use':'Traditionally worn to strengthen the associated graha after considering its functional role, dignity and the complete chart.'})
    return out[:3]

def _clean_chat_text(text: str) -> str:
    return ' '.join(str(text or '').split())


def _unique_chat(items, limit=8):
    out=[]; seen=set()
    for item in items:
        text=_clean_chat_text(item)
        if len(text) < 25:
            continue
        key=text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _current_dasha_chain(chart):
    periods=chart.get('dashas',{}).get('periods',[]) or []
    current=chart.get('current_transits',{}).get('datetime')
    if not current:
        return []
    try:
        return _dasha_chain_at(periods, _datetime_from_iso(current))
    except Exception:
        return []


def _dasha_answer(chart, interpretation, question):
    q=question.lower()
    rows=interpretation.get('dasha_interpretations',[]) or []
    chain=_current_dasha_chain(chart)
    level_map={1:'Mahadasha',2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'}
    requested=[]
    for word,level in [('mahadasha',1),('antardasha',2),('pratyantar',3),('sookshma',4),('sukshma',4),('prana',5)]:
        if word in q: requested.append(level)
    pieces=[]
    if chain:
        labels=[]
        for x in chain:
            level=x.get('level')
            labels.append(f"{level_map.get(level, 'Dasha')} {x.get('lord','—')} ({str(x.get('start',''))[:10]} to {str(x.get('end',''))[:10]})")
        pieces.append('Current Vimshottari chain: ' + ' → '.join(labels))
    if requested:
        active_lords={x.get('level'):x.get('lord') for x in chain}
        # For a direct current-level question, show the active period first and only
        # adjacent periods when the user explicitly asks for past/future context.
        for level in requested:
            lord=active_lords.get(level)
            match=next((x for x in rows if x.get('level')==level and x.get('lord')==lord and lord),None)
            if match:
                pieces.append(match.get('text',''))
            else:
                nearby=[x for x in rows if x.get('level')==level]
                pieces.extend(x.get('text','') for x in nearby[:2])
    else:
        for x in chain:
            level=x.get('level'); lord=x.get('lord')
            match=next((r for r in rows if r.get('level')==level and r.get('lord')==lord and r.get('start')==x.get('start')),None)
            if match: pieces.append(match.get('text',''))
    if any(k in q for k in ('past','previous','history','historical')):
        past=interpretation.get('dasha_context',{}).get('previous_mahadashas',[])
        if past:
            pieces.append('Previous Mahadashas: ' + '; '.join(f"{x.get('lord')} ({str(x.get('start',''))[:10]}–{str(x.get('end',''))[:10]})" for x in past[-5:]))
    if any(k in q for k in ('future','next','upcoming')):
        future=interpretation.get('dasha_context',{}).get('next_mahadashas',[])
        if future:
            pieces.append('Upcoming Mahadashas: ' + '; '.join(f"{x.get('lord')} ({str(x.get('start',''))[:10]}–{str(x.get('end',''))[:10]})" for x in future[:5]))
    return _unique_chat(pieces, 8)

def _yoga_answer(chart, interpretation, question, narrative=None):
    q=question.lower()
    rows=interpretation.get('yoga_interpretations',[]) or _build_yoga_interpretations(chart)
    fruit=(narrative or {}).get('yoga_fruitification_interpretations',[]) or []
    if not rows:
        return ['No applicable Yoga was returned by the current Yoga detection layer for this chart.']
    pieces=[f"Applicable Yogas found in this chart: {len(rows)} detected combinations. I will interpret the detected combinations for this native rather than only listing their textbook definitions."]
    show_timing=any(k in q for k in ('fruit','date','when','timing','activate','activation'))
    for y in rows:
        name=y.get('name','Yoga')
        text=y.get('interpretation') or y.get('basis','')
        pieces.append(f"{name}: {text}")
        if show_timing:
            dates=[x for x in fruit if x.get('yoga')==name]
            if dates:
                for x in dates[:5]:
                    pieces.append(f"{name} — calculated fruitification candidate {x.get('date')}: {x.get('interpretation','')}")
            else:
                pieces.append(f"{name}: no calculated fruitification date is available in the current timing scan.")
    return _unique_chat(pieces, 40)


def _dosha_answer(chart, interpretation):
    rows=interpretation.get('dosha_interpretations',[]) or []
    if not rows:
        return ['No applicable Dosha was returned by the current Dosha screening layer for this chart.']
    pieces=[f"This chart has {len(rows)} applicable Dosha conditions. The following describes their specific chart basis and life impact."]
    for d in rows:
        pieces.append(f"{d.get('name','Dosha')}: {d.get('interpretation') or d.get('basis','')}")
    return _unique_chat(pieces, 15)


def _nakshatra_answer(chart, interpretation):
    pieces=[]
    for x in interpretation.get('pada',[]) or []:
        p=x.get('planet'); n=x.get('nakshatra'); pada=x.get('pada')
        pieces.append(f"{p}: {n}, Pada {pada}. {x.get('text','')}")
    return _unique_chat(pieces, 12)


def _transit_answer(interpretation, question):
    ti=interpretation.get('transit_interpretations',{}) or {}
    pieces=[]
    current=ti.get('current',[]) or []
    future=ti.get('future_milestones',[]) or []
    requested_planets=[p for p in ('Jupiter','Saturn','Rahu','Ketu') if p.lower() in question.lower()]
    if requested_planets:
        current=[x for x in current if x.get('planet') in requested_planets] or current
        future=[x for x in future if x.get('planet') in requested_planets] or future
    pieces.extend(x.get('interpretation','') for x in current[:4])
    pieces.extend(x.get('interpretation','') for x in future[:6])
    return _unique_chat(pieces, 10)


def _prediction_answer(narrative, question):
    pred=narrative.get('predictions',{}) or {}
    rows=pred.get('predictions',[]) or []
    q=question.lower()
    requested=None
    if 'week' in q: requested='weekly'
    elif 'month' in q: requested='monthly'
    elif 'quarter' in q: requested='quarterly'
    elif 'year' in q or 'annual' in q: requested='yearly'
    if requested and requested != pred.get('granularity'):
        # The selected report horizon is authoritative; explain what is actually available.
        rows=rows[:8]
    else:
        rows=rows[:10]
    pieces=[f"The prediction section uses the selected {pred.get('granularity','forecast')} horizon and combines the calculated Vimshottari hierarchy, slow-planet transits, transit Nakshatra/Pada, Ashtakavarga, alternative Dashas, Sudarshana and exact astronomical events."]
    for r in rows:
        pieces.append(r.get('interpretation',''))
    return _unique_chat(pieces,12)

def _interpretation_chat(chart, narrative, question):
    q=_clean_chat_text(question).lower()
    i=narrative.get('interpretations',{}) if narrative else {}
    # Handle specific intents first so broad keywords do not contaminate the answer.
    if any(k in q for k in ('prediction','predict','forecast','future') ) and not any(k in q for k in ('dasha','yoga','dosha','nakshatra','pada','transit','career','job','business','marriage','gemstone')):
        answer=_prediction_answer(narrative,q)
    elif any(k in q for k in ('dasha','mahadasha','antardasha','pratyantar','sookshma','sukshma','prana')):
        answer=_dasha_answer(chart,i,q)
    elif 'dosha' in q and 'yoga' not in q:
        answer=_dosha_answer(chart,i)
    elif 'yoga' in q:
        answer=_yoga_answer(chart,i,q,narrative)
    elif any(k in q for k in ('nakshatra','pada')):
        answer=_nakshatra_answer(chart,i)
    elif any(k in q for k in ('transit','jupiter','saturn','rahu','ketu')):
        answer=_transit_answer(i,q)
    elif any(k in q for k in ('gemstone','gem','stone','ruby','emerald','sapphire','coral','pearl','hessonite','cat\'s eye')):
        answer=[f"{x.get('gemstone')} for {x.get('planet')}: {x.get('reason')}" for x in i.get('gemstone_recommendations',[])[:4]]
    elif any(k in q for k in ('sister','brother','sibling','siblings')):
        # Sibling topics are assessed from the natal chart and D3 when available;
        # do not infer a relative's literal fate from the native's chart alone.
        answer=[]
        for div in ('D3','Drekkana'):
            answer += [x.get('text','') for x in i.get('divisional',[]) if x.get('division')==div]
        answer += [x.get('text','') for x in i.get('integrated_factor_interpretations',[]) if any(k in str(x).lower() for k in ('third house','sibling','mars','communication'))][:4]
        answer.append('This is an indirect indication through your chart, not a substitute for your sister’s or brother’s own chart and current circumstances. Stronger timing claims require D3, the 3rd/11th-house factors, relevant Dasha and transits to agree.')
    elif any(k in q for k in ('court','lawsuit','litigation','legal case','legal dispute','judge','custody')):
        answer=[]
        answer += [x.get('text','') for x in i.get('divisional',[]) if x.get('division') in ('D6','D30')]
        answer += [x.get('text','') for x in i.get('integrated_factor_interpretations',[]) if any(k in str(x).lower() for k in ('sixth house','eighth house','twelfth house','saturn','mars','legal','dispute'))][:5]
        answer += [f"{x.get('date')}: activation {x.get('score')}; Dasha {x.get('dasha')}." for x in narrative.get('timing_windows',[])[:4]]
        answer.append('Court outcomes cannot be determined from a single factor. Read the 6th, 8th, 9th and 12th houses, their lords, Dasha sequence and relevant Vargas together; treat this as a symbolic timing assessment, not legal advice.')
    elif any(k in q for k in ('d9','navamsa','marriage','wife','husband','relationship','partner')):
        d9=[x for x in i.get('divisional',[]) if x.get('division')=='D9']
        answer=[x.get('text','') for x in d9]
        if any(k in q for k in ('marriage','timing','when')):
            answer += [f"{x.get('date')}: {x.get('score')} activation — {x.get('dasha','')}." for x in narrative.get('marriage_timing',{}).get('windows',[])[:5]]
    elif any(k in q for k in ('career','profession','job','work')):
        answer=[f"{x.get('option')}: {x.get('reason')}" for x in narrative.get('career_options',[])[:6]]
        if any(k in q for k in ('change','switch','when','timing')):
            answer += [f"{x.get('date')}: activation {x.get('score')}; Dasha {x.get('dasha')}." for x in narrative.get('job_change_timing',{}).get('windows',[])[:5]]
        d10=[x for x in i.get('divisional',[]) if x.get('division')=='D10']
        answer += [x.get('text','') for x in d10]
    elif 'business' in q or 'entrepreneur' in q:
        answer=[f"{x.get('date')}: activation {x.get('score')}; Dasha {x.get('dasha')}." for x in narrative.get('business_timing',{}).get('windows',[])[:7]]
        d10=[x for x in i.get('divisional',[]) if x.get('division')=='D10']
        answer += [x.get('text','') for x in d10]
    elif any(k in q for k in ('week','weekly')):
        answer=[x.get('interpretation','') for x in narrative.get('forecast_interpretations',{}).get('weekly',[])[:8]]
    elif any(k in q for k in ('month','monthly')):
        answer=[x.get('interpretation','') for x in narrative.get('forecast_interpretations',{}).get('monthly',[])[:8]]
    elif any(k in q for k in ('year','yearly','annual')):
        answer=[x.get('interpretation','') for x in narrative.get('forecast_interpretations',{}).get('yearly',[])[:6]]
    else:
        answer=list(i.get('executive',[])[:2]) + [x.get('interpretation','') for x in i.get('integrated_factor_interpretations',[])[:4]]
    answer=_unique_chat(answer, 10)
    if not answer:
        answer=['No matching interpretation was found for that question in the generated chart data. Try asking about a specific Dasha, Varga, Yoga, Dosha, Nakshatra/Pada, transit, career, marriage, business or gemstone.']
    return '\n\n'.join(answer)

def build_interpretation_library(chart):
    planets=chart.get('planets',{})
    out={
        'version':'1.0.4 audited deep multi-layer interpretation corpus',
        'executive':[],
        'planetary':[],
        'house_themes':[],
        'nakshatra':[],
        'pada':_pada_interpretations(chart),
        'yoga_interpretations':_build_yoga_interpretations(chart),
        'combination_interpretations':_combination_interpretations(chart),
        'divisional':_divisional_interpretations(chart),
        'dignity':[],
        'dasha_context':_dasha_context(chart),
        'dasha_interpretations':_dasha_interpretations(chart),
        'dosha_interpretations':_dosha_interpretations(chart),
        'gemstone_recommendations':_gemstone_recommendations(chart),
        'transit_interpretations':_transit_interpretations(chart),
        'reference_corpus':{
            'entries':len(_RUNTIME_CORPUS)*_VIRTUAL_VARIANTS_PER_RULE,
            'variant_depth':_VIRTUAL_VARIANTS_PER_RULE,
            'unique_depth_lenses':len(_VIRTUAL_LENSES),
            'planet_house_sign_rules':_CORPUS_COUNTS_BY_TYPE.get('planet_house_sign',0),
            'planet_sign_rules':_CORPUS_COUNTS_BY_TYPE.get('planet_sign',0),
            'nakshatra_pada_rules':_CORPUS_COUNTS_BY_TYPE.get('nakshatra_pada',0),
            'varga_rules':_CORPUS_COUNTS_BY_TYPE.get('varga',0),
            'timing_rules':_CORPUS_COUNTS_BY_TYPE.get('timing',0),
            'rule_counts_by_type':dict(sorted(_CORPUS_COUNTS_BY_TYPE.items())),
        },
    }
    lagna=chart.get('lagna_sign','Unknown')
    out['executive']=[
        f'Ascendant: {lagna}. The chart is interpreted through the Lagna, its lord, the Moon and the condition of the key angular and trinal houses.',
        f'Moon: {planets.get("Moon",{}).get("sign","—")} in {planets.get("Moon",{}).get("nakshatra",{}).get("name","—")}, pada {planets.get("Moon",{}).get("nakshatra",{}).get("pada","—")}. This sets the emotional, habitual and timing lens used in the reading.',
        f'Sun: {planets.get("Sun",{}).get("sign","—")} in house {planets.get("Sun",{}).get("house","—")}. The interpretation emphasizes purpose, authority and visibility in that house.',
    ]
    for p,d in planets.items():
        h=int(d.get('house') or 1); s=d.get('sign','Unknown'); dig=d.get('dignity','Neutral')
        text=_corpus_find('planet_house_sign',f'{p}|{h}|{s}') or f'{p} in house {h} and {s} links {PLANET_THEMES.get(p,p)} with the themes of that house and sign.'
        out['planetary'].append({'planet':p,'sign':s,'house':h,'text':text})
        out['dignity'].append({'planet':p,'dignity':dig,'text':f'{p} is {dig}. Interpret its significations through its house, lordship, associations, aspects, divisional strength and timing.'})
    for h in range(1,13):
        sign=chart.get('houses',[{}])[h-1].get('sign','—') if len(chart.get('houses',[]))>=h else '—'
        lord=chart.get('houses',[{}])[h-1].get('lord','—') if len(chart.get('houses',[]))>=h else '—'
        occ=[p for p,d in planets.items() if d.get('house')==h]
        text=_corpus_find('house',str(h)) or f'House {h} concerns {HOUSE_THEMES.get(h,"its life area")}. '
        if occ: text += f' Natal occupants: {", ".join(occ)}.'
        out['house_themes'].append({'house':h,'sign':sign,'lord':lord,'occupants':occ,'text':text})
    for p,d in planets.items():
        n=d.get('nakshatra',{})
        out['nakshatra'].append({'planet':p,'name':n.get('name','—'),'pada':n.get('pada','—'),'text':_corpus_find('nakshatra_pada',f'{n.get("name")}|{n.get("pada")}') or f'{p} in {n.get("name","—")}, pada {n.get("pada","—")} is read through the nakshatra lord, deity, shakti and pada refinement.'})
    return out


def _build_forecast_interpretations(chart):
    result={}
    for key,label in [('weekly','Week-by-week'),('monthly','Month-by-month')]:
        rows=_forecast_dates(chart,key)
        result[key]=_interpret_period_rows(chart,rows,key[:-2] if key.endswith('ly') else key)
    # Yearly summaries use monthly layers grouped by calendar year so the interpretation
    # reflects the full requested horizon rather than only the first few rows.
    monthly=result.get('monthly',[])
    years={}
    for r in monthly: years.setdefault(r['date'][:4],[]).append(r)
    yearly=[]
    for year,items in sorted(years.items()):
        scores={d:round(sum(x['scores'].get(d,50) for x in items)/len(items),1) for d in DOMAIN_HOUSE_WEIGHTS_LOCAL}
        top=sorted(scores.items(),key=lambda x:x[1],reverse=True)[:3]
        dashas=sorted({x['dasha'] for x in items if x.get('dasha') and x['dasha']!='—'})
        yearly.append({'year':year,'scores':scores,'focus':[d.replace('_',' ').title() for d,_ in top],'dasha':dashas,'interpretation':f'Year {year}: {", ".join(d.replace("_"," ").title() for d,_ in top)} carries the strongest average activation across the forecast. The principal Vimshottari periods touching the year are {", ".join(dashas[:6]) or "not available"}. Read the year through the relevant houses, divisional charts and the month-by-month windows.'})
    result['yearly']=yearly
    return result


def _integrated_factor_interpretations(chart):
    planets=chart.get('planets',{}); dashas=chart.get('dashas',{}).get('periods',[]); snap=chart.get('current_transits',{}).get('planets',{})
    out=[]
    now=_datetime_from_iso(chart.get('current_transits',{}).get('datetime')) if chart.get('current_transits',{}).get('datetime') else datetime.now()
    chain=_dasha_chain_at(dashas, now); active=' → '.join(x['lord'] for x in chain) if chain else 'current Vimshottari period'
    for p,d in planets.items():
        n=d.get('nakshatra',{}) or {}; current=snap.get(p)
        transit_text=''
        if current:
            tn=current.get('nakshatra',{}) or {}
            th=chart.get('current_transits',{}).get('slow_planet_houses',{}).get(p)
            if th is not None:
                transit_text=f'{p} is currently in {current.get("sign","—")}, house {th}, {tn.get("name","—")} pada {tn.get("pada","—")}. This shifts the immediate emphasis toward the transit house while interacting with the natal placement.'
        corpus=_corpus_find('planet_house_sign',f"{p}|{d.get('house')}|{d.get('sign')}",variants=1)
        text=(f'{p} in {d.get("sign","—")} in house {d.get("house","—")} and {n.get("name","—")} pada {n.get("pada","—")} links {PLANET_THEMES.get(p,p)} with {HOUSE_THEMES.get(int(d.get("house") or 1),"the occupied life area")}. '
              f'The Nakshatra/Pada refines the expression through {n.get("shakti","its Nakshatra themes")}; the active Vimshottari chain is {active}. {transit_text} {corpus}')
        out.append({'planet':p,'interpretation':' '.join(text.split()),'natal':{'sign':d.get('sign'),'house':d.get('house'),'nakshatra':n.get('name'),'pada':n.get('pada')},'active_dasha':active,'current_transit':current})
    return out



YOGA_MEANINGS = {
    'Vesi Yoga': ('independent initiative, resourcefulness and the ability to act through one’s own intelligence', 'This can make self-directed effort, communication and practical initiative more visible in the areas ruled by the planet forming the Yoga.'),
    'Vosi Yoga': ('planning, preparation, behind-the-scenes organization and deliberate use of resources', 'Its expression can become noticeable when the person works quietly before a visible result, especially through the planet forming the Yoga.'),
    'Ubhayachara Yoga': ('balanced self-expression, initiative and the ability to operate before and after major decisions', 'The chart can support a fuller range of expression around authority, planning and execution when the involved planets are activated.'),
    'Sunapha Yoga': ('self-generated capability, initiative and development of resources around the mind', 'The Moon’s needs can be supported by the planet forming the Yoga, making its house and lordship an important channel for practical development.'),
    'Anapha Yoga': ('independence, internal resources and the ability to recover direction without relying entirely on external support', 'The planet forming the Yoga can become a source of competence or focus in its natal house when its periods activate.'),
    'Durudhara Yoga': ('resourcefulness, adaptability and the ability to draw support from several directions', 'The planets on both sides of the Moon create multiple channels through which mental, material or social themes can develop.'),
    'Kemadruma Yoga': ('a need to develop self-generated stability, emotional structure and consistent support systems', 'When genuinely applicable after cancellation checks, it makes Moon-related themes more dependent on the Moon’s dignity, house, lordship and timing.'),
    'Adhi Yoga': ('strategic support, resilience and the ability to handle competition or demanding circumstances', 'Its practical expression depends strongly on which benefics form it and the houses they rule.'),
    'Chandra Mangala Yoga': ('initiative around money, enterprise, negotiation and practical execution', 'It can combine emotional responsiveness with decisive action, especially in the houses occupied and ruled by Moon and Mars.'),
    'Budha Aditya Yoga': ('intelligence, communication, analysis, visibility and the ability to combine reasoning with authority', 'The house containing Sun and Mercury becomes a major arena for learning, decisions, communication and recognition.'),
    'Gaja Kesari Yoga': ('learning, judgment, confidence, counsel and constructive expansion', 'Jupiter’s house and lordship show where support, knowledge and broader perspective can become more available during activation.'),
    'Guru Mangala Yoga': ('knowledge combined with execution, enterprise, courage and strategic action', 'It can help convert learning or opportunity into action, especially through the houses ruled and occupied by Jupiter and Mars.'),
    'Ruchaka Yoga': ('initiative, courage, technical ability, leadership and forceful execution', 'Mars-related matters can become more prominent and decisive, particularly through its house and lordships.'),
    'Bhadra Yoga': ('analysis, communication, commerce, technical skill and intellectual organization', 'Mercury’s house and lordships show where this capacity is most likely to become visible.'),
    'Hamsa Yoga': ('wisdom, teaching, guidance, ethics, learning and constructive expansion', 'Jupiter’s house and lordships determine where knowledge, mentors and principled judgment can become major resources.'),
    'Malavya Yoga': ('relationships, aesthetics, diplomacy, comfort, resources and refined social expression', 'Venus strengthens the areas it rules and occupies, especially when Venus periods or supportive transits activate them.'),
    'Sasa Yoga': ('discipline, endurance, administration, responsibility and long-term authority', 'Saturn’s house and lordships indicate where sustained effort can eventually produce durable structures or status.'),
    'Amala Yoga': ('clean professional reputation, visible contribution and sustained public usefulness', 'The house from which the benefic forms Amala shows the channel through which constructive public expression is developed.'),
    'Parvata Yoga': ('supportive foundations, protection, organization and the ability to build stable structures', 'Its practical expression is shaped by Jupiter and Venus and the houses they rule and occupy.'),
    'Kahala Yoga': ('courage, persistence, strategic effort and willingness to take initiative', 'The Lagna and fifth-house factors show where confidence and intelligent initiative can be applied.'),
    'Lakshmi Yoga': ('resources, capability, learning, fortune and the ability to convert opportunity into material or social support', 'Its actual expression depends on the strength and houses of the Lagna and ninth lords.'),
    'Saraswati Yoga': ('learning, language, analysis, creativity, teaching and intellectual refinement', 'The Mercury/Jupiter/Venus combination can make education, communication or knowledge-based work an important life resource.'),
    'Raja Yoga': ('a connection between Kendra and Trikona lords that links action, responsibility and dharma', 'For this native, the houses ruled by the participating planets can become mutually reinforcing, so progress in one area can create openings in another when the involved planets are activated.'),
    'Vasumati Yoga': ('resource development through benefic influence on Upachaya houses', 'For this native, the benefic planets involved can support gradual development of income, networks, competence and practical resources in the houses they occupy and rule.'),
    'Shubha Kartari Yoga': ('supportive benefic influence surrounding a key house', 'For this native, the enclosed house receives a constructive surrounding influence that can make its matters easier to organize when the participating benefics are activated.'),
    'Parivartana Yoga': ('a strong exchange of life themes between two houses', 'For this native, the exchanged houses become tightly connected, so developments in one area can repeatedly alter circumstances in the other. The exact house pair shown above determines the practical life domain.'),
    'Vipareeta Raja Yoga': ('growth through difficult circumstances, problem-solving, recovery and reversal of pressure', 'The dusthana relationship can make challenges become sources of competence or leverage, especially during the involved planet’s periods.'),
    'Neecha Bhanga Raja Yoga': ('recovery, correction of weakness and the ability to turn an initially difficult planetary condition into greater competence', 'Its practical result depends on the exact cancellation conditions, the debilitated planet’s house/lordship and its timing.'),
    'Vargottama Yoga': ('greater consistency of a planet’s core themes across D1 and D9', 'The planet’s natal house, lordship and D9 position become especially important because the same sign is repeated across the two foundational charts.'),
    'Pushkara Navamsha Yoga': ('supportive refinement and constructive expression of a planet placed in a traditional Pushkara Navamsha', 'For this native, the planet receives an additional traditional layer of support, expressed through its natal house, lordship, sign, Nakshatra and timing.'),
    'Pushkara Bhaga Yoga': ('a traditionally auspicious degree emphasis for the planet', 'The exact house, sign, lordship and Dasha determine where this degree-level factor can become visible.'),
    'Chatussagara Yoga': ('broad structural support across the four angular houses', 'The four kendras become important anchors for identity, foundations, partnerships and public life.'),
    'Mahabhagya Yoga': ('a traditionally auspicious alignment of Lagna, Sun and Moon', 'It can emphasize coherence between identity, vitality and emotional orientation when the required traditional conditions are satisfied.'),
    'Akhanda Samrajya Yoga': ('resource consolidation, influence and sustained capacity to build a durable position', 'Its expression depends on the strength of the second, fifth and eleventh lords and their actual chart houses.'),
    'Harsha Yoga': ('resilience, competence in competition and improvement through disciplined handling of problems', 'The sixth-house themes can become a field in which the person develops practical mastery.'),
    'Sarala Yoga': ('research ability, resilience and capacity to navigate transformation', 'The eighth-house themes can become a source of depth and problem-solving rather than merely disruption.'),
    'Vimala Yoga': ('independence, controlled expenditure, retreat from unhelpful patterns and disciplined handling of hidden matters', 'The twelfth-house themes can be managed more deliberately when the relevant planet is well supported and activated.'),
    'Daama Yoga': ('a concentrated distribution pattern across the seven classical planets', 'For this native, the distribution of the seven classical planets creates a particular style of resource use, attention and effort; the occupied signs and houses show where that concentration is experienced.'),
}

# The first sentence of each rule is intentionally written as a plain-language
# life meaning. Override a few technical legacy entries whose old wording was
# still too close to the placement test.
YOGA_PLAIN_MEANINGS={k:v[0] for k,v in YOGA_MEANINGS.items()}
YOGA_PLAIN_MEANINGS.update({
    'Daama Yoga':'Your life resources tend to become concentrated rather than scattered. When active, this shows as strong focus, specialization and repeated effort in the areas connected with the participating planets and houses.',
    'Vesi Yoga':'The period emphasizes what you can build through your own initiative, planning and practical intelligence.',
    'Vosi Yoga':'The period emphasizes preparation, strategy and using information or resources effectively before a visible result appears.',
    'Ubhayachara Yoga':'The pattern supports both initiative and follow-through, making it easier to carry an idea from decision to execution.',
})

def _yoga_personalized_interpretation(chart, yoga):
    name=yoga.get('name','Yoga')
    factors=yoga.get('planetary_factors') or []
    planets=chart.get('planets',{})
    meaning, impact=YOGA_MEANINGS.get(name, (
        'a chart-specific combination linking the significations of its planetary factors',
        'Its actual life expression is determined by the factors, houses, lordships, dignity and timing shown in this chart.'
    ))
    factor_bits=[]
    houses=[]
    for p in factors:
        d=planets.get(p,{})
        if not d: continue
        n=d.get('nakshatra',{}) or {}
        h=d.get('house'); sg=d.get('sign')
        if h: houses.append(int(h))
        factor_bits.append(f"{p} is in {sg}, house {h}, {n.get('name','—')} Pada {n.get('pada','—')}")
    active=(_dasha_context(chart).get('current_hierarchy') or [])
    chain=' → '.join(x.get('lord','') for x in active) if active else 'the current Vimshottari period'
    house_names=[]
    for h in dict.fromkeys(houses):
        if h in HOUSE_THEMES: house_names.append(f'house {h} ({HOUSE_THEMES[h]})')
    factor_text='; '.join(factor_bits) if factor_bits else yoga.get('basis','')
    house_text=', '.join(house_names)
    timing=f"The current active Dasha chain is {chain}." if chain else ''
    activation='Activation rule: when its planetary factors enter Mahadasha, Antardasha, Pratyantar or a close slow-planet transit, the stated life arenas become active and the Yoga delivers its characteristic result there. House, dignity and cancellation factors determine the exact form and strength of the result.'
    return ' '.join(x for x in [
        f"{name} in this chart signifies {meaning}.",
        f"The chart-specific factors are: {factor_text}.",
        f"Therefore its strongest life arenas are {house_text}." if house_text else '',
        f"For this person, the practical impact is: {impact[0].lower()+impact[1:] if impact else impact}.",
        timing,
        activation
    ] if x)


def _corpus_direct(type_name, key):
    rows=_CORPUS_INDEX.get((type_name,key),[])
    if not rows: return ''
    return rows[0].get('text','').strip()


def _build_yoga_interpretations(chart):
    out=[]
    for y in chart.get('yogas',[]) or []:
        item=dict(y); name=y.get('name','')
        item['interpretation']=_yoga_personalized_interpretation(chart,y)
        item['meaning']=YOGA_PLAIN_MEANINGS.get(name, 'In plain language, this yoga concentrates the life themes represented by its participating planets and houses; when activated, those themes become more visible in events, decisions and priorities.')
        item['life_impact']=YOGA_MEANINGS.get(name,('','Its impact depends on its planetary factors, houses and timing.'))[1]
        # A Yoga is not automatically a career + money + relationship + family
        # result. Select only the life areas actually supported by its planets,
        # participating houses and classical yoga type. The reader gets the top
        # two or three relevant domains rather than the same generic four-line
        # block repeated for every Yoga.
        impacts=[]
        factor_planets=set(y.get('planetary_factors') or [])
        basis=(y.get('basis') or '').lower()
        house_nums={int(x) for x in re.findall(r'\b(?:house|from|in)\s+(\d{1,2})\b',basis)}
        type_name=(y.get('type') or '').lower()
        domain_weights={
            'career':0,'money':0,'relationship':0,'family':0,'education':0,
            'health':0,'spirituality':0,'travel':0
        }
        for h,w in ((10,5),(6,3),(11,3),(2,2)):
            if h in house_nums: domain_weights['career']+=w
        for h,w in ((2,5),(11,5),(5,2),(9,2)):
            if h in house_nums: domain_weights['money']+=w
        for h,w in ((7,6),(2,2),(5,2),(8,1)):
            if h in house_nums: domain_weights['relationship']+=w
        for h,w in ((4,5),(2,3),(5,2),(9,2)):
            if h in house_nums: domain_weights['family']+=w
        for h,w in ((4,4),(5,5),(9,5),(2,1)):
            if h in house_nums: domain_weights['education']+=w
        for h,w in ((1,3),(6,5),(8,5),(12,3)):
            if h in house_nums: domain_weights['health']+=w
        for h,w in ((8,5),(9,5),(12,5)):
            if h in house_nums: domain_weights['spirituality']+=w
        for h,w in ((3,3),(9,5),(12,4)):
            if h in house_nums: domain_weights['travel']+=w
        planet_domains={
            'Sun':{'career':2,'health':2},'Moon':{'family':2,'relationship':2},
            'Mars':{'career':2,'money':2,'health':1},'Mercury':{'career':2,'money':2,'education':2},
            'Jupiter':{'education':3,'money':2,'family':2,'spirituality':2},
            'Venus':{'relationship':3,'money':2,'career':1},'Saturn':{'career':3,'health':1,'money':1},
            'Rahu':{'career':1,'money':1,'travel':2},'Ketu':{'spirituality':3,'health':1}
        }
        for planet in factor_planets:
            for domain,w in planet_domains.get(planet,{}).items(): domain_weights[domain]+=w
        if 'career' in type_name: domain_weights['career']+=4
        if 'wealth' in type_name or 'dhana' in name.lower() or 'lakshmi' in name.lower(): domain_weights['money']+=4
        if any(k in name.lower() for k in ('marriage','kalathra','malavya')): domain_weights['relationship']+=4
        if any(k in name.lower() for k in ('saraswati','vidya','budha','hamsa')): domain_weights['education']+=3
        if any(k in name.lower() for k in ('moksha','spiritual','siva','ketu')): domain_weights['spirituality']+=3
        ranked=[d for d,v in sorted(domain_weights.items(),key=lambda kv:(-kv[1],kv[0])) if v>0]
        for domain in ranked[:3]:
            text=_corpus_direct('yoga_life_impact',f'{name}|{domain}')
            if text: impacts.append({'domain':domain,'text':text,'relevance_score':domain_weights[domain]})
        if impacts:
            item['life_impact_by_domain']=impacts
            item['primary_life_areas']=[x['domain'] for x in impacts]
            item['life_impact']='Primary life areas: '+', '.join(x['domain'].replace('_',' ').title() for x in impacts)+'. '+ ' '.join(x['text'] for x in impacts)
            item['interpretation']+=' Primary life areas: '+', '.join(x['domain'].replace('_',' ').title() for x in impacts)+'.'
        out.append(item)
    return out

def _yoga_fruitification_interpretations(chart):
    rows=[]
    for y in chart.get('yogas',[]):
        f=y.get('fruitification',{}); dates=f.get('possible_dates',[])
        if not dates: continue
        for item in dates:
            dasha=item.get('active_dasha') or 'the active dasha'
            triggers=', '.join(f"{x.get('transit')} {x.get('aspect')}° to {x.get('natal')}" for x in item.get('transit_triggers',[])[:3])
            tp=[]
            for p,v in (item.get('transit_positions') or {}).items():
                if v: tp.append(f"{p} in {v.get('name','—')} pada {v.get('pada','—')}")
            rows.append({'yoga':y.get('name'),'date':item.get('date'),'interpretation':f"{y.get('name')} has a calculated fruitification candidate on {item.get('date')} because {dasha} activates one or more yoga factors and the slow-planet transit layer simultaneously contacts the natal yoga factors. {triggers}. Transit Nakshatra/Pada context: {', '.join(tp) or 'not available'}.",'evidence':item})
    return rows

def _active_alt_dasha(advanced, key, when):
    rows=((advanced or {}).get(key) or {}).get('periods') or []
    for row in rows:
        try:
            st=_datetime_from_iso(row.get('start')); en=_datetime_from_iso(row.get('end'))
        except Exception:
            continue
        if st <= when < en:
            return row
    return None

def _varga_domain_reading(chart, domain):
    mapping={
        'marriage':('D9','marriage, spouse and the mature expression of relationship factors'),
        'relationship':('D9','marriage, spouse and the mature expression of relationship factors'),
        'career':('D10','profession, authority, reputation and visible contribution'),
        'job_change':('D10','professional role, status and changes in work direction'),
        'business':('D10','professional independence, enterprise and public results'),
        'money':('D2','wealth, savings, family resources and material accumulation'),
        'finances':('D2','wealth, savings, family resources and material accumulation'),
        'family':('D12','parents, ancestry and inherited family patterns'),
        'education':('D24','formal learning, scholarship, skills and knowledge development'),
        'learning':('D24','formal learning, scholarship, skills and knowledge development'),
        'children':('D7','children, creativity and generative responsibilities'),
        'spirituality':('D20','worship, spiritual practice and inner development'),
        'travel':('D4','fortune, property and movement of foundational resources'),
        'property':('D4','property, fixed assets and foundational fortune'),
        'wellness':('D27','general strength, resilience and capacity under pressure'),
        'health':('D27','general strength, resilience and capacity under pressure'),
    }
    key,purpose=mapping.get(domain,('D1','the natal chart'))
    v=chart.get('divisional_charts',{}).get(key,{})
    if not v: return {'varga':key,'purpose':purpose,'text':''}
    planets=v.get('planets',{})
    h10=[p for p,d in planets.items() if d.get('house')==10]
    h7=[p for p,d in planets.items() if d.get('house')==7]
    focus=h7 if domain in ('marriage','relationship') else h10 if domain in ('career','job_change','business') else []
    details=[]
    if focus: details.append(f"{', '.join(focus)} occupy the {key} 7th/10th-house focus relevant to this domain")
    if not focus:
        strongest=[]
        for p,d in planets.items():
            if d.get('house') in (1,4,5,7,9,10,11): strongest.append(f"{p} in {d.get('sign')} (H{d.get('house')})")
        details.extend(strongest[:3])
    return {'varga':key,'purpose':purpose,'lagna':v.get('lagna_sign'),'text':f"{key} ({v.get('name')}) confirms the {purpose}. " + ("; ".join(details) if details else "its chart-specific placements are used as a secondary confirmation.")}


def _spouse_profile(chart):
    d1=chart.get('planets',{}); d9=chart.get('divisional_charts',{}).get('D9',{})
    h7=next((h for h in chart.get('houses',[]) if h.get('house')==7),{})
    h7sign=h7.get('sign','')
    d9h7=next((x for x in d9.get('planets',{}).values() if x.get('house')==7),None)
    d9_7_sign=(d9.get('lagna_sign_index') is not None and next((d.get('sign') for d in d9.get('planets',{}).values() if d.get('house')==7),None)) or ''
    occupants=h7.get('occupants',[]) or []
    venus=d1.get('Venus',{})
    sign_traits=SIGN_TRAITS.get(h7sign,'')
    planet_traits='; '.join(f"{p}: {PLANET_THEMES.get(p,p)}" for p in occupants[:4])
    d9_7_planets=[p for p,d in d9.get('planets',{}).items() if d.get('house')==7]
    lines=[f"Spouse/partner nature: the 7th house is in {h7sign}, giving a relationship style centred on {sign_traits}."]
    if occupants: lines.append(f"Natal 7th-house occupants add {planet_traits}.")
    if d9.get('lagna_sign'): lines.append(f"Navamsa (D9) Lagna is {d9.get('lagna_sign')}; its 7th-house sign and occupants refine the mature partner pattern.")
    if d9_7_planets: lines.append(f"D9 7th-house planets: {', '.join(d9_7_planets)}.")
    if venus.get('sign'): lines.append(f"Venus in {venus.get('sign')} / house {venus.get('house')} adds {SIGN_TRAITS.get(venus.get('sign'),'relationship and value themes')} to attraction and partnership behaviour.")
    return {'headline':'Nature of spouse / long-term partner','reading':' '.join(lines),'d1_7th_sign':h7sign,'d9_7th_planets':d9_7_planets,'d9_lagna':d9.get('lagna_sign'),'venus':{'sign':venus.get('sign'),'house':venus.get('house')}}


def _career_fields(chart):
    p=chart.get('planets',{}); d10=chart.get('divisional_charts',{}).get('D10',{})
    d10_10=[pl for pl,d in d10.get('planets',{}).items() if d.get('house')==10]
    d10_lagna=d10.get('lagna_sign','')
    fields=[]
    rules=[
        ('technology / software / data / analytics', ['Mercury'], ('Gemini','Virgo','Aquarius')),
        ('finance / banking / investment / accounting', ['Jupiter','Venus'], ('Taurus','Libra','Capricorn')),
        ('law / policy / consulting / advisory', ['Jupiter','Mercury'], ('Sagittarius','Libra','Capricorn')),
        ('engineering / operations / manufacturing', ['Mars','Saturn'], ('Aries','Scorpio','Capricorn')),
        ('medicine / diagnostics / research', ['Mars','Mercury','Ketu'], ('Virgo','Scorpio','Aquarius')),
        ('media / writing / communications / publishing', ['Mercury','Venus','Sun'], ('Gemini','Leo','Libra')),
        ('design / luxury / fashion / arts', ['Venus'], ('Taurus','Libra','Pisces')),
        ('education / teaching / academia', ['Jupiter','Mercury'], ('Sagittarius','Pisces','Virgo')),
        ('government / administration / institutional leadership', ['Sun','Saturn','Jupiter'], ('Leo','Capricorn','Aquarius')),
        ('sales / marketing / negotiation / client relations', ['Mercury','Venus'], ('Gemini','Libra','Taurus')),
        ('entrepreneurship / trading / independent business', ['Mars','Mercury','Rahu'], ('Aries','Gemini','Scorpio')),
        ('real estate / construction / property', ['Mars','Saturn','Moon'], ('Cancer','Capricorn','Taurus')),
        ('travel / logistics / international business', ['Rahu','Jupiter','Mercury'], ('Sagittarius','Gemini','Aquarius')),
        ('spiritual / counselling / healing work', ['Jupiter','Ketu','Moon'], ('Pisces','Sagittarius','Scorpio')),
    ]
    for label,pls,signs in rules:
        hits=[x for x in pls if p.get(x,{}).get('house') in (2,3,5,6,9,10,11)]
        sign_hits=[p.get(x,{}).get('sign') for x in pls if p.get(x,{}).get('sign') in signs]
        d10_hits=[x for x in d10_10 if x in pls]
        score=len(hits)*2+len(sign_hits)*2+len(d10_hits)*3
        if score>0: fields.append({'field':label,'score':score,'factors':hits+sign_hits+d10_hits})
    if d10_lagna: fields.append({'field':f"D10-Lagna-aligned work ({d10_lagna})",'score':3,'factors':[f'D10 Lagna {d10_lagna}']})
    fields.sort(key=lambda x:(-x['score'],x['field']))
    return fields[:14]


def _prediction_divisional_evidence(chart, focus):
    evidence=[]
    for domain in focus[:4]:
        key=domain.lower().replace(' ','_')
        r=_varga_domain_reading(chart,key)
        if r.get('text'): evidence.append(r)
    return evidence

def _prediction_row(chart, row, granularity):
    from datetime import datetime as _dt
    date=row.get('date')
    if not date:
        return None
    try:
        when=_dt.fromisoformat(date+'T00:00:00+00:00')
    except Exception:
        return None
    periods=chart.get('dashas',{}).get('periods',[])
    chain=_dasha_chain_at(periods, when)
    dasha=' → '.join(x.get('lord','') for x in chain) or '—'
    advanced=chart.get('advanced_timing',{})
    alt={k:_active_alt_dasha(advanced,k,when) for k in ('chara_dasha','ashtottari','yogini','narayana','kalachakra')}
    av=chart.get('ashtakavarga_classical',{})
    sav=av.get('sav') or []
    j_sign=row.get('planets',{}).get('Jupiter',0)//30 if row.get('planets') else None
    s_sign=row.get('planets',{}).get('Saturn',0)//30 if row.get('planets') else None
    j_bindu=sav[int(j_sign)] if j_sign is not None and int(j_sign)<len(sav) else None
    s_bindu=sav[int(s_sign)] if s_sign is not None and int(s_sign)<len(sav) else None
    sud_rows=advanced.get('sudarshana',{}).get('rows',[])
    sud=next((x for x in sud_rows if x.get('date')==date),None)
    domains=chart.get('performance',{}).get('domains',[])
    # Use the already-calculated performance layer rather than creating new scores.
    perf=next((x for x in chart.get('performance',{}).get('monthly',[]) if x.get('date')==date),None)
    if perf is None:
        perf=next((x for x in chart.get('performance',{}).get('monthly',[]) if str(x.get('date',''))[:7]==date[:7]),None)
    scores={d:round(float(perf.get(d,50)),1) for d in domains} if perf else {}
    top=sorted(scores.items(),key=lambda x:x[1],reverse=True)[:3]
    focus=[d.replace('_',' ').title() for d,_ in top]
    events=[]
    for ev in (chart.get('exact_astronomical_events',{}).get('events') or []):
        if str(ev.get('datetime',''))[:10]==date:
            events.append(ev.get('type','astronomical event'))
    eclipses=[]
    for ev in (chart.get('eclipses',{}).get('events') or []):
        if str(ev.get('maximum',''))[:10]==date:
            eclipses.append(ev.get('type','eclipse'))
    yoga_hits=[]
    for y in chart.get('yogas',[]) or []:
        for candidate in (y.get('fruitification',{}).get('possible_dates') or []):
            if candidate.get('date')==date:
                yoga_hits.append(y.get('name','Yoga'))
    tajaka_year=next((x for x in (chart.get('tajaka',{}).get('years') or []) if int(x.get('year',0) or 0)==when.year),None)
    jh=row.get('jupiter_house'); sh=row.get('saturn_house'); rh=row.get('rahu_house'); kh=row.get('ketu_house')
    nk=(row.get('transit_nakshatra') or {})
    parts=[f'{date} is a {granularity} forecast period with active Vimshottari chain {dasha}.']
    if focus:
        parts.append(f'The strongest calculated life-area activations are {", ".join(focus)}.')
    if jh is not None:
        parts.append(f'Jupiter activates house {jh}; its transit Nakshatra/Pada is {(nk.get("Jupiter") or {}).get("name","—")} / {(nk.get("Jupiter") or {}).get("pada","—")}.')
    if sh is not None:
        parts.append(f'Saturn activates house {sh}; its transit Nakshatra/Pada is {(nk.get("Saturn") or {}).get("name","—")} / {(nk.get("Saturn") or {}).get("pada","—")}.')
    if rh is not None and kh is not None:
        parts.append(f'The nodal axis activates houses {rh} and {kh}.')
    if j_bindu is not None or s_bindu is not None:
        parts.append(f'Classical SAV context: Jupiter transit sign has {j_bindu if j_bindu is not None else "—"} bindus and Saturn transit sign has {s_bindu if s_bindu is not None else "—"} bindus.')
    if sud:
        parts.append(f'Sudarshana three-reference composite is {sud.get("composite")}.')
    alt_bits=[]
    for key,val in alt.items():
        if val: alt_bits.append(f'{key.replace("_"," ").title()}: {val.get("sign") or val.get("lord") or "active"}')
    if alt_bits:
        parts.append('Alternative timing layers: ' + '; '.join(alt_bits) + '.')
    if events:
        parts.append('Exact astronomical events on this date: ' + ', '.join(events) + '.')
    if eclipses:
        parts.append('Eclipse layer: ' + ', '.join(eclipses) + '.')
    if yoga_hits:
        parts.append('Yoga activation evidence on this date: ' + ', '.join(yoga_hits) + '.')
    if tajaka_year:
        parts.append(f'Tajaka annual layer for {when.year}: Year Lord {tajaka_year.get("year_lord","—")}, Muntha {tajaka_year.get("muntha_sign","—")}.')
    divisional_evidence=_prediction_divisional_evidence(chart,focus)
    if divisional_evidence:
        parts.append('Divisional confirmation: ' + ' '.join(x['text'] for x in divisional_evidence))
    deep_rules=[]
    active_chain=chain or (_dasha_context(chart).get('current_hierarchy') or [])
    if len(active_chain)>=3:
        txt=_corpus_direct('dasha_triple','|'.join(x.get('lord','') for x in active_chain[:3]))
        if txt: deep_rules.append(txt)
    domain_varga_map={'career':'D10','job_change':'D10','business':'D10','marriage':'D9','finances':'D2','learning':'D24','family':'D12','education':'D24','property_home':'D4','children_creativity':'D7','spiritual_practice':'D20','routine_recovery':'D27','travel_foreign':'D4','authority_visibility':'D10','partnerships':'D9','investments':'D2'}
    lead=active_chain[0].get('lord') if active_chain else None
    for dom,_score in top:
        if lead:
            key=f'{dom}|{lead}|{jh or 1}|dasha_transit_overlap'
            txt=_corpus_direct('prediction_domain_timing',key)
            if txt: deep_rules.append(txt)
            vv=domain_varga_map.get(dom)
            if vv:
                txt=_corpus_direct('domain_varga_confirmation',f'{dom}|{lead}|{jh or 1}|{vv}')
                if txt: deep_rules.append(txt)
    deep_rules=list(dict.fromkeys(deep_rules))[:10]
    if deep_rules:
        parts.append('Deep rule synthesis: ' + ' '.join(deep_rules[:4]))
    return {'date':date,'granularity':granularity,'dasha':dasha,'focus':focus,'domain_scores':scores,'transit_houses':{'Jupiter':jh,'Saturn':sh,'Rahu':rh,'Ketu':kh},'transit_nakshatra':nk,'ashtakavarga':{'jupiter_sav':j_bindu,'saturn_sav':s_bindu},'alternative_dashas':alt,'sudarshana':sud,'tajaka':tajaka_year,'yoga_hits':yoga_hits,'exact_events':events,'eclipses':eclipses,'divisional_evidence':divisional_evidence,'deep_rules':deep_rules,'interpretation':' '.join(parts)}

def _build_predictions(chart):
    forecast=chart.get('forecast',{})
    gran=forecast.get('granularity') or 'monthly'
    layers=chart.get('forecast_layers',{})
    key=gran if gran in layers else ('monthly' if gran=='quarterly' else 'weekly')
    rows=layers.get(key) or chart.get('transits',[])
    predictions=[]
    seen=set()
    for row in rows:
        p=_prediction_row(chart,row,key)
        if p and p['date'] not in seen:
            seen.add(p['date']); predictions.append(p)
    # Keep the user's requested horizon intact; UI can paginate/filter.
    summary=[]
    if predictions:
        # First, strongest periods by each available life domain, using existing scores.
        domains=chart.get('performance',{}).get('domains',[])
        for domain in domains:
            best=max(predictions,key=lambda x:x.get('domain_scores',{}).get(domain,50))
            summary.append({'domain':domain,'date':best['date'],'score':best.get('domain_scores',{}).get(domain,50),'interpretation':best['interpretation']})
    return {'horizon':forecast,'granularity':key,'methods':['Vimshottari Dasha hierarchy','Current and future slow-planet transits with Nakshatra/Pada','Classical Ashtakavarga SAV context','Sudarshana Chakra three-reference screen','Chara Dasha','Ashtottari Dasha','Yogini Dasha','Narayana Dasha','Kalachakra Dasha','Tajaka / annual solar-return layer','Exact ingress/station/eclipse events'],'predictions':predictions,'domain_summary':summary,'count':len(predictions),'note':'Prediction rows are assembled only from calculated chart, dasha, transit, Ashtakavarga, alternative-dasha and astronomical-event data. No dates or placements are generated outside those sources.'}

def _expanded_narrative(chart):
    forecast=_build_forecast_interpretations(chart)
    marriage=_timing_windows_by_domain(chart,'marriage',12)
    job=_timing_windows_by_domain(chart,'job_change',12)
    business=_timing_windows_by_domain(chart,'business',12)
    return {
        'forecast_interpretations':forecast,
        'career_options':_career_options(chart),
        'career_fields':_career_fields(chart),
        'spouse_profile':_spouse_profile(chart),
        'marriage_timing':{'interpretation':'Marriage timing is read by combining the 7th house and lord, Venus, the Navamsha and the active Vimshottari chain with Jupiter/Saturn activation. The windows below are the periods where those factors are most strongly activated in this chart.','windows':marriage},
        'job_change_timing':{'interpretation':'Job-change timing is read through the 6th/10th/11th houses, their lords, D10, Saturn/Rahu/Mars triggers and the active dasha chain.','windows':job},
        'business_timing':{'interpretation':'Business timing is read through the 7th/10th/11th/2nd/3rd houses, Mercury/Venus/Jupiter/Mars and the D10 context, then narrowed by the active dasha and transits.','windows':business},
        'active_dashas':_active_dasha_analysis(chart),
        'applicable_doshas':_applicable_doshas(chart),
        'integrated_factor_interpretations':_integrated_factor_interpretations(chart),
        'yoga_fruitification_interpretations':_yoga_fruitification_interpretations(chart),
        'predictions':_build_predictions(chart),
    }


def build_ai_interpretation_payload(chart: Dict[str, Any], narrative: Dict[str, Any] | None = None) -> Dict[str, Any]:
    narrative = narrative or {}
    # Keep the payload rich enough for another model to reproduce the reading while
    # excluding runtime-only implementation details and duplicate transit structures.
    selected = {
        'meta': chart.get('meta', {}),
        'lagna': {'sign': chart.get('lagna_sign'), 'sign_index': chart.get('lagna_sign_index'), 'longitude': chart.get('lagna_longitude')},
        'houses': chart.get('houses', []),
        'planets': chart.get('planets', {}),
        'divisional_charts': chart.get('divisional_charts', {}),
        'nakshatra_analysis': chart.get('nakshatra_analysis', {}),
        'dashas': {'starting_lord': chart.get('dashas',{}).get('starting_lord'), 'system': chart.get('dashas',{}).get('system'), 'forecast_relevant_hierarchy': _active_dasha_analysis(chart), 'past_current_future_context': narrative.get('interpretations',{}).get('dasha_context',{}), 'mahadasha_timeline': chart.get('dashas',{}).get('mahadasha_timeline',[])},
        'yogas_applicable': chart.get('yogas', []),
        'yoga_interpretations_for_this_chart': narrative.get('interpretations',{}).get('yoga_interpretations',[]),
        'doshas_applicable': [d for d in chart.get('doshas', []) if d.get('status') in ('screen-positive','present','possible')],
        'planet_strengths': chart.get('planet_strengths', {}),
        'shadbala': chart.get('shadbala', {}),
        'ashtakavarga_classical': chart.get('ashtakavarga_classical', {}),
        'forecast': chart.get('forecast', {}),
        'forecast_layers': chart.get('forecast_layers', {}),
        'performance': chart.get('performance', {}),
        'advanced_timing': chart.get('advanced_timing', {}),
        'tajaka': chart.get('tajaka', {}),
    }
    prompt = '''You are the interpretation engine for a professional Vedic Jyotish application.

Use ONLY the supplied JSON chart data. Do not invent placements, dashas, dates or yogas. Give explicit interpretations, not instructions for the user to interpret the chart themselves.

Structure the response as:
1. Executive chart interpretation
2. D1 Rashi interpretation
3. D2-D60 divisional-chart interpretations, each separately
4. Planet-by-planet interpretations
5. House-by-house interpretations
6. Nakshatra and Pada interpretations for every applicable planet
7. Vimshottari Mahadasha → Antardasha → Pratyantar → Sookshma → Prana interpretations, including several past Mahadashas, the current Mahadasha hierarchy, and several future Mahadashas relevant to the forecast
8. ONLY the yogas that are actually present in the JSON
9. ONLY the doshas that are actually present in the JSON
10. Career options indicated by the chart and the astrological factors supporting each option
11. Marriage likelihood and timing windows
12. Job-change likelihood and timing windows
13. Business likelihood and timing windows
14. Current transit interpretation plus future Jupiter, Saturn, Rahu and Ketu milestones, including each transit Nakshatra and Pada, then week-by-week, month-by-month and year-by-year interpretations
15. Yoga fruitification: for each applicable yoga, use only the dated candidates present in the supplied fruitification data; give up to five dates when available, and fewer when the calculated evidence contains fewer. Never invent a date. Explain the active dasha chain, natal yoga factor, transit planet, transit Nakshatra/Pada and contact that support each date.
16. Integrated synthesis combining natal placements, divisional placements, Nakshatra, Pada, all relevant Vimshottari levels and current/future transits.
17. Advanced prediction section: use the supplied prediction rows exactly as calculated, preserve the selected horizon/granularity, and explain why each period is activated using Dasha, transit, Nakshatra/Pada, Ashtakavarga, alternative Dasha, Sudarshana, Tajaka and exact-event evidence when present.
18. Key synthesis and practical focus areas

For each timing statement, name the active dasha chain and the transit/divisional factors that create the timing. For career options, distinguish the chart factors from the interpretation. For marriage, job change and business, provide the strongest dated windows available in the supplied data rather than generic statements. Keep the interpretation direct and readable.'''
    return {'schema_version':'jyotish-lab-ai-1','prompt':prompt,'astrological_data':selected,'runtime_interpretation':narrative.get('interpretations',{}),'expanded_timing':{k:narrative.get(k) for k in ('forecast_interpretations','career_options','marriage_timing','job_change_timing','business_timing') if k in narrative}, 'integrated_interpretations': narrative.get('interpretations',{}).get('integrated_factor_interpretations',[]), 'yoga_fruitification': narrative.get('interpretations',{}).get('yoga_fruitification_interpretations',[]), 'predictions': narrative.get('predictions', {})}

_base_generate_narrative = generate_narrative

def generate_narrative(chart: Dict[str, Any]) -> Dict[str, Any]:
    narrative=_base_generate_narrative(chart)
    narrative['interpretations']=build_interpretation_library(chart)
    narrative.update(_expanded_narrative(chart))
    # Keep analysis focused: only the dashas and doshas that actually intersect the
    # requested forecast horizon are exposed in the analysis payload.
    narrative['analysis']={
        'applicable_dashas':narrative['active_dashas'],
        'applicable_doshas':narrative['applicable_doshas'],
    }
    narrative['opening']='This report gives explicit chart interpretations from the computed Lagna, planetary placements, Vargas, Nakshatra/Pada, Vimshottari timing, applicable yogas and applicable doshas.'
    narrative['disclaimer']='Interpretations are presented within the Jyotish systems and calculation methods selected in this report. Timing statements are reading windows derived from the supplied chart, dasha and transit layers.'
    return narrative


# ---------------------------------------------------------------------------
# 0.9.8 depth/prediction/gemstone/chat performance layer
# ---------------------------------------------------------------------------

_DEEP_INTERPRETIVE_LENSES = [
    'Manifestation: identify the concrete life arena in which the factor can become visible.',
    'Motivation: describe what the factor makes the native pursue, protect, learn or change.',
    'Behavior: describe the style in which the native approaches the affected life area.',
    'Development: explain what becomes more constructive as the planet gains maturity and support.',
    'Pressure: identify where the same factor can demand pacing, boundaries or better sequencing.',
    'Resource: identify how time, money, attention, skill or relationships are mobilized through the factor.',
    'Relationship: explain how other people can become a channel through which the factor manifests.',
    'Career: connect the factor to work style, contribution, authority, specialization or professional visibility when relevant.',
    'Finance: connect the factor to earning, savings, resources, expenditure or financial decision-making when relevant.',
    'Learning: connect the factor to study, analysis, teaching, certification, writing or mastery when relevant.',
    'Home: connect the factor to family, property, emotional foundations or domestic priorities when relevant.',
    'Transformation: explain how the factor can alter priorities after a major transition.',
    'Dharma: explain how the factor interacts with principles, mentors, meaning and long-term direction.',
    'Timing: identify the Dasha level that can make the natal promise more visible.',
    'Sub-period: explain how Antardasha/Pratyantar can narrow the broad Mahadasha theme.',
    'Fine timing: explain how Sookshma and Prana can make an already active theme more immediate.',
    'Transit: explain how current or future Jupiter, Saturn, Rahu or Ketu transits can activate the natal factor.',
    'Transit Nakshatra: use the actual transit Nakshatra and Pada supplied by the ephemeris to refine the style of activation.',
    'Ashtakavarga: use the actual SAV/BAV values supplied for the transit sign as supporting timing evidence.',
    'Varga: use the relevant divisional chart to determine whether the same theme is reinforced in its specialized field.',
    'D9 synthesis: when relationship, maturity or planetary strength is relevant, compare the natal factor with D9.',
    'D10 synthesis: when career is relevant, compare the natal factor with D10.',
    'Sequence: read the factor as part of a chain instead of treating one placement as an isolated outcome.',
    'Convergence: give greater narrative weight when independent calculated layers point to the same life area.',
    'Recurrence: explain how a theme can reappear through different Dashas or transit cycles.',
    'Long view: distinguish a slow structural development from a short-lived activation.',
    'Short view: distinguish an immediate trigger from the longer natal promise behind it.',
    'Decision context: explain what kind of choice or responsibility the period is likely to foreground.',
    'Practical expression: translate the symbolism into an observable area of life without inventing an event.',
    'Counterweight: identify a second chart factor that modifies or redirects the first factor.',
    'Dispositor: explain how the sign lord modifies the expression when its chart data is available.',
    'Nakshatra lord: explain how the Nakshatra lord adds a motivational/timing layer when available.',
    'Pada: explain the specific Pada tone rather than repeating the Nakshatra definition.',
    'Dignity: distinguish the planet’s expression when exalted, own-sign, moolatrikona, neutral or debilitated.',
    'Strength: use the supplied normalized strength/Shadbala data to describe relative availability of the planet’s themes.',
    'Affliction: account for combustion, node contact or difficult aspects only when the chart data explicitly shows them.',
    'Opportunity: identify the life area in which supportive activation can be used constructively.',
    'Challenge: identify the life area requiring more conscious management without turning it into a deterministic event.',
]


def _unique_deep_lenses(seed_text: str, count: int = 8):
    import hashlib
    seed = int(hashlib.sha256(seed_text.encode('utf-8')).hexdigest()[:12], 16)
    out=[]
    for i in range(count * 3):
        item=_DEEP_INTERPRETIVE_LENSES[(seed+i*7) % len(_DEEP_INTERPRETIVE_LENSES)]
        if item not in out: out.append(item)
        if len(out)>=count: break
    return out


def _safe_house_theme(h):
    try: return HOUSE_THEMES.get(int(h), 'the relevant life area')
    except Exception: return 'the relevant life area'


def _dasha_chain_text(chain):
    return ' → '.join(str(x.get('lord')) for x in chain if x.get('lord')) or 'the active Vimshottari period'


def _functional_house_map(chart):
    out={}
    for h in chart.get('houses',[]) or []:
        try: out[int(h.get('house'))]=h.get('lord')
        except Exception: pass
    return out


def _planet_chart_factors(chart, planet):
    p=chart.get('planets',{}).get(planet,{})
    n=p.get('nakshatra',{}) or {}
    strength=chart.get('planet_strengths',{}).get('planets',{}).get(planet,{})
    shadbala=chart.get('shadbala',{}).get('planets',{}).get(planet,{})
    return p,n,strength,shadbala


def _enhanced_gemstone_recommendations(chart):
    planets=chart.get('planets',{}) or {}
    house_lords=_functional_house_map(chart)
    strengths=chart.get('planet_strengths',{}).get('planets',{}) or {}
    shadbala=chart.get('shadbala',{}).get('planets',{}) or {}
    d9=chart.get('divisional_charts',{}).get('D9',{}).get('planets',{}) or {}
    current_chain=_dasha_chain_at(chart.get('dashas',{}).get('periods',[]) or [], _datetime_from_iso(chart.get('current_transits',{}).get('datetime'))) if chart.get('current_transits',{}).get('datetime') else []
    active_lords={x.get('lord') for x in current_chain}
    stone_map={
        'Sun':('Ruby','identity, authority, vitality and visible direction'),
        'Moon':('Pearl','emotional steadiness, belonging, receptivity and adaptive stability'),
        'Mars':('Red Coral','initiative, courage, technical execution and disciplined action'),
        'Mercury':('Emerald','learning, analysis, communication, commerce and systems thinking'),
        'Jupiter':('Yellow Sapphire','wisdom, guidance, education, expansion and constructive opportunity'),
        'Venus':('Diamond / White Sapphire','relationships, negotiation, aesthetics, comfort and value creation'),
        'Saturn':('Blue Sapphire','discipline, structure, endurance and long-term responsibility'),
        'Rahu':('Hessonite','unconventional ambition, experimentation and amplification'),
        'Ketu':("Cat's Eye",'specialization, detachment, research and inward focus'),
    }
    rows=[]
    for planet,(stone,focus) in stone_map.items():
        if planet not in planets: continue
        p=planets[planet]; h=int(p.get('house') or 0)
        ruled=[hh for hh,lord in house_lords.items() if lord==planet]
        functional=0.0
        functional_bits=[]
        for hh in ruled:
            if hh in (1,5,9): functional+=28; functional_bits.append(f'rules house {hh}')
            elif hh in (4,7,10): functional+=13; functional_bits.append(f'rules house {hh}')
            elif hh in (2,11): functional+=7; functional_bits.append(f'rules house {hh}')
            elif hh==3: functional-=5; functional_bits.append('rules house 3')
            elif hh in (6,8,12): functional-=22; functional_bits.append(f'rules house {hh}')
        dignity=str(p.get('dignity','Neutral'))
        dignity_score={'Exalted':24,'Own sign':20,'Moolatrikona':22,'Neutral':8,'Debilitated':-22}.get(dignity,6)
        combust_penalty=-18 if p.get('combust') else 0
        retro_bonus=3 if p.get('retrograde') else 0
        base_strength=float(strengths.get(planet,{}).get('score',50) or 50)
        strength_score=(base_strength-50)*0.45
        sb_pct=float(shadbala.get(planet,{}).get('strength_pct',100) or 100)
        sb_score=(sb_pct-100)*0.12
        d9d=d9.get(planet,{})
        d9_score=8 if d9d.get('sign') and d9d.get('sign')==p.get('sign') else 0
        if d9d.get('sign_index') is not None and d9d.get('sign_index')==p.get('sign_index'): d9_score+=5
        dasha_bonus=15 if planet in active_lords else 0
        transit_bonus=0
        current=chart.get('current_transits',{}).get('planets',{}).get(planet,{})
        if current and current.get('sign_index')==p.get('sign_index'): transit_bonus+=5
        node_afflict=0
        for a in chart.get('aspects',[]) or []:
            if planet in (a.get('a'),a.get('b')) and a.get('aspect') in (0,180,90):
                other=a.get('b') if a.get('a')==planet else a.get('a')
                if other in ('Rahu','Ketu'): node_afflict-=10
        if planet in ('Rahu','Ketu'): node_afflict-=18
        score=round(max(0.0,min(100.0,50+functional+dignity_score+combust_penalty+retro_bonus+strength_score+sb_score+d9_score+dasha_bonus+transit_bonus+node_afflict)),1)
        label='Primary consideration' if score>=85 else 'Conditional consideration' if score>=65 else 'Not prioritized'
        reasons=[]
        if functional_bits: reasons.append(', '.join(functional_bits))
        reasons.append(f'{dignity} natal dignity in house {h}')
        reasons.append(f'normalized strength {base_strength:.1f}/100')
        if sb_pct: reasons.append(f'Shadbala screen {sb_pct:.1f}% of stated minimum')
        if d9d.get('sign'): reasons.append(f'D9 placement {d9d.get("sign")} / H{d9d.get("house","—")}')
        if planet in active_lords: reasons.append('planet is active in the current Vimshottari chain')
        cautions=[]
        if dignity=='Debilitated': cautions.append('debilitated natal dignity makes strengthening more conditional')
        if p.get('combust'): cautions.append('combustion is present')
        if node_afflict<0: cautions.append('node contact/affliction is present in the supplied chart data')
        if any(hh in (6,8,12) for hh in ruled): cautions.append('the planet rules a dusthana house, so strengthening is more conditional')
        rows.append({
            'planet':planet,'gemstone':stone,'score':score,'priority':label,'chart_role':f'{planet} rules '+', '.join(map(str,ruled)) if ruled else f'{planet} does not rule a mapped house',
            'reason':f'{stone} is {label.lower()} because {"; ".join(reasons)}. The chart connects {planet} with {focus}.',
            'supporting_factors':reasons,'cautions':cautions,
            'natal':{'sign':p.get('sign'),'house':p.get('house'),'nakshatra':(p.get('nakshatra') or {}).get('name'),'pada':(p.get('nakshatra') or {}).get('pada'),'dignity':dignity},
            'd9':{'sign':d9d.get('sign'),'house':d9d.get('house')},
            'traditional_use':f'Traditionally associated with strengthening {planet}; the recommendation is individualized here from functional lordship, dignity, strength, D9 context and timing.'
        })
    # Keep conditional nodal stones below functional planetary candidates unless their score is genuinely supported.
    rows.sort(key=lambda x:(x['score'], x['planet'] in ('Rahu','Ketu')), reverse=True)
    return rows[:5]


def _enhanced_prediction_domains(chart, row, chain, base_scores):
    scores=dict(base_scores)
    planets=chart.get('planets',{})
    # Additional life domains are derived from the same explicit whole-sign house triggers.
    extra={
        'education':{5:0.9,9:1.0,2:0.35,3:0.5},
        'property_home':{4:1.0,2:0.4,8:0.25,11:0.45},
        'children_creativity':{5:1.0,2:0.25,9:0.45,11:0.55},
        'travel_foreign':{9:0.9,12:1.0,3:0.55,8:0.2},
        'authority_visibility':{1:0.4,9:0.55,10:1.0,11:0.7},
        'research_transformation':{8:1.0,12:0.65,6:0.4,9:0.35},
        'spiritual_practice':{5:0.35,8:0.75,9:1.0,12:0.95},
    }
    for domain,weights in extra.items():
        s=50.0
        for h,w in weights.items():
            if row.get('jupiter_house')==h: s+=18*w
            if row.get('saturn_house')==h: s+=12*w
            if row.get('rahu_house')==h: s+=5*w
            if row.get('ketu_house')==h: s+=4*w
            if chain and chain[0].get('lord') in planets and planets[chain[0]['lord']].get('house')==h: s+=10*w
        scores[domain]=round(max(0,min(100,s)),1)
    return scores


def _prediction_evidence(chart, row, chain, alt, sud, tajaka_year, yoga_hits, events, eclipses):
    evidence=[]
    if chain: evidence.append({'type':'Vimshottari','value':_dasha_chain_text(chain)})
    for p in ('Jupiter','Saturn','Rahu','Ketu'):
        h=row.get(f'{p.lower()}_house')
        nk=(row.get('transit_nakshatra') or {}).get(p) or {}
        if h is not None: evidence.append({'type':'Transit','planet':p,'house':h,'sign':nk.get('name'),'pada':nk.get('pada')})
    av=chart.get('ashtakavarga_classical',{}).get('sav') or []
    for p in ('Jupiter','Saturn'):
        lon=(row.get('planets') or {}).get(p)
        if lon is not None and av:
            idx=int(float(lon)//30)%12
            if idx<len(av): evidence.append({'type':'SAV','planet':p,'sign_index':idx,'bindus':av[idx]})
    for key,val in alt.items():
        if val: evidence.append({'type':'Alternative Dasha','system':key,'value':val.get('lord') or val.get('sign') or val.get('name') or 'active'})
    if sud: evidence.append({'type':'Sudarshana','composite':sud.get('composite')})
    if tajaka_year: evidence.append({'type':'Tajaka','year':tajaka_year.get('year'),'year_lord':tajaka_year.get('year_lord'),'muntha':tajaka_year.get('muntha_sign')})
    for y in yoga_hits: evidence.append({'type':'Yoga','name':y})
    for e in events: evidence.append({'type':'Astronomical event','name':e})
    for e in eclipses: evidence.append({'type':'Eclipse','name':e})
    return evidence



_DETERMINISTIC_DOMAIN_RESULTS = {
    'career': 'Career activity rises: responsibilities, visibility, role definition and measurable professional output become the dominant work theme.',
    'job_change': 'Job-change pressure is active: role movement, applications, negotiations, restructuring or a decisive change in employment conditions is indicated.',
    'business': 'Business activity rises: clients, contracts, commercial decisions, revenue channels and enterprise execution become the dominant theme.',
    'marriage': 'Relationship activity is active: partnership decisions, commitment, agreements, conflict resolution or a change in relationship status becomes prominent.',
    'finances': 'Financial activity rises: earnings, savings, capital allocation, gains, expenses or resource restructuring becomes prominent.',
    'learning': 'Learning activity rises: study, examinations, writing, certification, teaching and skill acquisition become prominent.',
    'family': 'Family and home activity rises: residence, property, family obligations, domestic decisions and emotional foundations become prominent.',
    'education': 'Education activity rises: formal study, scholarship, certification and intellectual specialization become prominent.',
    'property_home': 'Property and home activity rises: residence, property transactions, vehicles, repairs or domestic restructuring become prominent.',
    'children_creativity': 'Children and creativity activity rises: children, creative production, intelligence, romance and calculated risk become prominent.',
    'travel_foreign': 'Travel and foreign activity rises: long-distance travel, relocation, international contacts or foreign environments become prominent.',
    'authority_visibility': 'Authority and visibility rise: leadership, recognition, public responsibility and status become prominent.',
    'research_transformation': 'Transformation activity rises: research, inheritance, joint resources, hidden matters and irreversible restructuring become prominent.',
    'spiritual_practice': 'Spiritual activity rises: retreat, pilgrimage, mantra, contemplation, detachment and inner discipline become prominent.',
    'routine_recovery': 'Routine and recovery activity rises: work systems, service, discipline, problem-solving and health-maintenance routines become prominent.',
    'foreign_links': 'Foreign and international activity rises: overseas institutions, international networks and unfamiliar environments become prominent.',
    'public_reputation': 'Public reputation is activated: reputation management, authority, leadership and public visibility become prominent.',
    'legal_conflict': 'Conflict and legal activity is activated: disputes, litigation, competition, negotiations and problem-solving become prominent.',
    'partnerships': 'Partnership activity rises: clients, alliances, contracts and one-to-one dealings become prominent.',
    'investments': 'Investment activity rises: capital allocation, speculation, risk management and gains become prominent.',
}

def _deterministic_domain_prediction(domain, score, row, chain):
    score=float(score or 0)
    if score >= 75:
        strength='strongly'
        statement=_DETERMINISTIC_DOMAIN_RESULTS.get(domain, f'{domain.replace("_"," ").title()} is strongly activated.')
    elif score >= 60:
        strength='actively'
        statement=_DETERMINISTIC_DOMAIN_RESULTS.get(domain, f'{domain.replace("_"," ").title()} is active.')
    elif score >= 45:
        strength='moderately'
        statement=f'{domain.replace("_"," ").title()} remains active but secondary; the period gives it a supporting rather than dominant result.'
    else:
        strength='weakly'
        statement=f'{domain.replace("_"," ").title()} is weakly activated in this period and does not dominate the forecast.'
    return {
        'domain':domain,'score':round(score,1),'strength':strength,
        'prediction':statement,
        'dasha':_dasha_chain_text(chain) if chain else '—',
        'trigger_houses':{p:row.get(f'{p.lower()}_house') for p in ('Jupiter','Saturn','Rahu','Ketu')},
    }

def _enhanced_prediction_row(chart, row, granularity):
    base=_prediction_row(chart,row,granularity)
    if not base: return None
    date=base['date']
    try: when=_datetime_from_iso(date+'T00:00:00+00:00')
    except Exception: return base
    chain=_dasha_chain_at(chart.get('dashas',{}).get('periods',[]) or [],when)
    advanced=chart.get('advanced_timing',{}) or {}
    alt={k:_active_alt_dasha(advanced,k,when) for k in ('chara_dasha','ashtottari','yogini','narayana','kalachakra')}
    sud=next((x for x in (advanced.get('sudarshana',{}).get('rows',[]) or []) if x.get('date')==date),None)
    tajaka_year=next((x for x in (chart.get('tajaka',{}).get('years') or []) if int(x.get('year',0) or 0)==when.year),None)
    yoga_hits=base.get('yoga_hits') or []
    events=base.get('exact_events') or []
    eclipses=base.get('eclipses') or []
    scores=_enhanced_prediction_domains(chart,row,chain,base.get('domain_scores',{}))
    top=sorted(scores.items(),key=lambda x:x[1],reverse=True)[:4]
    focus=[x[0].replace('_',' ').title() for x in top]
    evidence=_prediction_evidence(chart,row,chain,alt,sud,tajaka_year,yoga_hits,events,eclipses)
    # Use the number of independent calculated layers only as an evidence-depth label.
    layer_types={e.get('type') for e in evidence}
    depth='convergent' if len(layer_types)>=5 else 'multi-layer' if len(layer_types)>=3 else 'single-layer'
    parts=[f'{date} is a {granularity} prediction period with Vimshottari chain {_dasha_chain_text(chain)}.',
           f'The leading activated life areas are {", ".join(focus)}.',
           f'This is a {depth} prediction supported by {len(layer_types)} independent calculated timing layers in the supplied data.']
    if chain:
        lead=chain[0].get('lord'); lp=chart.get('planets',{}).get(lead,{})
        if lp: parts.append(f'The Mahadasha lord {lead} is natal in {lp.get("sign","—")}, house {lp.get("house","—")}, so its natal promise colors the period.')
    nk=row.get('transit_nakshatra') or {}
    for p in ('Jupiter','Saturn'):
        h=row.get(f'{p.lower()}_house'); nd=nk.get(p,{})
        if h is not None: parts.append(f'{p} is in house {h}, {nd.get("name","—")} Pada {nd.get("pada","—")}; this refines the way its transit activates the house.')
    if yoga_hits: parts.append('Applicable Yoga timing intersects this period: '+', '.join(yoga_hits)+'.')
    if events: parts.append('Exact astronomical events calculated for this date: '+', '.join(events)+'.')
    if eclipses: parts.append('An eclipse event is calculated for this date: '+', '.join(eclipses)+'.')
    if tajaka_year: parts.append(f'Tajaka annual context for {when.year}: Year Lord {tajaka_year.get("year_lord","—")}, Muntha {tajaka_year.get("muntha_sign","—")}.')
    return {**base,'domain_scores':scores,'focus':focus,'evidence':evidence,'evidence_depth':depth,'alternative_dashas':alt,'sudarshana':sud,'tajaka':tajaka_year,'interpretation':' '.join(parts)}


def _enhanced_build_predictions(chart):
    forecast=chart.get('forecast',{}) or {}
    requested=forecast.get('granularity') or 'monthly'
    layers=chart.get('forecast_layers',{}) or {}
    layer_map={'daily':'daily','weekly':'weekly','monthly':'monthly','quarterly':'yearly'}
    selected_key=layer_map.get(requested,'monthly')
    selected_rows=layers.get(selected_key) or chart.get('transits',[]) or []
    predictions=[]; seen=set()
    for row in selected_rows:
        p=_enhanced_prediction_row(chart,row,requested)
        if p and p.get('date') not in seen:
            seen.add(p['date']); predictions.append(p)
    all_layers={}
    for key,rows in layers.items():
        out=[]; local_seen=set()
        for row in rows:
            p=_enhanced_prediction_row(chart,row,key)
            if p and p.get('date') not in local_seen:
                local_seen.add(p['date']); out.append(p)
        all_layers[key]=out
    summary=[]
    domains=sorted({d for p in predictions for d in p.get('domain_scores',{})})
    for domain in domains:
        best=max(predictions,key=lambda x:x.get('domain_scores',{}).get(domain,50))
        summary.append({'domain':domain,'date':best['date'],'score':best.get('domain_scores',{}).get(domain,50),'interpretation':best['interpretation'],'evidence_depth':best.get('evidence_depth')})
    return {
        'horizon':forecast,'granularity':requested,'methods':[
            'Vimshottari Dasha hierarchy', 'Vimshottari Mahadasha/Antardasha/Pratyantar/Sookshma/Prana','Jupiter/Saturn/Rahu/Ketu transits','Transit Nakshatra/Pada','Natal transit contacts','Classical Ashtakavarga SAV context', 'Classical Ashtakavarga SAV','Alternative Chara/Ashtottari/Yogini/Narayana/Kalachakra timing','Sudarshana Chakra three-reference screen', 'Sudarshana Chakra','Tajaka / Varshaphala','Exact ingress/station events','Solar and lunar eclipse timing','Applicable Yoga fruitification','D1 + relevant Varga synthesis'
        ],
        'predictions':predictions,'domain_summary':summary,'count':len(predictions),'all_granularities':all_layers,
        'scope':{'domains':domains,'domain_count':len(domains),'weekly_count':len(all_layers.get('weekly',[])),'monthly_count':len(all_layers.get('monthly',[])),'yearly_count':len(all_layers.get('yearly',[])),'daily_count':len(all_layers.get('daily',[]))},
        'note':'Every prediction row is assembled from calculated chart, Dasha, transit, Nakshatra/Pada, Ashtakavarga, alternative timing, Tajaka and astronomical-event data available for the requested horizon.'
    }


def _enhanced_integrated_factor_interpretations(chart):
    planets=chart.get('planets',{}) or {}; dashas=chart.get('dashas',{}).get('periods',[]) or []
    snap=chart.get('current_transits',{}).get('planets',{}) or {}
    now=_datetime_from_iso(chart.get('current_transits',{}).get('datetime')) if chart.get('current_transits',{}).get('datetime') else datetime.now()
    chain=_dasha_chain_at(dashas,now); active=_dasha_chain_text(chain)
    out=[]
    for p,d in planets.items():
        n=d.get('nakshatra',{}) or {}; current=snap.get(p) or {}
        current_house=chart.get('current_transits',{}).get('slow_planet_houses',{}).get(p)
        natal_house=int(d.get('house') or 0)
        clauses=[f'{p} in {d.get("sign","—")} in house {natal_house} connects {PLANET_THEMES.get(p,p)} with {_safe_house_theme(natal_house)}.',
                 f'Its Nakshatra is {n.get("name","—")}, Pada {n.get("pada","—")}; the Pada refines the style of expression through {n.get("shakti","its Nakshatra shakti")}.',
                 f'The active Vimshottari sequence is {active}.']
        if current_house is not None:
            cn=current.get('nakshatra',{}) or {}
            clauses.append(f'Its current transit layer places {p} in {current.get("sign","—")}, house {current_house}, {cn.get("name","—")} Pada {cn.get("pada","—")}.')
        d9d=chart.get('divisional_charts',{}).get('D9',{}).get('planets',{}).get(p,{})
        d10d=chart.get('divisional_charts',{}).get('D10',{}).get('planets',{}).get(p,{})
        if d9d: clauses.append(f'D9 places {p} in {d9d.get("sign","—")}, house {d9d.get("house","—")}, refining maturity and relationship/dharmic expression.')
        if d10d: clauses.append(f'D10 places {p} in {d10d.get("sign","—")}, house {d10d.get("house","—")}, refining professional expression.')
        clauses.extend(_unique_deep_lenses(f'{p}|{natal_house}|{d.get("sign")}|{n.get("name")}|{n.get("pada")}',6))
        text=' '.join(clauses)
        out.append({'planet':p,'interpretation':' '.join(text.split()),'natal':{'sign':d.get('sign'),'house':natal_house,'nakshatra':n.get('name'),'pada':n.get('pada')},'active_dasha':active,'current_transit':current,'depth_lenses':_unique_deep_lenses(f'{p}|{natal_house}|{d.get("sign")}',8)})
    return out


def build_chat_context(chart, narrative, question):
    q=(question or '').lower()
    i=narrative.get('interpretations',{}) if narrative else {}
    ctx={'chart_identity':{'name':chart.get('meta',{}).get('name'),'lagna':chart.get('lagna_sign'),'moon':(chart.get('planets',{}).get('Moon') or {}).get('sign')},'question':question}
    def put(key,value):
        if value: ctx[key]=value
    if any(k in q for k in ('gemstone','gem','ruby','emerald','sapphire','coral','pearl','hessonite','cat')):
        put('gemstone_recommendations',i.get('gemstone_recommendations'))
        put('planet_strengths',chart.get('planet_strengths'))
        put('shadbala',chart.get('shadbala'))
        put('houses',chart.get('houses'))
        put('dashas',_active_dasha_analysis(chart))
    elif any(k in q for k in ('prediction','predict','future','forecast','coming','next')):
        put('predictions',narrative.get('predictions'))
        put('transit_interpretations',i.get('transit_interpretations'))
        put('dasha_context',i.get('dasha_context'))
        put('yoga_fruitification',i.get('yoga_fruitification_interpretations'))
        put('timing_windows', {k:narrative.get(k) for k in ('marriage_timing','job_change_timing','business_timing')})
    elif any(k in q for k in ('d9','navamsa','marriage','relationship')):
        put('D9',chart.get('divisional_charts',{}).get('D9'))
        put('marriage_timing',narrative.get('marriage_timing'))
        put('dasha_context',i.get('dasha_context'))
        put('transits',i.get('transit_interpretations'))
    elif any(k in q for k in ('d10','career','job','profession','business')):
        put('D10',chart.get('divisional_charts',{}).get('D10'))
        put('career_options',narrative.get('career_options'))
        put('job_change_timing',narrative.get('job_change_timing'))
        put('business_timing',narrative.get('business_timing'))
        put('dasha_context',i.get('dasha_context'))
        put('transits',i.get('transit_interpretations'))
    elif any(k in q for k in ('yoga','yogas')):
        put('applicable_yogas',i.get('yoga_interpretations'))
        put('yoga_fruitification',i.get('yoga_fruitification_interpretations'))
        put('dasha_context',i.get('dasha_context'))
    elif any(k in q for k in ('dosha','doshas')):
        put('applicable_doshas',i.get('dosha_interpretations'))
    elif any(k in q for k in ('nakshatra','pada')):
        put('nakshatra',i.get('nakshatra'))
        put('pada',i.get('pada'))
        put('planets',chart.get('planets'))
    elif any(k in q for k in ('dasha','mahadasha','antardasha','pratyantar','sookshma','prana')):
        put('dasha_context',i.get('dasha_context'))
        put('dasha_interpretations',i.get('dasha_interpretations'))
    elif any(k in q for k in ('transit','jupiter','saturn','rahu','ketu')):
        put('transit_interpretations',i.get('transit_interpretations'))
        put('current_transits',chart.get('current_transits'))
        put('predictions',narrative.get('predictions'))
    else:
        put('executive',i.get('executive'))
        put('integrated_factor_interpretations',i.get('integrated_factor_interpretations'))
        put('predictions',narrative.get('predictions'))
        put('career_options',narrative.get('career_options'))
    return ctx

# Replace the runtime hooks with the deeper implementations above.
_BASE_PREDICTION_ROW = _prediction_row

_DETERMINISTIC_DOMAIN_RESULTS = {
    'career': 'Career activity rises: responsibilities, visibility, role definition and measurable professional output become the dominant work theme.',
    'job_change': 'Job-change pressure is active: role movement, applications, negotiations, restructuring or a decisive change in employment conditions is indicated.',
    'business': 'Business activity rises: clients, contracts, commercial decisions, revenue channels and enterprise execution become the dominant theme.',
    'marriage': 'Relationship activity is active: partnership decisions, commitment, agreements, conflict resolution or a change in relationship status becomes prominent.',
    'finances': 'Financial activity rises: earnings, savings, capital allocation, gains, expenses or resource restructuring becomes prominent.',
    'learning': 'Learning activity rises: study, examinations, writing, certification, teaching and skill acquisition become prominent.',
    'family': 'Family and home activity rises: residence, property, family obligations, domestic decisions and emotional foundations become prominent.',
    'education': 'Education activity rises: formal study, scholarship, certification and intellectual specialization become prominent.',
    'property_home': 'Property and home activity rises: residence, property transactions, vehicles, repairs or domestic restructuring become prominent.',
    'children_creativity': 'Children and creativity activity rises: children, creative production, intelligence, romance and calculated risk become prominent.',
    'travel_foreign': 'Travel and foreign activity rises: long-distance travel, relocation, international contacts or foreign environments become prominent.',
    'authority_visibility': 'Authority and visibility rise: leadership, recognition, public responsibility and status become prominent.',
    'research_transformation': 'Transformation activity rises: research, inheritance, joint resources, hidden matters and irreversible restructuring become prominent.',
    'spiritual_practice': 'Spiritual activity rises: retreat, pilgrimage, mantra, contemplation, detachment and inner discipline become prominent.',
    'routine_recovery': 'Routine and recovery activity rises: work systems, service, discipline, problem-solving and health-maintenance routines become prominent.',
    'foreign_links': 'Foreign and international activity rises: overseas institutions, international networks and unfamiliar environments become prominent.',
    'public_reputation': 'Public reputation is activated: reputation management, authority, leadership and public visibility become prominent.',
    'legal_conflict': 'Conflict and legal activity is activated: disputes, litigation, competition, negotiations and problem-solving become prominent.',
    'partnerships': 'Partnership activity rises: clients, alliances, contracts and one-to-one dealings become prominent.',
    'investments': 'Investment activity rises: capital allocation, speculation, risk management and gains become prominent.',
}

def _deterministic_domain_prediction(domain, score, row, chain):
    score=float(score or 0)
    if score >= 75:
        strength='strongly'
        statement=_DETERMINISTIC_DOMAIN_RESULTS.get(domain, f'{domain.replace("_"," ").title()} is strongly activated.')
    elif score >= 60:
        strength='actively'
        statement=_DETERMINISTIC_DOMAIN_RESULTS.get(domain, f'{domain.replace("_"," ").title()} is active.')
    elif score >= 45:
        strength='moderately'
        statement=f'{domain.replace("_"," ").title()} remains active but secondary; the period gives it a supporting rather than dominant result.'
    else:
        strength='weakly'
        statement=f'{domain.replace("_"," ").title()} is weakly activated in this period and does not dominate the forecast.'
    return {
        'domain':domain,'score':round(score,1),'strength':strength,
        'prediction':statement,
        'dasha':_dasha_chain_text(chain) if chain else '—',
        'trigger_houses':{p:row.get(f'{p.lower()}_house') for p in ('Jupiter','Saturn','Rahu','Ketu')},
    }

def _enhanced_prediction_row(chart, row, granularity):
    base = _BASE_PREDICTION_ROW(chart, row, granularity)
    if not base: return None
    date = base.get('date')
    try: when = _datetime_from_iso(date+'T00:00:00+00:00')
    except Exception: return base
    chain=_dasha_chain_at(chart.get('dashas',{}).get('periods',[]) or [],when)
    advanced=chart.get('advanced_timing',{}) or {}
    alt={k:_active_alt_dasha(advanced,k,when) for k in ('chara_dasha','ashtottari','yogini','narayana','kalachakra')}
    sud=next((x for x in (advanced.get('sudarshana',{}).get('rows',[]) or []) if x.get('date')==date),None)
    tajaka_year=next((x for x in (chart.get('tajaka',{}).get('years') or []) if int(x.get('year',0) or 0)==when.year),None)
    yoga_hits=base.get('yoga_hits') or []; events=base.get('exact_events') or []; eclipses=base.get('eclipses') or []
    scores=_enhanced_prediction_domains(chart,row,chain,base.get('domain_scores',{}))
    top=sorted(scores.items(),key=lambda x:x[1],reverse=True)[:4]
    focus=[x[0].replace('_',' ').title() for x in top]
    evidence=_prediction_evidence(chart,row,chain,alt,sud,tajaka_year,yoga_hits,events,eclipses)
    layer_types={e.get('type') for e in evidence}
    depth='convergent' if len(layer_types)>=5 else 'multi-layer' if len(layer_types)>=3 else 'single-layer'
    parts=[f'{date} is a {granularity} prediction period with Vimshottari chain {_dasha_chain_text(chain)}.',f'The leading activated life areas are {", ".join(focus)}.',f'This is a {depth} prediction supported by {len(layer_types)} independent calculated timing layers in the supplied data.']
    if chain:
        lead=chain[0].get('lord'); lp=chart.get('planets',{}).get(lead,{})
        if lp: parts.append(f'The Mahadasha lord {lead} is natal in {lp.get("sign","—")}, house {lp.get("house","—")}, so its natal promise colors the period.')
    nk=row.get('transit_nakshatra') or {}
    for p in ('Jupiter','Saturn'):
        h=row.get(f'{p.lower()}_house'); nd=nk.get(p,{})
        if h is not None: parts.append(f'{p} is in house {h}, {nd.get("name","—")} Pada {nd.get("pada","—")}; this refines the way its transit activates the house.')
    if yoga_hits: parts.append('Applicable Yoga timing intersects this period: '+', '.join(yoga_hits)+'.')
    if events: parts.append('Exact astronomical events calculated for this date: '+', '.join(events)+'.')
    if eclipses: parts.append('An eclipse event is calculated for this date: '+', '.join(eclipses)+'.')
    if tajaka_year: parts.append(f'Tajaka annual context for {when.year}: Year Lord {tajaka_year.get("year_lord","—")}, Muntha {tajaka_year.get("muntha_sign","—")}.')
    domain_predictions=[_deterministic_domain_prediction(domain,score,row,chain) for domain,score in sorted(scores.items(), key=lambda x:(-x[1],x[0]))]
    parts.append('Direct result: '+ ' '.join(x['prediction'] for x in domain_predictions[:4]))
    return {**base,'domain_scores':scores,'focus':focus,'evidence':evidence,'evidence_depth':depth,'alternative_dashas':alt,'sudarshana':sud,'tajaka':tajaka_year,'domain_predictions':domain_predictions,'prediction_mode':'deterministic-rule','interpretation':' '.join(parts)}

_gemstone_recommendations = _enhanced_gemstone_recommendations
_integrated_factor_interpretations = _enhanced_integrated_factor_interpretations
_prediction_row = _enhanced_prediction_row
_build_predictions = _enhanced_build_predictions
