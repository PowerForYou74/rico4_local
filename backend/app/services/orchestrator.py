from typing import Dict, Any

class RicoOrchestrator:
    def call_openai(self, prompt: str) -> Dict[str, Any]:
        return {"provider": "openai", "ok": True, "summary": "stub response"}

    def call_claude(self, prompt: str) -> Dict[str, Any]:
        return {"provider": "claude", "ok": True, "notes": "stub response"}

    def assemble_results(self, pieces: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "kurz_zusammenfassung": "Ergebnis aus mehreren KIs (Stub).",
            "kernbefunde": ["Punkt 1", "Punkt 2"],
            "action_plan": ["Schritt 1", "Schritt 2"],
            "risiken": ["Annahmen, Datenqualität"],
            "cashflow_radar": {"idee": "Stub-Idee"},
            "team_rolle": {
                "openai": bool(pieces.get("openai")),
                "claude": bool(pieces.get("claude")),
            },
        }

    def run_rico_loop(self, user_prompt: str) -> Dict[str, Any]:
        o = self.call_openai(user_prompt)
        c = self.call_claude(user_prompt)
        return self.assemble_results({"openai": o, "claude": c})