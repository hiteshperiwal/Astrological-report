from __future__ import annotations

import json
import os
from urllib.parse import urlsplit
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
from typing import Any, Dict
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _credentials() -> tuple[str|None,str|None,str,str]:
    key=os.getenv('AI_API_KEY') or os.getenv('OPENAI_API_KEY')
    url=os.getenv('AI_API_URL','https://api.openai.com/v1/chat/completions')
    model=os.getenv('AI_MODEL','gpt-4.1-mini')
    provider=os.getenv('AI_PROVIDER','openai-compatible')
    return key,url,model,provider


def _provider_url_error(url: str) -> str | None:
    try:
        parsed = urlsplit(url)
    except Exception:
        return "AI_API_URL is not a valid provider URL."
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in local_hosts):
        return "AI_API_URL must use HTTPS (HTTP is permitted only for localhost development)."
    if not parsed.hostname or parsed.username or parsed.password:
        return "AI_API_URL is not a valid provider URL."
    return None


def generate_ai_interpretation(chart: Dict[str,Any], narrative: Dict[str,Any]) -> Dict[str,Any]:
    key,url,model,provider=_credentials()
    if not key:
        return {'status':'unavailable','message':'AI interpretation is not available because AI credentials are not configured in the backend. Set AI_API_KEY (or OPENAI_API_KEY) and AI_MODEL to enable automatic interpretation.','provider':provider,'model':model}
    from .report import build_ai_interpretation_payload
    package=build_ai_interpretation_payload(chart,narrative)
    system='You are the AI interpretation layer for Jyotish Lab. Use only the supplied astrological JSON. Return direct, sectioned Vedic Jyotish interpretations. Do not invent chart placements, yogas, dashas or dates. Use deterministic rule language: state the astrological result plainly, state both constructive and difficult manifestations when the supplied factors support them, and do not dilute the reading with generic uncertainty language.'
    body={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':package['prompt']+'\n\nASTROLOGICAL JSON:\n'+json.dumps(package['astrological_data'],ensure_ascii=False)}],'temperature':0}
    url_error = _provider_url_error(url)
    if url_error:
        return {'status':'error','message':url_error,'provider':provider,'model':model}
    req=Request(url,data=json.dumps(body).encode('utf-8'),headers={'Content-Type':'application/json','Authorization':f'Bearer {key}'},method='POST')
    try:
        with urlopen(req,timeout=45) as resp:
            raw = resp.read(2_097_153)
            if len(raw) > 2_097_152:
                return {'status':'error','message':'AI provider response exceeded the 2 MB limit.','provider':provider,'model':model}
            data=json.loads(raw.decode('utf-8'))
        choices=data.get('choices') or []
        if choices:
            msg=choices[0].get('message',{})
            content=msg.get('content','')
            if isinstance(content,list): content=''.join(x.get('text','') for x in content if isinstance(x,dict))
            return {'status':'generated','provider':provider,'model':model,'text':content,'raw_id':data.get('id')}
        return {'status':'error','message':'AI provider returned no completion choices.','provider':provider,'model':model}
    except HTTPError as e:
        return {'status':'error','message':f'AI provider returned HTTP {e.code}. Check server-side provider configuration/logs.','provider':provider,'model':model}
    except (URLError,TimeoutError):
        return {'status':'error','message':'AI provider connection failed. Check server-side provider configuration and network access.','provider':provider,'model':model}
    except Exception:
        return {'status':'error','message':'AI interpretation failed. Check server-side provider configuration and logs.','provider':provider,'model':model}


def generate_ai_chat(chart: Dict[str,Any], narrative: Dict[str,Any], question: str, history: list[dict] | None = None) -> Dict[str,Any]:
    """Return the local rule-engine answer as the authoritative chatbot answer.

    The chatbot must not rewrite the answer through a second generative model because
    that can introduce a different conclusion from the calculated chart. AI remains
    available in the separate AI Interpretation tab.
    """
    from .report import _interpretation_chat, build_chat_context
    ground_truth=_interpretation_chat(chart,narrative,question)
    targeted_context=build_chat_context(chart,narrative,question)
    return {
        'status':'local',
        'mode':'deterministic',
        'text':ground_truth,
        'message':ground_truth,
        'provider':'local-rule-engine',
        'model':'deterministic',
        'context_scope':list(targeted_context.keys()),
        'question':question,
    }

