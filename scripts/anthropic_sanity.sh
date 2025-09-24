#!/usr/bin/env bash
set -euo pipefail

# Sanity-Check für Anthropic API nach Header-Fix
# Nutze nur lokal, nie in CI committen

[ -z "${ANTHROPIC_API_KEY:-}" ] && echo "❌ Set ANTHROPIC_API_KEY" && exit 1

echo "🔍 Anthropic API Sanity-Check"
echo "================================"

echo "→ Verfügbare Modelle:"
curl -s https://api.anthropic.com/v1/models \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" | head -c 400 ; echo

echo ""
echo "→ Test /messages mit korrekten Headern:"
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-7-sonnet-20250219","max_tokens":20,"messages":[{"role":"user","content":"Sag einen Fakt über Pferde."}]}' \
  | head -c 400 ; echo

echo ""
echo "✅ Sanity-Check abgeschlossen"
echo "→ Falls beide Calls funktionieren, sind die Header korrekt gesetzt"
