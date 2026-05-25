import calendar
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

# ── Load schedule ─────────────────────────────────────────────────────────────
schedule_df = session.sql(
    f"SELECT ID, MATCH_DAY, MATCH FROM {SCHEMA}.FIFA_VEIKKAUS_SCHEDULE ORDER BY ID"
).to_pandas()

# ── Load existing group-stage predictions ─────────────────────────────────────
existing_preds: dict[int, tuple] = {}
for _, row in session.sql(
    f"SELECT ID, HOME_TEAM_GOALS, AWAY_TEAM_GOALS FROM {PREDICTIONS_TABLE} "
    f"WHERE USER_EMAIL = '{user_email}' ORDER BY ID"
).to_pandas().iterrows():
    h, a = row["HOME_TEAM_GOALS"], row["AWAY_TEAM_GOALS"]
    existing_preds[int(row["ID"])] = (
        None if pd.isna(h) else h,
        None if pd.isna(a) else a,
    )

is_new = len(existing_preds) == 0

# ── Load existing playoff predictions ────────────────────────────────────────
playoff_existing: dict = {}
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
                playoff_existing[k] = v
except Exception:
    pass

playoff_new = len(playoff_existing) == 0


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
all_match_ids: set[int] = set(schedule_df["ID"].astype(int).tolist())

st.caption(
    "Vedä pokaalia oikealle (koti voittaa) tai vasemmalle (vieras voittaa). "
    "Tallenna kaikki veikkaukset sivun lopussa olevalla painikkeella."
)


@st.fragment
def _render_match_slider(gid: int, match: str, default: tuple | None) -> None:
    """Each match renders in its own fragment so dragging one slider only
    reruns that single block instead of the whole page."""
    home, _, away = match.partition(" vs ")
    momentum_slider(
        match_id=gid,
        home_team=with_flag(home.strip()),
        away_team=with_flag(away.strip()),
        default_score=default,
    )
    # After the user commits a score, check whether they just crossed a
    # 5-pick milestone — fires a full-app rerun that paints the overlay.
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

# ── Playoff bracket section ───────────────────────────────────────────────────
st.divider()
st.subheader("Pudotuspelibracket")
st.caption(
    "Veikkaa koko pudotuspelibracket etukäteen: lohkovoittajat ja kakkoset, "
    "parhaat kolmoset, R16-jatkajat ja edelleen aina mestariin asti. "
    "Lisäksi turnauksen maalikuningas ja oma musta hevosesi."
)


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


# ── Lohkovoittajat ja kakkoset (per group) ──────────────────────────────────
st.markdown("**Lohkovoittajat ja kakkoset**")
st.caption("Valitse kullekin lohkolle voittaja ja kakkonen (3 p + 3 p / lohko).")

group_picks: dict[str, tuple[str, str]] = {}
for letter in _GROUP_LETTERS:
    teams = GROUPS[letter]
    w_key = f"GROUP_{letter}_WINNER"
    r_key = f"GROUP_{letter}_RUNNERUP"
    flag_teams = [with_flag(t) for t in teams]
    expander_title = f"Lohko {letter}: {', '.join(flag_teams)}"
    with st.expander(expander_title, expanded=False):
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

# ── Parhaat kolmoset (8 best third-placed) ──────────────────────────────────
st.markdown("**Parhaat kolmoset – valitse 8 joukkuetta**")
st.caption("8 lohkokolmosta etenee R32-vaiheeseen (1 p / kpl).")

# Best-third candidates exclude any team already picked as a group winner
# or runner-up — a team can only qualify in one slot.
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

# ── R32 → Champion: visual bracket ──────────────────────────────────────────
st.markdown("**Bracket: R16 → Mestari**")
st.caption(
    "Klikkaa joukkuetta nostaaksesi sen seuraavaan vaiheeseen. "
    "Klikkaa uudelleen pudottaaksesi sen pois jatkosta."
)

# Build the R32 pool from current group + best-thirds picks. Order preserved
# to keep the bracket's chip order stable across reruns.
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

# ── Erikoisveikkaukset ──────────────────────────────────────────────────────
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

# ── Handle playoff submission ─────────────────────────────────────────────────
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
        st.success(f"Pudotuspeliveikkaukset tallennettu – **{display_name}**!")
        trigger_submit_celebrate()
        st.rerun()
    except Exception as e:
        st.error(f"Virhe pudotuspeliveikkausten tallennuksessa: {e}")
