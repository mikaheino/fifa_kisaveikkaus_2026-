# Project Overview

Internal football prediction competition tied to the **2026 FIFA World Cup** (USA, Canada & Mexico, June 11 – July 19, 2026). Users predict scores for all 72 group stage games before the tournament starts; standings are computed as results come in. **Prediction deadline: June 11, 2026 at 19:00 Finnish time (EEST)** — after this, predictions are locked.

Runs as a **Streamlit in Snowflake (SiS) warehouse runtime** app. Each viewer gets a personal Streamlit server instance. The app uses Snowpark for all database access; there is no external backend.

---

# Directory Structure

```
streamlit_app.py               # Production entry point (Snowflake)
streamlit_app_local.py         # Local dev entry point (MockSession, no Snowflake needed)
mock_session.py                # MockSession — mimics Snowpark Session API for local dev
trivia.py                      # MATCH_TRIVIA dict: one fact per group-stage matchup
environment.yml                # Snowflake warehouse runtime dependencies (Anaconda channel)
pyproject.toml                 # Local dev dependencies (uv) — NOT deployed to Snowflake
AGENTS.md                      # This file
CLAUDE.md                      # Claude Code essentials (brief, points here)
README.md                      # Project overview and administration guide
assets/
  logo_2026.png                # FIFA World Cup 2026 logo — shown at top of every page
  saku-koivu.jpg               # Background image — Standings page (placeholder, swap for football image)
  ioag9w7poe8ayrodgmlc.webp    # Background image — My Predictions + Rules pages (placeholder)
  logo.png                     # Legacy logo
  saku-koivu-tuulettaa-maalia-naganossa-1998.avif  # Legacy source (placeholder)
tests/
  __init__.py
  test_trivia.py               # Smoke tests for trivia.py (pure Python, no Snowflake)
app_pages/
  __init__.py
  my_predictions.py            # Combined submit + update predictions page
  standings.py                 # Leaderboard + per-player match detail
  rules.py                     # Scoring rules and prize info
  admin_results.py             # Admin page: enter match results (restricted by email)
  update_prediction.py         # Legacy — not in navigation
  prediction.py                # Legacy — not in navigation
```

---

# Tournament Structure

| Item | Value |
|---|---|
| Teams | 48 |
| Groups | 12 (A–L), 4 teams each |
| Group stage matches | 72 |
| Knockout entrants | 32 (top 2 from each group + 8 best third-placed) |
| Knockout rounds | Round of 32 → Round of 16 → Quarter-finals → Semi-finals → Final (+ 3rd-place playoff) |
| Knockout matches | 32 total (16 + 8 + 4 + 2 + 1 + 1) |
| Hosts | USA, Canada, Mexico |
| Opening match | June 11, 2026 (Mexico City) |
| Final | July 19, 2026 (MetLife Stadium, NJ) |

---

# Tech Stack

| Layer | Technology |
|---|---|
| UI framework | Streamlit 1.35.0 (warehouse runtime, see supported versions below) |
| Runtime | Snowflake SiS warehouse runtime, Python 3.11 |
| Database | Snowflake Snowpark (`snowflake-snowpark-python`) |
| Data manipulation | pandas |
| Local dev | `MockSession` (no Snowflake required), `uv` for deps |
| Tests | pytest |
| Formatter | Ruff |

### Supported Streamlit versions (warehouse runtime)

Pin explicitly in `environment.yml`. Always verify against the live doc before upgrading:
https://docs.snowflake.com/en/developer-guide/streamlit/app-development/dependency-management#supported-versions-of-the-streamlit-library-in-warehouse-runtimes

```
1.52.2, 1.52.1, 1.52.0, 1.51.0, 1.50.0, 1.49.1, 1.48.0, 1.47.0,
1.46.1, 1.45.1, 1.45.0, 1.44.1, 1.44.0, 1.42.0, 1.39.0, 1.35.0,
1.31.1, 1.29.0, 1.26.0, 1.22.0
```

---

# Coding Standards (Do)

