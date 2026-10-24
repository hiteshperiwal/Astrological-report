import json
from datetime import date
from app.engine import BirthData, analyze_birth, nakshatra_details, sign_index, vimshottari_dasha


def test_nakshatra_boundaries():
    assert nakshatra_details(0)['name'] == 'Ashwini'
    assert nakshatra_details(13.3334)['name'] == 'Bharani'


def test_sign_index_wraps():
    assert sign_index(0) == 0
    assert sign_index(359.999) == 11


def test_chart_generation():
    b = BirthData('Test', date(1990,1,1), '12:00:00', 22.5726, 88.3639, 'Asia/Kolkata', 'Kolkata')
    chart = analyze_birth(b, 1)
    assert chart['lagna_sign'] in {'Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'}
    assert set(chart['planets']) >= {'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'}
    assert len(chart['divisional_charts']) == 16
    assert len(chart['dashas']['periods']) >= 1
    assert 'sahams' in chart
    assert 'ashtakavarga' in chart


def test_dasha_has_nested_children():
    d = vimshottari_dasha(123.0, BirthData('T',date(2000,1,1),'10:00',0,0,'UTC').local_dt, 1, levels=5)
    assert d['periods'][0]['children']
    assert d['periods'][0]['children'][0]['children']

def test_forecast_is_upcoming_and_has_performance_profile():
    b = BirthData('Test', date(1990,1,1), '12:00:00', 22.5726, 88.3639, 'Asia/Kolkata', 'Kolkata')
    chart = analyze_birth(b, 1)
    assert chart['forecast']['years'] == 1
    assert chart['transits'][0]['date'] == chart['forecast']['start']
    assert len(chart['performance']['monthly']) == len(chart['transits'])
    assert set(chart['performance']['domains']) >= {'career','finances','marriage','family','learning','wellness','inner_growth'}
    assert all(0 <= r['career'] <= 100 for r in chart['performance']['monthly'])


def test_mundane_country_only_workflow():
    from app.mundane import analyze_country, search_historical_patterns, scan_mundane_forecast
    analysis = analyze_country('India')
    assert analysis['country'] == 'India'
    assert analysis['event']['event_name'] == 'Independence of India'
    hist = search_historical_patterns('India', limit=20)
    assert hist['corpus_size'] >= 20
    assert isinstance(hist['results'], list)
    forecast = scan_mundane_forecast('India', near_years=1, long_years=3)
    assert forecast['near_term']['monthly']
    assert forecast['long_term']['monthly']
    assert all(0 <= x['activation'] <= 100 for x in forecast['near_term']['monthly'])
    assert forecast['near_term']['monthly'][0]['global_historical_analogues']

def test_mundane_country_aliases():
    from app.mundane import analyze_country
    assert analyze_country('USA')['country'] == 'United States'


def test_extended_kundali_features_and_dynamic_horizon():
    from app.engine import BirthData, analyze_birth
    b=BirthData('T',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=30,forecast_unit='days')
    assert len(c['divisional_charts']) == 16
    assert isinstance(c['divisional_charts']['D9']['lagna_sign'], str)
    assert c['nakshatra_analysis']['moon']['pada'] in {1,2,3,4}
    assert len(c['chara_karakas']['karakas']) == 7
    assert len(c['arudha_padas']) == 12
    assert len(c['planet_strengths']['planets']) >= 9
    assert c['forecast']['unit'] == 'days'
    assert c['forecast']['granularity'] == 'daily'
    assert len(c['transits']) >= 30


def test_api_workspaces_are_independent():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    personal=client.post('/api/personal/analyze',json={'name':'T','dob':'1990-01-01','tob':'12:00:00','place':'Kolkata','latitude':22.5726,'longitude':88.3639,'timezone':'Asia/Kolkata','forecast_amount':2,'forecast_unit':'months'})
    mundane=client.post('/api/mundane/analyze',json={'country':'India','near_term_amount':2,'near_term_unit':'months','long_term_amount':2,'long_term_unit':'years'})
    assert personal.status_code == 200 and mundane.status_code == 200
    assert 'divisional_charts' in personal.json()['chart']
    assert 'country_chart' in mundane.json()['forecast']
    assert 'country_chart' not in personal.json()['chart']


