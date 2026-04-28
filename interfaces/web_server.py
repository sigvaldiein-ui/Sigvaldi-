"""Alvitur.is — Enterprise AI vefþjónn (Sprint 71 Track A complete).

Ultra-thin inngangspunktur. Öll virkni er í:
  - interfaces/app_factory.py (app creation)
  - interfaces/routes/ (allir endpoints)
  - interfaces/middleware/ (öryggi + errors)
  - interfaces/utils/ (helpers, quota, rate_limit)
  - interfaces/config_runtime.py (runtime globals)
"""
import os
import uvicorn
from dotenv import load_dotenv

# Hlaða .env áður en app er búið til (yfirskrifar EKKI núverandi env breytur)
load_dotenv("/workspace/.env", override=False)

from interfaces.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "interfaces.web_server:app",
        host="0.0.0.0",
        port=8000,
        workers=3,
        timeout_keep_alive=60,
    )
