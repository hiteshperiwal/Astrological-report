from pathlib import Path


JS = (Path(__file__).resolve().parents[1] / 'static' / 'app.js').read_text()


def test_dasha_and_yoga_tabs_use_full_response_not_chart_only():
    assert "'personal-dashas':()=>renderDashas(latest)" in JS
    assert "'personal-yogas':()=>renderYogas(latest)" in JS


def test_dasha_and_yoga_renderers_have_chart_fallbacks():
    assert "function renderDashas(source)" in JS
    assert "const c=source?.chart||source||{};" in JS
    assert "const narrative=source?.narrative||c.narrative||{};" in JS
    assert "function renderYogas(source)" in JS
    assert "const yogaRows=ys.length?ys:(c.yogas||[])" in JS
    assert "const doshaRows=ds.length?ds:(c.doshas||[])" in JS


def test_strength_uses_inline_retro_marker():
    assert "p+(d.components.retrograde?' (R)':'')" in JS
    assert "th(['Planet','Score','Dignity','House','Combust'])" in JS
    assert "['Planet','Score','Dignity','House','Retro','Combust']" not in JS


def test_mundane_event_object_is_rendered_as_event_name():
    assert "typeof r.event==='object'" in JS
    assert "mundaneValue(r.event" in JS
    assert "mundane-collapsible" in JS


def test_birth_datetime_field_opens_themed_picker_on_click():
    assert "field?.addEventListener('click',show)" in JS
    assert 'id="birthDateTime" type="text" readonly' in (Path(__file__).resolve().parents[1] / 'templates' / 'index.html').read_text(encoding='utf-8')
