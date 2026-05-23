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
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

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

    div[role="radiogroup"] {{ gap: 0.5rem; }}
    div[role="radiogroup"] label {{
        padding: 6px 16px !important;
        border: none !important;
        border-radius: 0 !important;
        cursor: pointer;
        background: rgba(140, 100, 25, 0.75) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(220, 180, 90, 0.70),
            inset -2px -2px rgba(20, 12, 4, 0.65),
            inset 2px 2px rgba(190, 155, 70, 0.28) !important;
    }}
    div[role="radiogroup"] label:has(input:checked) {{
        background: rgba(160, 110, 30, 0.92) !important;
        color: #f5c842 !important;
        box-shadow:
            inset -1px -1px rgba(220, 180, 90, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(190, 155, 70, 0.28),
            inset 2px 2px rgba(20, 12, 4, 0.65) !important;
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

pages = st.navigation(
    [
        st.Page("app_pages/my_predictions.py", title="Omat veikkaukset"),
        st.Page("app_pages/standings.py", title="Tilanne"),
        st.Page("app_pages/rules.py", title="Saannot"),
        st.Page("app_pages/admin_results.py", title="Syota tulokset"),
    ],
    position="top",
)

pages.run()
