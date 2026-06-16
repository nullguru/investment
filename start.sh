#!/usr/bin/env bash
# Ensure .venv exists, install dependencies, and run the app.
# Usage:
#   ./start.sh          — start web server (FastAPI + frontend)
#   ./start.sh cli ...  — run CLI command (e.g. ./start.sh cli sharia TCS)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer mise-managed Python 3.13 if available, fall back to system python3
MISE_PYTHON="$HOME/.local/share/mise/installs/python/3.13.7/bin/python3.13"
if [ -x "$MISE_PYTHON" ]; then
  PYTHON="$MISE_PYTHON"
else
  PYTHON="python3"
fi

if [ ! -d ".venv" ] || [ ! -x ".venv/bin/python" ]; then
  echo "Creating .venv with $PYTHON..."
  "$PYTHON" -m venv .venv
fi

echo "Installing dependencies..."
.venv/bin/pip install -q -r requirements.txt

if [ "$1" = "cli" ]; then
  shift
  exec .venv/bin/python cli.py "$@"
fi

echo "Starting server (FastAPI + frontend at http://localhost:8000)..."
echo "CLI also available: ./cli.py --help"
exec .venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
