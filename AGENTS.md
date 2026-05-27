# Project Overview

Internal football prediction competition tied to the **2026 FIFA World Cup** (USA, Canada & Mexico, June 11 – July 19, 2026). Users predict scores for all 72 group stage games before the tournament starts; standings are computed as results come in. **Prediction deadline: June 11, 2026 at 19:00 Finnish time (EEST)** — after this, predictions are locked.

Runs as a **Streamlit in Snowflake (SiS) app on the container runtime** (Snowflake Container Services) on the `FIFA_VEIKKAUS_POOL` compute pool. All viewers share a **single container instance** — unlike the warehouse runtime's per-viewer model — so `st.cache_data` / `st.cache_resource` are shared across sessions and code must be thread-safe. The app uses Snowpark for all database access; there is no external backend. The container runtime is required because the warehouse runtime strips `st.components.v2.component` (the four CCv2 pickers).

---

# Directory Structure

```
streamlit_app.py               # Production entry point — stores st.connection("snowflake"); pages query via conn.safe_session()
streamlit_app_local.py         # Local dev entry point — instantiates MockSession instead of Snowpark
mock_session.py                # MockSession class: fakes the Snowpark session.sql(...).collect()/.to_pandas()
                               #   surface, seeds the 72-game schedule + demo predictions + Saksa-wins playoff
pyproject.toml                 # Container-runtime dependency manifest (streamlit[snowflake]==1.57.0, pandas)
                               #   Also used by uv for local dev
deployed_to_snowflake          # Deployment status — tracks last deploy timestamp, Streamlit version,
                               #   and full file list pushed to the live version. Updated after each deploy.
AGENTS.md                      # This file
CLAUDE.md                      # Claude Code essentials (brief, points here)
README.md                      # Project overview and administration guide
assets/                        # Loaded via base64 CSS injection — Snowflake CSP blocks external URLs
  logo_2026.png                #   FIFA 2026 trophy logo, color-graded into the Maradona palette; shown
                               #   at the top of every page
  maradona.gif                 #   Tournament-spirit background; rendered at 16% opacity as a ghosted
                               #   watermark behind the 90s-arcade theme on the predictions page
  flags/                       #   48 country flags (SVG): Twemoji by default; flat flag-icons for
                               #   equal-band flags (de/at). Loaded as base64 by _momentum_slider.py
tools/
  download_flags.py            # Re-fetches assets/flags/*.svg from emoji codepoints (Twemoji + flag-icons)
data/                          # Canonical reference data — single source of truth, do not duplicate
  schedule_2026.json           #   48 teams (en+fi+flag), 12 groups, 16 venues, all 104 matches
                               #   (72 group + 32 knockout) with date/time/tz/venue
  build_schedule_2026.py       #   Builder script — declarative source for the JSON above. Edit + re-run
                               #   to regenerate after schedule corrections
db/                            # Snowflake bootstrap
  setup.sql                    #   Fresh-account: warehouse + DB + schema + tables + roles + grants +
                               #   stage + Streamlit object + schedule seed (idempotent MERGE)
tests/
  __init__.py
app_pages/
  __init__.py
  my_predictions.py            # Group-stage football score slider + playoff bracket picker
  standings.py                 # Leaderboard + points-over-time chart + all-players prediction table
  rules.py                     # Scoring rules and prize info
  admin_results.py             # Admin page: enter match results (restricted by email)
  _momentum_slider.py          # CCv2 component: dual-thumb football score picker (flag-filled box ends)
  _bracket_picker.py           # CCv2 component: visual R32 → Champion bracket
  _group_picker.py             # CCv2 component: per-group winner + runner-up selector
  _team_grid_picker.py         # CCv2 component: click-to-pick chip grid (best thirds)
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
| UI framework | Streamlit 1.57.0 (pinned in `pyproject.toml`) |
| Runtime | Snowflake SiS **container runtime** (`SYSTEM$ST_CONTAINER_RUNTIME_PY3_11`), Python 3.11 |
| Compute pool | `FIFA_VEIKKAUS_POOL` (CPU_X64_XS, 1 node) |
| Database | Snowflake Snowpark (`snowflake-snowpark-python`) |
| Data manipulation | pandas |
| Local dev | `MockSession` (no Snowflake required), `uv` for deps |
| Tests | pytest |
| Formatter | Ruff |

### Streamlit version pin

Container runtime is more permissive than warehouse runtime — most pip-installable Streamlit versions work. The current pin is **1.57.0** (needs a recent release for stable `st.components.v2.component`). Always verify against the live doc before upgrading:
https://docs.snowflake.com/en/developer-guide/streamlit/app-development/dependency-management

---

# Container Runtime Reference (Template for New Projects)

This project serves as the **template** for creating Streamlit-in-Snowflake apps on the container runtime. The following sections document the critical differences from warehouse runtime and the gotchas encountered during migration.

### Template repositories

When starting a new Streamlit-in-Snowflake project, clone whichever of these matches the runtime you need — they are the canonical, working references:

| Runtime | Template repository | Use when |
|---|---|---|
| **Container runtime** | https://github.com/mikaheino/fifa_kisaveikkaus_2026 | You need CCv2 custom components, full pip/PyPI dependency control, or thread-safe shared caching. This is the preferred default for new projects. |
| **Warehouse runtime** | https://github.com/mikaheino/mm_kisaveikkaus_2026 | You need the legacy warehouse runtime — simpler infra (no compute pool, no EAI), conda-based deps via `environment.yml`, per-viewer instance model. Note: CCv2 components are stripped here. |

### Required infrastructure (Snowflake objects)

| Object | Purpose |
|---|---|
| Compute pool (`CPU_X64_XS`, 1 node) | Hosts the Streamlit container process |
| Internal stage | Source files — `FROM` copies them into the app's embedded versioned stage |
| Network rule + External Access Integration (EAI) | Allows the container to reach PyPI for `pip install` |
| `pyproject.toml` in source root | Declares Python dependencies for the container (replaces `environment.yml`) |
| `QUERY_WAREHOUSE` (XS) | Executes Snowpark SQL queries issued by the app |

### CREATE STREAMLIT syntax (container runtime)

```sql
CREATE STREAMLIT my_app
    FROM '@my_db.my_schema.my_stage'
    MAIN_FILE = 'streamlit_app.py'
    RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
    COMPUTE_POOL = my_pool
    QUERY_WAREHOUSE = 'my_wh'
    EXTERNAL_ACCESS_INTEGRATIONS = (my_pypi_eai);

