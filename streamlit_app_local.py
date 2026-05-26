"""Local development entry point — uses MockSession instead of Snowflake."""
import base64
import os
import streamlit as st
from mock_session import MockSession

def _img_b64(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), filename)
    return base64.b64encode(open(path, "rb").read()).decode()

st.set_page_config(
    page_title="FIFA-veikkaus 2026 (local)",
    page_icon="assets/logo_2026.png",
    layout="centered",
)

_ioag_b64 = _img_b64("assets/maradona.gif")
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Press+Start+2P&display=swap');

    body, p, div, h1, h2, h3, h4, h5, h6,
    label, input, button, select, textarea, a, li, td, th, caption,
    [data-testid] > div, [data-testid] > p, [data-testid] > label {{
        font-family: 'Roboto', Arial, sans-serif !important;
    }}

    .stApp {{
        background-image: url("data:image/gif;base64,{_ioag_b64}");
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
        color: #f5e8c8;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(20, 14, 8, 0.68);
        pointer-events: none;
        z-index: 0;
    }}

    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp .stMarkdown, .stApp .stText {{ color: #f5e8c8 !important; }}

    [data-testid="stSidebar"] {{ color: #f5e8c8 !important; }}
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {{ color: #f5e8c8 !important; }}

    [data-testid="stForm"] {{ border: 0px; }}

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] > div,
    [data-testid="stNumberInput"] > div > div {{
        background-color: rgba(245, 220, 150, 0.94) !important;
        color: #1a1408 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(250, 230, 180, 0.55) !important;
    }}
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        min-height: 38px !important;
        padding: 6px 10px !important;
    }}
    [data-testid="stTextInput"] input::placeholder {{ color: #8a6a3a !important; }}

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        background-color: rgba(245, 220, 150, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        min-height: 38px !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(250, 230, 180, 0.55) !important;
    }}

    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] > div > div {{
        background-color: rgba(245, 220, 150, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(250, 230, 180, 0.55) !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="select"] * {{ color: #1a1408 !important; }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background-color: rgba(170, 120, 30, 0.85) !important;
        border-radius: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button {{ color: #f5e8c8 !important; }}
    [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stSelectbox"] [data-baseweb="select"] input {{ color: #1a1408 !important; }}
    [data-testid="stSelectbox"] [data-baseweb="select"] svg {{ fill: #1a1408 !important; }}

    [data-baseweb="popover"] > div {{ background-color: #1f1a0a !important; }}
    [data-baseweb="menu"] li {{ background-color: #1f1a0a !important; color: #f5e8c8 !important; }}
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] [aria-selected="true"] {{ background-color: #3d3014 !important; }}

    [data-testid="stExpander"] {{
        border: none !important;
        border-radius: 0 !important;
        background-color: rgba(40, 28, 10, 0.85) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.85),
            inset 1px 1px rgba(210, 175, 90, 0.50),
            inset -2px -2px rgba(20, 12, 4, 0.65),
            inset 2px 2px rgba(180, 140, 60, 0.22) !important;
    }}
    [data-testid="stExpander"] summary {{
        background-color: rgba(80, 55, 15, 0.85) !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.70),
            inset 1px 1px rgba(210, 175, 90, 0.55) !important;
        padding: 4px 8px !important;
    }}
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {{ color: #f5e8c8 !important; }}

    header[data-testid="stHeader"] {{
        background-color: rgba(20, 14, 8, 0.97) !important;
        border-bottom: 2px solid rgba(150, 110, 30, 0.55) !important;
    }}
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] span,
    header[data-testid="stHeader"] p,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] div {{ color: #f5e8c8 !important; }}
    header[data-testid="stHeader"] [aria-selected="true"],
    header[data-testid="stHeader"] [data-active="true"] {{
        border-bottom: 2px solid #d4a017 !important;
        color: #d4a017 !important;
    }}

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-secondary"] {{
        background-color: rgba(140, 100, 25, 0.85) !important;
        color: #f5e8c8 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(220, 180, 90, 0.70),
            inset -2px -2px rgba(20, 12, 4, 0.65),
            inset 2px 2px rgba(190, 155, 70, 0.28) !important;
    }}
    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {{
        background-color: rgba(190, 140, 35, 0.92) !important;
        color: #f5c842 !important;
    }}
    .stButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active {{
        box-shadow:
            inset -1px -1px rgba(220, 180, 90, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(190, 155, 70, 0.28),
            inset 2px 2px rgba(20, 12, 4, 0.65) !important;
    }}

    /* Horizontal nav radio — 90s amber-CRT arcade cabinet buttons */
    [data-testid="stRadio"] > div,
    div[role="radiogroup"] {{
        display: flex !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 0.7rem !important;
        margin: 0.5rem auto 1.25rem auto !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    div[role="radiogroup"] label {{
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 10px 18px !important;
        min-width: 140px !important;
        border: none !important;
        border-radius: 0 !important;
        cursor: pointer;
        background: linear-gradient(180deg, rgba(45, 30, 8, 0.95), rgba(25, 17, 5, 0.95)) !important;
        transition: background 0.12s ease, box-shadow 0.12s ease;
        box-shadow:
            inset 0 0 0 1px rgba(212, 160, 23, 0.55),
            inset -2px -2px 0 0 rgba(0, 0, 0, 0.75),
            inset 2px 2px 0 0 rgba(245, 200, 66, 0.30),
            0 0 6px rgba(212, 160, 23, 0.25) !important;
    }}
    div[role="radiogroup"] label > div:first-child,
    div[role="radiogroup"] label [data-baseweb="radio"],
    div[role="radiogroup"] label input[type="radio"] {{
        display: none !important;
    }}
    div[role="radiogroup"] label > div:last-child,
    div[role="radiogroup"] label p {{
        margin: 0 !important;
        color: #f5c842 !important;
        font-family: 'Press Start 2P', 'Courier New', monospace !important;
        font-size: 0.65rem !important;
        line-height: 1.4 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        text-shadow:
            0 0 4px rgba(245, 200, 66, 0.65),
            0 0 8px rgba(212, 160, 23, 0.40) !important;
    }}
    div[role="radiogroup"] label:hover {{
        background: linear-gradient(180deg, rgba(70, 48, 12, 0.97), rgba(45, 30, 8, 0.97)) !important;
        box-shadow:
            inset 0 0 0 1px rgba(245, 200, 66, 0.85),
            inset -2px -2px 0 0 rgba(0, 0, 0, 0.70),
            inset 2px 2px 0 0 rgba(245, 200, 66, 0.45),
            0 0 12px rgba(245, 200, 66, 0.45) !important;
    }}
    div[role="radiogroup"] label:hover p {{
        color: #ffe082 !important;
        text-shadow:
            0 0 6px rgba(255, 224, 130, 0.80),
            0 0 14px rgba(245, 200, 66, 0.55) !important;
    }}
    div[role="radiogroup"] label:has(input:checked) {{
        background: linear-gradient(180deg, rgba(110, 75, 18, 0.97), rgba(80, 55, 12, 0.97)) !important;
        box-shadow:
            inset 0 0 0 1px rgba(255, 224, 130, 1.0),
            inset 2px 2px 0 0 rgba(0, 0, 0, 0.70),
            inset -2px -2px 0 0 rgba(255, 224, 130, 0.55),
            0 0 18px rgba(255, 224, 130, 0.65) !important;
    }}
    div[role="radiogroup"] label:has(input:checked) p {{
        color: #fff4c2 !important;
        text-shadow:
            0 0 6px rgba(255, 244, 194, 0.95),
            0 0 14px rgba(255, 220, 100, 0.75),
            0 0 22px rgba(255, 180, 30, 0.55) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "snowpark_session" not in st.session_state:
    st.session_state.snowpark_session = MockSession()

# Match production: streamlit_app.py resolves user_email via CURRENT_USER() and
# admin_results.py gates on it. Set it locally so the admin page works without
# extra setup.
if "user_email" not in st.session_state:
    from mock_session import MOCK_CURRENT_USER
    st.session_state.user_email = MOCK_CURRENT_USER

_logo_b64 = base64.b64encode(open("assets/logo_2026.png", "rb").read()).decode()
st.markdown(
    f'<img src="data:image/png;base64,{_logo_b64}" '
    f'style="width:100%;opacity:0.45;display:block;margin-bottom:0.5rem;" '
    f'alt="FIFA 2026 -veikkaus" />',
    unsafe_allow_html=True,
)

import importlib
import sys

_ADMIN_EMAILS = {
    "mika.heino@recordlydata.com",
    "mikko.sulonen@recordlydata.com",
    "marko.laitinen@recordlydata.com",
}

_page_titles = ["Omat veikkaukset", "Tilanne", "Säännöt"]
if st.session_state.get("user_email") in _ADMIN_EMAILS:
    _page_titles.append("Admin: Tulokset")

_page_modules = {
    "Omat veikkaukset": "app_pages.my_predictions",
    "Tilanne":          "app_pages.standings",
    "Säännöt":          "app_pages.rules",
    "Admin: Tulokset":  "app_pages.admin_results",
}

selected = st.radio("Navigation", _page_titles, horizontal=True, label_visibility="collapsed")

_mod = _page_modules[selected]
if _mod in sys.modules:
    importlib.reload(sys.modules[_mod])
else:
    importlib.import_module(_mod)