def test_reference_library_profile_is_time_uncertain_when_unknown():
    from app.master_data import get_person
    p=get_person('Narendra Modi')
    assert p['dob']=='1950-09-17'
    assert p['time_status']=='unknown'

def test_yoga_catalog_and_fruitification():
    b=BirthData('Test Native',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=2,forecast_unit='years')
    assert c['yoga_catalog']['catalog_size'] >= 90
    assert isinstance(c['yogas'], list)
    assert all('fruitification' in y for y in c['yogas'])


def test_numerology_profile_is_deterministic():
    b=BirthData('Asha Example',date(1988,4,12),'09:15:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    n=c['numerology']
    assert n['core']['life_path'] == 33
    assert n['core']['destiny_expression'] > 0
    assert len(n['personal_years']) >= 1
    assert set(n['pinnacles']) == {'first','second','third','fourth'}


def test_mundane_backtest_is_reproducible():
    from app.backtest import retrospective_mundane_backtest
    a=retrospective_mundane_backtest(limit=10,window_days=7)
    b=retrospective_mundane_backtest(limit=10,window_days=7)
    assert a['events_tested']==10
    assert a['coverage_pct']==b['coverage_pct']


def test_pdf_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    personal={'name':'T','dob':'1990-01-01','tob':'12:00:00','place':'Kolkata','latitude':22.5726,'longitude':88.3639,'timezone':'Asia/Kolkata','forecast_amount':1,'forecast_unit':'years'}
    mundane={'country':'India','historical_limit':10,'near_term_amount':1,'near_term_unit':'years','long_term_amount':2,'long_term_unit':'years'}
    p=client.post('/api/personal/report.pdf',json=personal)
    m=client.post('/api/mundane/report.pdf',json=mundane)
    assert p.status_code==200 and p.content[:4]==b'%PDF'
    assert m.status_code==200 and m.content[:4]==b'%PDF'


def test_advanced_timing_and_astronomical_calendar():
    from app.engine import BirthData, analyze_birth
    b=BirthData('Advanced',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years',school='synthesis')
    assert set(c['shadbala']['planets']) == {'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'}
    assert len(c['ashtakavarga_classical']['sav']) == 12
    assert c['ashtakavarga_classical']['shodhya_pinda']['rasi_pinda'] >= 0
    assert c['advanced_timing']['chara_dasha']['periods']
    assert c['advanced_timing']['ashtottari']['periods']
    assert c['advanced_timing']['yogini']['periods']
    assert c['advanced_timing']['narayana']['periods']
    assert c['advanced_timing']['kalachakra']['periods']
    assert isinstance(c['exact_astronomical_events']['events'], list)
    assert isinstance(c['eclipses']['events'], list)
    assert c['tajaka']['years']


def test_mundane_corpus_and_walk_forward_validation():
    from app.mundane import available_countries, analyze_country
    from app.validation import mundane_walk_forward_backtest
    assert len(available_countries()) >= 25
    assert analyze_country('Canada')['country'] == 'Canada'
    result=mundane_walk_forward_backtest(window_days=5, threshold=40)
    assert result['events_tested'] > 20
    assert 0 <= result['coverage_pct'] <= 100
    assert 'mean_control_signal' in result

def test_runtime_interpretation_layers_are_populated():
    from app.report import generate_narrative
    b=BirthData('Interpretation Test',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=6,forecast_unit='months')
    n=generate_narrative(c)
    assert len(n['interpretations']['divisional']) == 16
    assert len(n['interpretations']['pada']) >= 9
    assert n['interpretations']['reference_corpus']['entries'] >= 1500
    assert n['forecast_interpretations']['weekly']
    assert n['forecast_interpretations']['monthly']
    assert n['forecast_interpretations']['yearly']
    assert 'career_options' in n and n['career_options']
    assert 'marriage_timing' in n and 'windows' in n['marriage_timing']
    assert 'job_change_timing' in n and 'windows' in n['job_change_timing']
    assert 'business_timing' in n and 'windows' in n['business_timing']


def test_interpretation_corpus_is_expanded():
    import json
    from pathlib import Path
    p=Path(__file__).resolve().parent.parent/'data'/'interpretation_corpus.json'
    data=json.loads(p.read_text(encoding='utf-8'))
    assert len(data['entries']) >= 4740

def test_divisional_planets_match_whole_sign_houses():
    from app.engine import BirthData, analyze_birth
    from datetime import date
    b=BirthData('Test',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    for v in c['divisional_charts'].values():
        for d in v['planets'].values():
            assert d['house']==((d['sign_index']-v['lagna_sign_index'])%12)+1

def test_v08_yoga_transit_dasha_and_ai_layers():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _RUNTIME_CORPUS
    b=BirthData('V08',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur')
    c=analyze_birth(b,forecast_amount=2,forecast_unit='years')
    assert len(_RUNTIME_CORPUS) * 90 >= 426600
    assert len(c['yogas']) >= 5
    assert c['current_transits']['planets']['Jupiter']['sign']
    n=generate_narrative(c)
    ctx=n['interpretations']['dasha_context']
    assert ctx['current_mahadasha']
    assert ctx['next_mahadashas']
    assert ctx['current_hierarchy']
    assert n['interpretations']['transit_interpretations']['current']
    assert 'disclaimer' in n


def test_yoga_fruitification_uses_real_transit_dates_and_at_most_five():
    from app.engine import analyze_birth
    from app.schemas import BirthRequest
    from datetime import date, time
    from app.engine import BirthData
    b=BirthData(name='Test',dob=date(2001,2,6),tob='17:57:00',latitude=28.8777942,longitude=74.0633619,timezone='Asia/Kolkata',place='Jaipur, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    for y in c['yogas']:
        assert len(y.get('fruitification',{}).get('possible_dates',[])) <= 5
        for row in y.get('fruitification',{}).get('possible_dates',[]):
            assert any(t.get('date')==row.get('date') for t in (c.get('forecast_layers',{}).get('weekly') or c.get('transits',[])))


def test_transit_rows_have_nakshatra_pada():
    from app.engine import analyze_birth, BirthData
    from datetime import date, time
    b=BirthData(name='Test',dob=date(2001,2,6),tob='17:57:00',latitude=28.8777942,longitude=74.0633619,timezone='Asia/Kolkata',place='Jaipur, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    assert c['transits']
    for p in ('Jupiter','Saturn','Rahu','Ketu'):
        assert c['transits'][0]['transit_nakshatra'][p].get('name')
        assert 1 <= c['transits'][0]['transit_nakshatra'][p]['pada'] <= 4


def test_interpretation_depth_features():
    from app.report import generate_narrative
    from app.engine import BirthData, analyze_birth
    from datetime import date
    b=BirthData('Depth Test',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years',school='synthesis')
    n=generate_narrative(c)
    i=n['interpretations']
    assert i['dasha_interpretations']
    assert 'gemstone_recommendations' in i
    assert 'dosha_interpretations' in i
    assert len(i['transit_interpretations']['current']) == 4
    assert all(x.get('house') is not None for x in i['transit_interpretations']['current'])


def test_chat_intent_routing_is_targeted_and_has_no_none_labels():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _interpretation_chat
    from datetime import date
    b=BirthData('Chat Test',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=5,forecast_unit='years',school='synthesis')
    n=generate_narrative(c)
    d9=_interpretation_chat(c,n,'What does my D9 say about marriage and relationship timing?')
    assert 'D9 Navamsha' in d9 and 'None' not in d9
    dasha=_interpretation_chat(c,n,'What is my current Pratyantar Dasha?')
    assert 'Pratyantar Dasha' in dasha and 'None' not in dasha
    assert 'Jupiter Mahadasha sets the broad life chapter' not in dasha
    yoga=_interpretation_chat(c,n,'What are my applicable Yogas and when can they fruitify?')
    assert 'Applicable Yogas found in this chart' in yoga
    assert 'None' not in yoga

def test_yoga_interpretations_are_person_specific_and_chat_grounded():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _interpretation_chat
    b=BirthData('Hitesh',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Lunkaransar Tehsil, Bikaner, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=2,forecast_unit='years')
    n=generate_narrative(c)
    rows=n['interpretations']['yoga_interpretations']
    assert rows
    assert all(x.get('interpretation') and x.get('life_impact') for x in rows)
    assert any('house' in x['interpretation'].lower() for x in rows)
    ans=_interpretation_chat(c,n,'What are my applicable yogas and what impact will they have in my life?')
    assert 'Applicable Yogas' in ans
    assert any(y['name'] in ans for y in rows)
    assert 'planet other than' not in ans.lower() or 'meaning' in ans.lower()

def test_d9_chat_returns_actual_d9_not_generic_fallback():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _interpretation_chat
    b=BirthData('Hitesh',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Lunkaransar Tehsil, Bikaner, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=2,forecast_unit='years')
    n=generate_narrative(c)
    ans=_interpretation_chat(c,n,'What does my D9 say about marriage?')
    assert 'D9 Navamsha' in ans
    assert c['divisional_charts']['D9']['lagna_sign'] in ans

def test_chat_api_returns_person_specific_yoga_interpretation():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    payload={'question':'What are my applicable yogas and what impact will they have in my life?','birth':{'name':'Hitesh','dob':'2001-02-06','tob':'17:57:00','place':'Jaipur, Rajasthan, India','latitude':28.8777942,'longitude':74.0633619,'timezone':'Asia/Kolkata','forecast_amount':2,'forecast_unit':'years'}}
    r=client.post('/api/personal/chat',json=payload)
    assert r.status_code==200
    text=' '.join(r.json().get('message',[]) if isinstance(r.json().get('message'),list) else [r.json().get('message','')])
    assert 'Applicable Yogas found in this chart' in text
    assert 'For this person' in text
    assert 'house' in text.lower()

def test_yoga_chat_has_no_repeated_grammar_phrase():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _interpretation_chat
    b=BirthData('Hitesh',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    n=generate_narrative(c)
    ans=_interpretation_chat(c,n,'What are my yogas and their impact?')
    assert 'can manifest as this can make' not in ans.lower()
    assert 'practical impact is:' in ans.lower()


def test_v085_predictions_respect_selected_horizon_and_use_advanced_layers():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _VIRTUAL_VARIANTS_PER_RULE, _VIRTUAL_LENSES
    from datetime import date
    b=BirthData('Prediction Test',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur')
    c=analyze_birth(b,forecast_amount=6,forecast_unit='months',forecast_granularity='weekly',school='synthesis')
    n=generate_narrative(c)
    p=n['predictions']
    assert p['granularity']=='weekly'
    assert p['count']==len(c['forecast_layers']['weekly'])
    assert p['methods'] and 'Vimshottari Dasha hierarchy' in p['methods']
    assert 'Classical Ashtakavarga SAV context' in p['methods']
    assert 'Sudarshana Chakra three-reference screen' in p['methods']
    assert all(x.get('dasha') for x in p['predictions'])
    assert all('Jupiter' in x.get('transit_houses',{}) for x in p['predictions'])
    assert all(x.get('transit_nakshatra',{}).get('Jupiter') for x in p['predictions'])
    assert all('alternative_dashas' in x and 'tajaka' in x for x in p['predictions'])
    assert _VIRTUAL_VARIANTS_PER_RULE==720
    assert len(_VIRTUAL_LENSES)>=180
    assert n['interpretations']['reference_corpus']['entries'] >= 853200

def test_v085_prediction_chat_returns_prediction_layer():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative, _interpretation_chat
    from datetime import date
    b=BirthData('Prediction Chat',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur')
    c=analyze_birth(b,forecast_amount=3,forecast_unit='months',forecast_granularity='monthly')
    n=generate_narrative(c)
    ans=_interpretation_chat(c,n,'What are my predictions for the future?')
    assert 'prediction section' in ans.lower()
    assert c['forecast']['start'] in ans
    assert 'Vimshottari' in ans

def test_v085_local_chat_returns_text_field():
    from app.ai_interpreter import generate_ai_chat
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative
    from datetime import date
    b=BirthData('Chat Text',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='months',forecast_granularity='monthly')
    n=generate_narrative(c)
    r=generate_ai_chat(c,n,'What are my predictions for the future?')
    assert r['status']=='local'
    assert r.get('text')
    assert r.get('message')==r.get('text')


def test_reference_library_expanded_to_200_plus_profiles():
    from app.master_data import search_people, get_person
    rows=search_people()
    assert len(rows) >= 210
    assert len({p["name"] for p in rows}) == len(rows)
    assert get_person("Barack Obama")["dob"] == "1961-08-04"
    assert get_person("Lionel Messi")["category"] == "sport"

def test_reference_profile_analysis_uses_same_chart_pipeline():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    r=client.post('/api/library/analyze',json={'name':'Barack Obama','forecast_amount':1,'forecast_unit':'years','school':'synthesis'})
    assert r.status_code == 200
    d=r.json()
    assert d['profile']['name']=='Barack Obama'
    assert 'divisional_charts' in d['chart'] and len(d['chart']['divisional_charts'])==16
    assert 'interpretations' in d['narrative']

def test_mundane_country_corpus_expanded():
    from app.mundane import available_countries, analyze_country
    assert len(available_countries()) >= 79
    assert analyze_country('Portugal')['country']=='Portugal'
    assert analyze_country('Nepal')['country']=='Nepal'

def test_world_event_sync_parser_reaches_1000_with_fixture(tmp_path, monkeypatch):
    import scripts.sync_world_events as sync
    lines=[]
    for i in range(1200):
        year=1800 + (i//12)
        month=(i%12)+1
        day=(i%27)+1
        lines.append(f"{year}\t1\t{sync.MONTHS.keys().__iter__().__next__()} {day}\tFixture world event {i}")
    # Replace the month helper with a deterministic month name for each row.
    lines=[]
    names=list(sync.MONTHS)
    for i in range(1200):
        year=1800+(i//12); month=names[i%12]; day=(i%27)+1
        lines.append(f"{year}\t1\t{month} {day}\tFixture world event {i}")
    class Resp:
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def read(self): return ('\n'.join(lines)).encode()
    monkeypatch.setattr(sync,'urlopen',lambda *a,**k: Resp())
    monkeypatch.setattr(sync,'OUT',tmp_path/'world_historical_events.json')
    n=sync.parse(1000)
    assert n==1000
    data=json.loads((tmp_path/'world_historical_events.json').read_text())
    assert len(data)==1000 and data[0]['country']=='World'


def test_dasha_context_has_two_previous_three_next_and_deep_active_chain():
    from datetime import date
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative
    b=BirthData('Dasha Scope',date(1990,8,15),'10:30:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    n=generate_narrative(c)
    ctx=n['interpretations']['dasha_context']
    assert len(ctx['selected_mahadashas']) == 6
    assert len(ctx['previous_mahadashas']) == 2
    assert len(ctx['next_mahadashas']) == 3
    assert all(len(x.get('children',[])) == 9 for x in ctx['selected_mahadashas'])
    assert len(ctx['current_hierarchy']) >= 5


def test_mundane_forecast_uses_array_rows_for_india():
    from app.mundane import scan_mundane_forecast
    result=scan_mundane_forecast('India',2,2,'months','years')
    assert isinstance(result['near_term']['monthly'], list)
    assert isinstance(result['long_term']['monthly'], list)
    assert len(result['near_term']['monthly']) > 0


def test_deterministic_expanded_interpretation_corpus_and_combinations():
    import json
    from pathlib import Path
    from datetime import date
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative
    data=json.loads((Path(__file__).resolve().parent.parent/'data'/'interpretation_corpus.json').read_text())
    assert len(data['entries']) >= 30000
    assert data['variants_per_rule'] >= 180
    b=BirthData('Expanded',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=2,forecast_unit='months')
    n1=generate_narrative(c)['interpretations']
    n2=generate_narrative(c)['interpretations']
    assert n1['combination_interpretations']==n2['combination_interpretations']
    assert n1['reference_corpus']['rule_counts_by_type']['deterministic_synthesis'] > 10000


def test_mundane_forecast_rows_expose_event_classification():
    from app.mundane import scan_mundane_forecast
    result=scan_mundane_forecast('India',2,2,'months','years')
    row=result['near_term']['monthly'][0]
    assert row['prediction_mode']=='astrological-event-classification'
    assert row['signal_level'] in ('low','moderate','high')
    assert row['blunt_interpretation']
    assert row['global_historical_analogues']

def test_parashari_varga_boundary_matrix():
    from app.engine import _varga_sign

    # D9: Taurus (fixed) starts from Capricorn; each Navamsha advances one sign.
    assert _varga_sign(30.0 + 0.0, 9) == 9       # 0° Taurus -> Capricorn
    assert _varga_sign(30.0 + 3.33334, 9) == 10  # 3°20' Taurus -> Aquarius
    assert _varga_sign(30.0 + 26.66667, 9) == 5  # 26°40' Taurus -> Virgo

    # D30: unequal classical bands; Cancer is even.
    assert _varga_sign(90.0 + 2.0, 30) == 6    # Venus -> Libra
    assert _varga_sign(90.0 + 7.0, 30) == 5    # Mercury -> Virgo
    assert _varga_sign(90.0 + 15.0, 30) == 11   # Jupiter -> Pisces
    assert _varga_sign(90.0 + 22.0, 30) == 9    # Saturn -> Capricorn
    assert _varga_sign(90.0 + 27.0, 30) == 7    # Mars -> Scorpio

    # D30 odd sign: Gemini.
    assert _varga_sign(60.0 + 2.0, 30) == 0     # Mars -> Aries
    assert _varga_sign(60.0 + 7.0, 30) == 10    # Saturn -> Aquarius
    assert _varga_sign(60.0 + 15.0, 30) == 8    # Jupiter -> Sagittarius
    assert _varga_sign(60.0 + 22.0, 30) == 2    # Mercury -> Gemini
    assert _varga_sign(60.0 + 27.0, 30) == 6    # Venus -> Libra

    # D60: one sign per 0.5°; sign mapping advances from natal sign.
    assert _varga_sign(0.0, 60) == 0
    assert _varga_sign(0.5, 60) == 1
    assert _varga_sign(5.9, 60) == 11
    assert _varga_sign(6.0, 60) == 0


def test_corrected_parashari_varga_mappings():
    from app.engine import _varga_sign
    # 15° Taurus is the 5th Navamsha of a fixed sign: Capricorn -> Taurus.
    assert _varga_sign(45.0, 9) == 1
    # 15° Taurus is the 5th D16 division: Leo -> Sagittarius.
    assert _varga_sign(45.0, 16) == 0
    # 15° Taurus is the 11th D20 division: Sagittarius -> Leo.
    assert _varga_sign(45.0, 20) == 6
    # 15° Gemini is an airy D27 sign: Libra + 14th part wraps to Scorpio.
    assert _varga_sign(75.0, 27) == 7
    # 15° Taurus D40 is counted from Libra, not from the natal sign.
    assert _varga_sign(45.0, 40) == 2
    # D60 sign remapping counts forward from the natal sign for both parities.
    assert _varga_sign(31.0, 60) == 3


def test_expanded_personal_predictions_include_varga_evidence():
    from app.report import generate_narrative
    b=BirthData('Varga Prediction Test',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=3,forecast_unit='months')
    n=generate_narrative(c)
    assert n['spouse_profile']['reading']
    assert n['career_fields']
    assert any(x.get('divisional_evidence') for x in n['predictions']['predictions'])


def test_numerology_expanded_layers():
    b=BirthData('Asha Example',date(1988,4,12),'09:15:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    n=c['numerology']
    assert 'name_analysis' in n
    assert 'karmic_lessons' in n['name_analysis']
    assert 'planes_of_expression' in n['name_analysis']
    assert len(n['number_meanings']) == 9
    assert set(n['long_cycles']) == {'formative','productive','mature'}


def test_mundane_forecast_exposes_specific_event_indications():
    from app.mundane import scan_mundane_forecast
    f=scan_mundane_forecast('India',near_amount=2,near_unit='months',long_amount=1,long_unit='years')
    rows=f['near_term']['monthly']
    assert rows
    for r in rows:
        assert r['prediction_mode']=='astrological-event-classification'
        assert 'event_indications' in r
        assert r['global_historical_analogues']


def test_hitesh_d9_regression_saturn_in_first_house():
    from app.engine import BirthData, analyze_birth
    from datetime import date
    b=BirthData('Hitesh',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Lunkaransar Tehsil, Bikaner, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    d9=c['divisional_charts']['D9']
    assert d9['lagna_sign'] == 'Capricorn'
    assert d9['planets']['Saturn']['sign'] == 'Capricorn'
    assert d9['planets']['Saturn']['house'] == 1
    # Exact natal Saturn longitude is ~0°20' Taurus sidereal, which falls in
    # Capricorn Navamsha under the project's declared Parashari mapping.
    assert abs(c['planets']['Saturn']['longitude'] - 30.3390029752) < 1e-6

def test_hitesh_all_vargas_keep_d9_and_valid_house_assignments():
    from app.engine import BirthData, analyze_birth
    from datetime import date
    b=BirthData('Hitesh',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur, Lunkaransar Tehsil, Bikaner, Rajasthan, India')
    c=analyze_birth(b,forecast_amount=1,forecast_unit='years')
    expected={'D1','D2','D3','D4','D7','D9','D10','D12','D16','D20','D24','D27','D30','D40','D45','D60'}
    assert set(c['divisional_charts']) == expected
    for key,v in c['divisional_charts'].items():
        assert v['lagna_sign']
        assert all(1 <= int(d['house']) <= 12 for d in v['planets'].values())


def test_report_dasha_subperiods_start_with_parent_lord():
    from app.report import _dasha_context
    from datetime import datetime, timezone, timedelta
    now=datetime.now(timezone.utc)
    chart={'current_transits':{'datetime':now.isoformat()},'dashas':{'mahadasha_timeline':[{'lord':'Saturn','start':(now-timedelta(days=1)).isoformat(),'end':(now+timedelta(days=1)).isoformat()}]}}
    ctx=_dasha_context(chart,before=0,after=0)
    assert [x['lord'] for x in ctx['current_mahadasha']['children'][:3]] == ['Saturn','Mercury','Ketu']


def test_mundane_country_has_expanded_interpretation_corpus():
    from app.mundane import analyze_country
    a=analyze_country('India')
    assert a['interpretation_corpus']['mundane_rule_count'] >= 30000


def test_v097_mundane_event_combination_corpus_is_multifold():
    from app.mundane import _mundane_event_combinations, MUNDANE_EVENT_CLASSES
    assert len(MUNDANE_EVENT_CLASSES) >= 25
    assert len(_mundane_event_combinations) >= 10000
    labels={x['id'] for x in MUNDANE_EVENT_CLASSES}
    assert {'aviation_incident','terror_attack','border_clash','market_shock'} <= labels


def test_v097_mundane_event_indications_have_specificity():
    from app.mundane import scan_mundane_forecast
    f=scan_mundane_forecast('India',near_amount=3,near_unit='months',long_amount=1,long_unit='months')
    rows=f['near_term']['monthly']
    assert rows
    assert f['event_class_count'] >= 25
    assert f['event_combination_rule_count'] >= 10000
    assert all('event_indications' in r for r in rows)


def test_v096_multilayer_corpus_has_specific_context_rules():
    from app.report import _RUNTIME_CORPUS, _VIRTUAL_VARIANTS_PER_RULE
    types={x.get('type') for x in _RUNTIME_CORPUS}
    assert len(_RUNTIME_CORPUS) >= 100000
    assert _VIRTUAL_VARIANTS_PER_RULE >= 720
    for required in ('planet_contextual','dasha_triple','domain_varga_confirmation','career_field_rule','spouse_profile_rule','planet_pair_sign_context','dasha_varga_prediction','prediction_domain_timing'):
        assert required in types


def test_v096_predictions_expose_deep_rule_synthesis():
    from app.engine import BirthData, analyze_birth
    from app.report import generate_narrative
    from datetime import date
    b=BirthData('Deep Prediction',date(2001,2,6),'17:57:00',28.8777942,74.0633619,'Asia/Kolkata','Jaipur')
    c=analyze_birth(b,forecast_amount=3,forecast_unit='months',forecast_granularity='monthly',school='synthesis')
    n=generate_narrative(c)
    rows=n['predictions']['predictions']
    assert rows
    assert all('deep_rules' in r for r in rows)


def test_v096_mundane_rows_expose_deep_historical_interpretation():
    from app.mundane import scan_mundane_forecast
    f=scan_mundane_forecast('India',near_amount=1,near_unit='months',long_amount=1,long_unit='months')
    rows=f['near_term']['monthly']
    assert rows
    assert all('historical_evidence' in r and 'deep_interpretation' in r for r in rows)

def test_mundane_positive_event_catalog_includes_science_and_sport():
    from app.mundane import MUNDANE_EVENT_CLASSES, _mundane_event_combinations
    ids = {x['id'] for x in MUNDANE_EVENT_CLASSES}
    assert 'exceptional_scientific_discovery' in ids
    assert 'major_sports_victory' in ids
    assert 'sporting_record' in ids
    assert 'space_mission_success' in ids
    assert 'economic_expansion' in ids
    assert 'diplomatic_breakthrough' in ids
    assert len(_mundane_event_combinations) > 20000


def test_mundane_positive_event_indications_are_explicit():
    from app.mundane import _mundane_event_indications
    planets = ['Jupiter','Mercury','Uranus','Sun','Mars','Venus','Moon','Saturn','Rahu','Ketu']
    natal = {p: {'sign_index': 0} for p in planets}
    transit = {p: {'sign_index': 0} for p in planets}
    rows = _mundane_event_indications(
        ['Jupiter 0 Mercury', 'Mercury 0 Jupiter', 'Uranus 120 Mercury'],
        natal,
        transit,
        {'sign_index': 0},
        []
    )
    positive = [x for x in rows if x.get('polarity') == 'positive']
    assert positive
    assert all('Positive astrological indication' in x['reading'] for x in positive)


def test_ashtakavarga_canonical_totals_and_planetwise_shodhana_are_exposed():
    from app.advanced import classical_ashtakavarga
    signs={'Sun':0,'Moon':3,'Mars':6,'Mercury':2,'Jupiter':8,'Venus':10,'Saturn':4,'Rahu':1,'Ketu':7}
    planets={p:{'longitude':s*30+1} for p,s in signs.items()}
    result=classical_ashtakavarga(planets,9)
    assert result['validation']['sav_total_pass'] is True
    assert result['validation']['actual_sav_total']==337
    assert set(result['trikona_shodhana'])=={'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'}
    assert set(result['ekadhipatya_shodhana'])==set(result['bav'])
    assert set(result['shodhya_pinda']['per_planet'])==set(result['bav'])
    for item in result['shodhya_pinda']['per_planet'].values():
        assert item['rasi_pinda']>=0 and item['graha_pinda']>=0
        assert item['shodhya_pinda']==item['rasi_pinda']+item['graha_pinda']


def test_shadbala_screen_never_claims_canonical_accuracy():
    from app.advanced import shadbala
    from app.engine import BirthData, analyze_birth
    from datetime import date
    birth=BirthData('Strength fixture',date(1990,1,1),'12:00:00',22.5726,88.3639,'Asia/Kolkata','Kolkata')
    chart=analyze_birth(birth,forecast_amount=1,forecast_unit='months')
    result=chart['shadbala']
    assert 'not a complete canonical' in result['method']
    assert all(p in result['planets'] for p in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'))