ALTER STREAMLIT my_app ADD LIVE VERSION FROM LAST;
```

**Critical:** `ADD LIVE VERSION FROM LAST` is mandatory — without it the app returns "not live" errors.

### Viewer identity

| API | Returns |
|---|---|
| `st.user.email` | Viewer's email (e.g. `mika.heino@recordlydata.com`) |
| `st.user.user_name` | Viewer's Snowflake username (e.g. `MIKA.HEINO`) |
| `CURRENT_USER()` in SQL | **Service account** (e.g. `Stplatstreamlit15690228`) — NOT the viewer |
| `st.connection("snowflake-callers-rights")` | Session running as the viewer (restricted caller's rights, Preview) |

### Session management

All viewers share **one** container instance, so the connection's underlying
Snowpark session is shared across every viewer's script-runner thread. **Snowpark
sessions are not thread-safe** — concurrent queries on a shared session race on the
single underlying connection and can return one viewer's result rows to another
viewer's thread (a real cross-user data leak). Always go through the connection's
thread-safe `safe_session()` context manager; never hold the raw `.session()`.

```python
# Container runtime (correct) — store the CONNECTION, query via safe_session()
st.session_state.snowpark_conn = st.connection("snowflake")
user_email = st.user.email.lower()

conn = st.session_state.snowpark_conn
with conn.safe_session() as session:           # built-in thread-safe lock
    df = session.sql("SELECT ...").to_pandas()

# Keep a DELETE+INSERT (or any multi-statement unit) inside ONE safe_session
# block so no other viewer's query interleaves. safe_session() locks are NOT
# reentrant — never nest one inside another (it deadlocks).

# WRONG — bare session shared across threads, no lock
# session = st.connection("snowflake").session()   # races under concurrency

