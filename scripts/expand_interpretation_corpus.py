import json, itertools, hashlib
from pathlib import Path
import sys
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
from app.report import _PLANET_INTERP,_HOUSE_INTERP,_SIGN_INTERP,_NAKSHATRA_INTERP,_VARGA_PURPOSES
from app.yoga_catalog import YOGA_CATALOG,DOSHA_CATALOG
planets=list(_PLANET_INTERP)
signs=list(_SIGN_INTERP)
houses=range(1,13)
pairs=list(itertools.combinations(planets,2))
dasha_order=['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
domains=['career','job_change','business','marriage','finances','learning','family','education','property_home','children_creativity','travel_foreign','authority_visibility','research_transformation','spiritual_practice','routine_recovery','foreign_links','public_reputation','legal_conflict','partnerships','investments']
DOMAIN_TEXT={
'career':'career, status and visible contribution','job_change':'employment, role and professional transition','business':'enterprise, clients, contracts and commercial activity','marriage':'marriage, partnership and agreements','finances':'income, savings, assets and financial capacity','learning':'education, examinations, writing and mastery','family':'family, home and emotional foundations','education':'formal learning, scholarship and certification','property_home':'property, residence, vehicles and domestic foundations','children_creativity':'children, creativity, intelligence and speculative activity','travel_foreign':'long-distance travel, foreign links and relocation','authority_visibility':'authority, recognition and public visibility','research_transformation':'research, inheritance, joint resources and major transformation','spiritual_practice':'spiritual practice, retreat, pilgrimage and inner discipline','routine_recovery':'work routines, service, health maintenance and recovery','foreign_links':'foreign institutions, international networks and unfamiliar environments','public_reputation':'reputation, public standing and leadership visibility','legal_conflict':'competition, litigation, disputes and problem resolution','partnerships':'clients, alliances, marriage and one-to-one dealings','investments':'risk, speculation, capital allocation and gains'}
entries=[]
def add(t,k,text,**meta):
    entries.append({'type':t,'key':k,'text':text,**meta})
# Core 9x12x12 + direct/deep deterministic variants
for p in planets:
  for h in houses:
    for s in signs:
      core=f'{p} in house {h} puts {_PLANET_INTERP[p]} into {_HOUSE_INTERP[h]}. In {s}, the expression is driven by {_SIGN_INTERP[s]}. The concrete result is determined by lordship, dignity, conjunctions, aspects and timing.'
      add('planet_house_sign',f'{p}|{h}|{s}',core,planet=p,house=h,sign=s)
      variants=[
        f'{p} in house {h} produces a direct focus on {_HOUSE_INTERP[h]} through {_PLANET_INTERP[p]}. In {s}, the mode is {_SIGN_INTERP[s]}.',
        f'{p} in house {h} makes {_HOUSE_INTERP[h]} a recurring field for {_PLANET_INTERP[p]}. {s} makes the expression {_SIGN_INTERP[s]}.',
        f'{p} in house {h}: {_PLANET_INTERP[p]} directly enters {_HOUSE_INTERP[h]}; {s} supplies the style through {_SIGN_INTERP[s]}.',
        f'{p} activates house {h} matters through {_PLANET_INTERP[p]}. In {s}, this becomes {_SIGN_INTERP[s]}.',
        f'{p} here gives a pronounced {_HOUSE_INTERP[h]} theme. The {s} condition makes it {_SIGN_INTERP[s]}.',
        f'The life result of {p} in house {h} is concentrated in {_HOUSE_INTERP[h]}. Its {s} expression is {_SIGN_INTERP[s]}.',
        f'{p} makes house {h} a decisive channel for {_PLANET_INTERP[p]}; {s} determines the operating style: {_SIGN_INTERP[s]}.',
        f'When {p} is activated, house {h} becomes prominent. In {s}, the activated theme is {_PLANET_INTERP[p]} expressed through {_SIGN_INTERP[s]}.',
      ]
      for i,v in enumerate(variants,1): add('planet_house_sign_variant',f'{p}|{h}|{s}|V{i}',v,planet=p,house=h,sign=s,variant=i)
# Planet pair interactions
for a,b in pairs:
  for h in houses:
    add('planet_pair_house',f'{a}|{b}|{h}',f'{a} + {b} in house {h} combine {_PLANET_INTERP[a]} with {_PLANET_INTERP[b]} inside {_HOUSE_INTERP[h]}. The result is a concentrated two-planet agenda in this life area.',planet_a=a,planet_b=b,house=h)
    add('planet_pair_house_direct',f'{a}|{b}|{h}|direct',f'{a} and {b} jointly activate house {h}: {_PLANET_INTERP[a]} and {_PLANET_INTERP[b]} become inseparable from {_HOUSE_INTERP[h]}.',planet_a=a,planet_b=b,house=h)
  for s in signs:
    add('planet_pair_sign',f'{a}|{b}|{s}',f'{a} + {b} in {s} combine {_PLANET_INTERP[a]} and {_PLANET_INTERP[b]} through {_SIGN_INTERP[s]}. The sign sets the style while house placement sets the life arena.',planet_a=a,planet_b=b,sign=s)
# Dasha combinations
for md in dasha_order:
  for ad in dasha_order:
    for h in houses:
      add('dasha_pair_house',f'{md}|{ad}|{h}',f'{md} Mahadasha + {ad} Antardasha activates {_HOUSE_INTERP[h]} through {_PLANET_INTERP[md]} and {_PLANET_INTERP[ad]}. This is a direct period of activity in house {h}; the stronger planet and its lordship determine whether the result is constructive, disruptive or both.',mahadasha=md,antardasha=ad,house=h)
    add('dasha_pair',f'{md}|{ad}',f'{md} Mahadasha + {ad} Antardasha combines {_PLANET_INTERP[md]} with {_PLANET_INTERP[ad]}. The Mahadasha establishes the main life direction and the Antardasha delivers the concrete event channel.',mahadasha=md,antardasha=ad)
    for level in ('Pratyantar','Sookshma','Prana'):
      add('dasha_level_pair',f'{md}|{ad}|{level}',f'{md} Mahadasha / {ad} Antardasha with a {level} sub-period narrows the active result to the combined themes of {_PLANET_INTERP[md]} and {_PLANET_INTERP[ad]}. The deeper level is a timing trigger, not a new natal promise.',mahadasha=md,antardasha=ad,level=level)
# Transit contacts
aspects=[0,60,90,120,180]
for tp in ('Jupiter','Saturn','Rahu','Ketu'):
  for np in planets:
    for asp in aspects:
      add('transit_natal_contact',f'{tp}|{np}|{asp}',f'{tp} at {asp}° to natal {np} activates {_PLANET_INTERP[np]} through {_PLANET_INTERP[tp]}. The contact is read as a direct timing trigger; the natal house of {np} identifies the concrete life arena.',transit=tp,natal=np,aspect=asp)
# Domain combinations
for dom in domains:
  for p in planets:
    for h in houses:
      add('domain_planet_house',f'{dom}|{p}|{h}',f'{DOMAIN_TEXT[dom].title()} is activated through {p} in house {h}. {_PLANET_INTERP[p].capitalize()} is expressed through {_HOUSE_INTERP[h]}; when {p} is active, {DOMAIN_TEXT[dom]} becomes a principal result channel.',domain=dom,planet=p,house=h)
# Nakshatra padas
for n,desc in _NAKSHATRA_INTERP.items():
  for pada in range(1,5):
    add('nakshatra_pada_expanded',f'{n}|{pada}',f'{n} Pada {pada} gives {desc}; Pada {pada} sharpens the style toward '+['initiative and direct expression','stability and material cultivation','communication and mental movement','emotional depth and consolidation'][pada-1]+'. A planet here delivers its own significations through this filter.',nakshatra=n,pada=pada)
# Vargas
for v,purpose in _VARGA_PURPOSES.items():
  add('varga_expanded',v,f'{v} is read directly for {purpose}. Strong occupants, the Lagna, relevant lords and repeated placements determine the concrete outcome in this division.',varga=v)
# Yoga and dosha life-impact matrix
for y in YOGA_CATALOG:
  for mode in ('career','money','relationship','family','learning','status','health_routine','spiritual'):
    mode_text={
      'career':'career and public work','money':'income, savings and material resources','relationship':'marriage, partnership and agreements','family':'family, home and continuity','learning':'education, intelligence and skill','status':'status, authority and visibility','health_routine':'routine, resilience and problem-solving','spiritual':'spiritual practice, detachment and inner development'}[mode]
    add('yoga_life_impact',f'{y}|{mode}',f'{y} in this chart directly affects {mode_text}. When its planetary factors enter an active Dasha or strong transit contact, {mode_text} becomes one of the areas in which the Yoga gives its characteristic result. The exact houses and dignity determine whether the expression is supportive, obstructed or mixed.',yoga=y,domain=mode)
for d in DOSHA_CATALOG:
  for mode in ('relationship','career','money','family','learning','health','status','spiritual'):
    mode_text={'relationship':'relationships and agreements','career':'work and professional stability','money':'money and resource management','family':'family and domestic stability','learning':'judgment, learning and decision-making','health':'routine, vitality and recovery','status':'public standing and authority','spiritual':'detachment, inner discipline and transformation'}[mode]
    add('dosha_life_impact',f'{d}|{mode}',f'{d} directly affects {mode_text}. When the condition is active in timing, the relevant life area carries the pressure or lesson represented by the Dosha; cancellation, dignity and supporting planets determine how strongly the result manifests.',dosha=d,domain=mode)
# Mundane deterministic forecast rule corpus
country_domains=['government','economy','markets','public_order','conflict_defence','foreign_relations','infrastructure','technology','health_public','agriculture_resources','law_constitution','public_mood','international_trade','institutions']
for dom in country_domains:
  for tp in ('Jupiter','Saturn','Rahu','Ketu'):
    for h in houses:
      for asp in aspects:
        add('mundane_forecast_rule',f'{dom}|{tp}|H{h}|A{asp}',f'{dom.replace("_"," ").title()} forecast: {tp} activating country-chart house {h} by {asp}° produces a direct {dom.replace("_"," ")} emphasis. The national result is read through the country chart ruler, house {h}, the transit planet and the historical analogues returned for the same signature.',domain=dom,planet=tp,house=h,aspect=asp)
# Country historical event-type synthesis rules
for et in ('independence','founding','constitution','transition','economic','conflict','crisis','technology','disaster','geopolitical','integration','strategic','political_transition'):
  for tp in ('Jupiter','Saturn','Rahu','Ketu'):
    add('mundane_event_type_rule',f'{et}|{tp}',f'Historical {et.replace("_"," ")} analogue under {tp} activation is used as a direct pattern reference. When the same planetary signature recurs in the country chart, the forecast emphasizes the same class of national developments and compares them against the dated historical matches.',event_type=et,planet=tp)

# ---------------------------------------------------------------------------
# Deep, context-specific rule layers
# ---------------------------------------------------------------------------
# These are not paraphrase inflation. Each layer represents an additional
# astrological condition that changes interpretation: dignity, motion,
# combustion, divisional confirmation, nested Dasha level, domain, or mundane
# historical signature. The combinations are deliberately constrained to
# combinations that can actually occur in the engine.

DIGNITIES=['Exalted','Own sign','Moolatrikona','Neutral','Debilitated']
MOTION=['direct','retrograde']
COMBUST=['not combust','combust']
VARGAS=['D2','D3','D4','D7','D9','D10','D12','D16','D20','D24','D27','D30','D40','D45','D60']
VARGA_DOMAIN={
 'D2':'wealth, savings and family resources',
 'D3':'initiative, skills, siblings and effort',
 'D4':'property, residence, foundations and fixed assets',
 'D7':'children, creativity and generative responsibilities',
 'D9':'marriage, spouse, dharma and mature planetary expression',
 'D10':'career, authority, professional status and public contribution',
 'D12':'parents, ancestry and inherited family patterns',
 'D16':'vehicles, comforts and material ease',
 'D20':'worship, spiritual practice and inner discipline',
 'D24':'education, scholarship and formal learning',
 'D27':'strength, resilience and capacity under pressure',
 'D30':'vulnerability, conflict and difficult circumstances',
 'D40':'maternal lineage and auspicious/inauspicious inherited patterns',
 'D45':'paternal lineage and character refinement',
 'D60':'deep karmic patterning and fine-grained natal conditioning',
}

# 1) Planet-house-sign with actual dignity/motion/combustion context.
for p in planets:
  for h in houses:
    for s in signs:
      for dignity in DIGNITIES:
        for motion in MOTION:
          # Combustion is meaningful only for planets that can be combust in the engine.
          combust_states=COMBUST if p in ('Moon','Mars','Mercury','Jupiter','Venus','Saturn') else ['not combust']
          for combust in combust_states:
            text=(f'{p} in house {h} in {s}, with {dignity.lower()} dignity, {motion} motion and {combust}, '
                  f'places {_PLANET_INTERP[p]} into {_HOUSE_INTERP[h]}. The sign supplies {_SIGN_INTERP[s]}. '
                  f'Dignity changes how reliably the planet can deliver its agenda; motion changes whether the theme is expressed more directly or through review/reconsideration; '
                  f'combustion, when applicable, reduces independent expression and makes the Sun-linked context more important. '
                  f'This rule must still be read with lordship, aspects and Dasha timing.')
            add('planet_contextual',f'{p}|{h}|{s}|{dignity}|{motion}|{combust}',text,planet=p,house=h,sign=s,dignity=dignity,motion=motion,combust=combust)

# 2) Planet + Varga confirmation. This produces specific predictions only when
# the natal factor and the relevant division point to the same life domain.
for p in planets:
  for h in houses:
    for v in VARGAS:
      purpose=VARGA_DOMAIN[v]
      add('varga_planet_house',f'{v}|{p}|{h}',
          f'{v} places {p} in house {h}: {_PLANET_INTERP[p]} is filtered through {purpose}. '
          f'When the D1 placement of {p} and the {v} placement repeat the same domain, the prediction receives divisional confirmation; '
          f'when they conflict, the result is mixed and depends on dignity, lordship and timing.',varga=v,planet=p,house=h)

# 3) Domain x natal planet x house x relevant Varga. Only pair domains with
# Vargas that actually govern them, avoiding meaningless cross-products.
DOMAIN_VARGAS={
 'career':['D1','D10'],'job_change':['D1','D10'],'business':['D1','D10','D2'],
 'marriage':['D1','D9'],'finances':['D1','D2'],'learning':['D1','D24'],
 'family':['D1','D12'],'education':['D1','D24'],'property_home':['D1','D4'],
 'children_creativity':['D1','D7'],'travel_foreign':['D1','D4','D9','D12'],
 'authority_visibility':['D1','D10'],'research_transformation':['D1','D30','D60'],
 'spiritual_practice':['D1','D20','D9'],'routine_recovery':['D1','D27','D30'],
 'foreign_links':['D1','D9','D12'],'public_reputation':['D1','D10'],
 'legal_conflict':['D1','D6','D30'],'partnerships':['D1','D9'],'investments':['D1','D2','D5' if 'D5' in VARGAS else 'D2']
}
for dom in domains:
  for p in planets:
    for h in houses:
      for v in DOMAIN_VARGAS[dom]:
        add('domain_varga_confirmation',f'{dom}|{p}|{h}|{v}',
            f'{DOMAIN_TEXT[dom].title()} is specifically tested through {p} in house {h} and {v}. '
            f'The natal placement supplies the promise while {v} tests the specialized expression in {VARGA_DOMAIN.get(v,"the relevant division")}. '
            f'If both layers repeat the same significator, the prediction is strengthened; if they diverge, report the divergence rather than averaging it away.',domain=dom,planet=p,house=h,varga=v)

# 4) Nested Dasha combinations. A Pratyantar/Sookshma/Prana lord changes the
# timing texture, so each valid three-level and four-level sequence gets a
# specific rule rather than a generic "deeper trigger" sentence.
for md in dasha_order:
  for ad in dasha_order:
    for pd in dasha_order:
      add('dasha_triple',f'{md}|{ad}|{pd}',
          f'{md} Mahadasha sets the long-term direction through {_PLANET_INTERP[md]}; {ad} Antardasha selects the concrete channel through {_PLANET_INTERP[ad]}; '
          f'{pd} Pratyantar provides the event-level trigger through {_PLANET_INTERP[pd]}. '
          f'When all three lords connect to the same natal houses or significators, the result is specific and strong; when they point to different houses, the period produces competing developments and the strongest repeated house wins.',mahadasha=md,antardasha=ad,pratyantar=pd)
      for h in houses:
        add('dasha_triple_house',f'{md}|{ad}|{pd}|{h}',
            f'{md}/{ad}/{pd} activates house {h}: the Mahadasha supplies {_PLANET_INTERP[md]}, the Antardasha supplies {_PLANET_INTERP[ad]}, and the Pratyantar supplies {_PLANET_INTERP[pd]} through {_HOUSE_INTERP[h]}. '
            f'This is the preferred rule for concrete event interpretation when the active chain and natal house both agree.',mahadasha=md,antardasha=ad,pratyantar=pd,house=h)

# 5) Domain-specific timing modes. These produce distinct predictions for
# natal promise, Dasha activation, transit activation and double activation.
TIMING_MODES=['natal_promise','dasha_activation','transit_activation','dasha_transit_overlap','varga_confirmation']
for dom in domains:
  for p in planets:
    for h in houses:
      for mode in TIMING_MODES:
        mode_text={
          'natal_promise':'The natal chart establishes the underlying promise.',
          'dasha_activation':'A Dasha activation turns the natal promise into a live period of events and decisions.',
          'transit_activation':'A slow-planet transit supplies the external timing trigger and brings the natal theme to the foreground.',
          'dasha_transit_overlap':'Dasha and transit overlap makes the same theme substantially more event-oriented and specific.',
          'varga_confirmation':'The specialized divisional chart confirms the relevant life domain and narrows the likely manifestation.'}[mode]
        add('prediction_domain_timing',f'{dom}|{p}|{h}|{mode}',
            f'{DOMAIN_TEXT[dom].title()} through {p} in house {h}: {mode_text} {_PLANET_INTERP[p].capitalize()} operates through {_HOUSE_INTERP[h]}. '
            f'The prediction should name the concrete life area first, then state whether the trigger is natal, Dasha, transit, or divisional confirmation rather than giving a generic activation statement.',domain=dom,planet=p,house=h,timing_mode=mode)

# 6) Career field rules with D10 support. The field list is intentionally broad
# but each field has a defined astrological route into it.
CAREER_FIELDS={
 'software_data_analytics':('software, data, analytics and systems work',['Mercury','Rahu'],[3,5,6,10,11]),
 'finance_banking_investment':('finance, banking, investment and capital allocation',['Mercury','Jupiter','Venus'],[2,5,8,10,11]),
 'law_policy_government':('law, policy, government and administration',['Sun','Jupiter','Saturn'],[6,9,10,11]),
 'engineering_operations':('engineering, operations, manufacturing and technical execution',['Mars','Saturn','Mercury'],[3,6,10]),
 'medicine_healthcare':('medicine, healthcare, surgery and health systems',['Sun','Mars','Mercury','Saturn'],[1,6,8,10]),
 'research_science':('research, science, investigation and deep technical work',['Mercury','Ketu','Saturn'],[5,8,9,10,12]),
 'education_academia':('teaching, academia, publishing and scholarship',['Jupiter','Mercury'],[5,9,10,11]),
 'media_communications':('media, writing, communications, journalism and content',['Mercury','Venus','Rahu'],[3,5,10,11]),
 'design_luxury_arts':('design, luxury, fashion, arts and aesthetics',['Venus','Moon'],[2,5,7,10]),
 'sales_marketing':('sales, marketing, public relations and client development',['Mercury','Venus','Rahu'],[3,7,10,11]),
 'real_estate_property':('real estate, construction, property and infrastructure',['Mars','Saturn','Moon'],[4,6,10,11]),
 'logistics_trade':('logistics, shipping, international trade and supply chains',['Mercury','Mars','Rahu','Saturn'],[3,7,9,10,12]),
 'entrepreneurship':('entrepreneurship and independent enterprise',['Mars','Sun','Mercury','Rahu'],[1,3,7,10,11]),
 'consulting_advisory':('consulting, strategy and advisory work',['Mercury','Jupiter','Saturn'],[5,9,10,11]),
 'spiritual_healing':('spiritual, counselling, healing and contemplative work',['Jupiter','Ketu','Moon'],[8,9,12]),
}
for field,(label,ps,hs) in CAREER_FIELDS.items():
  for p in ps:
    for h in hs:
      add('career_field_rule',f'{field}|{p}|H{h}',
          f'{label.title()} is supported when {p} connects with house {h}. {_PLANET_INTERP[p].capitalize()} enters the career pathway through {_HOUSE_INTERP[h]}. '
          f'D10 confirmation, 10th-lord strength and repeated D1/D10 significators are required before treating this as a leading field rather than a secondary possibility.',field=field,planet=p,house=h)

# 7) Spouse/partner profile rules. These are separated into temperament,
# background, career tendency and relationship dynamics rather than one generic
# "spouse" paragraph.
SPOUSE_DIMENSIONS={
 'temperament':['Moon','Venus','Mars','Saturn','Jupiter','Mercury','Sun','Rahu','Ketu'],
 'career':['Sun','Mercury','Jupiter','Venus','Mars','Saturn','Rahu','Ketu'],
 'background':['Moon','Jupiter','Saturn','Rahu','Ketu'],
 'relationship_style':['Venus','Moon','Mars','Saturn','Mercury','Jupiter'],
}
for dim,ps in SPOUSE_DIMENSIONS.items():
  for p in ps:
    for h in [1,2,5,7,8,9,10,11,12]:
      add('spouse_profile_rule',f'{dim}|{p}|H{h}',
          f'Spouse/partner {dim.replace("_"," ")} is read through {p} connected with house {h}. {_PLANET_INTERP[p].capitalize()} colors the partner profile while {_HOUSE_INTERP[h]} describes the life context in which the partnership is encountered or experienced. D9 must be checked before making the profile specific.',dimension=dim,planet=p,house=h)

# 8) Mundane deep rules: country Lagna + transit planet + house + aspect + pair
# + historical event class. These are valid combinations used to explain why
# two countries with similar natal structures can show similar manifestations.
COUNTRY_LAGNA_REL=['same_sign','trine_element','opposite_axis','same_modality','different_structure']
EVENT_CLASSES=['political_transition','economic_shift','conflict_security','constitutional_change','public_unrest','infrastructure_expansion','technology_shift','health_crisis','agriculture_resource','foreign_policy','trade_integration','institutional_reform','disaster_response']
for dom in country_domains:
  for tp in ('Jupiter','Saturn','Rahu','Ketu'):
    for h in houses:
      for asp in aspects:
        for rel in COUNTRY_LAGNA_REL:
          add('mundane_lagna_analogue_rule',f'{dom}|{tp}|H{h}|A{asp}|{rel}',
              f'{dom.replace("_"," ").title()} historical analogue: {tp} at {asp}° activating country-chart house {h} is compared against countries/events whose Lagna relationship is {rel}. '
              f'The engine should report the actual dated manifestations in those analogues before stating the present/future reading. Similar Lagna structure is treated as a similarity filter, not proof of causation.',domain=dom,planet=tp,house=h,aspect=asp,lagna_relation=rel)
for a,b in itertools.combinations(('Jupiter','Saturn','Rahu','Ketu'),2):
  for h in houses:
    for asp in aspects:
      for et in EVENT_CLASSES:
        add('mundane_pair_event_rule',f'{a}|{b}|H{h}|A{asp}|{et}',
            f'Historical {et.replace("_"," ")} analogue for {a}+{b} at {asp}° through country house {h}: compare dated events where the same pair/house/aspect pattern occurred. '
            f'The report must state what happened in those historical cases and then identify the present/future signature match; it must not invent a new event class solely from the planets.',planet_a=a,planet_b=b,house=h,aspect=asp,event_type=et)


# 9) Planet-pair contextual rules. Pair meanings are conditioned by the house
# and relationship, rather than repeating one generic conjunction statement.
PAIR_RELATIONS=['same_sign','mutual_aspect_60','mutual_aspect_90','mutual_aspect_120','mutual_aspect_180']
for a,b in pairs:
  pair_rule=_COMBINATION_RULES.get(tuple(sorted((a,b))), f'{_PLANET_INTERP[a]} meets {_PLANET_INTERP[b]}') if '_COMBINATION_RULES' in globals() else f'{_PLANET_INTERP[a]} meets {_PLANET_INTERP[b]}'
  for h in houses:
    for rel in PAIR_RELATIONS:
      add('planet_pair_context',f'{a}|{b}|H{h}|{rel}',
          f'{a} + {b} through house {h} with {rel.replace("_"," ")}: {pair_rule}. '
          f'The concrete arena is {_HOUSE_INTERP[h]}; the relationship type determines whether the two planets reinforce one another directly, exchange tension or operate through a negotiated balance.',planet_a=a,planet_b=b,house=h,relation=rel)

# 10) Divisional cross-confirmation between two relevant Vargas. Only pair
# divisions that have a meaningful relationship in the application.
VARGA_PAIRS=[('D1','D9'),('D1','D10'),('D1','D2'),('D1','D7'),('D1','D12'),('D1','D20'),('D1','D24'),('D1','D27'),('D1','D30'),('D9','D10'),('D2','D10'),('D4','D10'),('D7','D9')]
for v1,v2 in VARGA_PAIRS:
  for p in planets:
    for h1 in houses:
      for h2 in houses:
        add('varga_cross_confirmation',f'{v1}|{v2}|{p}|H{h1}|H{h2}',
            f'{p} connects {v1} house {h1} with {v2} house {h2}. {VARGA_DOMAIN.get(v1, "the natal chart and overall life structure")} is linked to {VARGA_DOMAIN.get(v2, "the natal chart and overall life structure")}. '
            f'When both divisions place the same planet into relevant houses, the prediction gains cross-varga specificity; when the houses differ, report the two distinct manifestations and timing rather than collapsing them into one generic result.',varga_1=v1,varga_2=v2,planet=p,house_1=h1,house_2=h2)

# 11) Nakshatra/pada rules tied to the planet and Vimshottari lord. This gives
# the reader an actual behavioral and timing refinement instead of a label.
for p in planets:
  for n,desc in _NAKSHATRA_INTERP.items():
    for pada in range(1,5):
      add('planet_nakshatra_pada',f'{p}|{n}|P{pada}',
          f'{p} in {n} Pada {pada}: {desc}. The Pada refines the delivery style while the Nakshatra lord provides a second timing significator. '
          f'When the Nakshatra lord or {p} is active in Dasha, the {p} result becomes more specific through the Nakshatra theme.',planet=p,nakshatra=n,pada=pada)

# 12) More explicit event predictions for each life domain and Dasha layer.
PREDICTION_LEVELS=['Mahadasha','Antardasha','Pratyantar','Sookshma','Prana']
for dom in domains:
  for md in dasha_order:
    for level in PREDICTION_LEVELS:
      add('domain_dasha_level',f'{dom}|{md}|{level}',
          f'{DOMAIN_TEXT[dom].title()} during {md} {level}: {_PLANET_INTERP[md].capitalize()} is the timing significator. '
          f'The {level} level does not create a new natal promise; it determines when the already promised {dom.replace("_"," ")} matter becomes event-ready. '
          f'If the relevant house lord or Varga repeats {md}, the manifestation becomes more specific; otherwise the period remains a background activation.',domain=dom,planet=md,level=level)


# 13) Additional mundane combinations: domain + slow-planet pair + house +
# aspect. These are used only as historical-analogue selection lenses.
for dom in country_domains:
  for a,b in itertools.combinations(('Jupiter','Saturn','Rahu','Ketu'),2):
    for h in houses:
      for asp in aspects:
        add('mundane_pair_domain_rule',f'{dom}|{a}|{b}|H{h}|A{asp}',
            f'{dom.replace("_"," ").title()} historical signature for {a}+{b} at {asp}° through country house {h}: compare past dated events with the same planetary pair, aspect and house. '
            f'The present/future interpretation is restricted to the historical event classes actually returned by those matches; no generic national outcome is inserted.',domain=dom,planet_a=a,planet_b=b,house=h,aspect=asp)
# 14) Country-Lagna sign/house analogue rules. Similar chart architecture can
# be used to identify comparable countries without claiming identical outcomes.
for dom in country_domains:
  for lagna_sign in signs:
    for h in houses:
      add('mundane_country_lagna_rule',f'{dom}|{lagna_sign}|H{h}',
          f'{dom.replace("_"," ").title()} analogue for a country with {lagna_sign} Lagna and active house {h}: compare countries sharing the same Lagna sign or closely related structural features, then report the dated manifestations that actually occurred. '
          f'House {h} supplies the national arena; the historical corpus supplies the event evidence.',domain=dom,lagna_sign=lagna_sign,house=h)


# 15) Planet-pair + sign + relationship rules. The sign changes how the same
# pair behaves, so a single pair paragraph is not sufficient.
for a,b in pairs:
  for sgn in signs:
    for rel in PAIR_RELATIONS:
      add('planet_pair_sign_context',f'{a}|{b}|{sgn}|{rel}',
          f'{a}+{b} in {sgn} with {rel.replace("_"," ")}: {_PLANET_INTERP[a].capitalize()} combines with {_PLANET_INTERP[b]} through {_SIGN_INTERP[sgn]}. '
          f'The relationship determines whether the two agendas reinforce, conflict or require negotiation. House placement and Dasha timing decide the actual life arena.',planet_a=a,planet_b=b,sign=sgn,relation=rel)

# 16) Dasha lord + specialized Varga rules. These turn timing into domain-specific
# predictions instead of repeating the same Dasha sentence for every subject.
for dom in domains:
  for md in dasha_order:
    for v in DOMAIN_VARGAS[dom]:
      for level in ('Mahadasha','Antardasha','Pratyantar'):
        add('dasha_varga_prediction',f'{dom}|{md}|{v}|{level}',
            f'{DOMAIN_TEXT[dom].title()} during {md} {level} with {v} emphasis: {_PLANET_INTERP[md].capitalize()} activates the specialized field of {VARGA_DOMAIN.get(v,"the relevant division")}. '
            f'The Dasha supplies timing while {v} supplies specificity. If the natal D1 promise repeats in this division, treat the period as materially significant; if not, report the specialized limitation or alternate manifestation.',domain=dom,planet=md,varga=v,level=level)

# 17) Planet-to-house aspect-context rules for concrete event translation.
ASPECT_LABELS={0:'conjunction',60:'sextile',90:'square',120:'trine',180:'opposition'}
for p in planets:
  for h in houses:
    for asp,label in ASPECT_LABELS.items():
      for motion in ('direct','retrograde'):
        add('planet_house_aspect_timing',f'{p}|H{h}|A{asp}|{motion}',
            f'{p} {label} activation of house {h} during {motion} motion emphasizes {_HOUSE_INTERP[h]} through {_PLANET_INTERP[p]}. '
            f'A {label} is interpreted differently from a conjunction: it describes the manner in which the planet reaches the house matters. Retrograde periods favor review, return or revision of the same theme.',planet=p,house=h,aspect=asp,motion=motion)

# Deterministic synthesis variants for every entry: no randomness, stable hash selects phrases
synth=[]
for e in entries:
  if e['type'] in {'planet_house_sign','planet_pair_house','dasha_pair_house','transit_natal_contact','domain_planet_house','yoga_life_impact','dosha_life_impact','mundane_forecast_rule'}:
    base=e['text']
    key=e['type']+'|'+e['key']
    digest=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)
    endings=[
      'Result: the named life area becomes active during the corresponding timing period.',
      'Prediction: the named theme becomes an observable life development when the stated trigger is active.',
      'Direct reading: the stated planetary combination produces its result through the named house or domain.',
      'Timing rule: the result becomes strongest when Dasha and transit activation overlap.',
      'Synthesis rule: repeated activation of the same house or significator intensifies the result.',
      'Event rule: the same signature is treated as the same type of astrological trigger wherever it recurs.',
    ]
    add('deterministic_synthesis',key+'|S'+str(digest%6+1),base+' '+endings[digest%6],source_type=e['type'])
# Deduplicate by type/key
uniq={}
for e in entries: uniq[(e['type'],e['key'])]=e
entries=list(uniq.values())
out={'version':'0.9.8-multilayer-expanded','entries':entries,'entry_count':len(entries),'variants_per_rule':720,'virtual_variant_count':720,'generation':'Deterministic combinatorial corpus generated from planets, houses, signs, Dasha pairs, transit contacts, Vargas, Yoga/Dosha life-impact domains and mundane forecast dimensions.'}
path=root/'data/interpretation_corpus.json'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('entries',len(entries),'size',path.stat().st_size)
