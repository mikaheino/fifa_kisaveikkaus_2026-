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
        background: linear-gradient(135deg, #08101f 0%, #0d1a35 50%, #08101f 100%);
        color: #dce8f5;
    }

    /* Global text */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp .stMarkdown, .stApp .stText {
        color: #dce8f5 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { color: #dce8f5 !important; }
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label { color: #dce8f5 !important; }

    /* Form */
    [data-testid="stForm"] { border: 0px; }

    /* Inputs + Selectbox - shared 98.css sunken style */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] > div,
    [data-testid="stNumberInput"] > div > div {
        background-color: rgba(195, 215, 250, 0.94) !important;
        color: #07111f !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(220, 235, 255, 0.55) !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        min-height: 38px !important;
        padding: 6px 10px !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: #4a6a8a !important; }

    /* Selectbox - 98.css sunken style */
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: rgba(195, 215, 250, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        min-height: 38px !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(220, 235, 255, 0.55) !important;
    }

    /* Multiselect - same sunken style */
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] > div > div {
        background-color: rgba(195, 215, 250, 0.94) !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset 1px 1px rgba(0, 0, 0, 0.85),
            inset -1px -1px rgba(220, 235, 255, 0.55) !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] * { color: #07111f !important; }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: rgba(30, 80, 180, 0.80) !important;
        border-radius: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button { color: #dce8f5 !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stSelectbox"] [data-baseweb="select"] input { color: #07111f !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] svg { fill: #07111f !important; }

    /* Selectbox dropdown */
    [data-baseweb="popover"] > div { background-color: #0d1e3f !important; }
    [data-baseweb="menu"] li { background-color: #0d1e3f !important; color: #dce8f5 !important; }
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] [aria-selected="true"] { background-color: #1a3a70 !important; }

    /* Expander - 98.css raised window style */
    [data-testid="stExpander"] {
        border: none !important;
        border-radius: 0 !important;
        background-color: rgba(10, 22, 55, 0.80) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.85),
            inset 1px 1px rgba(160, 195, 255, 0.50),
            inset -2px -2px rgba(0, 0, 20, 0.55),
            inset 2px 2px rgba(130, 170, 255, 0.22) !important;
    }
    [data-testid="stExpander"] summary {
        background-color: rgba(20, 50, 115, 0.75) !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.70),
            inset 1px 1px rgba(160, 200, 255, 0.55) !important;
        padding: 4px 8px !important;
    }
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span { color: #dce8f5 !important; }

    /* Top navigation bar */
    header[data-testid="stHeader"] {
        background-color: rgba(8, 16, 31, 0.97) !important;
        border-bottom: 2px solid rgba(70, 120, 200, 0.40) !important;
    }
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] span,
    header[data-testid="stHeader"] p,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] div { color: #dce8f5 !important; }
    header[data-testid="stHeader"] [aria-selected="true"],
    header[data-testid="stHeader"] [data-active="true"] {
        border-bottom: 2px solid #4a90d9 !important;
        color: #4a90d9 !important;
    }

    /* Buttons - 98.css raised style (all button types) */
    .stButton > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-secondary"] {
        background-color: rgba(18, 45, 105, 0.85) !important;
        color: #dce8f5 !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(170, 200, 255, 0.70),
            inset -2px -2px rgba(0, 0, 20, 0.55),
            inset 2px 2px rgba(140, 175, 255, 0.28) !important;
    }
    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: rgba(25, 60, 145, 0.92) !important;
        color: #7ec8ff !important;
    }
    .stButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active {
        box-shadow:
            inset -1px -1px rgba(170, 200, 255, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(140, 175, 255, 0.28),
            inset 2px 2px rgba(0, 0, 20, 0.55) !important;
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
        background: rgba(18, 45, 105, 0.75) !important;
        box-shadow:
            inset -1px -1px rgba(0, 0, 0, 0.90),
            inset 1px 1px rgba(170, 200, 255, 0.70),
            inset -2px -2px rgba(0, 0, 20, 0.55),
            inset 2px 2px rgba(140, 175, 255, 0.28) !important;
    }
    div[role="radiogroup"] label:has(input:checked) {
        background: rgba(30, 70, 165, 0.92) !important;
        color: #7ec8ff !important;
        box-shadow:
            inset -1px -1px rgba(170, 200, 255, 0.70),
            inset 1px 1px rgba(0, 0, 0, 0.90),
            inset -2px -2px rgba(140, 175, 255, 0.28),
            inset 2px 2px rgba(0, 0, 20, 0.55) !important;
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

# -- Display logo --
st.image("assets/logo_2026.png")

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
