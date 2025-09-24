# backend/app/services/llm_clients.py
import os
from typing import Dict, Any, List, Optional
import json
import re
import time
import httpx
import asyncio

# --- OpenAI ---
from openai import OpenAI
# --- Anthropic ---
import anthropic

# Zentrale Config verwenden
from ..config import (
    OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY,
    OPENAI_MODEL, CLAUDE_MODEL, PPLX_MODEL,
    LLM_TIMEOUT_SECONDS, LLM_RETRIES
)

# Provider IDs
PERPLEXITY_PROVIDER_ID = "perplexity"

# Timeout und Retry-Konfiguration
REQUEST_TIMEOUT = LLM_TIMEOUT_SECONDS
RETRY_COUNT = LLM_RETRIES

def _json_from_text(text: str) -> Dict[str, Any]:
    """
    Robust: zieht JSON auch aus ```json ... ``` oder gemischtem Text.
    """
    if not text:
        return {}
    # code-fences entfernen
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    raw = fenced[0] if fenced else text
    # erste { ... }-Struktur fangen
    brace = re.search(r"\{.*\}", raw, flags=re.S)
    if brace:
        raw = brace.group(0)
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _rico_schema() -> Dict[str, Any]:
    """Leeres Fallback-Schema, auf das das UI getrimmt ist."""
    return {
        "kurz_zusammenfassung": "",
        "kernergebnisse": [],
        "action_plan": [],
        "risiken": [],
        "cashflow_radar": {"idee": ""},
        "team_rolle": {"openai": False, "claude": False, "perplexity": False},
    }

PROMPT_TEMPLATE = """Du bist Teil meines Systems "Rico 4.0".
Analysiere die folgende Eingabe und antworte **NUR** als reines JSON im Format:

{{
  "kurz_zusammenfassung": "1–3 Sätze",
  "kernergebnisse": ["Punkt 1","Punkt 2","Punkt 3"],
  "action_plan": ["Schritt 1","Schritt 2"],
  "risiken": ["Risiko 1","Risiko 2"],
  "cashflow_radar": {{"idee": "kurzer Hinweis"}}
}}

WICHTIG:
- Keine Erklärtexte außerhalb des JSON.
- Keine Markdown-Codeblöcke, nur reines JSON.
- Wenn etwas unklar ist, triff sinnvolle Annahmen und schreibe sie unter "risiken".

Eingabe:
\"\"\"{user_text}\"\"\"
"""

def ask_openai(user_text: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return {}
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = PROMPT_TEMPLATE.format(user_text=user_text)
    
    # Retry-Mechanismus mit exponentieller Backoff
    for attempt in range(RETRY_COUNT + 1):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                timeout=REQUEST_TIMEOUT
            )
            content = resp.choices[0].message.content if resp.choices else ""
            data = _json_from_text(content)
            if data:
                data.setdefault("cashflow_radar", {}).setdefault("idee", "")
                data.setdefault("team_rolle", {})["openai"] = True
            return data
            
        except Exception as e:
            if attempt < RETRY_COUNT:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"OpenAI API Fehler (Versuch {attempt + 1}/{RETRY_COUNT + 1}): {e}")
                print(f"Warte {wait_time} Sekunden vor erneutem Versuch...")
                time.sleep(wait_time)
            else:
                print(f"OpenAI API endgültig fehlgeschlagen nach {RETRY_COUNT + 1} Versuchen: {e}")
                # Einheitliches Fehler-Mapping
                error_type = "server"
                if "401" in str(e) or "Unauthorized" in str(e):
                    error_type = "auth"
                elif "429" in str(e) or "rate" in str(e).lower():
                    error_type = "rate_limit"
                elif "timeout" in str(e).lower():
                    error_type = "timeout"
                return {
                    "error": error_type,
                    "team_rolle": {"openai": False, "claude": False, "perplexity": False}
                }
    
    return {}

def ask_claude(user_text: str) -> Dict[str, Any]:
    if not CLAUDE_API_KEY:
        return {}
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = PROMPT_TEMPLATE.format(user_text=user_text)
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    # Claude gibt Content als Liste
    text = "".join(part.text for part in msg.content if getattr(part, "type", "") == "text")
    data = _json_from_text(text)
    if data:
        data.setdefault("cashflow_radar", {}).setdefault("idee", "")
        data.setdefault("team_rolle", {})["claude"] = True
    return data