# Warehouse runtime (legacy — DO NOT USE in container runtime)
# from snowflake.snowpark.context import get_active_session
# session = get_active_session()  # NOT THREAD-SAFE
```

### Dependency management

- Container runtime uses **`pyproject.toml`** or **`requirements.txt`** (searched in entrypoint directory, then up).
- `environment.yml` is **ignored** — it only works in warehouse runtime.
- Without an EAI, only pre-installed packages are available and version pins will fail.
- Pin with `==` (PyPI syntax), not `=` (conda syntax).

Minimal `pyproject.toml`:
```toml
[project]
name = "my-app"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "streamlit[snowflake]==1.57.0",
    "pandas",
]
```

### External Access Integration (PyPI)

Required to install any pinned or extra packages:

```sql
CREATE OR REPLACE NETWORK RULE pypi_network_rule
    MODE = EGRESS  TYPE = HOST_PORT
    VALUE_LIST = ('pypi.org', 'files.pythonhosted.org');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
    ALLOWED_NETWORK_RULES = (pypi_network_rule)
    ENABLED = TRUE;
```

Then attach to the Streamlit object: `EXTERNAL_ACCESS_INTEGRATIONS = (pypi_access_integration)`.

### Updating deployed code

Container runtime apps use an **embedded versioned stage** (not the source stage directly). After PUT-ing files to the source stage:

```sql
-- Get the live URI
DESCRIBE STREAMLIT my_app;  -- look at live_version_location_uri

-- Copy specific changed files into the live version
COPY FILES INTO '<live_version_location_uri>'
    FROM @my_stage FILES = ('streamlit_app.py', 'app_pages/page.py');
