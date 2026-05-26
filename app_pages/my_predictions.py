import calendar
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

from app_pages._momentum_slider import momentum_slider
from app_pages._bracket_picker import bracket_picker
from app_pages._team_grid_picker import team_grid_picker
from app_pages._group_picker import group_picker

from app_pages._theme import apply_theme
from app_pages._celebrate import (
    maybe_celebrate,
    maybe_celebrate_groups_complete,
    trigger_submit_celebrate,
    consume_pending,
)

apply_theme()
consume_pending()

# ── Session + tables ──────────────────────────────────────────────────────────
session = st.session_state.snowpark_session
SCHEMA = "FIFA_VEIKKAUS"
PREDICTIONS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PREDICTIONS"
PLAYOFF_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS"

# June 11, 2026 19:00 Finnish EEST (= 16:00 UTC). Tournament opening match.
_LOCK_DATETIME = datetime(2026, 6, 11, 16, 0, 0)
_TARGET_MS = calendar.timegm(_LOCK_DATETIME.timetuple()) * 1000
is_locked = datetime.utcnow() >= _LOCK_DATETIME

# ── Groups + teams (mirror mock_session.py for local parity) ──────────────────
from schedule_data import GROUPS, TEAMS, FLAGS as _FLAGS, GROUP_LETTERS as _GROUP_LETTERS

# ── Playoff schema (must match Snowflake table column order) ──────────────────
_GROUP_POS_COLS = (
    [f"GROUP_{L}_WINNER"   for L in _GROUP_LETTERS] +
    [f"GROUP_{L}_RUNNERUP" for L in _GROUP_LETTERS]
)
_THIRD_COLS    = [f"THIRD_{i}" for i in range(1, 9)]
_R16_COLS      = [f"R16_{i}"   for i in range(1, 17)]
_QF_COLS       = [f"QF_{i}"    for i in range(1, 9)]
_SF_COLS       = [f"SF_{i}"    for i in range(1, 5)]
_FINALIST_COLS = ["FINALIST_1", "FINALIST_2"]
_PLAYOFF_COLS = (
    _GROUP_POS_COLS + _THIRD_COLS + _R16_COLS + _QF_COLS + _SF_COLS +
    _FINALIST_COLS + ["CHAMPION", "TOP_SCORER", "DARK_HORSE"]
)

# ── Finnish date helpers ──────────────────────────────────────────────────────
_FI_DAYS = ["Maanantai","Tiistai","Keskiviikko","Torstai","Perjantai","Lauantai","Sunnuntai"]
_FI_MONTHS = ["","tammikuuta","helmikuuta","maaliskuuta","huhtikuuta","toukokuuta","kesäkuuta",
               "heinäkuuta","elokuuta","syyskuuta","lokakuuta","marraskuuta","joulukuuta"]

def _fi_date(d) -> str:
    dt = pd.to_datetime(str(d))
    return f"{_FI_DAYS[dt.weekday()]} {dt.day}. {_FI_MONTHS[dt.month]}"


def flagged(match: str) -> str:
    parts = match.split(" vs ")
    if len(parts) == 2:
        h, a = parts[0].strip(), parts[1].strip()
        return f"{_FLAGS.get(h, '')} {h} vs {_FLAGS.get(a, '')} {a}"
    return match


def with_flag(team: str) -> str:
    return f"{_FLAGS.get(team, '')} {team}".strip()


def _flag_label(t: str) -> str:
    """Used as ``format_func`` for selectboxes — leaves the '—' placeholder
    alone but prefixes real team names with their flag emoji."""
    return "—" if not t or t == "—" else with_flag(t)


def email_to_display_name(email: str) -> str:
    local = email.split("@")[0]
    parts = local.replace(".", " ").split()
    return " ".join(p.capitalize() for p in parts)


# ── Auto-identify user ────────────────────────────────────────────────────────
user_email = (
    st.session_state.get("user_email")
    or session.sql("SELECT CURRENT_USER()").collect()[0][0].lower()
)
display_name = email_to_display_name(user_email)

st.subheader(f"Tervetuloa, {display_name}")

