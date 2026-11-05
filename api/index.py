"""
WorkPulse — Vercel Serverless Function API Entrypoint.
Re-exports the application instance for standard `/api` folder convention.
"""

from app import app, application, handler

__all__ = ["app", "application", "handler"]
