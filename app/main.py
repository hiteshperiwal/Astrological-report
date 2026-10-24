from __future__ import annotations
import json
import os
from datetime import date, datetime
import logging
import time
import sys
from functools import lru_cache
import copy
from pathlib import Path
from urllib.parse import urlencode
import hmac
from urllib.request import Request, urlopen

try:
    from timezonefinder import TimezoneFinder
except Exception:  # optional at import time; requirements installs it in normal use
    TimezoneFinder = None

from fastapi import FastAPI, HTTPException, Query, Request as FastAPIRequest
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from fastapi.templating import Jinja2Templates

from .engine import BirthData, analyze_birth
from .pdf_report import build_pdf, build_mundane_pdf
from .report import generate_narrative, build_ai_interpretation_payload
from .ai_interpreter import generate_ai_interpretation, generate_ai_chat
from .schemas import BirthRequest, MundaneRequest, MuhurtaRequest, LibraryAnalyzeRequest, PersonalChatRequest
from .mundane import analyze_country, search_historical_patterns, scan_mundane_forecast, available_countries, world_event_status, reload_world_events, retrospective_event_forecast_backtest
from .backtest import retrospective_mundane_backtest
from .master_data import search_people, get_person

BASE = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE / ".env", override=False)
except Exception:
    pass
DOCS_ENABLED = os.getenv("APP_ENV", "development").lower() not in {"production", "prod"}
app = FastAPI(title="Jyotish Lab", version="1.0.6", docs_url="/api/docs" if DOCS_ENABLED else None, redoc_url=None, openapi_url="/openapi.json" if DOCS_ENABLED else None)


@lru_cache(maxsize=12)
def _cached_chat_chart(name, dob, tob, latitude, longitude, timezone, place, amount, unit, granularity, school, forecast_start_date=None, forecast_end_date=None):
    log_phase('CHAT-CACHE', 'Cache miss; calculating chart', name=name, forecast=f'{amount} {unit}', granularity=granularity, school=school, custom_start=forecast_start_date, custom_end=forecast_end_date)
    birth=BirthData(name,date.fromisoformat(dob),tob,float(latitude),float(longitude),timezone,place)
    return analyze_birth(birth,forecast_amount=int(amount),forecast_unit=unit,forecast_granularity=granularity,school=school,forecast_start_date=forecast_start_date,forecast_end_date=forecast_end_date)
app.add_middleware(GZipMiddleware, minimum_size=1000)
logger = logging.getLogger("jyotish_lab")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

def log_phase(scope: str, message: str, **data):
    sensitive = {"name", "dob", "place", "latitude", "longitude", "question", "query", "leader_name", "leader_dob", "leader_place"}
    safe_data = {k: ("[redacted]" if k.lower() in sensitive else v) for k, v in data.items()}
    suffix = " " + " ".join(f"{k}={v!r}" for k, v in safe_data.items()) if safe_data else ""
    logger.info("[%s] %s%s", scope, message, suffix)

MAX_REQUEST_BYTES = 1_000_000

