# backend/app/services/orchestrator.py
import os
import re
import json
import time
import asyncio
from typing import Dict, Any, Optional, Tuple, Callable

import httpx

# Zentrale Config verwenden
from ..config import (
    OPENAI_API_KEY, CLAUDE_API_KEY, PPLX_API_KEY,
    OPENAI_MODEL, CLAUDE_MODEL, PPLX_MODEL,
    LLM_TIMEOUT_SECONDS, LLM_RETRIES, AUTO_RACE_TIMEOUT
)

REQUEST_TIMEOUT = LLM_TIMEOUT_SECONDS
RETRY_COUNT = LLM_RETRIES

# ------------------------------------------------------------
# Ziel-Schema (passt zu deinem Streamlit-Renderer)
# ------------------------------------------------------------
SCHEMA_EXAMPLE: Dict[str, Any] = {
    "kurz_zusammenfassung": "string",
    "kernbefunde": ["string", "..."],
    "action_plan": ["string", "..."],
    "risiken": ["string", "..."],
    "cashflow_radar": {"idee": "string"},
    "team_rolle": {"openai": False, "claude": False, "perplexity": False},
    "aufgabenverteilung": ["string", "..."],
}

# ------------------------------------------------------------
# Hilfen: Fallback + JSON-Recovery
# ------------------------------------------------------------
def normalize_result(text: str, provider: str) -> Dict[str, Any]:
    """Sinnvolles Fallback, falls Modelle kein valides JSON liefern."""
    # Sicherstellen, dass text ein String ist
    safe_text = str(text) if text is not None else ""
    
    return {
        "kurz_zusammenfassung": safe_text.strip()
        or "Analyse der aktuellen Situation und Identifikation von Verbesserungspotenzialen.",
        "kernbefunde": [],
        "action_plan": [],
        "risiken": [],
        "cashflow_radar": {"idee": ""},
        "team_rolle": {"openai": provider == "openai", "claude": provider == "claude", "perplexity": provider == "perplexity"},
        "aufgabenverteilung": [],
        "orchestrator_log": "",
        "raw_text": safe_text or "",
        "meta": {"provider": provider},
    }


def _coerce_list(x: Any) -> list:
    if isinstance(x, list):
        return [str(i) for i in x]
    if isinstance(x, str) and x.strip():
        # einfache Aufzählung durch Zeilen umbrechen
        return [s.strip("- •\t ").strip() for s in x.splitlines() if s.strip()]
    return []


