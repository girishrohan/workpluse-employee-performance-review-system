"""
WorkPulse — Employee Performance Review System.
Streamlit-only application entry point.

Run with: streamlit run app.py
"""

import os
import sys

import streamlit as st

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workpulse_ui import main

if __name__ == "__main__":
    main()