class RequestBodyLimitMiddleware:
    """Bound request bodies even when Content-Length is missing or misleading."""
    def __init__(self, app, max_bytes: int = MAX_REQUEST_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("method") in {"GET", "HEAD", "OPTIONS"}:
            await self.app(scope, receive, send)
            return
        messages = []
        total = 0
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                return
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    body = b'{"detail":"Request body exceeds the 1 MB limit."}'
                    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()),
                               (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"),
                               (b"x-frame-options", b"DENY"), (b"referrer-policy", b"strict-origin-when-cross-origin"),
                               (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")]
                    await send({"type": "http.response.start", "status": 413, "headers": headers})
                    await send({"type": "http.response.body", "body": body})
                    return
                messages.append(message)
                if not message.get("more_body", False):
                    break
        index = 0
        async def replay_receive():
            nonlocal index
            if index < len(messages):
                msg = messages[index]
                index += 1
                return msg
            return {"type": "http.disconnect"}
        await self.app(scope, replay_receive, send)

app.add_middleware(RequestBodyLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)

@app.middleware("http")
async def request_logger(request: FastAPIRequest, call_next):
    """Apply response hardening, enforce a request-size ceiling and log no user data."""
    started = time.perf_counter()
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                response = JSONResponse({"detail": "Request body exceeds the 1 MB limit."}, status_code=413)
                return _secure_response_headers(response)
        except ValueError:
            response = JSONResponse({"detail": "Invalid Content-Length header."}, status_code=400)
            return _secure_response_headers(response)
    try:
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        logger.info("HTTP %s %s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, elapsed)
        return _secure_response_headers(response)
    except Exception:
        elapsed = (time.perf_counter() - started) * 1000
        logger.exception("HTTP request failed: %s %s duration_ms=%.1f", request.method, request.url.path, elapsed)
        raise

def _secure_response_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
    response.headers.setdefault("Cache-Control", "no-store" if response.headers.get("content-type", "").startswith("application/json") else "private, no-cache")
    return response
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

COMMON_PLACES = {
    "Kolkata": {"latitude":22.5726,"longitude":88.3639,"timezone":"Asia/Kolkata"},
    "Mumbai": {"latitude":19.0760,"longitude":72.8777,"timezone":"Asia/Kolkata"},
    "Delhi": {"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"},
    "Bengaluru": {"latitude":12.9716,"longitude":77.5946,"timezone":"Asia/Kolkata"},
    "Chennai": {"latitude":13.0827,"longitude":80.2707,"timezone":"Asia/Kolkata"},
    "Hyderabad": {"latitude":17.3850,"longitude":78.4867,"timezone":"Asia/Kolkata"},
    "Pune": {"latitude":18.5204,"longitude":73.8567,"timezone":"Asia/Kolkata"},
    "Jaipur": {"latitude":26.9124,"longitude":75.7873,"timezone":"Asia/Kolkata"},
    "Lucknow": {"latitude":26.8467,"longitude":80.9462,"timezone":"Asia/Kolkata"},
    "Patna": {"latitude":25.5941,"longitude":85.1376,"timezone":"Asia/Kolkata"},
    "Guwahati": {"latitude":26.1445,"longitude":91.7362,"timezone":"Asia/Kolkata"},
    "London": {"latitude":51.5074,"longitude":-0.1278,"timezone":"Europe/London"},
    "New York": {"latitude":40.7128,"longitude":-74.0060,"timezone":"America/New_York"},
    "Los Angeles": {"latitude":34.0522,"longitude":-118.2437,"timezone":"America/Los_Angeles"},
    "Toronto": {"latitude":43.6532,"longitude":-79.3832,"timezone":"America/Toronto"},
    "Singapore": {"latitude":1.3521,"longitude":103.8198,"timezone":"Asia/Singapore"},
    "Dubai": {"latitude":25.2048,"longitude":55.2708,"timezone":"Asia/Dubai"},
    "Sydney": {"latitude":-33.8688,"longitude":151.2093,"timezone":"Australia/Sydney"},
}

@app.get("/", response_class=HTMLResponse)
async def index(request: FastAPIRequest):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.get("/api/place")
async def place_search(q: str):
    q=q.strip()
    if len(q) > 120:
        raise HTTPException(status_code=422, detail="Place search must be 120 characters or fewer.")
    if not q:
        return JSONResponse({"results":[]})
    log_phase("PLACE", "Searching location", query=q)
    for k,v in COMMON_PLACES.items():
        if q.lower()==k.lower():
            result={"display_name":k+", preset",**v,"source":"preset","timezone_needs_confirmation":False}
            log_phase("PLACE", "Preset location matched", place=k, timezone=v["timezone"])
            return JSONResponse({"results":[result]})
    url="https://nominatim.openstreetmap.org/search?"+urlencode({"format":"jsonv2","limit":6,"q":q})
    try:
        req=Request(url,headers={"User-Agent":"JyotishLab/0.9.8 (+local-user-tool)"})
        with urlopen(req,timeout=8) as r:
            raw = r.read(512_001)
            if len(raw) > 512_000:
                raise ValueError("Geocoder response exceeded the size limit")
            data=json.loads(raw.decode("utf-8"))
        tf=TimezoneFinder() if TimezoneFinder else None
        results=[]
        for x in data:
            lat=float(x["lat"]); lon=float(x["lon"])
            tz=tf.timezone_at(lat=lat, lng=lon) if tf else None
            results.append({"display_name":x.get("display_name",""),"latitude":lat,"longitude":lon,"timezone":tz or "UTC","timezone_needs_confirmation":not bool(tz),"source":"nominatim"})
        log_phase("PLACE", "Geocoder returned results", count=len(results), timezone_resolved=sum(1 for x in results if not x["timezone_needs_confirmation"]))
        return JSONResponse({"results":results})
    except Exception as exc:
        logger.warning("[PLACE] Geocoder request failed (%s)", type(exc).__name__)
        return JSONResponse({"results":[],"warning":"Geocoder unavailable. Enter coordinates manually if needed."})

def _birth_from_payload(payload: BirthRequest):
    y,m,d=map(int,payload.dob.split("-")); amount=payload.forecast_amount
    if payload.forecast_years is not None and payload.forecast_amount==5 and payload.forecast_unit=="years": amount=payload.forecast_years
    return BirthData(payload.name,date(y,m,d),payload.tob,payload.latitude,payload.longitude,payload.timezone,payload.place),amount

@app.post("/api/muhurta/search")
async def api_muhurta_search(payload: MuhurtaRequest):
    try:
        natal_moon = None
        if payload.natal_dob and payload.natal_tob:
            from zoneinfo import ZoneInfo
            from .engine import norm360
            import swisseph as swe
            birth_dt = datetime.fromisoformat(payload.natal_dob + "T" + payload.natal_tob).replace(tzinfo=ZoneInfo(payload.natal_timezone or payload.timezone))
            utc_dt = birth_dt.astimezone(__import__('datetime').timezone.utc)
            jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            natal_moon = norm360(swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0])
        from .muhurta import search_muhurta
        return search_muhurta(activity=payload.activity, start_date=payload.start_date, end_date=payload.end_date,
            latitude=payload.latitude, longitude=payload.longitude, timezone_name=payload.timezone,
            natal_moon_longitude=natal_moon)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("[MUHURTA] Search failed")
        raise HTTPException(status_code=500, detail="Muhurta calculation failed. Check the request and server logs.")


@app.post("/api/personal/analyze")
async def api_personal(payload: BirthRequest):
    started=time.perf_counter()
    log_phase("PERSONAL", "Starting Kundali calculation", name=payload.name, dob=payload.dob, place=payload.place, school=payload.school, forecast=f"{payload.forecast_amount} {payload.forecast_unit}")
    try:
        birth,amount=_birth_from_payload(payload)
        log_phase("PERSONAL", "Birth data normalized", timezone=payload.timezone, latitude=payload.latitude, longitude=payload.longitude)
        log_phase("PERSONAL", "Running astronomical/chart engine")
        chart=analyze_birth(birth,forecast_amount=amount,forecast_unit=payload.forecast_unit,forecast_granularity=payload.forecast_granularity, school=payload.school, forecast_start_date=payload.forecast_start_date, forecast_end_date=payload.forecast_end_date)
        log_phase("PERSONAL", "Chart engine complete", planets=len(chart.get("planets",{})), vargas=len(chart.get("divisional_charts",{})), forecast_rows=len(chart.get("transits",[])))
        chart["meta"]["name"]=payload.name
        from .validation import personal_calculation_audit
        log_phase("PERSONAL", "Running calculation audit")
        chart["validation_audit"]=personal_calculation_audit(chart)
        log_phase("PERSONAL", "Generating narrative")
        narrative=generate_narrative(chart)
        ai_result=generate_ai_interpretation(chart,narrative)
        narrative['ai_interpretation']=ai_result
        chart['ai_interpretation']=ai_result
        log_phase("PERSONAL", "AI interpretation stage complete", status=ai_result.get('status'))
        log_phase("PERSONAL", "Kundali request complete", duration_ms=round((time.perf_counter()-started)*1000,1))
        return {"chart":chart,"narrative":narrative}
    except Exception as e:
        logger.exception("[PERSONAL] Calculation failed")
        raise HTTPException(status_code=500,detail="Calculation failed. Check the request and server logs.")


@app.post("/api/personal/chat")
async def api_personal_chat(payload: PersonalChatRequest):
    started=time.perf_counter()
    question=payload.question
    try:
        birth_payload=payload.birth
        birth,amount=_birth_from_payload(birth_payload)
        log_phase('CHAT','Building chart context',name=birth_payload.name,question=question[:120])
        cached=_cached_chat_chart(birth_payload.name,birth_payload.dob,birth_payload.tob,birth_payload.latitude,birth_payload.longitude,birth_payload.timezone,birth_payload.place,amount,birth_payload.forecast_unit,birth_payload.forecast_granularity,birth_payload.school,birth_payload.forecast_start_date,birth_payload.forecast_end_date)
        chart=copy.deepcopy(cached)
        chart['meta']['name']=birth_payload.name
        narrative=generate_narrative(chart)
        result=generate_ai_chat(chart,narrative,question,[m.model_dump() for m in payload.history])
        log_phase('CHAT','Answer ready',status=result.get('status'),duration_ms=round((time.perf_counter()-started)*1000,1))
        return result
    except Exception as e:
        logger.exception('[CHAT] Failed')
        raise HTTPException(status_code=500,detail='Chat failed. Check the request and server logs.')

@app.post("/api/analyze")
async def api_analyze(payload: BirthRequest):
    return await api_personal(payload)

@app.post("/api/personal/ai-payload")
async def api_personal_ai_payload(payload: BirthRequest):
    started=time.perf_counter()
    log_phase("AI", "Building AI interpretation payload", name=payload.name)
    try:
        birth,amount=_birth_from_payload(payload)
        chart=analyze_birth(birth,forecast_amount=amount,forecast_unit=payload.forecast_unit,forecast_granularity=payload.forecast_granularity, school=payload.school)
        chart["meta"]["name"]=payload.name
        narrative=generate_narrative(chart)
        out=build_ai_interpretation_payload(chart,narrative)
        log_phase("AI", "AI payload ready", bytes=len(json.dumps(out)), duration_ms=round((time.perf_counter()-started)*1000,1))
        return out
    except Exception as e:
        logger.exception("[AI] Payload generation failed")
        raise HTTPException(status_code=500,detail="AI payload generation failed. Check the request and server logs.")

@app.post("/api/personal/report.pdf")
async def api_personal_pdf(payload: BirthRequest):
    try:
        birth,amount=_birth_from_payload(payload)
        chart=analyze_birth(birth,forecast_amount=amount,forecast_unit=payload.forecast_unit,forecast_granularity=payload.forecast_granularity, school=payload.school)
        chart["meta"]["name"]=payload.name
        narrative=generate_narrative(chart)
        ai_result=generate_ai_interpretation(chart,narrative)
        narrative['ai_interpretation']=ai_result
        chart['ai_interpretation']=ai_result
        pdf=build_pdf(chart,narrative)
        return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=jyotish-lab-personal-report.pdf"})
    except Exception: logger.exception("[PDF] Personal PDF export failed"); raise HTTPException(status_code=500,detail="PDF export failed. Check server logs for details.")

@app.post("/api/report.pdf")
async def api_pdf(payload: BirthRequest): return await api_personal_pdf(payload)

@app.get("/api/library")
async def api_library(q: str = Query(default="", max_length=120), category: str | None = Query(default=None, max_length=80)):
    rows=search_people(q,category)
    return {"results":rows,"categories":sorted({p["category"] for p in search_people()})}

@app.post("/api/library/analyze")
async def api_library_analyze(payload: LibraryAnalyzeRequest):
    try:
        p=get_person(payload.name)
        # Noon is a clearly labelled reference time when public birth time is unavailable.
        tob=p.get("tob") or "12:00:00"
        birth=BirthData(p["name"],date.fromisoformat(p["dob"]),tob,p["latitude"],p["longitude"],p["timezone"],p["place"])
        chart=analyze_birth(birth,forecast_amount=payload.forecast_amount,forecast_unit=payload.forecast_unit,school=payload.school)
        chart["meta"]["reference_profile"]={"category":p["category"],"time_status":p["time_status"],"source":p["source"],"note":"No verified public birth time is stored; chart uses 12:00 local as a reference and should not be treated as a verified timed Kundali."}
        chart["meta"]["name"]=p["name"]
        return {"profile":p,"chart":chart,"narrative":generate_narrative(chart)}
    except Exception as e: raise HTTPException(status_code=400,detail="Reference profile calculation failed. Check the selected profile and server logs.")

@app.get("/api/mundane/world-events/status")
async def api_world_event_status():
    return world_event_status()

@app.post("/api/mundane/world-events/sync")
async def api_world_event_sync(request: FastAPIRequest):
    started=time.perf_counter()
    expected = os.getenv("WORLD_EVENTS_SYNC_TOKEN", "").strip()
    supplied = request.headers.get("x-admin-token", "")
    if not expected:
        raise HTTPException(status_code=503, detail="World-event sync is disabled. Configure WORLD_EVENTS_SYNC_TOKEN to enable the administrative action.")
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="Administrative token is missing or invalid.")
    try:
        from subprocess import run
        script=BASE / "scripts" / "sync_world_events.py"
        log_phase("WORLD-EVENTS", "Starting source sync", target=1000)
        proc=run([sys.executable, str(script)], capture_output=True, text=True, timeout=90, cwd=str(BASE))
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "world-event sync failed")
        loaded=reload_world_events()
        log_phase("WORLD-EVENTS", "World historical corpus loaded", events=loaded, duration_ms=round((time.perf_counter()-started)*1000,1))
        return {**world_event_status(),"message":"World historical corpus synchronized."}
    except Exception as e:
        logger.exception("[WORLD-EVENTS] Sync failed")
        raise HTTPException(status_code=500,detail="World historical sync failed. Check server logs for details.")