def massage_to_schema(d: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Synonyme mappen & Felder in das UI-Schema biegen."""
    if not isinstance(d, dict):
        return normalize_result(str(d), provider)

    mapped = {
        "kurz_zusammenfassung": d.get("kurz_zusammenfassung")
        or d.get("kurzfassung")
        or d.get("summary")
        or "",
        "kernbefunde": _coerce_list(
            d.get("kernbefunde") or d.get("kern_ergebnisse") or d.get("key_findings") or []
        ),
        "action_plan": _coerce_list(d.get("action_plan") or d.get("plan") or []),
        "risiken": _coerce_list(d.get("risiken") or d.get("annahmen") or d.get("risks") or []),
        "cashflow_radar": d.get("cashflow_radar") or d.get("cashflow") or {"idee": ""},
        "team_rolle": d.get("team_rolle") or {"openai": False, "claude": False, "perplexity": False},
        "aufgabenverteilung": _coerce_list(
            d.get("aufgabenverteilung") or d.get("aufgaben") or d.get("tasks") or d.get("task_distribution") or []
        ),
        "orchestrator_log": str(d.get("orchestrator_log") or d.get("log") or d.get("orchestrator") or ""),
    }

    # Typen absichern
    if not isinstance(mapped["cashflow_radar"], dict):
        mapped["cashflow_radar"] = {"idee": str(mapped["cashflow_radar"])}
    elif "idee" not in mapped["cashflow_radar"]:
        # Falls cashflow_radar ein Dict ist, aber kein "idee" Feld hat
        mapped["cashflow_radar"]["idee"] = ""

    if not isinstance(mapped["team_rolle"], dict):
        mapped["team_rolle"] = {"openai": False, "claude": False, "perplexity": False}

    mapped["team_rolle"]["openai"] = bool(
        mapped["team_rolle"].get("openai", False) or provider == "openai"
    )
    mapped["team_rolle"]["claude"] = bool(
        mapped["team_rolle"].get("claude", False) or provider == "claude"
    )
    mapped["team_rolle"]["perplexity"] = bool(
        mapped["team_rolle"].get("perplexity", False) or provider == "perplexity"
    )

    mapped["meta"] = {"provider": provider}
    mapped["raw_text"] = d.get("raw_text") or ""
    return mapped


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Robustes JSON-Parsing (auch wenn im Codeblock oder mit einfachen Quotes)."""
    if not isinstance(text, str) or not text.strip():
        return None

    candidates = [text]

    # Codeblöcke extrahieren
    for m in re.finditer(r"```(?:json)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL):
        block = m.group(1).strip()
        if block:
            candidates.append(block)

    for raw in candidates:
        # 1) direkt versuchen
        try:
            return json.loads(raw)
        except Exception:
            pass
        # 2) einfache Quotes -> doppelte (vorsichtig)
        try:
            fixed = re.sub(r'(?<!\\)\'', '"', raw)
            return json.loads(fixed)
        except Exception:
            pass
        # 3) Backticks entfernen
        try:
            stripped = raw.strip("` \n\t")
            return json.loads(stripped)
        except Exception:
            pass

    return None


# ------------------------------------------------------------
# Prompts
# ------------------------------------------------------------
def system_prompt(task_type: str) -> str:
    return (
        "You are Rico 4.0 - a structured business assistant.\n"
        f"Task-Type: {task_type}\n"
        "RESPOND EXCLUSIVELY with a JSON object in this schema (no explanations, no flowing text):\n\n"
        + '{\n  "kurz_zusammenfassung": "string",\n  "kernbefunde": ["string", "..."],\n  "action_plan": ["string", "..."],\n  "risiken": ["string", "..."],\n  "cashflow_radar": {"idee": "string"},\n  "team_rolle": {"openai": false, "claude": false, "perplexity": false},\n  "aufgabenverteilung": ["string", "..."]\n}'
        + "\n\n"
        "Rules:\n"
        "- Return only valid JSON (without markdown code blocks).\n"
        "- Short, concise bullet lists.\n"
        "- Always include fields. Empty lists are allowed."
    )


def user_prompt(prompt: str) -> str:
    return f"Use this content:\n\n{prompt}"


# ------------------------------------------------------------
# LLM-Aufrufe
# ------------------------------------------------------------
async def _call_openai(prompt: str, task_type: str) -> Tuple[bool, Dict[str, Any], float]:
    if not OPENAI_API_KEY:
        return False, {"error": "OPENAI_API_KEY missing"}, 0.0

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt(task_type)},
            {"role": "user", "content": user_prompt(prompt)},
        ],
        "temperature": 0.2,
    }

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions", headers=headers, json=body
            )
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            parsed = try_parse_json(text)
            res = massage_to_schema(
                parsed if parsed is not None else {"kurz_zusammenfassung": text},
                "openai",
            )
            dur = time.perf_counter() - t0
            
            # Orchestrator-Log füllen
            json_status = "✓ JSON geparst" if parsed is not None else "✗ JSON-Fehler, Fallback verwendet"
            res["orchestrator_log"] = f"OpenAI {OPENAI_MODEL} | {round(dur, 2)}s | {json_status}"
            res["meta"].update({"duration_s": round(dur, 3)})
            return True, res, dur
    except Exception as e:
        dur = time.perf_counter() - t0
        error_msg = f"openai: {e}"
        return False, {"error": error_msg, "orchestrator_log": f"OpenAI {OPENAI_MODEL} | {round(dur, 2)}s | ✗ Fehler: {str(e)[:100]}"}, dur


def _extract_claude_text(data: Dict[str, Any]) -> str:
    """Claude v1/messages → content: [{type:'text', text:'...'}, …] - robust extrahieren"""
    parts = []
    
    # Hauptpfad: content-Liste durchgehen
    for blk in data.get("content", []) or []:
        if isinstance(blk, dict) and blk.get("type") == "text":
            t = blk.get("text")
            if isinstance(t, str) and t.strip():
                parts.append(t.strip())
    
    # Fallback: Falls content leer, versuche completion (für ältere API-Versionen)
    if not parts:
        completion = data.get("completion")
        if isinstance(completion, str) and completion.strip():
            parts.append(completion.strip())
    
    # Fallback: Falls immer noch leer, versuche text direkt
    if not parts:
        text = data.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    
    return "\n".join(parts).strip()