# ── Live countdown timer ──────────────────────────────────────────────────────
components.html(
    f"""
    <div style="background:rgba(0,0,0,0.55);border:1px solid rgba(255,255,255,0.15);
                border-radius:10px;padding:12px 20px;text-align:center;
                font-family:'Source Sans Pro',sans-serif;color:white;">
      <div style="font-size:0.78rem;color:#d4b878;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:4px;">
        Veikkaukset lukittuvat
      </div>
      <div id="cd-timer"
           style="font-size:1.6rem;font-weight:700;color:#f5c842;
                  font-variant-numeric:tabular-nums;letter-spacing:2px;">
        Lasketaan...
      </div>
      <div style="font-size:0.72rem;color:#aa9466;margin-top:2px;">
        11.6.2026 klo 19:00 (Helsinki)
      </div>
    </div>
    <script>
    (function() {{
      var target = {_TARGET_MS};
      function tick() {{
        var el = document.getElementById('cd-timer');
        if (!el) {{ setTimeout(tick, 200); return; }}
        var diff = target - Date.now();
        if (diff <= 0) {{
          el.style.color = '#ff6b6b';
          el.textContent = 'Veikkaukset lukittu';
          return;
        }}
        var d = Math.floor(diff / 86400000);
        var h = Math.floor((diff % 86400000) / 3600000);
        var m = Math.floor((diff % 3600000) / 60000);
        var s = Math.floor((diff % 60000) / 1000);
        el.textContent = d + 'pv  '
          + String(h).padStart(2,'0') + 'h  '
          + String(m).padStart(2,'0') + 'm  '
          + String(s).padStart(2,'0') + 's';
        setTimeout(tick, 1000);
      }}
      tick();
    }})();
    </script>
    """,
    height=110,
)

if is_locked:
    st.warning("Veikkaukset on lukittu – turnaus on alkanut. Ennustuksia ei voi enää muokata.")
    st.stop()

# ── Snowflake loads (cached so picker clicks don't re-query the warehouse) ───
# The schedule is global + immutable during the tournament, so cache shared
# across all viewers. The per-user predictions live in st.session_state and
# are invalidated explicitly after a successful save.
@st.cache_data(ttl=3600, show_spinner=False)
def _load_schedule(_session) -> pd.DataFrame:
    return _session.sql(
        f"SELECT ID, MATCH_DAY, MATCH FROM {SCHEMA}.FIFA_VEIKKAUS_SCHEDULE ORDER BY ID"
    ).to_pandas()


def _load_existing_preds(user_email: str) -> dict[int, tuple]:
    out: dict[int, tuple] = {}
    for _, row in session.sql(
        f"SELECT ID, HOME_TEAM_GOALS, AWAY_TEAM_GOALS FROM {PREDICTIONS_TABLE} "
        f"WHERE USER_EMAIL = '{user_email}' ORDER BY ID"
    ).to_pandas().iterrows():
        h, a = row["HOME_TEAM_GOALS"], row["AWAY_TEAM_GOALS"]
        out[int(row["ID"])] = (
            None if pd.isna(h) else h,
            None if pd.isna(a) else a,
        )
    return out


def _load_playoff_existing(user_email: str) -> dict:
    out: dict = {}
    try:
        pp_df = session.sql(
            f"SELECT * FROM {PLAYOFF_TABLE} WHERE USER_EMAIL = '{user_email}'"
        ).to_pandas()
        if len(pp_df) > 0:
            for k in _PLAYOFF_COLS:
                if k not in pp_df.columns:
                    continue
                v = pp_df.iloc[0][k]
                if v is not None and not (isinstance(v, float) and pd.isna(v)) and v != "":
                    out[k] = v
    except Exception:
        pass
    return out


schedule_df = _load_schedule(session)

# Per-user caches keyed by email — flushed on user switch or after a save.
if st.session_state.get("_preds_cache_user") != user_email:
    st.session_state.pop("_existing_preds", None)
    st.session_state.pop("_playoff_existing", None)
    st.session_state._preds_cache_user = user_email

if "_existing_preds" not in st.session_state:
    st.session_state._existing_preds = _load_existing_preds(user_email)
existing_preds = st.session_state._existing_preds

if "_playoff_existing" not in st.session_state:
    st.session_state._playoff_existing = _load_playoff_existing(user_email)
playoff_existing = st.session_state._playoff_existing

is_new = len(existing_preds) == 0
playoff_new = len(playoff_existing) == 0

all_match_ids: set[int] = set(schedule_df["ID"].astype(int).tolist())


# ── Floating progress counter (top-right, persists on scroll) ────────────────
# Counter lives in its own `components.html` iframe (so it can run JS) and
# updates live by subscribing to a `BroadcastChannel('fifa-picks')`. Every
# CCv2 picker (slider, group, thirds-grid, bracket) broadcasts on commit, so
# the count refreshes without any Streamlit rerun. Initial state is seeded
# from session_state + DB so the count is accurate on page load.
_GROUP_TOTAL = 72
_PLAYOFF_TOTAL = 12 + 12 + 8 + 16 + 8 + 4 + 2 + 1 + 1 + 1  # 65
_TOTAL_TARGET = _GROUP_TOTAL + _PLAYOFF_TOTAL  # 137


