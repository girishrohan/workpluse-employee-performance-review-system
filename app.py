"""
WorkPulse — Employee Performance Review System
Unified Application Entry Point.

This module provides dual-mode execution:
1. Vercel Serverless & WSGI Runtime:
   Exports top-level variables `app`, `application`, and `handler` for
   Vercel's Python runtime (@vercel/python).
2. Streamlit Interactive Presentation UI:
   When executed via `streamlit run app.py` (or `python -m streamlit run app.py`),
   detects the active Streamlit runtime and launches the full interactive UI.
"""

import os
import sys

# -----------------------------------------------------------------------------
# 1. Initialize & Export WSGI Application for Vercel Serverless Runtime
# -----------------------------------------------------------------------------
from services.api_service import create_app

app = create_app()
application = app
handler = app

# -----------------------------------------------------------------------------
# 2. Check for Active Streamlit Runtime
# -----------------------------------------------------------------------------
try:
    import streamlit as st
    _is_streamlit = hasattr(st, "runtime") and st.runtime.exists()
except Exception:
    _is_streamlit = False

if _is_streamlit:
    from workpulse_ui import main
    main()

# -----------------------------------------------------------------------------
# 3. Direct CLI Execution (python app.py)
# -----------------------------------------------------------------------------
if __name__ == "__main__" and not _is_streamlit:
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"============================================================")
    print(f"  WorkPulse — Employee Performance Review System")
    print(f"  REST API & Web Portal active on http://127.0.0.1:{port}")
    print(f"  For Streamlit UI, run: python -m streamlit run app.py")
    print(f"============================================================")
    app.run(host=host, port=port, debug=False)