- **Formatter**: Ruff. Run `ruff format .` before committing.
- **Linter**: Ruff. Run `ruff check .` and fix all issues before committing.
- **Naming**: player names uppercased and whitespace-stripped via `clean_name()` in `mock_session.py`; table names follow `{CLEANED_NAME}_FIFA_VEIKKAUS`.
- **NaN handling**: Snowpark returns `NaN` for NULL numerics. Always use `pd.isna()` — never `is None` or `== None`.
- **Widget keys**: scope `st.data_editor` and other stateful widgets to the current contestant: `key=f"editor_{contestant}_{date_key}"`.
- **Background images**: base64-encode and inject as CSS `data:` URIs (Snowflake CSP blocks external URLs). Use `os.path.join(os.path.dirname(__file__), "..", "assets", "filename")` from `app_pages/`. Always guard with `if os.path.exists(_img_path):`.
- **CSS in f-strings**: escape all CSS braces as `{{` / `}}`. In non-f-string markdown use plain `{` / `}`.
- **No experimental APIs**: use `st.rerun()` not `st.experimental_rerun()`, etc.
- **No comments** unless the WHY is non-obvious. Never write what the code does — only hidden constraints or surprising invariants.
- **Major changes**: use `/plan` mode before writing code. Commit after each logical step.

---

# Don'ts