```

Changes are visible to viewers on their next interaction — no restart needed.

### Key differences: container vs warehouse runtime

| Aspect | Warehouse runtime | Container runtime |
|---|---|---|
| `CREATE STREAMLIT` | `ROOT_LOCATION` or `FROM` | `FROM` only (+ `ADD LIVE VERSION`) |
| Dependencies | `environment.yml` (conda) | `pyproject.toml` / `requirements.txt` (pip/uv) |
| Session | `get_active_session()` | `st.connection("snowflake")` + `conn.safe_session()` |
| Viewer identity | `CURRENT_USER()` = viewer | `st.user.email` / `st.user.user_name` |
| `CURRENT_USER()` | Viewer's username | Internal service account |
| Execution model | One instance per viewer | One shared instance, all viewers |
| Caching | Not shared between sessions | `st.cache_data` / `st.cache_resource` shared |
| Thread safety | Not required | Required (concurrent viewers) |
| Custom components (CCv2) | Stripped by frontend allowlist | Fully supported |
| Cold start | Per-viewer (few seconds) | Pool resume (~60-90s) then fast for all |
| Stored procedure syntax | `ALTER COMPUTE POOL ... STOP ALL` works | Must use `EXECUTE IMMEDIATE` inside SQL SP |

### Checklist for new container-runtime apps

1. Create compute pool (`CPU_X64_XS`, `AUTO_RESUME=TRUE`, `INITIALLY_SUSPENDED=TRUE`)
2. Create network rule + EAI for PyPI
3. Create `pyproject.toml` with `streamlit[snowflake]==<version>` + other deps
4. Use `st.connection("snowflake")` + `conn.safe_session()` (thread-safe) for Snowpark
5. Use `st.user.email` / `st.user.user_name` for viewer identity
   > **Every new page** must follow both: `conn = st.session_state.snowpark_conn` with all queries inside `conn.safe_session()`, and identity from `st.user.email` only (fail closed, never `CURRENT_USER()`). Mirror an existing `app_pages/*.py`.
6. Use `FROM` syntax in `CREATE STREAMLIT` + `ADD LIVE VERSION FROM LAST`
7. Attach EAI: `EXTERNAL_ACCESS_INTEGRATIONS = (my_eai)`
8. Grant `USAGE` on compute pool + Streamlit object to viewer roles
9. Consider activity-driven auto-suspend Task for cost control

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
- **Never commit credentials or `.env` files.** The Snowflake connection is handled by `st.connection("snowflake")` in production and `MockSession` locally — no hardcoded connection strings.
- **Never run destructive SQL (`DROP`, `TRUNCATE`, `DELETE`) in production** without explicit user instruction and confirmation.
- **Never use `get_active_session()`** — it is not thread-safe and returns the service account in container runtime. Use `st.connection("snowflake")` and run every query inside `conn.safe_session()`.
- **Never hold the raw `.session()` across threads.** The container instance is shared by all viewers; a bare Snowpark session used concurrently leaks result rows between viewers. Wrap each query in `with conn.safe_session() as session:` (and never nest those blocks — the lock is not reentrant).
- **Never use `CURRENT_USER()` to identify the viewer** — it returns the internal service account (e.g. `Stplatstreamlit15690228`) in container runtime. Use `st.user.email` or `st.user.user_name` instead, and **fail closed** (`st.error` + `st.stop()`) if it is missing rather than falling back to `CURRENT_USER()`, which would silently mis-attribute one viewer's save to another identity.
- **Never use `ROOT_LOCATION` in `CREATE STREAMLIT`** — it only supports warehouse runtime. Always use `FROM` + `ADD LIVE VERSION FROM LAST`.
- **Never use `environment.yml` for container runtime** — it is ignored. Use `pyproject.toml` or `requirements.txt`.
- **Never use `st.experimental_*` APIs** — they are removed in current Streamlit versions and will break on deployment.
- **Never skip `--no-verify`** on git commits unless the user explicitly requests it.
- **Never push to `main`** without user confirmation.

---

# Snowflake-Specific Settings

| Setting | Value |
|---|---|
| Database | `STREAMLIT_APPS` |
| Schema | `FIFA_VEIKKAUS` |
| Warehouse | `FIFA_VEIKKAUS_WH` (XS, auto-suspend 60s) — used as `QUERY_WAREHOUSE` for Snowpark SQL |
| Compute pool | `FIFA_VEIKKAUS_POOL` (CPU_X64_XS, 1 node, AUTO_SUSPEND_SECS 300) — hosts the Streamlit container |
| EAI | `PYPI_ACCESS_INTEGRATION` — allows container to install packages from PyPI |
| Activity table | `FIFA_VEIKKAUS_ACTIVITY` (TS, USER_EMAIL) — written on every session start |
| Auto-suspend Task | `FIFA_VEIKKAUS_AUTOSTOP_TASK` (every 30 min) — suspends pool if no activity in last 60 min |
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

### Production deployment workflow

There are three scenarios. Pick the one that fits the situation and follow
the steps in order — each one composes the more detailed sub-sections that
follow.

**A. First-time deploy to a brand-new Snowflake account.** End-to-end ≈ 5
minutes once you have admin access:

1. **Edit `db/setup.sql` section 9** — uncomment + adjust the
   `GRANT ROLE … TO USER …` block for every participant (player or admin).
2. **Run the bootstrap** as `ACCOUNTADMIN`:
   `snowsql -a <account> -u <admin_user> -f db/setup.sql`
   → creates warehouse / database / schema / tables / view / roles / stage,
   seeds the 72-game schedule. The `CREATE STREAMLIT …` line at the bottom
   will warn until step 4 — that's expected.
3. **Upload the source tree** to `@FIFA_VEIKKAUS_STAGE` using the `PUT`
   block in *Deploying files after changes* below.
4. **Re-run** the `CREATE STREAMLIT FIFA_VEIKKAUS_APP` statement (it's
   idempotent — same script). The app object now resolves the uploaded files.
5. **Verify** by opening the app URL from
   `SHOW STREAMLITS LIKE 'FIFA_VEIKKAUS_APP';` and confirming the predictions
   page renders 12 group expanders with the real teams.

**B. Code change (no schema change, no data change).** This is the common
path during the tournament — UI tweaks, bug fixes, new components:

1. **PUT the changed files** to `@FIFA_VEIKKAUS_STAGE` (see block below).
2. **Copy into the live version:**
   ```sql
   COPY FILES INTO 'snow://streamlit/STREAMLIT_APPS.FIFA_VEIKKAUS.FIFA_VEIKKAUS_APP/versions/live/'
       FROM @FIFA_VEIKKAUS_STAGE FILES = ('streamlit_app.py', 'app_pages/my_predictions.py');
   ```
3. Viewers see updates on their next interaction (container runtime reflects
   changes immediately — no `CREATE STREAMLIT` or `DROP STREAMLIT` needed).

**C. Schema / reference-data change.** Touches any of: tables, view, stage,
roles, `data/schedule_2026.json` (which the seed MERGE pulls from), or a
column shape:

1. **Run the migration SQL FIRST** as `ACCOUNTADMIN` — either re-run the
   relevant section of `db/setup.sql` (e.g. section 7 for schedule
   corrections) or a version-specific migration block in `RELEASE_NOTES.md`.
   The MERGE statements are idempotent and use `WHEN MATCHED THEN UPDATE`
   so re-running on previously seeded data corrects rows in place.
2. **Verify** the sanity-check `SELECT COUNT(*)` returns expected counts
   (section 10 of `db/setup.sql`).
3. **Then** deploy the code per scenario B.

Deploying code before the migration in scenario C breaks the running app —
the new code expects new columns / new strings that the DB doesn't have yet.

### Fresh-account bootstrap

For a brand-new Snowflake account, run `db/setup.sql` end-to-end as
`ACCOUNTADMIN`. It is idempotent:

```bash
snowsql -a <account> -u <admin_user> -f db/setup.sql
```

The script creates the warehouse, database, schema, tables, view, stage,
two roles (`FIFA_VEIKKAUS_PLAYER_ROLE`, `FIFA_VEIKKAUS_ADMIN_ROLE`), all
required grants, and seeds the 72-game group-stage schedule. It also
creates the Streamlit object — **upload the source files to
`FIFA_VEIKKAUS_STAGE` first** (PUT block below), then either re-run the
script or just the `CREATE STREAMLIT` section.

The last section (section 9) of `db/setup.sql` is commented-out
`GRANT ROLE ... TO USER ...` templates — uncomment + adjust for the real
participant accounts before running, or run those statements separately.

### Deploying files after changes

Upload changed files to the stage, then copy them into the live version. **Do NOT drop the app** — the app URL is shared with end users and dropping would change it.

**After deploying, update the `deployed_to_snowflake` file** in the project root with the current timestamp, Streamlit version, and the list of files deployed. This file is the source of truth for what is currently live.

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE STREAMLIT_APPS;
USE SCHEMA FIFA_VEIKKAUS;
USE WAREHOUSE FIFA_VEIKKAUS_WH;

-- Upload all source files
PUT file:///path/to/streamlit_app.py                @FIFA_VEIKKAUS_STAGE/           AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/schedule_data.py                @FIFA_VEIKKAUS_STAGE/           AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/my_predictions.py     @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/standings.py          @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/rules.py              @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/admin_results.py      @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/_momentum_slider.py   @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/_bracket_picker.py    @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/_group_picker.py      @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/_team_grid_picker.py  @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/_theme.py             @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/app_pages/_celebrate.py         @FIFA_VEIKKAUS_STAGE/app_pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Reference data (groups, teams, flags, schedule — schedule_data.py reads this)
PUT file:///path/to/data/schedule_2026.json @FIFA_VEIKKAUS_STAGE/data/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Assets (only when images change)
PUT file:///path/to/assets/logo_2026.png @FIFA_VEIKKAUS_STAGE/assets/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/assets/maradona.gif  @FIFA_VEIKKAUS_STAGE/assets/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/assets/pirlo.gif     @FIFA_VEIKKAUS_STAGE/assets/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Country flags (only when flags change; the slider loads these as base64)
PUT file:///path/to/assets/flags/*.svg   @FIFA_VEIKKAUS_STAGE/assets/flags/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Bundled fonts (Snowflake CSP blocks fonts.googleapis.com — woff2 is inlined as base64 in _theme.py)
PUT file:///path/to/assets/fonts/Bungee.woff2       @FIFA_VEIKKAUS_STAGE/assets/fonts/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/assets/fonts/PressStart2P.woff2 @FIFA_VEIKKAUS_STAGE/assets/fonts/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file:///path/to/assets/fonts/VT323.woff2        @FIFA_VEIKKAUS_STAGE/assets/fonts/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Dependencies (only when pyproject.toml changes)
PUT file:///path/to/pyproject.toml @FIFA_VEIKKAUS_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Copy changed files into the live version (container runtime picks up immediately)
COPY FILES INTO 'snow://streamlit/STREAMLIT_APPS.FIFA_VEIKKAUS.FIFA_VEIKKAUS_APP/versions/live/'
    FROM @FIFA_VEIKKAUS_STAGE
    FILES = ('streamlit_app.py', 'app_pages/my_predictions.py');  -- list only what changed
```

Only drop and recreate the app as a last resort (e.g., the app is completely broken and won't start). This changes the app URL and breaks existing bookmarks/shared links:

```sql
-- LAST RESORT ONLY — changes the app URL
DROP STREAMLIT FIFA_VEIKKAUS_APP;

CREATE STREAMLIT FIFA_VEIKKAUS_APP
    FROM '@STREAMLIT_APPS.FIFA_VEIKKAUS.FIFA_VEIKKAUS_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    RUNTIME_NAME  = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
    COMPUTE_POOL  = FIFA_VEIKKAUS_POOL
    QUERY_WAREHOUSE = 'FIFA_VEIKKAUS_WH'
    EXTERNAL_ACCESS_INTEGRATIONS = (PYPI_ACCESS_INTEGRATION);

ALTER STREAMLIT FIFA_VEIKKAUS_APP ADD LIVE VERSION FROM LAST;
```

### Auto-suspend behaviour (cost control)

The Streamlit container itself runs on `FIFA_VEIKKAUS_POOL` (CPU_X64_XS, ~0.06 credits/hr). To avoid 24/7 billing during the tournament, a Snowflake Task force-suspends the pool when idle:

1. `streamlit_app.py` writes a row to `FIFA_VEIKKAUS_ACTIVITY` on each session start (try/except, never fatal).
2. `FIFA_VEIKKAUS_AUTOSTOP_TASK` runs every 30 minutes. If `MAX(TS) < now() - 60 min`, it calls `ALTER COMPUTE POOL FIFA_VEIKKAUS_POOL STOP_ALL; SUSPEND;`.
3. When the next viewer opens the app URL, `AUTO_RESUME = TRUE` on the pool brings it back. Cold start: **~60-90 seconds** of loading spinner before the page renders.

Knobs (in `db/setup.sql` section 7c):

- Idle threshold (currently 60 min): adjust the `DATEADD(minute, -60, ...)` inside `FIFA_VEIKKAUS_AUTOSTOP_SP`.
- Poll interval (currently 30 min): adjust `SCHEDULE = '30 MINUTE'` on `FIFA_VEIKKAUS_AUTOSTOP_TASK`.
- Disable temporarily during heavy tournament hours: `ALTER TASK FIFA_VEIKKAUS_AUTOSTOP_TASK SUSPEND;` (resume with `RESUME`).

Inspect:

```sql
SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME=>'FIFA_VEIKKAUS_AUTOSTOP_TASK'))
ORDER BY SCHEDULED_TIME DESC LIMIT 20;

SHOW COMPUTE POOLS LIKE 'FIFA_VEIKKAUS_POOL';
```

### Database migrations

Schema and data migrations live in `RELEASE_NOTES.md` under the corresponding version heading. Each migration is a self-contained SQL block wrapped in `BEGIN; ... COMMIT;` and ends with sanity-check `SELECT COUNT(*)` queries — both should return `0` after a successful run.

**Order of operations for a release with a migration:**

1. **Run the migration SQL first** (as `ACCOUNTADMIN` in a Snowflake worksheet) — see `RELEASE_NOTES.md`.
2. **Verify** the sanity-check counts return `0`.
3. **Then deploy the code** via the `PUT` block above.

If you deploy the code first, the running app will still query the old (un-migrated) values and most lookups (e.g. `_FLAGS.get(...)`) will silently miss — flags disappear and playoff defaults don't pre-populate.

Migrations are written to be **idempotent**: running them again on already-migrated data is a no-op because the source strings (English names) no longer exist in the table.

### Team-name convention

All team names in the database and UI are stored **in Finnish**. Keep the translation map in sync across:

- `mock_session.py` (`GROUPS`)
- `_FLAGS` dicts in `app_pages/*.py`
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

The local entry point `streamlit_app_local.py` swaps `st.connection("snowflake")` for `MockSession`, so the full UI runs without a Snowflake connection. `MockSession.safe_session()` yields the mock itself, so the same `with conn.safe_session() as session:` pattern works locally and in production.

```bash
# Start the local server (default port 8501)
python3 -m streamlit run streamlit_app_local.py --server.port 8501 --server.headless true
```

`--server.headless true` skips the "Open browser?" prompt; useful when running in the background or when an agent will drive the browser via Playwright.

### Hot-reload gotcha: imported modules are cached

Streamlit re-runs the script on each browser refresh, but Python's import system caches imported modules. Edits to **`mock_session.py`, the `app_pages/_*.py` CCv2 components, or any other module imported by a page** are **not** picked up by hot reload — only edits to the page file itself reload cleanly.

When you change an imported module, restart the server:

```bash
# Find and kill the running server
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep ':8501'
kill <PID>

# Start it again
python3 -m streamlit run streamlit_app_local.py --server.port 8501 --server.headless true
```

If you see stale behaviour after editing `mock_session.py` or any imported component module and a refresh doesn't fix it, this is the cause.

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
4. **Restart the server when you edit `mock_session.py` or any imported component module.** See the hot-reload gotcha above. Page-file edits (`app_pages/*.py`, `streamlit_app_local.py`) do hot-reload — a `page.reload()` is enough.

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
