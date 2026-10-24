from __future__ import annotations
from datetime import date
from typing import Any, Dict, List
import re

VOWELS = set('AEIOU')
PYTHAGOREAN = {c: ((ord(c)-65)%9)+1 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
CHALDEAN = {
    **dict.fromkeys('AIJQY',1), **dict.fromkeys('BKR',2), **dict.fromkeys('CGLS',3),
    **dict.fromkeys('DMT',4), **dict.fromkeys('EHNX',5), **dict.fromkeys('UVW',6),
    **dict.fromkeys('OZ',7), **dict.fromkeys('FP',8),
}
MASTER_NUMBERS={11,22,33}

def _digits(n:int)->List[int]: return [int(x) for x in str(abs(n)) if x.isdigit()]

def reduce_number(n:int, keep_master:bool=True)->int:
    n=abs(int(n))
    while n>9 and not (keep_master and n in MASTER_NUMBERS):
        n=sum(_digits(n))
    return n

def _name_letters(name:str)->str:
    return ''.join(c for c in name.upper() if 'A'<=c<='Z')

def _py_sum(text:str)->int:
    return sum(PYTHAGOREAN[c] for c in _name_letters(text))

def _chal_sum(text:str)->int:
    return sum(CHALDEAN.get(c,0) for c in _name_letters(text))

def _vowel_sum(text:str)->int:
    return sum(PYTHAGOREAN[c] for c in _name_letters(text) if c in VOWELS)

def _consonant_sum(text:str)->int:
    return sum(PYTHAGOREAN[c] for c in _name_letters(text) if c not in VOWELS)

def _birth_path(dob:date)->int:
    # Common Pythagorean reduction of the complete birth date, preserving 11/22/33.
    return reduce_number(sum(_digits(dob.year))+sum(_digits(dob.month))+sum(_digits(dob.day)))

def _personal_year(dob:date, year:int)->int:
    return reduce_number(dob.day+dob.month+year)

def _personal_month(personal_year:int, month:int)->int:
    return reduce_number(personal_year+month)

def _personal_day(personal_month:int, day:int)->int:
    return reduce_number(personal_month+day)

def _pinnacles(dob:date)->Dict[str,int]:
    day=reduce_number(dob.day,False); month=reduce_number(dob.month,False); year=reduce_number(dob.year,False)
    return {
        'first': reduce_number(month+day),
        'second': reduce_number(day+year),
        'third': reduce_number(reduce_number(month+day)+reduce_number(day+year)),
        'fourth': reduce_number(month+year),
    }

def _challenges(dob:date)->Dict[str,int]:
    d=reduce_number(dob.day,False); m=reduce_number(dob.month,False); y=reduce_number(dob.year,False)
    return {'first':abs(m-d),'second':abs(d-y),'main':abs(abs(m-d)-abs(d-y)),'fourth':abs(m-y)}

def _cycle_label(n:int)->str:
    labels={1:'initiative / beginnings',2:'partnership / patience',3:'expression / visibility',4:'structure / work',5:'change / freedom',6:'responsibility / family',7:'study / introspection',8:'management / material results',9:'completion / release',11:'intuition / inspiration',22:'large-scale building',33:'service / teaching'}
    return labels.get(n,'development')

def _letter_counts(text:str)->Dict[str,int]:
    out={c:0 for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
    for c in _name_letters(text): out[c]+=1
    return out

def _hidden_passion(counts:Dict[str,int])->List[int]:
    if not counts: return []
    mx=max(counts.values())
    return sorted({PYTHAGOREAN[c] for c,n in counts.items() if n==mx and n>0})

def _karmic_lessons(counts:Dict[str,int])->List[int]:
    present={PYTHAGOREAN[c] for c,n in counts.items() if n>0}
    return [n for n in range(1,10) if n not in present]

def _first_vowel_consonant(text:str):
    letters=_name_letters(text)
    return next((c for c in letters if c in VOWELS),None), next((c for c in letters if c not in VOWELS),None)

def _planes_of_expression(counts:Dict[str,int])->Dict[str,List[int]]:
    planes={'mental':[1,8],'physical':[4,5],'emotional':[2,3,6],'intuitive':[7,9]}
    present={PYTHAGOREAN[c] for c,n in counts.items() if n>0}
    return {k:[n for n in vals if n in present] for k,vals in planes.items()}

def _name_cycles(name:str)->Dict[str,Any]:
    letters=_name_letters(name); counts=_letter_counts(name)
    fv,fc=_first_vowel_consonant(name)
    return {
        'hidden_passion':_hidden_passion(counts),
        'karmic_lessons':_karmic_lessons(counts),
        'first_vowel':{'letter':fv,'number':PYTHAGOREAN.get(fv) if fv else None},
        'first_consonant':{'letter':fc,'number':PYTHAGOREAN.get(fc) if fc else None},
        'planes_of_expression':_planes_of_expression(counts),
        'repeated_numbers':sorted({n for n in range(1,10) if sum(1 for c in letters if PYTHAGOREAN[c]==n)>=2}),
        'letter_frequency':{str(n):sum(1 for c in letters if PYTHAGOREAN[c]==n) for n in range(1,10)},
        'name_length':len(letters),
    }

def _number_meanings()->Dict[int,Dict[str,str]]:
    return {
      1:{'strength':'initiative, autonomy, leadership','shadow':'impatience, over-control, isolation','career':'entrepreneurship, leadership, independent specialist work'},
      2:{'strength':'cooperation, diplomacy, sensitivity','shadow':'indecision, over-accommodation, dependency','career':'partnerships, mediation, HR, client support, coordination'},
      3:{'strength':'expression, creativity, communication','shadow':'scattered effort, exaggeration, inconsistency','career':'media, writing, teaching, marketing, performance'},
      4:{'strength':'structure, discipline, reliability','shadow':'rigidity, pessimism, overwork','career':'engineering, operations, accounting, administration'},
      5:{'strength':'adaptability, freedom, experimentation','shadow':'restlessness, impulsiveness, excess','career':'sales, travel, trading, communications, technology'},
      6:{'strength':'responsibility, care, aesthetics','shadow':'over-responsibility, control, perfectionism','career':'design, education, counselling, management, hospitality'},
      7:{'strength':'analysis, research, introspection','shadow':'withdrawal, scepticism, secrecy','career':'research, data, investigation, spirituality, specialist work'},
      8:{'strength':'management, authority, material execution','shadow':'power struggles, material fixation, burnout','career':'finance, management, law, enterprise, institutional leadership'},
      9:{'strength':'humanitarianism, completion, broad perspective','shadow':'over-giving, detachment, unfinished practical details','career':'public service, teaching, arts, international or social-impact work'},
    }


NUMBER_PROFILES = {
    1:{'plain':'You operate best when you take initiative, make the decision and lead rather than wait for permission.','relationships':'You need independence and respect; control becomes a problem when independence becomes isolation.','money':'Money improves through initiative, ownership and leadership; impulsive solo decisions are the main financial risk.','career':'Leadership, entrepreneurship, independent specialist work, sales leadership and roles where you own the result.'},
    2:{'plain':'Your strongest mode is cooperation, timing, listening and working through people rather than force.','relationships':'Partnership is central. You need reciprocity and can become over-accommodating to avoid conflict.','money':'Money grows through collaboration, client relationships, coordination and patient accumulation.','career':'Mediation, HR, counselling, client management, diplomacy, coordination and partnership-driven work.'},
    3:{'plain':'Your life expression is strongest through communication, creativity, visibility and putting ideas into words or performance.','relationships':'You need conversation and emotional expression; silence and scattered attention create friction.','money':'Income is strongest when communication or creativity is monetised; inconsistent execution is the drag.','career':'Media, writing, teaching, marketing, content, public speaking, design and performance.'},
    4:{'plain':'You build through structure, repetition, discipline and practical systems. Results come from making things reliable.','relationships':'You show care through responsibility, but rigidity can make relationships feel controlled.','money':'Wealth is built through disciplined saving, assets, systems and long-term work rather than quick speculation.','career':'Engineering, operations, accounting, administration, project management, construction and systems work.'},
    5:{'plain':'Change, movement, experimentation and freedom are major drivers. A stagnant routine drains your momentum.','relationships':'You need space and novelty; possessiveness and impulsive decisions create instability.','money':'Income can come through sales, commerce, travel, communication and technology, but novelty can increase spending.','career':'Sales, travel, trading, communications, technology, marketing and fast-changing commercial roles.'},
    6:{'plain':'Responsibility, family, service, aesthetics and creating a stable environment are central themes.','relationships':'You seek commitment and loyalty; carrying other adults or controlling them creates strain.','money':'Financial stability improves through service, management, property, design and dependable long-term value.','career':'Education, design, counselling, hospitality, healthcare support, management and people-centred work.'},
    7:{'plain':'You need depth, privacy, research and time to understand things before committing.','relationships':'You need a partner who respects privacy and mental space; withdrawal is the main challenge.','money':'Money improves through specialist knowledge, research and expertise rather than constant social exposure.','career':'Research, data, investigation, engineering, analysis, spirituality and specialist professional work.'},
    8:{'plain':'Power, management, material execution and measurable results are central. You are pushed toward responsibility.','relationships':'You value competence and loyalty, but power struggles or work-first behaviour can strain intimacy.','money':'Strong material potential comes through management, enterprise, finance, assets and institutional authority; over-leverage is the danger.','career':'Finance, management, law, enterprise, institutional leadership, operations and high-responsibility roles.'},
    9:{'plain':'You are pulled toward completion, broad perspective, service and causes larger than immediate personal gain.','relationships':'You need meaning and emotional breadth; detachment or rescuing everyone creates distance.','money':'Money is strongest when practical work serves a broader mission; boundaries prevent over-giving.','career':'Public service, teaching, arts, international work, social impact and mission-driven leadership.'},
    11:{'plain':'Sensitivity, intuition, insight and inspiration are amplified. You absorb patterns quickly and need a channel for them.','relationships':'You need emotional depth and mental connection; idealisation and overstimulation create disappointment.','money':'Financial results improve when intuition is converted into a disciplined craft.','career':'Teaching, writing, research, counselling, creative direction, spiritual work and visionary leadership.'},
    22:{'plain':'You are oriented toward building something large, practical and lasting from an ambitious idea.','relationships':'Commitment is serious and practical; work pressure must not crowd out emotional presence.','money':'Strong potential for large-scale assets, enterprise and institution-building when risk is controlled.','career':'Large projects, engineering, infrastructure, enterprise, management, property and institution-building.'},
    33:{'plain':'Service, teaching, protection and uplifting others become unusually strong themes.','relationships':'You give heavily and need boundaries so care does not become self-sacrifice.','money':'Financial stability improves when service is organised professionally rather than given away without limits.','career':'Teaching, counselling, healing, education, leadership, arts and service institutions.'},
}

def _profile(n:int)->Dict[str,str]:
    return NUMBER_PROFILES.get(n, NUMBER_PROFILES[reduce_number(n)])

def _personal_year_prediction(number:int)->str:
    texts={1:'Start projects, take ownership, change direction and establish a new cycle.',2:'Prioritise partnership, negotiation, patience, alliances and gradual development.',3:'Prioritise communication, publishing, networking, learning, creativity and visibility.',4:'Build systems, clear obligations, organise money and make durable practical progress.',5:'Expect a change-oriented cycle: travel, role changes, experimentation and breaks from stale routines.',6:'Put family, home, commitment, management and relationship decisions at the centre.',7:'Prioritise study, research, specialisation, retreat, analysis and reassessment.',8:'Focus on money, authority, management, negotiations and measurable professional outcomes.',9:'Finish cycles, release obsolete commitments and prepare for the next beginning.',11:'Develop ideas, teaching, intuition and influential communication into concrete work.',22:'Convert a large plan into structures, assets, systems or institutions that can last.',33:'Prioritise service, mentoring, teaching and meaningful responsibility for others.'}
    return texts.get(number,texts[reduce_number(number)])

def _personal_month_prediction(number:int)->str:
    return _personal_year_prediction(number)

def analyze(name:str,dob:date, years:int=10)->Dict[str,Any]:
    clean=_name_letters(name)
    py_total=_py_sum(name); ch_total=_chal_sum(name); soul_total=_vowel_sum(name); personality_total=_consonant_sum(name)
    lp=_birth_path(dob); birth_day=reduce_number(dob.day)
    maturity=reduce_number(lp+reduce_number(py_total))
    now_year=date.today().year
    personal_years=[]
    for y in range(now_year,now_year+max(1,min(years,30))):
        py=_personal_year(dob,y)
        months=[{'month':m,'number':_personal_month(py,m),'theme':_cycle_label(_personal_month(py,m)),'prediction':_personal_month_prediction(_personal_month(py,m))} for m in range(1,13)]
        personal_years.append({'year':y,'number':py,'theme':_cycle_label(py),'interpretation':_profile(py)['plain'],'prediction':_personal_year_prediction(py),'months':months})
    return {
        'system':'Pythagorean core + Chaldean name cross-check',
        'name':name,'clean_name':clean,
        'core':{
            'life_path':lp,'life_path_theme':_cycle_label(lp),
            'birthday':birth_day,'destiny_expression':reduce_number(py_total),'destiny_raw':py_total,
            'soul_urge':reduce_number(soul_total),'soul_urge_raw':soul_total,
            'personality':reduce_number(personality_total),'personality_raw':personality_total,
            'maturity':maturity,
            'chaldean_name':reduce_number(ch_total),'chaldean_raw':ch_total,
        },
        'pinnacles':_pinnacles(dob),'challenges':_challenges(dob),
        'personal_years':personal_years,
        'name_analysis':_name_cycles(name),
        'number_meanings':_number_meanings(),
        'interpretive_profiles':{str(k):_profile(k) for k in sorted(set(list(range(1,10))+[11,22,33]))},
        'birth_date_components':{'day':dob.day,'month':dob.month,'year':dob.year,'day_number':birth_day,'month_number':reduce_number(dob.month),'year_number':reduce_number(sum(_digits(dob.year)),False)},
        'predictive_summary':{
            'life_path':_profile(lp)['plain'],
            'career':_profile(reduce_number(py_total))['career'],
            'relationships':_profile(lp)['relationships'],
            'money':_profile(lp)['money'],
            'current_personal_year':{'year':now_year,'number':_personal_year(dob,now_year),'prediction':_personal_year_prediction(_personal_year(dob,now_year))},
        },
        'long_cycles':{
            'formative':{'number':reduce_number(dob.month+dob.day),'theme':_cycle_label(reduce_number(dob.month+dob.day))},
            'productive':{'number':reduce_number(dob.day+sum(_digits(dob.year))),'theme':_cycle_label(reduce_number(dob.day+sum(_digits(dob.year))))},
            'mature':{'number':reduce_number(dob.month+sum(_digits(dob.year))),'theme':_cycle_label(reduce_number(dob.month+sum(_digits(dob.year))))},
        },
        'method_notes':[
            'Numerology is a symbolic/divinatory framework, not an empirically validated predictive science.',
            'Master numbers 11, 22 and 33 are preserved in reductions where applicable.',
            'Name numbers depend on the exact spelling supplied by the user.',
        ],
    }