- **Never bypass Snowflake RBAC.** All database actions must go through the assigned role (`FIFA_VEIKKAUS_PLAYER_ROLE` or `FIFA_VEIKKAUS_ADMIN_ROLE`). Never use `ACCOUNTADMIN` for app queries.
- **Never commit credentials or `.env` files.** The Snowflake connection is handled by `get_active_session()` in production and `MockSession` locally — no hardcoded connection strings.
- **Never run destructive SQL (`DROP`, `TRUNCATE`, `DELETE`) in production** without explicit user instruction and confirmation.
- **Never add packages to `environment.yml`** unless they exist in the Snowflake Anaconda Channel (https://repo.anaconda.com/pkgs/snowflake/). No PyPI packages in production.
- **Never use `st.experimental_*` APIs** — they are removed in current Streamlit versions and will break on deployment.
- **Never skip `--no-verify`** on git commits unless the user explicitly requests it.
- **Never push to `main`** without user confirmation.

---

# Snowflake-Specific Settings

| Setting | Value |
|---|---|
| Database | `STREAMLIT_APPS` |
| Schema | `FIFA_VEIKKAUS` |
| Warehouse | `FIFA_VEIKKAUS_WH` (XS, auto-suspend 60s) |
| Stage | `FIFA_VEIKKAUS_STAGE` |
| App object | `FIFA_VEIKKAUS_APP` |
| Player role | `FIFA_VEIKKAUS_PLAYER_ROLE` → DB role `FIFA_VEIKKAUS_USER` |
| Admin role | `FIFA_VEIKKAUS_ADMIN_ROLE` → DB role `FIFA_VEIKKAUS_ADMIN` |

### Key tables

| Table | Purpose |
|---|---|
| `FIFA_VEIKKAUS_SCHEDULE` | 72 group-stage games: ID, MATCH_DAY, MATCH, GROUP_LETTER |
| `FIFA_VEIKKAUS_RESULTS` | Actual group-stage results (admin-filled) |
| `FIFA_VEIKKAUS_RESULTS_V` | Results view with computed winner column |
| `FIFA_VEIKKAUS_PREDICTIONS` | Per-user group-stage predictions (one row per user × match) |
| `FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS` | Per-user knockout bracket + top scorer predictions (one row per user) — R32, R16, QF, SF, finalists, champion |
| `FIFA_VEIKKAUS_PLAYOFF_RESULTS` | Actual knockout bracket + top scorer (admin-filled, single row) |
| `{NAME}_FIFA_VEIKKAUS` | Legacy per-player predictions (pre-v1.0), no longer written |

### Deploying files after changes

Upload changed files to the stage. The app picks up new files on the next viewer session — no need to drop or recreate the app object. **Do NOT drop the app** — the app URL is shared with end users and dropping would change it.

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE STREAMLIT_APPS;
USE SCHEMA FIFA_VEIKKAUS;
USE WAREHOUSE FIFA_VEIKKAUS_WH;

-- Upload all source files
PUT file:///path/to/streamlit_app.py @FIFA_VEIKKAUS_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/my_predictions.py @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/standings.py @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/rules.py @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/admin_results.py @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/trivia.py @FIFA_VEIKKAUS_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Assets (only when images change)
PUT file:///path/to/assets/logo_2026.png @FIFA_VEIKKAUS_STAGE/assets/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/assets/saku-koivu.jpg @FIFA_VEIKKAUS_STAGE/assets/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/assets/ioag9w7poe8ayrodgmlc.webp @FIFA_VEIKKAUS_STAGE/assets/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Dependencies (only when environment.yml changes)
PUT file:///path/to/environment.yml @FIFA_VEIKKAUS_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

Only drop and recreate the app as a last resort (e.g., the app is completely broken and won't start). This changes the app URL and breaks existing bookmarks/shared links:

```sql
-- LAST RESORT ONLY — changes the app URL
DROP STREAMLIT FIFA_VEIKKAUS_APP;

CREATE STREAMLIT FIFA_VEIKKAUS_APP
    ROOT_LOCATION = '@FIFA_VEIKKAUS_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'FIFA_VEIKKAUS_WH';
```

### Database migrations

Schema and data migrations live in `RELEASE_NOTES.md` under the corresponding version heading. Each migration is a self-contained SQL block wrapped in `BEGIN; ... COMMIT;` and ends with sanity-check `SELECT COUNT(*)` queries — both should return `0` after a successful run.

**Order of operations for a release with a migration:**

1. **Run the migration SQL first** (as `ACCOUNTADMIN` in a Snowflake worksheet) — see `RELEASE_NOTES.md`.
2. **Verify** the sanity-check counts return `0`.
3. **Then deploy the code** via the `PUT` block above.

If you deploy the code first, the running app will still query the old (un-migrated) values and most lookups (e.g. `_FLAGS.get(...)`, `MATCH_TRIVIA.get(...)`) will silently miss — flags disappear, trivia stops rendering, playoff defaults don't pre-populate.

Migrations are written to be **idempotent**: running them again on already-migrated data is a no-op because the source strings (English names) no longer exist in the table.

### Team-name convention

All team names in the database and UI are stored **in Finnish**. Keep the translation map in sync across:

- `mock_session.py` (`GROUPS_A_THROUGH_L`)
- `_FLAGS` dicts in `app_pages/*.py`
- `trivia.py` keys
- Any migration SQL that touches team strings

Examples (non-exhaustive — full map lives next to `_FLAGS`):

| English | Finnish |
|---|---|
| Argentina | Argentiina |
| Belgium | Belgia |
| Brazil | Brasilia |
| Canada | Kanada |
| Croatia | Kroatia |
| Denmark | Tanska |
| England | Englanti |
| France | Ranska |
| Germany | Saksa |
| Italy | Italia |
| Japan | Japani |
| Mexico | Meksiko |
| Morocco | Marokko |
| Netherlands | Alankomaat |
| Norway | Norja |
| Portugal | Portugali |
| South Korea | Etelä-Korea |
| Spain | Espanja |
| Sweden | Ruotsi |
| United States | Yhdysvallat |

---

# Testing & Quality

```bash
# Run tests (pure Python, no Snowflake needed)
python3 -m pytest tests/ -v

# Format
ruff format .

# Lint
ruff check .
```

Tests live in `tests/`. Keep them pure Python — no Streamlit imports, no Snowflake connection. `MockSession` exists for local logic testing if needed.

There is no CI/CD pipeline. Deploys are manual SQL PUT commands (see Snowflake-Specific Settings above).

---

# Local Development

The local entry point `streamlit_app_local.py` swaps `get_active_session()` for `MockSession`, so the full UI runs without a Snowflake connection.

```bash
# Start the local server (default port 8501)
python3 -m streamlit run streamlit_app_local.py --server.port 8501 --server.headless true
```

`--server.headless true` skips the "Open browser?" prompt; useful when running in the background or when an agent will drive the browser via Playwright.

### Hot-reload gotcha: imported modules are cached

Streamlit re-runs the script on each browser refresh, but Python's import system caches imported modules. Edits to **`trivia.py`, `mock_session.py`, or any other module imported by a page** are **not** picked up by hot reload — only edits to the page file itself reload cleanly.

When you change an imported module, restart the server:

```bash
# Find and kill the running server
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep ':8501'
kill <PID>

# Start it again
python3 -m streamlit run streamlit_app_local.py --server.port 8501 --server.headless true
```

If you see stale data after editing `trivia.py` or `mock_session.py` and a refresh doesn't fix it, this is the cause.

### MockSession scope

`MockSession` provides the 72-game group-stage schedule, results for the first few games, and an empty in-memory predictions / playoff-predictions store. It implements just enough of the Snowpark `session.sql(...).collect()` and `.to_pandas()` surface to drive the UI; arbitrary SQL is **not** evaluated. If you add a new query pattern in a page, extend `mock_session.py` to handle it or the local view will silently return empty data.

### Mock vs production parity

Names stored in `FIFA_VEIKKAUS_*` tables (team names, schedule `MATCH` strings) must match between `mock_session.py` and Snowflake. After running a DB migration, update `mock_session.py` groups and any hard-coded team names in the same commit, otherwise local will not match production behavior.

---

# Developing with Playwright

Playwright lets an agent drive a real browser against the local Streamlit server — useful for visual verification of CSS changes, screenshot diffs, and interaction flows that pure unit tests can't cover.

### Setup

```bash
# Install once (local dev only — not in environment.yml)
uv pip install playwright
python3 -m playwright install chromium
```

### Standard agent workflow

1. **Start Streamlit headless.** Keep it running in the background so multiple Playwright runs reuse the same server.
   ```bash
   python3 -m streamlit run streamlit_app_local.py --server.port 8501 --server.headless true
   ```
2. **Wait for it to come up** before driving the browser. The first request after startup can take 2–4 s.
   ```bash
   sleep 3 && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501   # expect 200
   ```
3. **Drive the page** with a small Python script. Always wait for the Streamlit script-runner to settle before reading the DOM or taking screenshots:
   ```python
   from playwright.sync_api import sync_playwright

   with sync_playwright() as p:
       browser = p.chromium.launch()
       page = browser.new_page(viewport={"width": 1280, "height": 1600})
       page.goto("http://localhost:8501")
       page.wait_for_selector("[data-testid='stAppViewContainer']", state="visible")
       page.wait_for_timeout(1500)  # let async reruns finish
       page.screenshot(path="/tmp/predictions.png", full_page=True)
       browser.close()
   ```
4. **Restart the server when you edit `trivia.py`, `mock_session.py`, or any imported module.** See the hot-reload gotcha above. Page-file edits (`app_pages/*.py`, `streamlit_app_local.py`) do hot-reload — a `page.reload()` is enough.

### Verifying CSS changes

Computed styles are more reliable than visual diffs when checking colors, borders, or backgrounds — screenshots can compress or alpha-blend in misleading ways.

```python
bg = page.evaluate(
    "() => getComputedStyle("
    "document.querySelector('[data-testid=\"stMultiSelect\"] [data-baseweb=\"select\"] > div')"
    ").backgroundColor"
)
print(bg)   # e.g. "rgba(195, 215, 250, 0.94)"
```

### Things that will not work in Playwright but do in SiS

- **Google Fonts via `@import url(...)` in CSS** loads in local Playwright but is blocked by Snowflake's CSP in some warehouse runtimes. Verify font rendering on Snowflake after deploy if you change the font stack.
- **`components.html(...)` `<script>` tags** execute in both, but `st.markdown` strips `<script>`. The countdown timer in `my_predictions.py` is the canonical example — if a screenshot shows static text where you expect a live counter, you used `st.markdown` instead of `components.html`.
- **The "Press Enter to submit form" tooltip** is a Chrome native UI element and visible in Playwright screenshots; it does **not** appear in Snowflake's embedded iframe. Don't try to hide it with CSS — there is none.

### Screenshot review tips

- Save to `/tmp/<feature>.png` rather than the repo to avoid polluting git.
- Use `full_page=True` to capture below the fold.
- For mobile-style layouts, set `viewport={"width": 412, "height": 915}` (Pixel-class) before `goto`.
- For dark-overlay backgrounds, sample `getComputedStyle` on the actual element instead of trusting screenshot pixel colors — the `::before` overlay can fool the eye.

---

# Custom Skills & SubAgents Guide

### `developing-with-streamlit`

**Load with:** `/developing-with-streamlit` (or the Skill tool with `skill: "developing-with-streamlit"`)

**Use for:** any Streamlit task — creating, editing, debugging, styling, theming, optimizing, or deploying pages. Also covers layout, widget selection, session state, data display, and Snowflake connection patterns.

**Sub-skills available inside it:**

| Sub-skill | When to use |
|---|---|
| `organizing-streamlit-code` | restructuring pages or modules |
| `improving-streamlit-design` | visual polish, icons, badges |
| `using-streamlit-layouts` | columns, tabs, sidebar, expanders |
| `displaying-streamlit-data` | dataframes, column config, charts |
| `optimizing-streamlit-performance` | caching, fragments, slow reruns |
| `connecting-streamlit-to-snowflake` | `st.connection`, query caching |
| `creating-streamlit-themes` | CSS, colors, dark mode |
| `using-streamlit-session-state` | widget keys, callbacks, state bugs |
| `building-streamlit-multipage-apps` | navigation, shared state across pages |

**Do not** use this skill for pure Snowflake SQL or schema changes — those are handled directly.
