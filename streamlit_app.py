import streamlit as st

# -- Page config (must be first Streamlit call) --
st.set_page_config(
    page_title="FIFA-veikkaus 2026",
    page_icon="assets/logo_2026.png",
    layout="centered",
)

# -- CSS: 98.css-inspired style with transparency and minimal blue palette --
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* Apply Roboto to text elements only — leave icon/symbol font elements untouched */
    body, p, div, h1, h2, h3, h4, h5, h6,
    label, input, button, select, textarea, a, li, td, th, caption,
    [data-testid] > div, [data-testid] > p, [data-testid] > label {
        font-family: 'Roboto', Arial, sans-serif !important;
    }

    /* Background */
    .stApp {
        background: linear-gradient(135deg, #1a1408 0%, #2a2110 50%, #1a1408 100%);
        color: #f5e8c8;
    }

    /* Global text */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp .stMarkdown, .stApp .stText {
        color: #f5e8c8 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { color: #f5e8c8 !important; }
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label { color: #f5e8c8 !important; }

    /* Form */
    [data-testid="stForm"] { border: 0px; }

    /* Inputs + Selectbox - shared 98.css sunken style */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] > div,
    [data-testid="stNumberInput"] > div > div {
        background-color: rgba(245, 220, 150, 0.94) !important;
        color: #1a1408 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(250, 230, 180, 0.55) !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        min-height: 38px !important;
        padding: 6px 10px !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: #8a6a3a !important; }

    /* Selectbox - 98.css sunken style */
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: rgba(245, 220, 150, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        min-height: 38px !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(250, 230, 180, 0.55) !important;
    }

    /* Multiselect - same sunken style */
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] > div > div {
        background-color: rgba(245, 220, 150, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(250, 230, 180, 0.55) !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] * { color: #1a1408 !important; }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: rgba(170, 120, 30, 0.85) !important;
        border-radius: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button { color: #f5e8c8 !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stSelectbox"] [data-baseweb="select"] input { color: #1a1408 !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] svg { fill: #1a1408 !important; }

    /* Selectbox dropdown */
    [data-baseweb="popover"] > div { background-color: #1f1a0a !important; }
    [data-baseweb="menu"] li { background-color: #1f1a0a !important; color: #f5e8c8 !important; }
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] [aria-selected="true"] { background-color: #3d3014 !important; }

    /* Expander - 98.css raised window style */
    [data-testid="stExpander"] {
        border: none !important;
        border-radius: 0 !important;
        background-color: rgba(40, 28, 10, 0.85) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.85),
            inset 1px 1px rgba(210, 175, 90, 0.50),
            inset -2px -2px rgba(20, 12, 4, 0.65),
            inset 2px 2px rgba(180, 140, 60, 0.22) !important;
    }
    [data-testid="stExpander"] summary {
        background-color: rgba(80, 55, 15, 0.85) !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.70),
            inset 1px 1px rgba(210, 175, 90, 0.55) !important;
        padding: 4px 8px !important;
    }
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span { color: #f5e8c8 !important; }

    /* Top navigation bar */
    header[data-testid="stHeader"] {
        background-color: rgba(20, 14, 8, 0.97) !important;
        border-bottom: 2px solid rgba(150, 110, 30, 0.55) !important;
    }
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] span,
    header[data-testid="stHeader"] p,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] div { color: #f5e8c8 !important; }
    header[data-testid="stHeader"] [aria-selected="true"],
    header[data-testid="stHeader"] [data-active="true"] {
        border-bottom: 2px solid #d4a017 !important;
        color: #d4a017 !important;
    }

    /* Buttons - 98.css raised style (all button types) */
    .stButton > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-secondary"] {
        background-color: rgba(140, 100, 25, 0.85) !important;
        color: #f5e8c8 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(220, 180, 90, 0.70),
            inset -2px -2px rgba(20, 12, 4, 0.65),
            inset 2px 2px rgba(190, 155, 70, 0.28) !important;
    }
    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: rgba(190, 140, 35, 0.92) !important;
        color: #f5c842 !important;
    }
    .stButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active {
        box-shadow:
            inset -1px -1px rgba(220, 180, 90, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(190, 155, 70, 0.28),
            inset 2px 2px rgba(20, 12, 4, 0.65) !important;
    }

    /* Logo image full-width */
    [data-testid="stImage"] img { width: 100% !important; max-width: 100%; }

    /* Horizontal nav radio */
    div[role="radiogroup"] { gap: 0.5rem; }
    div[role="radiogroup"] label {
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
    }
    div[role="radiogroup"] label:has(input:checked) {
        background: rgba(160, 110, 30, 0.92) !important;
        color: #f5c842 !important;
        box-shadow:
            inset -1px -1px rgba(220, 180, 90, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(190, 155, 70, 0.28),
            inset 2px 2px rgba(20, 12, 4, 0.65) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -- Snowflake session (get_active_session works in both classic SiS and vNext) --
from snowflake.snowpark.context import get_active_session
st.session_state.snowpark_session = get_active_session()

# -- Resolve the viewer's identity --
# In vNext SiS get_active_session() is scoped to the viewer, so CURRENT_USER()
# returns their Snowflake username, which equals their email address at Recordly.
st.session_state.user_email = st.session_state.snowpark_session.sql(
    "SELECT CURRENT_USER()"
).collect()[0][0].lower()

# -- Display logo (rendered as <img> so we can apply opacity) --
import base64
_logo_b64 = base64.b64encode(open("assets/logo_2026.png", "rb").read()).decode()
st.markdown(
    f'<img src="data:image/png;base64,{_logo_b64}" '
    f'style="width:100%;opacity:0.45;display:block;margin-bottom:0.5rem;" '
    f'alt="FIFA 2026 -veikkaus" />',
    unsafe_allow_html=True,
)

# -- Multi-page navigation (sidebar, compatible with all SiS Streamlit versions) --
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

selected = st.radio("", _page_titles, horizontal=True, label_visibility="collapsed")

_mod = _page_modules[selected]
if _mod in sys.modules:
    importlib.reload(sys.modules[_mod])
else:
    importlib.import_module(_mod)
