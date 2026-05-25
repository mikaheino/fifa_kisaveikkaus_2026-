"""Shared 90s-arcade theme — applied at the top of every app page.

Single source of truth so every page has the same:
  - background (green-field stripes + ghosted Maradona watermark)
  - fonts (Bungee headers, VT323 captions, Roboto body via Streamlit default)
  - widget styling (chunky gold expanders, red-CTA primary buttons)

Call ``apply_theme()`` once per page, before any other UI. Safe to call
twice; Streamlit just emits two duplicate <style> blocks.
"""
from __future__ import annotations

import base64
import os

import streamlit as st

_MARADONA = os.path.join(os.path.dirname(__file__), "..", "assets", "maradona.gif")


def apply_theme() -> None:
    """Inject background, fonts, and chunky widget styles for this page."""
    if os.path.exists(_MARADONA):
        _b64 = base64.b64encode(open(_MARADONA, "rb").read()).decode()
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: none !important;
                background:
                    repeating-linear-gradient(
                        90deg,
                        rgba(40, 90, 50, 0.10) 0px,
                        rgba(40, 90, 50, 0.10) 80px,
                        rgba(20, 60, 35, 0.10) 80px,
                        rgba(20, 60, 35, 0.10) 160px
                    ),
                    radial-gradient(
                        ellipse at top,
                        #0d2418 0%,
                        #061308 65%,
                        #02080a 100%
                    ) !important;
            }}
            [data-testid="stAppViewContainer"]::before {{
                content: "";
                position: fixed;
                inset: 0;
                background-image: url("data:image/gif;base64,{_b64}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                opacity: 0.16;
                filter: sepia(0.55) contrast(1.1) saturate(0.85);
                mix-blend-mode: screen;
                pointer-events: none;
                z-index: 0;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Bungee&display=swap');

        /* Section headers — Italia '90 broadcast vibe */
        [data-testid="stMainBlockContainer"] h1,
        [data-testid="stMainBlockContainer"] h2,
        [data-testid="stMainBlockContainer"] h3 {
            font-family: 'Bungee', 'Impact', sans-serif !important;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #f5e8c8 !important;
            text-shadow: 3px 3px 0 #1a1408, 6px 6px 0 rgba(0,0,0,0.5);
        }
        [data-testid="stMainBlockContainer"] strong {
            font-family: 'Bungee', 'Impact', sans-serif !important;
            letter-spacing: 0.5px;
            color: #ffd95c !important;
        }
        /* Pixel-y captions for the arcade subtitle look */
        [data-testid="stCaptionContainer"], .stCaption {
            font-family: 'VT323', 'Courier New', monospace !important;
            font-size: 1.05rem !important;
            color: #b8d4a8 !important;
            letter-spacing: 0.5px;
        }
        /* Chunky expander frames */
        [data-testid="stExpander"] {
            border: 2px solid #f5c842 !important;
            border-radius: 0 !important;
            background: linear-gradient(180deg, #0e2814, #061308) !important;
            box-shadow:
                4px 4px 0 #1a1408,
                inset 0 0 0 1px rgba(0,0,0,0.55) !important;
            margin-bottom: 14px !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] details > summary {
            font-family: 'Bungee', 'Impact', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #ffd95c !important;
        }
        /* Primary button — NFL-broadcast red CTA */
        [data-testid="stMainBlockContainer"] [kind="primary"],
        [data-testid="stMainBlockContainer"] button[kind="primary"] {
            font-family: 'Bungee', 'Impact', sans-serif !important;
            font-size: 1.1rem !important;
            letter-spacing: 2px;
            text-transform: uppercase;
            background: linear-gradient(180deg, #d83434 0%, #921818 100%) !important;
            color: #fff5d0 !important;
            border: 3px solid #ffd95c !important;
            border-radius: 0 !important;
            box-shadow:
                5px 5px 0 #1a1408,
                inset 0 2px 0 rgba(255,230,180,0.6) !important;
            text-shadow: 2px 2px 0 #1a1408;
        }
        [data-testid="stMainBlockContainer"] [kind="primary"]:hover {
            transform: translate(-2px, -2px);
            box-shadow: 7px 7px 0 #1a1408, inset 0 2px 0 rgba(255,230,180,0.6) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
