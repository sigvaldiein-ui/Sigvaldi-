#!/bin/bash
cd /workspace/Sigvaldi-/interfaces
export PYTHONPATH=/workspace/Sigvaldi-
python3 -m uvicorn web_server:app --host 0.0.0.0 --port 8000
