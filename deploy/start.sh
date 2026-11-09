#!/bin/sh
# Container entry point: fetch model weights, then serve the API.
set -e
python -m backend.deploy.models download
exec python -m uvicorn backend.app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-7860}" --workers 1