async def _call_claude(prompt: str, task_type: str) -> Tuple[bool, Dict[str, Any], float]:
    if not CLAUDE_API_KEY:
        return False, {"error": "CLAUDE_API_KEY missing"}, 0.0

    # Nutze den neuen Claude-Client mit abgesicherten Headern
    from .provider_clients import build_provider_client
    
    t0 = time.perf_counter()
    try:
        client = build_provider_client("claude")
        result = client.generate(
            messages=[{"role": "user", "content": f"{system_prompt(task_type)}\n\n{user_prompt(prompt)}"}],
            temperature=0.2,
            max_tokens=1400
        )
        
        # Prüfe auf Fehler
        if "error_type" in result:
            dur = time.perf_counter() - t0
            error_msg = f"claude: {result.get('message_safe', 'Unknown error')}"
            return False, {"error": error_msg, "orchestrator_log": f"Claude {CLAUDE_MODEL} | {round(dur, 2)}s | ✗ Fehler: {result.get('message_safe', 'Unknown error')}"}, dur
        
        # Extrahiere Text aus Claude-Response
        text = result.get("content", "")
        parsed = try_parse_json(text)
        res = massage_to_schema(
            parsed if parsed is not None else {"kurz_zusammenfassung": text},
            "claude",
        )
        dur = time.perf_counter() - t0
        
        # Orchestrator-Log füllen
        json_status = "✓ JSON geparst" if parsed is not None else "✗ JSON-Fehler, Fallback verwendet"
        res["orchestrator_log"] = f"Claude {CLAUDE_MODEL} | {round(dur, 2)}s | {json_status}"
        res["meta"].update({"duration_s": round(dur, 3)})
        return True, res, dur
    except Exception as e:
        dur = time.perf_counter() - t0
        error_msg = f"claude: {e}"
        return False, {"error": error_msg, "orchestrator_log": f"Claude {CLAUDE_MODEL} | {round(dur, 2)}s | ✗ Fehler: {str(e)[:100]}"}, dur


async def _call_perplexity(prompt: str, task_type: str) -> Tuple[bool, Dict[str, Any], float]:
    if not PPLX_API_KEY:
        return False, {"error": "PPLX_API_KEY missing"}, 0.0

    # Nutze den neuen Perplexity-Client mit abgesicherten Headern
    from .provider_clients import build_provider_client
    
    t0 = time.perf_counter()
    try:
        client = build_provider_client("perplexity")
        result = client.generate(
            messages=[{"role": "user", "content": f"{system_prompt(task_type)}\n\n{user_prompt(prompt)}"}],
            temperature=0.2,
            max_tokens=1000
        )
        
        # Prüfe auf Fehler
        if "error_type" in result:
            dur = time.perf_counter() - t0
            error_msg = f"perplexity: {result.get('message_safe', 'Unknown error')}"
            return False, {"error": error_msg, "orchestrator_log": f"Perplexity {PPLX_MODEL} | {round(dur, 2)}s | ✗ Fehler: {result.get('message_safe', 'Unknown error')}"}, dur
        
        # Extrahiere Text aus Perplexity-Response
        text = result.get("content", "")
        parsed = try_parse_json(text)
        res = massage_to_schema(
            parsed if parsed is not None else {"kurz_zusammenfassung": text},
            "perplexity",
        )
        dur = time.perf_counter() - t0
        
        # Orchestrator-Log füllen
        json_status = "✓ JSON geparst" if parsed is not None else "✗ JSON-Fehler, Fallback verwendet"
        res["orchestrator_log"] = f"Perplexity {PPLX_MODEL} | {round(dur, 2)}s | {json_status}"
        res["meta"].update({"duration_s": round(dur, 3)})
        return True, res, dur
    except Exception as e:
        dur = time.perf_counter() - t0
        error_msg = f"perplexity: {e}"
        return False, {"error": error_msg, "orchestrator_log": f"Perplexity {PPLX_MODEL} | {round(dur, 2)}s | ✗ Fehler: {str(e)[:100]}"}, dur


