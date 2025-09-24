# backend/app/services/providers/pplx_client.py
from __future__ import annotations
import time
import requests
from typing import Dict, Any, List, Optional

class PerplexityClient:
    BASE_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str, model: str, timeout_s: float, retries: int):
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.retries = retries

    def _headers(self) -> Dict[str, str]:
        # Perplexity nutzt Authorization: Bearer
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2,
                 max_tokens: int = 800, stream: bool = False, system: Optional[str] = None) -> Dict[str, Any]:
        chat = []
        if system:
            chat.append({"role": "system", "content": system})
        chat.extend(messages)

        payload = {
            "model": self.model,
            "messages": chat,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # Debug: Log das verwendete Modell
        print(f"DEBUG Perplexity using model: {self.model}")

        attempt, start = 0, time.time()
        while True:
            attempt += 1
            try:
                resp = requests.post(self.BASE_URL, headers=self._headers(),
                                     json=payload, timeout=self.timeout_s)
            except requests.exceptions.Timeout:
                if attempt <= self.retries:
                    continue
                return {"error_type": "timeout", "message_safe": "Perplexity timeout", "provider": "perplexity"}
            except requests.exceptions.RequestException:
                if attempt <= self.retries:
                    continue
                return {"error_type": "server", "message_safe": "Perplexity request error", "provider": "perplexity"}

            dur = round(time.time() - start, 3)
            s = resp.status_code
            if s == 200:
                try:
                    data = resp.json()
                    
                    # Perplexity API-Struktur: choices[0].message.content
                    choices = data.get("choices", [])
                    if not choices:
                        return {"error_type": "server", "message_safe": "Perplexity no choices in response", "provider": "perplexity"}
                    
                    choice = choices[0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    
                    if not content:
                        return {"error_type": "server", "message_safe": "Perplexity empty content", "provider": "perplexity"}
                    
                    usage = data.get("usage", {}) or {}
                    return {
                        "content": content,
                        "tokens_in": usage.get("prompt_tokens"),
                        "tokens_out": usage.get("completion_tokens"),
                        "provider": "perplexity",
                        "provider_model": self.model,
                        "duration_s": dur,
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                except Exception as e:
                    # Falls JSON-Parsing fehlschlägt, als Server-Fehler behandeln
                    return {"error_type": "server", "message_safe": f"Perplexity response parsing error: {str(e)[:100]}", "provider": "perplexity"}

            # Alle anderen Status-Codes behandeln
            if s in (401, 403):
                err = {"error_type": "auth", "http_status": s, "message_safe": "Perplexity auth error", "provider": "perplexity"}
            elif s == 429:
                err = {"error_type": "rate_limit", "http_status": s, "message_safe": "Perplexity rate limit", "provider": "perplexity"}
            elif 500 <= s < 600:
                err = {"error_type": "server", "http_status": s, "message_safe": "Perplexity server error", "provider": "perplexity"}
            else:
                # Für alle anderen Status-Codes (inkl. 200 mit Parsing-Fehlern)
                try:
                    error_data = resp.json()
                    error_msg = error_data.get("error", {}).get("message", f"HTTP {s}")
                except:
                    error_msg = f"HTTP {s}"
                err = {"error_type": "server", "http_status": s, "message_safe": f"Perplexity error: {error_msg}", "provider": "perplexity"}

            if attempt <= self.retries:
                continue
            return err
