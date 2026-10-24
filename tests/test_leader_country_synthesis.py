from app.schemas import MundaneRequest
from app.main import _combine_country_leader_forecasts


def test_mundane_request_accepts_selected_and_custom_leader_fields():
    req = MundaneRequest(country="India", leader_name="Narendra Modi")
    assert req.leader_name == "Narendra Modi"
    custom = MundaneRequest(country="India", leader_custom=True, leader_name="Test Leader",
                            leader_dob="1980-01-02", leader_tob="10:30",
                            leader_place="Kolkata, India", leader_latitude=22.57,
                            leader_longitude=88.36, leader_timezone="Asia/Kolkata",
                            leader_time_status="reported")
    assert custom.leader_custom is True
    assert custom.leader_time_status == "reported"


def test_leader_country_synthesis_labels_unknown_time_and_keeps_layers_separate():
    result = _combine_country_leader_forecasts(
        {"start": "2026-11-01", "long_end": "2026-12-01", "near_term": {"monthly": []}, "long_term": {"monthly": []}},
        {"meta": {"name": "Example Leader"}, "transits": []}, "unknown", "fixture"
    )
    assert result["leader_name"] == "Example Leader"
    assert "noon reference" in result["data_quality_note"]
    assert "primary collective chart" in result["method"]
    assert result["corroborations"] == []