def _combine_country_leader_forecasts(country_forecast, leader_chart, time_status, source):
    """Overlay leader timing as a separate corroboration layer; never replace national chart."""
    start = country_forecast.get("start")
    end = country_forecast.get("long_end")
    timing_windows = leader_chart.get("timing_windows", []) or []
    country_rows = (country_forecast.get("near_term", {}).get("monthly", []) or []) + (country_forecast.get("long_term", {}).get("monthly", []) or [])
    # Match date proximity only where a country event indication and leader timing row overlap.
    # Do not interpret absence of overlap as proof of weakness or government failure.
    by_date = {}
    for row in timing_windows:
        d = str(row.get("start", row.get("date", "")))[:10]
        if d: by_date.setdefault(d, []).append(row)
    corroborations=[]
    for row in country_rows:
        d=str(row.get("date", ""))[:10]
        near=[]
        try:
            from datetime import date as _date, timedelta as _td
            dt=_date.fromisoformat(d)
            for offset in (-7,0,7):
                near.extend(by_date.get((dt+_td(days=offset)).isoformat(), []))
        except Exception: pass
        if near and float(row.get("activation", 0) or 0) >= 55:
            corroborations.append({"date":d,"country_event_types":row.get("event_types",row.get("classes",[])),
                                   "country_activation":row.get("activation"),"leader_timing_rows":len(near),
                                   "leader_dasha_lords":sorted({str(x.get("dasha", "")) for x in near if x.get("dasha")}),
                                   "interpretation":"Date-level overlap between country activation and leader Dasha/transit screening windows only; not a validated joint probability."})
    quality = {"verified":"User marked birth time verified","reported":"Reported birth time; provenance should be checked","approximate":"Approximate birth time; houses, Lagna and divisional charts are uncertain","unknown":"Birth time unknown; noon reference chart used, so house-based and divisional conclusions are not reliable"}.get(time_status,"Birth-time quality unverified")
    return {"leader_name":leader_chart.get("meta",{}).get("name") or leader_chart.get("name"),
            "source":source,"birth_time_status":time_status,"data_quality_note":quality,
            "leader_chart":leader_chart,"country_forecast_period":{"start":start,"end":end},
            "corroborations":corroborations[:100],
            "method":"Country chart remains the primary collective chart. Leader natal chart is a separate, secondary timing lens; dates are surfaced as overlaps, not merged into an uncalibrated single score.",
            "interpretation_limits":["A strong individual chart does not by itself prove that a government will be strong or make successful decisions.","If birth time is unknown, noon-reference Lagna, houses and Vargas are not treated as reliable evidence.","Concordance is an astrological research signal, not validated predictive accuracy."]}


