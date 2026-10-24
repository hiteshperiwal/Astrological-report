import pytest
from pydantic import ValidationError
from app.schemas import BirthRequest, MundaneRequest
from app.engine import _varga_sign


def test_birth_schema_rejects_impossible_date_and_clock_time():
    with pytest.raises(ValidationError):
        BirthRequest(name='Bad date', dob='2001-02-30', tob='12:00', latitude=0, longitude=0)
    with pytest.raises(ValidationError):
        BirthRequest(name='Bad time', dob='2001-02-28', tob='25:99', latitude=0, longitude=0)


def test_custom_forecast_ranges_reject_reverse_and_invalid_dates():
    with pytest.raises(ValidationError):
        BirthRequest(name='Reverse', dob='2001-02-28', tob='12:00', latitude=0, longitude=0,
                     forecast_start_date='2027-01-01', forecast_end_date='2026-12-31')
    with pytest.raises(ValidationError):
        MundaneRequest(country='India', period_start_date='2026-02-30', period_end_date='2026-03-01')
    with pytest.raises(ValidationError):
        MundaneRequest(country='India', period_start_date='2027-01-01', period_end_date='2026-01-01')


def test_single_day_custom_period_is_allowed():
    req = MundaneRequest(country='India', period_start_date='2026-11-01', period_end_date='2026-11-01')
    assert req.period_start_date == req.period_end_date


def test_custom_leader_requires_minimum_birth_location_data():
    with pytest.raises(ValidationError):
        MundaneRequest(country='India', leader_custom=True, leader_name='Custom')


def test_d30_even_sign_band_boundaries_follow_parashari_thresholds():
    # Cancer (90 degrees) is even. Thresholds are 5, 10, 18, 25, 30 degrees.
    assert _varga_sign(90 + 4.9999, 30) == 6   # Venus / Libra
    assert _varga_sign(90 + 5.0, 30) == 5      # Mercury / Virgo
    assert _varga_sign(90 + 9.9999, 30) == 5
    assert _varga_sign(90 + 10.0, 30) == 11    # Jupiter / Pisces
    assert _varga_sign(90 + 17.9999, 30) == 11
    assert _varga_sign(90 + 18.0, 30) == 9    # Saturn / Capricorn
    assert _varga_sign(90 + 24.9999, 30) == 9
    assert _varga_sign(90 + 25.0, 30) == 7    # Mars / Scorpio


def test_sunapha_and_anapha_do_not_count_the_sun_as_the_required_planet():
    from app.engine import detect_yogas
    # Moon in Aries; Sun alone in Taurus (2nd from Moon). No other classical
    # graha occupies Taurus or Pisces, so Sun alone must not trigger Sunapha.
    signs = {'Sun': 1, 'Moon': 0, 'Mars': 4, 'Mercury': 6, 'Jupiter': 8,
             'Venus': 10, 'Saturn': 3, 'Rahu': 5, 'Ketu': 11}
    planets = {p: {'longitude': sign * 30.0 + 1.0} for p, sign in signs.items()}
    names = {x['name'] for x in detect_yogas(planets, 0)}
    assert 'Sunapha Yoga' not in names
    # Move Sun to Pisces alone (12th from Moon); it must not trigger Anapha either.
    signs['Sun'] = 11
    planets = {p: {'longitude': sign * 30.0 + 1.0} for p, sign in signs.items()}
    names = {x['name'] for x in detect_yogas(planets, 0)}
    assert 'Anapha Yoga' not in names


def test_chat_chart_cache_key_and_engine_call_include_custom_dates(monkeypatch):
    import app.main as main
    seen = {}
    def fake_analyze(birth, **kwargs):
        seen.update(kwargs)
        return {'forecast': {'start': kwargs.get('forecast_start_date'), 'end': kwargs.get('forecast_end_date')}}
    monkeypatch.setattr(main, 'analyze_birth', fake_analyze)
    main._cached_chat_chart.cache_clear()
    main._cached_chat_chart('A', '2001-01-01', '12:00', 0, 0, 'UTC', '', 5, 'years', None, 'synthesis', '2026-11-01', '2026-11-30')
    assert seen['forecast_start_date'] == '2026-11-01'
    assert seen['forecast_end_date'] == '2026-11-30'
    main._cached_chat_chart.cache_clear()


def test_coordinate_and_timezone_validation_rejects_out_of_bounds_inputs():
    with pytest.raises(ValidationError):
        BirthRequest(name='Bad lat', dob='2001-01-01', tob='12:00', latitude=91, longitude=0)
    with pytest.raises(ValidationError):
        BirthRequest(name='Bad lon', dob='2001-01-01', tob='12:00', latitude=0, longitude=181)
    with pytest.raises(ValidationError):
        BirthRequest(name='Bad tz', dob='2001-01-01', tob='12:00', latitude=0, longitude=0, timezone='Mars/Olympus')


def test_calculation_audit_detects_inconsistent_chart_instead_of_only_counting_sections():
    from app.validation import personal_calculation_audit
    fixture = {
        'planets': {'Sun': {'longitude': 10, 'sign_index': 1, 'sign': 'Taurus'}},
        'divisional_charts': {}, 'shadbala': {'planets': {}},
        'ashtakavarga_classical': {'sav': []},
        'forecast': {'start': '2026-01-01', 'end': '2026-02-01'},
        'transits': [], 'nakshatra_analysis': {'moon': {'pada': 9}},
    }
    result = personal_calculation_audit(fixture)
    assert not result['all_passed']
    assert any(x['name'] == 'natal_longitude_sign_consistency' and not x['passed'] for x in result['checks'])


def test_health_endpoint_reports_current_build_version():
    from fastapi.testclient import TestClient
    from app.main import app
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json()['version'] == '1.0.6'
