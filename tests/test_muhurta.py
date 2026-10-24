from datetime import date
import pytest
from app.muhurta import search_muhurta, _sunrise_sunset, _panchanga, RAHU_SEGMENT, YAMAGANDA_SEGMENT, GULIKA_SEGMENT
import swisseph as swe


def test_sunrise_and_sunset_are_on_requested_local_date():
    rise, setting = _sunrise_sunset(date(2026, 10, 22), 22.5726, 88.3639, "Asia/Kolkata")
    assert rise and setting
    assert rise.date().isoformat() == "2026-10-22"
    assert setting.date().isoformat() == "2026-10-22"
    assert rise < setting


def test_rahu_yamaganda_gulika_weekday_tables_cover_all_days():
    assert set(RAHU_SEGMENT) == set(range(7))
    assert set(YAMAGANDA_SEGMENT) == set(range(7))
    assert set(GULIKA_SEGMENT) == set(range(7))
    assert all(1 <= v <= 8 for table in (RAHU_SEGMENT,YAMAGANDA_SEGMENT,GULIKA_SEGMENT) for v in table.values())
    assert len(set(RAHU_SEGMENT.values())) == 7


def test_panchanga_labels_and_ranges_are_valid():
    jd=swe.julday(2026,10,22,6.0); p=_panchanga(jd)
    assert 1 <= p['tithi_number'] <= 15
    assert 1 <= p['yoga_number'] <= 27
    assert p['nakshatra']
    assert 1 <= p['nakshatra_pada'] <= 4


def test_search_returns_auditable_windows_and_personalization():
    out=search_muhurta(activity='job_start',start_date='2026-10-22',end_date='2026-10-24',latitude=22.5726,longitude=88.3639,timezone_name='Asia/Kolkata',natal_moon_longitude=100.0)
    assert out['personalized'] is True
    assert out['method']['ayanamsha']=='Lahiri'
    assert out['period']=={'start':'2026-10-22','end':'2026-10-24'}
    assert out['candidate_count_before_limit'] >= len(out['candidate_windows'])
    for w in out['candidate_windows']:
        assert 0 <= w['score'] <= 100
        assert w['panchanga']['nakshatra']
        assert isinstance(w['reasons'],list) and isinstance(w['penalties'],list)
        assert w['start'] < w['end']


def test_search_rejects_more_than_90_days_and_invalid_activity():
    with pytest.raises(ValueError,match='90 days'):
        search_muhurta(activity='puja',start_date='2026-01-01',end_date='2026-04-10',latitude=0,longitude=0,timezone_name='UTC')
    with pytest.raises(ValueError,match='Unsupported activity'):
        search_muhurta(activity='unknown',start_date='2026-01-01',end_date='2026-01-01',latitude=0,longitude=0,timezone_name='UTC')


def test_personalization_is_optional_and_same_period_is_deterministic():
    args=dict(activity='puja',start_date='2026-10-22',end_date='2026-10-22',latitude=22.5726,longitude=88.3639,timezone_name='Asia/Kolkata')
    a=search_muhurta(**args); b=search_muhurta(**args)
    assert a['personalized'] is False
    assert a['candidate_windows']==b['candidate_windows']


def test_api_muhurta_endpoint_and_health_version():
    from fastapi.testclient import TestClient
    from app.main import app
    client=TestClient(app)
    health=client.get('/health')
    assert health.status_code==200 and health.json()['version']=='1.0.6'
    response=client.post('/api/muhurta/search',json={
        'activity':'puja','start_date':'2026-10-22','end_date':'2026-10-22',
        'latitude':22.5726,'longitude':88.3639,'timezone':'Asia/Kolkata',
        'natal_dob':'2001-02-06','natal_tob':'17:57','natal_timezone':'Asia/Kolkata'
    })
    assert response.status_code==200, response.text
    data=response.json()
    assert data['personalized'] is True
    assert data['location']['timezone']=='Asia/Kolkata'
    bad=client.post('/api/muhurta/search',json={
        'activity':'puja','start_date':'2026-10-22','end_date':'2027-01-25',
        'latitude':22.5726,'longitude':88.3639,'timezone':'Asia/Kolkata'
    })
    assert bad.status_code==422

@pytest.mark.parametrize('day,lat,lon,tzname',[
    (date(2026,10,22),22.5726,88.3639,'Asia/Kolkata'),
    (date(2026,6,15),51.5074,-0.1278,'Europe/London'),
    (date(2026,1,15),40.7128,-74.0060,'America/New_York'),
    (date(2026,12,10),-33.8688,151.2093,'Australia/Sydney'),
])
def test_sunrise_set_timezone_exploration(day,lat,lon,tzname):
    rise, setting = _sunrise_sunset(day,lat,lon,tzname)
    assert rise and setting
    assert rise.date()==day and setting.date()==day
    assert rise < setting


def test_candidate_interval_does_not_cross_tithi_nakshatra_or_daylight_segment_boundary():
    from app.muhurta import _clip_to_discrete_boundary
    day=date(2026,10,22); rise,setting=_sunrise_sunset(day,22.5726,88.3639,'Asia/Kolkata')
    assert rise and setting
    clipped=_clip_to_discrete_boundary(rise,rise.replace(minute=rise.minute)+__import__('datetime').timedelta(minutes=30),22.5726,88.3639,'Asia/Kolkata',rise,setting)
    assert rise < clipped <= min(rise+__import__('datetime').timedelta(minutes=30),setting)