@app.post("/api/mundane/analyze")
async def api_mundane(payload: MundaneRequest):
    started=time.perf_counter()
    log_phase("MUNDANE", "Starting country analysis", country=payload.country, historical_limit=payload.historical_limit, near=f"{payload.near_term_amount} {payload.near_term_unit}", long=f"{payload.long_term_amount} {payload.long_term_unit}")
    try:
        log_phase("MUNDANE", "Resolving national chart from corpus")
        analysis=analyze_country(payload.country)
        log_phase("MUNDANE", "National chart resolved", canonical_country=analysis.get("country"), chart_selection=(analysis.get("chart_source") or {}).get("chart_selection", "unknown"))
        log_phase("MUNDANE", "Searching historical analogues")
        history=search_historical_patterns(payload.country,payload.historical_limit,payload.historical_event_types)
        log_phase("MUNDANE", "Historical search complete", matches=len(history.get("results",[])), corpus=history.get("corpus_size"))
        log_phase("MUNDANE", "Scanning forecast horizons")
        forecast=scan_mundane_forecast(payload.country, payload.near_term_amount, payload.long_term_amount, payload.near_term_unit, payload.long_term_unit, period_start_date=payload.period_start_date, period_end_date=payload.period_end_date)
        leader_result = None
        if payload.leader_custom:
            required = [payload.leader_dob, payload.leader_place, payload.leader_latitude, payload.leader_longitude]
            if any(v is None or v == "" for v in required):
                raise ValueError("Custom leader chart requires birth date, birthplace, latitude and longitude")
            from zoneinfo import ZoneInfo
            ZoneInfo(payload.leader_timezone)
            leader_name = (payload.leader_name or "Custom country leader").strip()
            leader_tob = payload.leader_tob or "12:00:00"
            leader_birth = BirthData(leader_name, date.fromisoformat(payload.leader_dob), leader_tob,
                                     float(payload.leader_latitude), float(payload.leader_longitude),
                                     payload.leader_timezone, payload.leader_place)
            leader_chart = analyze_birth(leader_birth, forecast_amount=1, forecast_unit="years",
                                         forecast_start_date=payload.period_start_date,
                                         forecast_end_date=payload.period_end_date)
            leader_result = _combine_country_leader_forecasts(forecast, leader_chart, payload.leader_time_status,
                                                               "custom-entered")
        elif payload.leader_name:
            try:
                person = get_person(payload.leader_name)
            except KeyError:
                raise ValueError("Leader is not in the reference database. Choose custom leader details to continue.")
            leader_tob = person.get("tob") or "12:00:00"
            leader_birth = BirthData(person["name"], date.fromisoformat(person["dob"]), leader_tob,
                                     float(person["latitude"]), float(person["longitude"]),
                                     person["timezone"], person["place"])
            leader_chart = analyze_birth(leader_birth, forecast_amount=1, forecast_unit="years",
                                         forecast_start_date=payload.period_start_date,
                                         forecast_end_date=payload.period_end_date)
            leader_result = _combine_country_leader_forecasts(forecast, leader_chart, person.get("time_status", "unknown"), person.get("source", "reference database"))
        if leader_result:
            forecast["leader_country_synthesis"] = leader_result
        log_phase("MUNDANE", "Forecast scan complete", near_rows=len(forecast.get("near_term",{}).get("monthly",[])), long_rows=len(forecast.get("long_term",{}).get("monthly",[])))
        log_phase("MUNDANE", "Country request complete", duration_ms=round((time.perf_counter()-started)*1000,1))
        return {"analysis":analysis,"historical":history,"forecast":forecast,"available_countries":available_countries()}
    except Exception as e:
        logger.exception("[MUNDANE] Calculation failed")
        raise HTTPException(status_code=500,detail="Mundane calculation failed. Check the request and server logs.")

