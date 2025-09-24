# backend/app/services/providers/claude_client.py
from __future__ import annotations
import time
import requests
from typing import Dict, Any, List, Optional

class ClaudeClient:
    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str, timeout_s: float, retries: int):
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.retries = retries

    def _headers(self) -> Dict[str, str]:
        # ⚠️ Wichtig: KEIN Authorization: Bearer; NUR diese Header!
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
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
        
        # Debug: Log die verwendeten Header und das Modell
        print(f"DEBUG Claude using model: {self.model}")
        print(f"DEBUG Claude headers: {self._headers()}")

        attempt, start = 0, time.time()
        while True:
            attempt += 1
            try:
                resp = requests.post(self.BASE_URL, headers=self._headers(),
                                     json=payload, timeout=self.timeout_s)
            except requests.exceptions.Timeout:
                if attempt <= self.retries:
                    continue
                return {"error_type": "timeout", "message_safe": "Claude timeout", "provider": "claude"}
            except requests.exceptions.RequestException:
                if attempt <= self.retries:
                    continue
                return {"error_type": "server", "message_safe": "Claude request error", "provider": "claude"}

            dur = round(time.time() - start, 3)
            s = resp.status_code
            if s == 200:
                data = resp.json()
                choice = (data.get("content") or data.get("choices") or [{}])[0]
                # Anthropic /messages liefert "content" (array of blocks) – wir vereinfachen:
                content = ""
                if "text" in choice:
                    content = choice["text"]
                elif isinstance(choice, dict) and "message" in choice:
                    content = (choice["message"] or {}).get("content", "")
                usage = data.get("usage", {}) or {}
                return {
                    "content": content,
                    "tokens_in": usage.get("input_tokens") or usage.get("prompt_tokens"),
                    "tokens_out": usage.get("output_tokens") or usage.get("completion_tokens"),
                    "provider": "claude",
                    "provider_model": self.model,
                    "duration_s": dur,
                    "finish_reason": (data.get("stop_reason") or "stop"),
                }

            if s in (401, 403):
                err = {"error_type": "auth", "http_status": s, "message_safe": "Claude auth error", "provider": "claude"}
            elif s == 429:
                err = {"error_type": "rate_limit", "http_status": s, "message_safe": "Claude rate limit", "provider": "claude"}
            elif 500 <= s < 600:
                err = {"error_type": "server", "http_status": s, "message_safe": "Claude server error", "provider": "claude"}
            else:
                err = {"error_type": "server", "http_status": s, "message_safe": "Claude unknown error", "provider": "claude"}

            if attempt <= self.retries:
                continue
            return err
