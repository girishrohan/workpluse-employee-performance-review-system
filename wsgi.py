"""
WorkPulse WSGI Entrypoint for Vercel and other WSGI servers.

Usage with Vercel:
    In vercel.json:
    {
      "functions": {
        "wsgi.py": {
          "runtime": "python3.11"
        }
      }
    }

Usage with Gunicorn:
    gunicorn wsgi:app

Usage with uWSGI:
    uwsgi --http :8000 --module wsgi:app
"""

from app import app, application, handler

__all__ = ["app", "application", "handler"]