@app.post("/api/mundane/report.pdf")
async def api_mundane_pdf(payload: MundaneRequest):
    try:
        analysis=analyze_country(payload.country)
        history=search_historical_patterns(payload.country,payload.historical_limit,payload.historical_event_types)
        forecast=scan_mundane_forecast(payload.country, payload.near_term_amount, payload.long_term_amount, payload.near_term_unit, payload.long_term_unit, period_start_date=payload.period_start_date, period_end_date=payload.period_end_date)
        leader_result = None
        if payload.leader_custom:
            required = [payload.leader_dob, payload.leader_place, payload.leader_latitude, payload.leader_longitude]
            if any(v is None or v == "" for v in required):
                raise ValueError("Custom leader chart requires birth date, birthplace, latitude and longitude")
            from zoneinfo import ZoneInfo
            ZoneInfo(payload.leader_timezone)
            leader_name = (payload.leader_name or "Custom country leader").strip()
            leader_tob = payload.leader_tob or "12:00:00"
            leader_birth = BirthData(leader_name, date.fromisoformat(payload.leader_dob), leader_tob,
                                     float(payload.leader_latitude), float(payload.leader_longitude),
                                     payload.leader_timezone, payload.leader_place)
            leader_chart = analyze_birth(leader_birth, forecast_amount=1, forecast_unit="years",
                                         forecast_start_date=payload.period_start_date,
                                         forecast_end_date=payload.period_end_date)
            leader_result = _combine_country_leader_forecasts(forecast, leader_chart, payload.leader_time_status,
                                                               "custom-entered")
        elif payload.leader_name:
            try:
                person = get_person(payload.leader_name)
            except KeyError:
                raise ValueError("Leader is not in the reference database. Choose custom leader details to continue.")
            leader_tob = person.get("tob") or "12:00:00"
            leader_birth = BirthData(person["name"], date.fromisoformat(person["dob"]), leader_tob,
                                     float(person["latitude"]), float(person["longitude"]),
                                     person["timezone"], person["place"])
            leader_chart = analyze_birth(leader_birth, forecast_amount=1, forecast_unit="years",
                                         forecast_start_date=payload.period_start_date,
                                         forecast_end_date=payload.period_end_date)
            leader_result = _combine_country_leader_forecasts(forecast, leader_chart, person.get("time_status", "unknown"), person.get("source", "reference database"))
        if leader_result:
            forecast["leader_country_synthesis"] = leader_result
        pdf=build_mundane_pdf({"analysis":analysis,"historical":history,"forecast":forecast})
        return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=jyotish-lab-mundane-report.pdf"})
    except Exception as e:
        logger.exception("[PDF] Mundane PDF export failed"); raise HTTPException(status_code=500,detail="Mundane PDF export failed. Check server logs for details.")