def _initial_counter_state() -> dict:
    """Snapshot of every counted slot at the start of this render. JS then
    mutates this object via broadcast messages from the picker iframes."""
    matches_filled: list[int] = []
    for gid in all_match_ids:
        st_obj = st.session_state.get(f"mom_{gid}")
        score = getattr(st_obj, "score", None) if st_obj is not None else None
        if isinstance(score, dict) and "home" in score and "away" in score:
            matches_filled.append(int(gid))
            continue
        ep = existing_preds.get(gid, (None, None))
        if ep[0] is not None:
            matches_filled.append(int(gid))

    groups: dict[str, dict] = {}
    for letter in _GROUP_LETTERS:
        grp_state = st.session_state.get(f"grp_{letter}")
        grp_pick = getattr(grp_state, "pick", None) if grp_state is not None else None
        if isinstance(grp_pick, dict):
            w = grp_pick.get("winner") or None
            r = grp_pick.get("runnerup") or None
        else:
            w = playoff_existing.get(f"GROUP_{letter}_WINNER") or None
            r = playoff_existing.get(f"GROUP_{letter}_RUNNERUP") or None
        groups[letter] = {"winner": w, "runnerup": r}

    third_state = st.session_state.get("grid_third")
    third_live = getattr(third_state, "selected", None) if third_state is not None else None
    if isinstance(third_live, list):
        thirds = [t for t in third_live if t]
    else:
        thirds = [
            playoff_existing[f"THIRD_{i}"]
            for i in range(1, 9)
            if playoff_existing.get(f"THIRD_{i}")
        ]

    bracket_state = st.session_state.get("bracket_picker")
    bracket_picks = (
        getattr(bracket_state, "picks", None) if bracket_state is not None else None
    )
    bracket: dict = {"r16": [], "qf": [], "sf": [], "finalists": [], "champion": None}
    if isinstance(bracket_picks, dict):
        for stage in ("r16", "qf", "sf", "finalists"):
            v = bracket_picks.get(stage)
            if isinstance(v, list):
                bracket[stage] = [t for t in v if t]
        champ = bracket_picks.get("champion")
        bracket["champion"] = champ if (champ and champ != "—") else None
    else:
        for stage, count in (("r16", 16), ("qf", 8), ("sf", 4), ("finalists", 2)):
            prefix = "FINALIST" if stage == "finalists" else stage.upper()
            bracket[stage] = [
                playoff_existing[f"{prefix}_{i}"]
                for i in range(1, count + 1)
                if playoff_existing.get(f"{prefix}_{i}")
            ]
        champ = playoff_existing.get("CHAMPION")
        bracket["champion"] = champ if (champ and champ != "—") else None

    scorer_state = st.session_state.get("ti_scorer")
    scorer = (
        scorer_state
        if scorer_state is not None
        else (playoff_existing.get("TOP_SCORER") or "")
    )
    scorer_set = bool(isinstance(scorer, str) and scorer.strip())

    dark_state = st.session_state.get("sel_darkhorse")
    dark = dark_state if dark_state is not None else playoff_existing.get("DARK_HORSE")
    dark_set = bool(dark and dark != "—")

    return {
        "matches": matches_filled,
        "groups": groups,
        "thirds": thirds,
        "bracket": bracket,
        "scorer_set": scorer_set,
        "dark_set": dark_set,
    }


_counter_initial = _initial_counter_state()
_counter_initial_json = json.dumps(_counter_initial)


def _initial_count(state: dict) -> int:
    n = len(state["matches"])
    for g in state["groups"].values():
        if g.get("winner") and g["winner"] != "—": n += 1
        if g.get("runnerup") and g["runnerup"] != "—": n += 1
    n += min(len(state["thirds"]), 8)
    n += min(len(state["bracket"]["r16"]), 16)
    n += min(len(state["bracket"]["qf"]), 8)
    n += min(len(state["bracket"]["sf"]), 4)
    n += min(len(state["bracket"]["finalists"]), 2)
    if state["bracket"]["champion"]: n += 1
    if state["scorer_set"]: n += 1
    if state["dark_set"]: n += 1
    return n


_initial_n = _initial_count(_counter_initial)
_initial_pct = (_initial_n / _TOTAL_TARGET) * 100 if _TOTAL_TARGET else 0
_initial_row_cls = "pred-counter-row done" if _initial_n >= _TOTAL_TARGET else "pred-counter-row"

