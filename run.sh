#!/bin/bash
cd "$(dirname "$0")/ai-ml"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt
echo "Pathwise is running at http://localhost:8000"
(sleep 5; (xdg-open http://localhost:8000 || open http://localhost:8000) >/dev/null 2>&1) &
.venv/bin/python -m uvicorn api.app:app --port 8000
