from app.mundane import MUNDANE_EVENT_CLASSES, _mundane_event_combinations, scan_mundane_forecast
from app.schemas import BirthRequest, MundaneRequest


def test_custom_country_forecast_is_limited_to_selected_dates():
    req = MundaneRequest(country='India', period_start_date='2026-11-01', period_end_date='2026-11-03')
    result = scan_mundane_forecast(req.country, period_start_date=req.period_start_date, period_end_date=req.period_end_date)
    assert result['custom_period'] is True
    assert result['requested_period'] == {'start': '2026-11-01', 'end': '2026-11-03'}
    assert result['long_term']['monthly'] == []
    assert all('2026-11-01' <= row['date'] <= '2026-11-03' for row in result['near_term']['monthly'])


def test_personal_custom_date_fields_are_supported():
    req = BirthRequest(name='Fixture', dob='2000-01-01', tob='12:00', latitude=22.57, longitude=88.36,
                       forecast_start_date='2026-11-01', forecast_end_date='2026-11-30')
    assert req.forecast_start_date == '2026-11-01'
    assert req.forecast_end_date == '2026-11-30'


def test_political_event_classes_have_combinations():
    ids = {x['id'] for x in MUNDANE_EVENT_CLASSES}
    combo_classes = {x['event_class'] for x in _mundane_event_combinations}
    assert {'public_uprising', 'government_fall', 'executive_removal', 'constitutional_crisis'} <= ids
    assert {'public_uprising', 'government_fall', 'executive_removal', 'constitutional_crisis'} <= combo_classes
