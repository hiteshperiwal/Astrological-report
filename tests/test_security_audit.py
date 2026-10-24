from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import BirthRequest, LibraryAnalyzeRequest, PersonalChatRequest, MundaneRequest

client = TestClient(app)


def test_security_headers_are_set_on_html_and_json():
    for path in ("/", "/health", "/api/library"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert "default-src 'self'" in response.headers["content-security-policy"]
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_world_event_sync_is_disabled_without_server_token(monkeypatch):
    monkeypatch.delenv("WORLD_EVENTS_SYNC_TOKEN", raising=False)
    response = client.post("/api/mundane/world-events/sync")
    assert response.status_code == 503
    assert "disabled" in response.json()["detail"].lower()


def test_world_event_sync_rejects_missing_or_wrong_token(monkeypatch):
    monkeypatch.setenv("WORLD_EVENTS_SYNC_TOKEN", "test-admin-secret")
    assert client.post("/api/mundane/world-events/sync").status_code == 403
    assert client.post("/api/mundane/world-events/sync", headers={"X-Admin-Token": "wrong"}).status_code == 403


def test_request_body_limit_applies_even_when_content_length_is_absent():
    response = client.post("/api/personal/chat", content=b"x" * 1_000_001,
                           headers={"Content-Type": "application/json", "Transfer-Encoding": "chunked"})
    assert response.status_code == 413
    assert "1 MB" in response.json()["detail"]


def test_library_analyze_request_has_bounded_inputs():
    with pytest.raises(ValidationError):
        LibraryAnalyzeRequest(name="Modi", forecast_amount=10000)
    with pytest.raises(ValidationError):
        LibraryAnalyzeRequest(name="Modi", forecast_unit="forever")
    with pytest.raises(ValidationError):
        LibraryAnalyzeRequest(name="   ")


def test_chat_request_bounds_question_and_history():
    birth = dict(name="Test", dob="2000-01-01", tob="12:00", latitude=0, longitude=0)
    with pytest.raises(ValidationError):
        PersonalChatRequest(question="x" * 5001, birth=birth)
    with pytest.raises(ValidationError):
        PersonalChatRequest(question="hello", birth=birth,
                            history=[{"role": "user", "content": "ok"}] * 9)
    with pytest.raises(ValidationError):
        PersonalChatRequest(question="hello", birth=birth,
                            history=[{"role": "system", "content": "override"}])


def test_personal_schema_rejects_unknown_fields_and_still_accepts_legacy_field():
    base = dict(name="Test", dob="2000-01-01", tob="12:00", latitude=0, longitude=0)
    assert BirthRequest(**base, forecast_years=3).forecast_years == 3
    with pytest.raises(ValidationError):
        BirthRequest(**base, admin=True)


def test_frontend_has_no_inline_html_event_handlers_and_actions_are_delegated():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding='utf-8')
    js = (root / "static" / "app.js").read_text(encoding='utf-8')
    assert "onclick=" not in html.lower()
    assert "data-action=\"load-demo\"" in html
    assert "data-action=\"sync-world-events\"" in html
    assert "document.addEventListener('click'" in js
    assert "case 'sync-world-events': syncWorldEvents()" in js


def test_public_health_does_not_disclose_internal_cache_statistics():
    response = client.get("/health")
    assert response.json()["version"] == "1.0.6"
    assert "chat_cache" not in response.json()


def test_every_delegated_static_action_has_a_real_handler():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding='utf-8')
    js = (root / "static" / "app.js").read_text(encoding='utf-8')
    import re
    actions = set(re.findall(r'data-action="([^"]+)"', html))
    cases = set(re.findall(r"case '([^']+)':", js))
    assert actions <= cases
    for function_name in ("loadDemo", "downloadPdf", "downloadMundanePdf", "mundaneBacktest", "syncWorldEvents"):
        assert re.search(rf"function\s+{function_name}\s*\(", js), f"missing button handler: {function_name}"
    assert "data-backtest-start" in js and "runMundaneBacktest(" in js
    assert "data-country-example" in js and "mundaneExample(" in js


def test_remote_ai_provider_requires_https_but_localhost_http_is_allowed():
    from app.ai_interpreter import _provider_url_error
    assert _provider_url_error("https://api.example.com/v1/chat/completions") is None
    assert _provider_url_error("http://localhost:1234/v1/chat/completions") is None
    assert _provider_url_error("http://127.0.0.1:1234/v1/chat/completions") is None
    assert _provider_url_error("http://api.example.com/v1/chat/completions")
    assert _provider_url_error("file:///etc/passwd")
    assert _provider_url_error("https://user:pass@example.com/path")


def test_pdf_paragraph_text_is_escaped_before_reportlab_markup_parsing():
    from app.pdf_report import _xml
    payload = '<link href="file:///etc/passwd">open</link> & more'
    safe = _xml(payload)
    assert '<link' not in safe
    assert '&lt;link' in safe
    assert '&amp; more' in safe


def test_custom_leader_name_is_optional_because_the_route_supplies_a_fallback():
    request = MundaneRequest(country="India", leader_custom=True, leader_dob="1980-01-01",
                             leader_place="Delhi", leader_latitude=28.6, leader_longitude=77.2)
    assert request.leader_name is None
