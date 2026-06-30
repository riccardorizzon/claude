#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

if python3 -m venv .venv 2>/dev/null; then
  source .venv/bin/activate
  pip install -q -r chat/requirements.txt
else
  echo "venv non disponibile, uso pip di sistema"
  pip3 install -q -r chat/requirements.txt
fi

: "${CHAT_PORT:=8765}"
: "${CHAT_HOST:=0.0.0.0}"

echo "Avvio Cursor Mini Chat su http://${CHAT_HOST}:${CHAT_PORT}"
echo "Auth: imposta CURSOR_API_KEY oppure usa CHAT_USE_MOCK=1 per demo"
python chat/run.py