# Fixed-position chrome rendered into the parent DOM (st.markdown strips
# <script> but keeps the styled box). The live values get rewritten by the
# hidden iframe below whenever a picker broadcasts on the BroadcastChannel.
st.markdown(
    f"""
    <style>
    .pred-counter {{
        position: fixed; top: 14px; right: 18px; z-index: 100000;
        display: flex; flex-direction: column; gap: 8px;
        padding: 14px 18px 16px; min-width: 260px;
        background: linear-gradient(180deg, rgba(58, 36, 8, 0.97), rgba(22, 14, 4, 0.97));
        font-family: 'Press Start 2P', 'Courier New', monospace;
        text-transform: uppercase; letter-spacing: 0.08em;
        border: 3px solid #f5c842; border-radius: 4px;
        box-shadow:
            inset 0 0 0 2px rgba(0, 0, 0, 0.85),
            inset 0 0 12px rgba(245, 200, 66, 0.18),
            0 0 0 1px rgba(0, 0, 0, 0.85),
            0 0 14px rgba(245, 200, 66, 0.55),
            0 0 28px rgba(212, 110, 23, 0.45);
    }}
    .pred-counter-player {{
        font-size: 0.62rem; color: #ff5edc; text-align: center; line-height: 1.4;
        text-shadow: 1px 1px 0 #1a0814, 0 0 6px rgba(255, 94, 220, 0.85), 0 0 14px rgba(255, 94, 220, 0.55);
        padding-bottom: 6px; border-bottom: 2px dashed rgba(245, 200, 66, 0.45);
    }}
    .pred-counter-player .pred-counter-player-label {{
        color: #6ff0ff; text-shadow: 1px 1px 0 #001818, 0 0 6px rgba(111, 240, 255, 0.85); margin-right: 6px;
    }}
    .pred-counter-title {{
        font-size: 0.72rem; color: #ffd95c; text-align: center;
        text-shadow: 1px 1px 0 #1a1208, 0 0 6px rgba(255, 217, 92, 0.85), 0 0 14px rgba(245, 165, 20, 0.55);
    }}
    .pred-counter-row {{
        display: flex; justify-content: space-between; align-items: center; gap: 10px;
        font-size: 0.80rem; color: #f5c842;
        text-shadow: 1px 1px 0 #1a1208, 0 0 6px rgba(245, 200, 66, 0.85), 0 0 14px rgba(212, 160, 23, 0.55);
    }}
    .pred-counter-row.done {{
        color: #c8ff70;
        text-shadow: 1px 1px 0 #0a1404, 0 0 6px rgba(200, 255, 112, 0.90), 0 0 14px rgba(160, 220, 60, 0.60);
    }}
    .pred-counter-row .pred-counter-count {{ font-size: 1.10rem; white-space: nowrap; letter-spacing: 0.06em; }}
    .pred-counter-bar {{
        height: 8px; width: 100%; background: rgba(0, 0, 0, 0.85);
        box-shadow: inset 0 0 0 2px rgba(245, 200, 66, 0.65), inset 0 0 4px rgba(0, 0, 0, 0.9);
        margin-top: 4px;
    }}
    .pred-counter-bar-fill {{
        height: 100%; background: linear-gradient(90deg, #ff5edc, #ffd95c, #6ff0ff);
        box-shadow: 0 0 6px rgba(255, 217, 92, 0.85), 0 0 12px rgba(245, 200, 66, 0.65);
        transition: width 0.25s ease-out;
    }}
    @media (max-width: 640px) {{
        .pred-counter {{ top: 8px; right: 8px; min-width: 190px; padding: 10px 12px 12px; gap: 6px; }}
        .pred-counter-player {{ font-size: 0.50rem; }}
        .pred-counter-title {{ font-size: 0.58rem; }}
        .pred-counter-row {{ font-size: 0.60rem; }}
        .pred-counter-row .pred-counter-count {{ font-size: 0.85rem; }}
        .pred-counter-bar {{ height: 6px; }}
    }}
    </style>
    <div class="pred-counter">
      <div class="pred-counter-player">
        <span class="pred-counter-player-label">Player:</span>{display_name}
      </div>
      <div class="pred-counter-title">Challenge status</div>
      <div id="pc-row" class="{_initial_row_cls}">
        <span>Veikkaukset</span><span id="pc-count" class="pred-counter-count">{_initial_n} / {_TOTAL_TARGET}</span>
      </div>
      <div class="pred-counter-bar"><div id="pc-bar" class="pred-counter-bar-fill" style="width: {_initial_pct:.1f}%;"></div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Hidden iframe carries the JS that listens for BroadcastChannel pings from the
# picker iframes and rewrites the counter elements in the parent DOM (same
# Streamlit origin → cross-frame DOM access is allowed). Falls back silently
# if the API is unavailable.
_counter_js_html = f"""<!doctype html><html><head><meta charset="utf-8"></head><body><script>
(function() {{
  const TARGET = {_TOTAL_TARGET};
  const state = {_counter_initial_json};
  state.matches = new Set((state.matches || []).map(Number));
  state.groups = state.groups || {{}};
  state.thirds = Array.isArray(state.thirds) ? state.thirds.filter(Boolean) : [];
  state.bracket = state.bracket || {{r16: [], qf: [], sf: [], finalists: [], champion: null}};
  ["r16","qf","sf","finalists"].forEach(k => {{
    state.bracket[k] = Array.isArray(state.bracket[k]) ? state.bracket[k].filter(Boolean) : [];
  }});

  function recount() {{
    let n = 0;
    n += state.matches.size;
    for (const k of Object.keys(state.groups)) {{
      const g = state.groups[k] || {{}};
      if (g.winner && g.winner !== '—') n++;
      if (g.runnerup && g.runnerup !== '—') n++;
    }}
    n += Math.min(state.thirds.length, 8);
    n += Math.min(state.bracket.r16.length, 16);
    n += Math.min(state.bracket.qf.length, 8);
    n += Math.min(state.bracket.sf.length, 4);
    n += Math.min(state.bracket.finalists.length, 2);
    if (state.bracket.champion && state.bracket.champion !== '—') n++;
    if (state.scorer_set) n++;
    if (state.dark_set) n++;
    return n;
  }}

  // Walk up to the topmost same-origin window that hosts the counter chrome.
  function getParentDoc() {{
    let w = window;
    for (let i = 0; i < 6; i++) {{
      try {{
        const next = w.parent;
        if (!next || next === w) return w.document;
        // Probe access; throws if cross-origin.
        void next.document;
        w = next;
      }} catch (_) {{
        return w.document;
      }}
    }}
    return w.document;
  }}

  function paintIn(doc) {{
    const n = recount();
    const c = doc.getElementById('pc-count');
    const b = doc.getElementById('pc-bar');
    const r = doc.getElementById('pc-row');
    if (c) c.textContent = `${{n}} / ${{TARGET}}`;
    if (b) b.style.width = `${{Math.min(100, (n / TARGET) * 100).toFixed(1)}}%`;
    if (r) {{
      if (n >= TARGET) r.classList.add('done');
      else r.classList.remove('done');
    }}
    return !!c;
  }}

  function paint() {{
    // Try parent chain first; if elements not found there, also try our own
    // document and window.top as fallbacks.
    if (paintIn(getParentDoc())) return;
    try {{ if (paintIn(window.top.document)) return; }} catch (_) {{}}
    paintIn(document);
  }}

  paint();

  try {{
    const channel = new BroadcastChannel('fifa-picks');
    channel.onmessage = (e) => {{
      const m = e.data || {{}};
      if (m.type === 'match') {{
        const id = Number(m.id);
        if (m.filled) state.matches.add(id);
        else state.matches.delete(id);
      }} else if (m.type === 'group') {{
        state.groups[m.letter] = {{winner: m.winner || null, runnerup: m.runnerup || null}};
      }} else if (m.type === 'thirds') {{
        state.thirds = Array.isArray(m.teams) ? m.teams.filter(Boolean) : [];
      }} else if (m.type === 'bracket') {{
        const p = m.picks || {{}};
        ["r16","qf","sf","finalists"].forEach(k => {{
          state.bracket[k] = Array.isArray(p[k]) ? p[k].filter(Boolean) : [];
        }});
        state.bracket.champion = p.champion || null;
      }} else {{
        return;
      }}
      paint();
    }};
  }} catch (e) {{
    console.warn('fifa-picks broadcast unavailable:', e);
  }}
}})();
</script></body></html>"""
components.html(_counter_js_html, height=0)


# ── Incomplete warning ────────────────────────────────────────────────────────
_unfilled_ids = [
    gid for gid in schedule_df["ID"].astype(int)
    if existing_preds.get(gid, (None, None))[0] is None
]
if existing_preds and _unfilled_ids:
    st.warning(f"{len(_unfilled_ids)} ottelulla ei ole vielä ennustetta.")

# ── Group-stage section ───────────────────────────────────────────────────────
st.subheader("Alkulohkon ottelut")
st.caption(
    "Ennusta jokaisen ottelun lopputulos (koti – vieras). "
    "Voit tallentaa veikkaukset osittain ja täydentää ne myöhemmin – "
    "kaikki veikkaukset lukittuvat turnauksen alkaessa."
)

dates = sorted(schedule_df["MATCH_DAY"].unique())

st.caption(
    "Vedä pokaalia oikealle (koti voittaa) tai vasemmalle (vieras voittaa). "
    "Tallenna kaikki veikkaukset sivun lopussa olevalla painikkeella."
)


@st.fragment
def _render_match_slider(gid: int, match: str, default: tuple | None) -> None:
    """Each match renders in its own fragment so dragging one slider only
    reruns that single block instead of the whole page. The Pirlo overlay
    is emitted *inside* this fragment when a Saksa/USA pick lands — no
    app-rerun, so the 71 other slider iframes are untouched."""
    home, _, away = match.partition(" vs ")
    # Pass plain names — the slider renders each country's flag as a giant
    # faded background image, so the emoji prefix would be visually redundant.
    momentum_slider(
        match_id=gid,
        home_team=home.strip(),
        away_team=away.strip(),
        default_score=default,
    )
    maybe_celebrate()


# Flat list — all 72 matches visible at once, grouped only by a date header.
for date in dates:
    day_df = schedule_df[schedule_df["MATCH_DAY"] == date].copy()
    day_ids = day_df["ID"].astype(int).tolist()
    day_complete = bool(existing_preds) and all(
        existing_preds.get(gid, (None, None))[0] is not None for gid in day_ids
    )
    date_label = _fi_date(date)
    check = "  ✓" if day_complete else ""
    st.markdown(
        f"<div style='font-family:Bungee,Impact,sans-serif;text-transform:uppercase;"
        f"letter-spacing:1.5px;color:#ffd95c;font-size:0.95rem;margin-top:18px;"
        f"margin-bottom:8px;border-bottom:2px solid rgba(245,200,80,0.45);"
        f"padding-bottom:4px;'>{date_label} — {len(day_df)} ottelua{check}</div>",
        unsafe_allow_html=True,
    )
    for _, row in day_df.iterrows():
        gid = int(row["ID"])
        ep = existing_preds.get(gid, (None, None))
        default = (int(ep[0]), int(ep[1])) if ep[0] is not None else None
        _render_match_slider(gid, row["MATCH"], default)

submit_label = "Tallenna veikkaukset" if is_new else "Päivitä veikkaukset"
submit = st.button(submit_label, type="primary", use_container_width=True)

# ── Handle group-stage submission ─────────────────────────────────────────────
if submit:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parsed: dict[int, tuple] = {}
    skipped: list[str] = []

    # Read each match's score from the slider's session state. If untouched
    # in this session, fall back to any previously saved prediction.
    for gid in sorted(all_match_ids):
        slider_state = st.session_state.get(f"mom_{gid}")
        slider_score = getattr(slider_state, "score", None) if slider_state else None
        if isinstance(slider_score, dict) and "home" in slider_score and "away" in slider_score:
            parsed[gid] = (int(slider_score["home"]), int(slider_score["away"]))
            continue
        ep = existing_preds.get(gid, (None, None))
        if ep[0] is not None:
            parsed[gid] = (int(ep[0]), int(ep[1]))
        else:
            parsed[gid] = (None, None)
            skipped.append(schedule_df[schedule_df["ID"] == gid].iloc[0]["MATCH"])

    rows_out = []
    for gid, goals in parsed.items():
        srow = schedule_df[schedule_df["ID"] == gid].iloc[0]
        rows_out.append({
            "USER_EMAIL": user_email,
            "ID": gid,
            "MATCH_DAY": srow["MATCH_DAY"],
            "MATCH": srow["MATCH"],
            "HOME_TEAM_GOALS": goals[0],
            "AWAY_TEAM_GOALS": goals[1],
        })

    final_df = pd.DataFrame(rows_out).sort_values("ID").reset_index(drop=True)
    try:
        session.sql(
            f"DELETE FROM {PREDICTIONS_TABLE} WHERE USER_EMAIL = '{user_email}'"
        ).collect()
        values_parts = []
        for _, r in final_df.iterrows():
            h_sql = "NULL" if pd.isna(r["HOME_TEAM_GOALS"]) else str(int(r["HOME_TEAM_GOALS"]))
            a_sql = "NULL" if pd.isna(r["AWAY_TEAM_GOALS"]) else str(int(r["AWAY_TEAM_GOALS"]))
            values_parts.append(
                f"('{r['USER_EMAIL']}', {int(r['ID'])}, '{r['MATCH_DAY']}', "
                f"'{r['MATCH']}', {h_sql}, {a_sql}, '{now_str}')"
            )
        session.sql(
            f"INSERT INTO {PREDICTIONS_TABLE} "
            f"(USER_EMAIL, ID, MATCH_DAY, MATCH, HOME_TEAM_GOALS, AWAY_TEAM_GOALS, INSERTED) "
            f"VALUES {', '.join(values_parts)}"
        ).collect()
        st.session_state.pop("_existing_preds", None)
        if skipped:
            st.warning(
                f"Tallennettu, mutta {len(skipped)} ottelulla ei ennustetta: "
                f"{', '.join(skipped[:5])}{'...' if len(skipped) > 5 else ''}"
            )
        else:
            st.success(f"Ennustukset tallennettu – **{display_name}**!")
        st.rerun()
    except Exception as e:
        st.error(f"Virhe tallennuksessa: {e}")

# ── Playoff bracket section (wrapped in a fragment so picker clicks rerun
#    only this block, not the 72 match sliders above) ──────────────────────
st.divider()


@st.fragment
def _render_playoff_section() -> None:
    # Re-read each rerun so the fragment sees fresh data after a save.
    playoff_existing = st.session_state.get("_playoff_existing") or {}
    playoff_new = len(playoff_existing) == 0

    def _sel_default(key: str, options: list[str]) -> int:
        v = playoff_existing.get(key)
        if v in options:
            return options.index(v)
        return 0

    def _ms_defaults(prefix: str, count: int) -> list[str]:
        out = []
        for i in range(1, count + 1):
            v = playoff_existing.get(f"{prefix}_{i}")
            if v and isinstance(v, str) and v in TEAMS:
                out.append(v)
        return out

    def _str_default(key: str) -> str:
        v = playoff_existing.get(key, "")
        return v if isinstance(v, str) else ""

    st.subheader("Pudotuspelibracket")
    st.caption(
        "Veikkaa koko pudotuspelibracket etukäteen: lohkovoittajat ja kakkoset, "
        "parhaat kolmoset, R16-jatkajat ja edelleen aina mestariin asti. "
        "Lisäksi turnauksen maalikuningas ja oma musta hevosesi."
    )

    # ── Lohkovoittajat ja kakkoset (per group) ──────────────────────────────
    st.markdown("**Lohkovoittajat ja kakkoset**")
    st.caption("Valitse kullekin lohkolle voittaja ja kakkonen (3 p + 3 p / lohko).")

    group_picks: dict[str, tuple[str, str]] = {}
    for letter in _GROUP_LETTERS:
        teams = GROUPS[letter]
        w_key = f"GROUP_{letter}_WINNER"
        r_key = f"GROUP_{letter}_RUNNERUP"
        flag_teams = [with_flag(t) for t in teams]
        expander_title = f"Lohko {letter}: {', '.join(flag_teams)}"
        with st.expander(expander_title, expanded=True):
            pick = group_picker(
                teams=teams,
                team_labels={t: with_flag(t) for t in teams},
                winner=playoff_existing.get(w_key) if playoff_existing.get(w_key) in teams else None,
                runnerup=playoff_existing.get(r_key) if playoff_existing.get(r_key) in teams else None,
                key=f"grp_{letter}",
            )
            w = pick["winner"] or "—"
            r = pick["runnerup"] or "—"
            group_picks[letter] = (w, r)

    maybe_celebrate_groups_complete(group_picks)

    # ── Parhaat kolmoset (8 best third-placed) ──────────────────────────────
    st.markdown("**Parhaat kolmoset – valitse 8 joukkuetta**")
    st.caption("8 lohkokolmosta etenee R32-vaiheeseen (1 p / kpl).")

    _picked_w_r = {
        t for (w, r) in group_picks.values() for t in (w, r) if t and t != "—"
    }
    _third_options = [t for t in TEAMS if t not in _picked_w_r]

    third_teams = team_grid_picker(
        teams=_third_options,
        selected=_ms_defaults("THIRD", 8),
        team_labels={t: with_flag(t) for t in _third_options},
        max_selected=8,
        key="grid_third",
    )

    # ── R32 → Champion: visual bracket ──────────────────────────────────────
    st.markdown("**Bracket: R16 → Mestari**")
    st.caption(
        "Klikkaa joukkuetta nostaaksesi sen seuraavaan vaiheeseen. "
        "Klikkaa uudelleen pudottaaksesi sen pois jatkosta."
    )

    _r32_pool: list[str] = []
    _seen: set[str] = set()
    for letter in _GROUP_LETTERS:
        w, r = group_picks[letter]
        for team in (w, r):
            if team and team != "—" and team not in _seen:
                _r32_pool.append(team)
                _seen.add(team)
    for team in third_teams:
        if team and team not in _seen:
            _r32_pool.append(team)
            _seen.add(team)

    _n_winners = sum(1 for (w, _) in group_picks.values() if w and w != "—")
    _n_runners = sum(1 for (_, r) in group_picks.values() if r and r != "—")
    _n_thirds  = len(third_teams)
    _pool_total = len(_r32_pool)

    if _pool_total >= 32:
        bracket_picks = bracket_picker(
            teams_r32=_r32_pool,
            team_labels={t: with_flag(t) for t in _r32_pool},
            initial_picks={
                "r16": _ms_defaults("R16", 16),
                "qf": _ms_defaults("QF", 8),
                "sf": _ms_defaults("SF", 4),
                "finalists": _ms_defaults("FINALIST", 2),
                "champion": _str_default("CHAMPION") or None,
            },
            key="bracket_picker",
        )
    else:
        _missing_parts = []
        if _n_winners < 12: _missing_parts.append(f"lohkovoittajat **{_n_winners}/12**")
        if _n_runners < 12: _missing_parts.append(f"kakkoset **{_n_runners}/12**")
        if _n_thirds  < 8:  _missing_parts.append(f"parhaat kolmoset **{_n_thirds}/8**")
        st.info(
            f"R32-pooli **{_pool_total} / 32** — bracket aukeaa, kun kaikki 32 joukkuetta on valittu.\n\n"
            f"Vielä puuttuu: {', '.join(_missing_parts) if _missing_parts else 'ei mitään 🎉'}."
        )
        bracket_picks = {"r16": [], "qf": [], "sf": [], "finalists": [], "champion": None}

    # ── Erikoisveikkaukset ──────────────────────────────────────────────────
    st.markdown("**Erikoisveikkaukset**")
    col_e1, col_e2 = st.columns(2)
    top_scorer = col_e1.text_input(
        "Maalikuningas (pelaajan nimi)",
        value=_str_default("TOP_SCORER"),
        key="ti_scorer",
        help="15 p oikeasta turnauksen maalikuninkaasta.",
    )
    dark_opts = ["—"] + TEAMS
    dark_horse = col_e2.selectbox(
        "Musta hevonen (etenee puolivälieriin)",
        options=dark_opts,
        index=_sel_default("DARK_HORSE", dark_opts),
        format_func=_flag_label,
        key="sel_darkhorse",
        help="15 p jos valitsemasi joukkue selviää puolivälieriin asti.",
    )

    _po_label = "Tallenna pudotuspeliveikkaukset" if playoff_new else "Päivitä pudotuspeliveikkaukset"
    playoff_submit = st.button(_po_label, type="primary", use_container_width=True, key="btn_po_submit")

    if playoff_submit:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def _s(v) -> str:
            if not v or v == "—":
                return "NULL"
            return "'" + str(v).replace("'", "''") + "'"

        third_v = (list(third_teams)             + [None] * 8)[:8]
        r16_v   = (list(bracket_picks["r16"])    + [None] * 16)[:16]
        qf_v    = (list(bracket_picks["qf"])     + [None] * 8)[:8]
        sf_v    = (list(bracket_picks["sf"])     + [None] * 4)[:4]
        fi_v    = (list(bracket_picks["finalists"]) + [None] * 2)[:2]
        champion = bracket_picks["champion"]

        values: list[str] = [f"'{user_email}'"]
        for letter in _GROUP_LETTERS:
            values.append(_s(group_picks[letter][0]))
        for letter in _GROUP_LETTERS:
            values.append(_s(group_picks[letter][1]))
        for v in third_v: values.append(_s(v))
        for v in r16_v:   values.append(_s(v))
        for v in qf_v:    values.append(_s(v))
        for v in sf_v:    values.append(_s(v))
        for v in fi_v:    values.append(_s(v))
        values.append(_s(champion))
        values.append(_s(top_scorer.strip() if top_scorer else None))
        values.append(_s(dark_horse))
        values.append(f"'{now_str}'")

        col_list = "USER_EMAIL, " + ", ".join(_PLAYOFF_COLS) + ", INSERTED"
        val_list = ", ".join(values)

        try:
            session.sql(
                f"DELETE FROM {PLAYOFF_TABLE} WHERE USER_EMAIL = '{user_email}'"
            ).collect()
            session.sql(
                f"INSERT INTO {PLAYOFF_TABLE} ({col_list}) VALUES ({val_list})"
            ).collect()
            # Refresh per-user cache and force a full-app rerun so the floating
            # counter (rendered at script top) reflects the new playoff total.
            st.session_state._playoff_existing = _load_playoff_existing(user_email)
            st.success(f"Pudotuspeliveikkaukset tallennettu – **{display_name}**!")
            trigger_submit_celebrate()
            st.rerun(scope="app")
        except Exception as e:
            st.error(f"Virhe pudotuspeliveikkausten tallennuksessa: {e}")


_render_playoff_section()