# ------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------
class RicoOrchestrator:
    def __init__(self) -> None:
        pass

    async def run_rico_loop(
        self,
        prompt: str,
        task_type: str = "analysis",
        provider: str = "auto",
    ) -> Dict[str, Any]:
        """
        Rückgabe:
        {
          "ok": bool,
          "task_type": str,
          "used_provider": "openai"|"claude"|None,
          "result": {...}  # im UI-Schema
        }
        """

        async def with_retry(fn: Callable[[], asyncio.Future]):
            last = (False, {"error": "unknown"}, 0.0)
            for _ in range(max(RETRY_COUNT, 1)):
                ok, res, dur = await fn()
                if ok:
                    return ok, res, dur
                last = (ok, res, dur)
            return last

        # Fester Provider
        if provider == "openai":
            ok, res, _ = await with_retry(lambda: _call_openai(prompt, task_type))
            return {
                "ok": ok,
                "task_type": task_type,
                "used_provider": "openai",
                "result": res,
            }

        if provider == "claude":
            ok, res, _ = await with_retry(lambda: _call_claude(prompt, task_type))
            return {
                "ok": ok,
                "task_type": task_type,
                "used_provider": "claude",
                "result": res,
            }

        if provider == "perplexity":
            ok, res, _ = await with_retry(lambda: _call_perplexity(prompt, task_type))
            return {
                "ok": ok,
                "task_type": task_type,
                "used_provider": "perplexity",
                "result": res,
            }

        # AUTO: parallelisieren, nimm ersten Erfolg
        async def openai_job():
            return await with_retry(lambda: _call_openai(prompt, task_type))

        async def claude_job():
            return await with_retry(lambda: _call_claude(prompt, task_type))

        async def perplexity_job():
            return await with_retry(lambda: _call_perplexity(prompt, task_type))

        # Nur Provider mit vorhandenen Keys hinzufügen
        tasks = {asyncio.create_task(openai_job()), asyncio.create_task(claude_job())}
        if PPLX_API_KEY:  # Nur wenn PPLX_API_KEY gesetzt ist
            tasks.add(asyncio.create_task(perplexity_job()))

        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
            timeout=AUTO_RACE_TIMEOUT
        )

        winner: Optional[Dict[str, Any]] = None
        used: Optional[str] = None
        ok_flag = False

        for d in done:
            try:
                ok, res, _ = d.result()
                if ok:
                    winner, ok_flag, used = res, True, res.get("meta", {}).get("provider")
                    break
            except Exception as e:
                winner = {"error": f"auto first result error: {e}"}

        # Sauberes Cleanup von abgebrochenen Tasks
        for p in pending:
            try:
                p.cancel()
                # Warten auf tatsächliche Cancellation
                await asyncio.wait_for(p, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass  # Erwartetes Verhalten bei Cancellation

        if not ok_flag:
            # versuche den anderen noch
            for d in done:
                try:
                    ok, res, _ = d.result()
                    if ok:
                        winner, ok_flag, used = res, True, res.get("meta", {}).get("provider")
                        break
                except Exception:
                    pass

        # Notfall: seriell
        if not ok_flag:
            ok2, res2, _ = await openai_job()
            if ok2:
                winner, ok_flag, used = res2, True, "openai"
            else:
                ok3, res3, _ = await claude_job()
                if ok3:
                    winner, ok_flag, used = res3, True, "claude"
                else:
                    # Perplexity als letzter Versuch (nur wenn Key vorhanden)
                    if PPLX_API_KEY:
                        ok4, res4, _ = await perplexity_job()
                        if ok4:
                            winner, ok_flag, used = res4, True, "perplexity"
                        else:
                            winner = {
                                "error": {"openai": res2.get("error"), "claude": res3.get("error"), "perplexity": res4.get("error")}
                            }
                    else:
                        winner = {
                            "error": {"openai": res2.get("error"), "claude": res3.get("error")}
                        }

        # Meta-Daten korrekt setzen
        if ok_flag and winner:
            winner["team_rolle"]["perplexity"] = (used == "perplexity")
            winner["meta"].update({
                "provider": used,
                "provider_model": {
                    "openai": OPENAI_MODEL,
                    "claude": CLAUDE_MODEL,
                    "perplexity": PPLX_MODEL
                }.get(used, ""),
                "used_provider": used,
                "duration_s": winner.get("meta", {}).get("duration_s", 0.0)
            })
        
        return {
            "ok": ok_flag,
            "task_type": task_type,
            "used_provider": used,
            "result": winner,
        }

    async def run_autopilot_task(self, task: Dict) -> Dict[str, Any]:
        """
        Führt einen Autopilot-Task aus.
        
        Args:
            task: Task-Dictionary mit id, prompt, task_type, provider, etc.
            
        Returns:
            Dict mit success, task_id, timestamp und result
        """
        from datetime import datetime
        
        task_id = task.get('id', 'unknown')
        prompt = task.get('prompt', '')
        task_type = task.get('task_type', 'analysis')
        provider = task.get('provider', 'auto')
        
        logger = __import__('logging').getLogger(__name__)
        
        try:
            logger.info(f"Starte Autopilot-Task: {task_id} ({task_type})")
            
            # Rico-Orchestrator verwenden
            result = await self.run_rico_loop(prompt, task_type, provider)
            
            return {
                'success': result['ok'],
                'task_id': task_id,
                'task_type': task_type,
                'provider': result.get('used_provider', provider),
                'timestamp': datetime.now().isoformat(),
                'result': result.get('result', {}),
                'error': result.get('result', {}).get('error') if not result['ok'] else None
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Autopilot-Task {task_id}: {e}")
            return {
                'success': False,
                'task_id': task_id,
                'task_type': task_type,
                'provider': provider,
                'timestamp': datetime.now().isoformat(),
                'result': {},
                'error': str(e)
            }