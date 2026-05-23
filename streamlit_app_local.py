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

_ioag_b64 = _img_b64("assets/ioag9w7poe8ayrodgmlc.webp")
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
        background-image: url("data:image/webp;base64,{_ioag_b64}");
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
        color: #dce8f5;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(5, 10, 30, 0.68);
        pointer-events: none;
        z-index: 0;
    }}

    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp .stMarkdown, .stApp .stText {{ color: #dce8f5 !important; }}

    [data-testid="stSidebar"] {{ color: #dce8f5 !important; }}
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {{ color: #dce8f5 !important; }}

    [data-testid="stForm"] {{ border: 0px; }}

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] > div,
    [data-testid="stNumberInput"] > div > div {{
        background-color: rgba(195, 215, 250, 0.94) !important;
        color: #07111f !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(220, 235, 255, 0.55) !important;
    }}
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        min-height: 38px !important;
        padding: 6px 10px !important;
    }}
    [data-testid="stTextInput"] input::placeholder {{ color: #4a6a8a !important; }}

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        background-color: rgba(195, 215, 250, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        min-height: 38px !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(220, 235, 255, 0.55) !important;
    }}

    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] > div > div {{
        background-color: rgba(195, 215, 250, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(220, 235, 255, 0.55) !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="select"] * {{ color: #07111f !important; }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background-color: rgba(30, 80, 180, 0.80) !important;
        border-radius: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button {{ color: #dce8f5 !important; }}
    [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stSelectbox"] [data-baseweb="select"] input {{ color: #07111f !important; }}
    [data-testid="stSelectbox"] [data-baseweb="select"] svg {{ fill: #07111f !important; }}

    [data-baseweb="popover"] > div {{ background-color: #0d1e3f !important; }}
    [data-baseweb="menu"] li {{ background-color: #0d1e3f !important; color: #dce8f5 !important; }}
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] [aria-selected="true"] {{ background-color: #1a3a70 !important; }}

    [data-testid="stExpander"] {{
        border: none !important;
        border-radius: 0 !important;
        background-color: rgba(10, 22, 55, 0.80) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.85),
            inset 1px 1px rgba(160, 195, 255, 0.50),
            inset -2px -2px rgba(0, 0, 20, 0.55),
            inset 2px 2px rgba(130, 170, 255, 0.22) !important;
    }}
    [data-testid="stExpander"] summary {{
        background-color: rgba(20, 50, 115, 0.75) !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.70),
            inset 1px 1px rgba(160, 200, 255, 0.55) !important;
        padding: 4px 8px !important;
    }}
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {{ color: #dce8f5 !important; }}

    header[data-testid="stHeader"] {{
        background-color: rgba(8, 16, 31, 0.97) !important;
        border-bottom: 2px solid rgba(70, 120, 200, 0.40) !important;
    }}
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] span,
    header[data-testid="stHeader"] p,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] div {{ color: #dce8f5 !important; }}
    header[data-testid="stHeader"] [aria-selected="true"],
    header[data-testid="stHeader"] [data-active="true"] {{
        border-bottom: 2px solid #4a90d9 !important;
        color: #4a90d9 !important;
    }}

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-secondary"] {{
        background-color: rgba(18, 45, 105, 0.85) !important;
        color: #dce8f5 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(170, 200, 255, 0.70),
            inset -2px -2px rgba(0, 0, 20, 0.55),
            inset 2px 2px rgba(140, 175, 255, 0.28) !important;
    }}
    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {{
        background-color: rgba(25, 60, 145, 0.92) !important;
        color: #7ec8ff !important;
    }}
    .stButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active {{
        box-shadow:
            inset -1px -1px rgba(170, 200, 255, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(140, 175, 255, 0.28),
            inset 2px 2px rgba(0, 0, 20, 0.55) !important;
    }}

    div[role="radiogroup"] {{ gap: 0.5rem; }}
    div[role="radiogroup"] label {{
        padding: 6px 16px !important;
        border: none !important;
        border-radius: 0 !important;
        cursor: pointer;
        background: rgba(18, 45, 105, 0.75) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(170, 200, 255, 0.70),
            inset -2px -2px rgba(0, 0, 20, 0.55),
            inset 2px 2px rgba(140, 175, 255, 0.28) !important;
    }}
    div[role="radiogroup"] label:has(input:checked) {{
        background: rgba(30, 70, 165, 0.92) !important;
        color: #7ec8ff !important;
        box-shadow:
            inset -1px -1px rgba(170, 200, 255, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(140, 175, 255, 0.28),
            inset 2px 2px rgba(0, 0, 20, 0.55) !important;
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

st.image("assets/logo_2026.png", width="stretch")

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