@app.get("/api/mundane/backtest")
async def api_mundane_backtest(limit:int=Query(default=100, ge=1, le=500), window_days:int=Query(default=15, ge=1, le=365)):
    try:
        return retrospective_mundane_backtest(limit=limit, window_days=window_days)
    except Exception:
        logger.exception("[BACKTEST] Mundane backtest failed")
        raise HTTPException(status_code=500,detail="Backtest failed. Check the request and server logs.")

@app.get("/api/mundane/historical-backtest")
async def api_mundane_historical_backtest(country: str = Query(min_length=1, max_length=120), start_date: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"), end_date: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"), horizon_days: int = Query(default=30, ge=1, le=365), step_days: int = Query(default=30, ge=14, le=365)):
    try:
        start = date.fromisoformat(start_date); end = date.fromisoformat(end_date)
        if end < start:
            raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
        if (end - start).days > 14610:
            raise HTTPException(status_code=422, detail="Historical backtest range cannot exceed 40 years")
        return retrospective_event_forecast_backtest(country, start_date, end_date, horizon_days, step_days)
    except HTTPException:
        raise
    except Exception:
        logger.exception("[BACKTEST] Historical backtest failed")
        raise HTTPException(status_code=500, detail="Historical backtest failed. Check the request and server logs.")

@app.get("/api/validation/mundane-walk-forward")
async def api_mundane_walk_forward(window_days:int=Query(default=15, ge=1, le=365), threshold:float=Query(default=40.0, ge=0.0, le=100.0)):
    from .validation import mundane_walk_forward_backtest
    return mundane_walk_forward_backtest(window_days=window_days, threshold=threshold)

@app.get("/api/advanced/schools")
async def api_advanced_schools():
    from .advanced import SCHOOL_PROFILES
    return {"schools": SCHOOL_PROFILES}

@app.get("/api/advanced/mundane-events")
async def api_advanced_mundane_events():
    from .mundane import REFERENCE_EVENTS
    return {"count": len(REFERENCE_EVENTS), "events": [e.__dict__ for e in REFERENCE_EVENTS]}

@app.get("/health")
def health(): return {"status":"ok","engine":"Jyotish Lab","version":"1.0.6"}
