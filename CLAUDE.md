# FIFA-veikkaus 2026 — Claude Code Instructions

Full project documentation is in **AGENTS.md**. Read that file for file structure, Snowflake schema, deploy steps, key patterns, and compatibility rules.

## Streamlit-in-Snowflake template repos

This repo is the **container runtime** template. For new SiS projects, start from whichever runtime fits:

- **Container runtime** (this repo, preferred default): https://github.com/mikaheino/fifa_kisaveikkaus_2026 — CCv2 components, `pyproject.toml`, compute pool + EAI.
- **Warehouse runtime** (legacy, simpler infra): https://github.com/mikaheino/mm_kisaveikkaus_2026 — `environment.yml`, `get_active_session()`, no compute pool. CCv2 components are stripped here.

## Essential rules for Claude Code

- **Runtime**: Snowflake SiS **container runtime** on `FIFA_VEIKKAUS_POOL` (XS, auto-suspended by `FIFA_VEIKKAUS_AUTOSTOP_TASK`), Python 3.11. Anaconda channel preferred; pip allowed.
- **Session**: the shared connection lives at `st.session_state.snowpark_conn`. Run **every** query inside `with conn.safe_session() as session:` — the container instance is shared across all viewers and a bare Snowpark session is not thread-safe (concurrent queries leak result rows between viewers). Never nest `safe_session()` blocks (the lock is not reentrant).
- **Identity**: resolve the viewer only from `st.user.email` (set in `streamlit_app.py`). **Never** fall back to `CURRENT_USER()` — in the container runtime it returns the service account, not the viewer. Fail closed if the email is missing.
- **New pages**: any page added under `app_pages/` MUST follow both patterns above — `conn = st.session_state.snowpark_conn` with every query in a `conn.safe_session()` block, and identity from `st.user.email` only. Mirror an existing page (`my_predictions.py`, `standings.py`, `admin_results.py`).
- **Images**: live in `assets/`; loaded via base64 CSS injection (Snowflake CSP blocks external URLs)
- **NaN vs None**: Snowpark returns NaN for NULL numerics — always use `pd.isna()`, never `is None`
- **No experimental APIs**: use `st.rerun()` not `st.experimental_rerun()`, etc.
- **Widget keys**: scope to current contestant (`key=f"editor_{contestant}_{date_key}"`)
- **Local dev**: `python3 -m streamlit run streamlit_app_local.py` — no Snowflake needed
- **Tests**: `python3 -m pytest tests/` — pure Python, no Snowflake needed
- **Major changes**: use `/plan` mode before writing code
- **After major changes**: `git add` + `git commit`