def merge_results(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sehr einfache Fusion: Strings bevorzugen a, Listen werden zusammengeführt (dedupliziert).
    """
    base = _rico_schema()
    for k in base.keys():
        if k in ("team_rolle", "cashflow_radar"):
            continue
        av = a.get(k)
        bv = b.get(k)
        if isinstance(base[k], list):
            merged = []
            if isinstance(av, list): merged += av
            if isinstance(bv, list): merged += bv
            # dedupe bei Listen
            seen = set()
            out = []
            for item in merged:
                if isinstance(item, str) and item.strip() and item not in seen:
                    out.append(item)
                    seen.add(item)
            base[k] = out
        elif isinstance(base[k], str):
            base[k] = (av or bv or "")
    # cashflow_radar
    base["cashflow_radar"]["idee"] = (
        (a.get("cashflow_radar") or {}).get("idee")
        or (b.get("cashflow_radar") or {}).get("idee")
        or ""
    )
    # team_rolle
    base["team_rolle"]["openai"] = bool(a.get("team_rolle", {}).get("openai"))
    base["team_rolle"]["claude"] = bool(b.get("team_rolle", {}).get("claude"))
    base["team_rolle"]["perplexity"] = bool(a.get("team_rolle", {}).get("perplexity") or b.get("team_rolle", {}).get("perplexity"))
    return base


async def call_perplexity(prompt: str, system: str, model: str, timeout: float) -> str:
    """
    Perplexity API Client - async implementation
    
    Args:
        prompt: User prompt
        system: System prompt  
        model: Model name (default: sonar)
        timeout: Request timeout in seconds
        
    Returns:
        Response text from Perplexity API
        
    Raises:
        httpx.HTTPError: On API errors
        ValueError: On invalid response format
    """
    if not PPLX_API_KEY:
        raise ValueError("PPLX_API_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": f"{system}\n\n{prompt}"}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=body
            )
            response.raise_for_status()
            
            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise ValueError("Invalid response format from Perplexity API")
                
            return data["choices"][0]["message"]["content"]
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ValueError("auth")
        elif e.response.status_code == 429:
            raise ValueError("rate_limit")
        elif e.response.status_code >= 500:
            raise ValueError("server")
        else:
            raise ValueError(f"server")
    except httpx.TimeoutException:
        raise ValueError("timeout")
    except Exception as e:
        raise ValueError(f"server")


def ask_perplexity(user_text: str) -> Dict[str, Any]:
    """
    Synchron wrapper for Perplexity API call
    Uses asyncio to run the async call_perplexity function
    """
    if not PPLX_API_KEY:
        return {}
    
    prompt = PROMPT_TEMPLATE.format(user_text=user_text)
    
    # Retry-Mechanismus mit exponentieller Backoff
    for attempt in range(RETRY_COUNT + 1):
        try:
            # Async call in sync context
            result = asyncio.run(call_perplexity(
                prompt=prompt,
                system="Du bist Rico 4.0 - ein strukturierter Business-Assistent.",
                model=PPLX_MODEL,
                timeout=REQUEST_TIMEOUT
            ))
            
            data = _json_from_text(result)
            if data:
                data.setdefault("cashflow_radar", {}).setdefault("idee", "")
                data.setdefault("team_rolle", {})["perplexity"] = True
            return data
            
        except Exception as e:
            if attempt < RETRY_COUNT:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Perplexity API Fehler (Versuch {attempt + 1}/{RETRY_COUNT + 1}): {e}")
                print(f"Warte {wait_time} Sekunden vor erneutem Versuch...")
                time.sleep(wait_time)
            else:
                print(f"Perplexity API endgültig fehlgeschlagen nach {RETRY_COUNT + 1} Versuchen: {e}")
                # Einheitliches Fehler-Mapping
                error_type = "server"
                if "auth" in str(e).lower():
                    error_type = "auth"
                elif "rate_limit" in str(e).lower():
                    error_type = "rate_limit"
                elif "timeout" in str(e).lower():
                    error_type = "timeout"
                return {
                    "error": error_type,
                    "team_rolle": {"openai": False, "claude": False, "perplexity": False}
                }
    
    return {}