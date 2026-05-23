import base64
import calendar
import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

# ── Background image ──────────────────────────────────────────────────────────
_img_path = os.path.join(os.path.dirname(__file__), "..", "assets", "ioag9w7poe8ayrodgmlc.webp")
if os.path.exists(_img_path):
    _b64 = base64.b64encode(open(_img_path, "rb").read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/webp;base64,{_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(5, 10, 30, 0.72);
            pointer-events: none;
            z-index: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

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
GROUPS: dict[str, list[str]] = {
    "A": ["Meksiko",     "Argentiina",  "Marokko",          "Australia"],
    "B": ["Kanada",      "Espanja",     "Senegal",          "Japani"],
    "C": ["Brasilia",    "Englanti",    "Kolumbia",         "Uzbekistan"],
    "D": ["Yhdysvallat", "Ranska",      "Egypti",           "Iran"],
    "E": ["Saksa",       "Norja",       "Tunisia",          "Etelä-Korea"],
    "F": ["Portugali",   "Sveitsi",     "Algeria",          "Qatar"],
    "G": ["Alankomaat",  "Belgia",      "Norsunluurannikko","Bolivia"],
    "H": ["Kroatia",     "Itävalta",    "Ghana",            "Saudi-Arabia"],
    "I": ["Skotlanti",   "Ruotsi",      "Etelä-Afrikka",    "Jordania"],
    "J": ["Turkki",      "Tšekki",      "Kongon DT",        "Panama"],
    "K": ["Bosnia",      "Uruguay",     "Kap Verde",        "Paraguay"],
    "L": ["Ecuador",     "Irak",        "Haiti",            "Curaçao"],
}

_FLAGS = {
    "Alankomaat": "🇳🇱", "Algeria": "🇩🇿", "Argentiina": "🇦🇷",
    "Australia": "🇦🇺", "Belgia": "🇧🇪", "Bolivia": "🇧🇴",
    "Bosnia": "🇧🇦", "Brasilia": "🇧🇷", "Curaçao": "🇨🇼",
    "Ecuador": "🇪🇨", "Egypti": "🇪🇬", "Englanti": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Espanja": "🇪🇸", "Etelä-Afrikka": "🇿🇦", "Etelä-Korea": "🇰🇷",
    "Ghana": "🇬🇭", "Haiti": "🇭🇹", "Iran": "🇮🇷",
    "Irak": "🇮🇶", "Itävalta": "🇦🇹", "Japani": "🇯🇵",
    "Jordania": "🇯🇴", "Kanada": "🇨🇦", "Kap Verde": "🇨🇻",
    "Kolumbia": "🇨🇴", "Kongon DT": "🇨🇩", "Kroatia": "🇭🇷",
    "Marokko": "🇲🇦", "Meksiko": "🇲🇽", "Norja": "🇳🇴",
    "Norsunluurannikko": "🇨🇮", "Panama": "🇵🇦", "Paraguay": "🇵🇾",
    "Portugali": "🇵🇹", "Qatar": "🇶🇦", "Ranska": "🇫🇷",
    "Ruotsi": "🇸🇪", "Saksa": "🇩🇪", "Saudi-Arabia": "🇸🇦",
    "Senegal": "🇸🇳", "Skotlanti": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Sveitsi": "🇨🇭",
    "Tšekki": "🇨🇿", "Tunisia": "🇹🇳", "Turkki": "🇹🇷",
    "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿", "Yhdysvallat": "🇺🇸",
}

TEAMS = sorted({t for teams in GROUPS.values() for t in teams})

# ── Playoff schema (must match Snowflake table column order) ──────────────────
_GROUP_LETTERS = sorted(GROUPS.keys())
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
      <div style="font-size:0.78rem;color:#aab4c8;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:4px;">
        Veikkaukset lukittuvat
      </div>
      <div id="cd-timer"
           style="font-size:1.6rem;font-weight:700;color:#4da6ff;
                  font-variant-numeric:tabular-nums;letter-spacing:2px;">
        Lasketaan...
      </div>
      <div style="font-size:0.72rem;color:#8899aa;margin-top:2px;">
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
all_inputs: dict[int, tuple] = {}

with st.form("prediction_form"):
    for date in dates:
        day_df = schedule_df[schedule_df["MATCH_DAY"] == date].copy()
        day_ids = day_df["ID"].astype(int).tolist()

        day_complete = bool(existing_preds) and all(
            existing_preds.get(gid, (None, None))[0] is not None for gid in day_ids
        )
        date_label = _fi_date(date)
        label = (
            f"{date_label} — {len(day_df)} ottelua  ✓"
            if day_complete
            else f"{date_label} — {len(day_df)} ottelua"
        )

        with st.expander(label, expanded=not day_complete):
            hdr1, hdr2, hdr3 = st.columns([5, 1, 1])
            hdr2.caption("Koti")
            hdr3.caption("Vieras")
            for _, row in day_df.iterrows():
                gid = int(row["ID"])
                ep = existing_preds.get(gid, (None, None))
                h_def = str(int(ep[0])) if ep[0] is not None else ""
                a_def = str(int(ep[1])) if ep[1] is not None else ""
                c1, c2, c3 = st.columns([5, 1, 1])
                c1.write(flagged(row["MATCH"]))
                home_in = c2.text_input("H", value=h_def, key=f"h_{gid}",
                                        label_visibility="collapsed")
                away_in = c3.text_input("A", value=a_def, key=f"a_{gid}",
                                        label_visibility="collapsed")
                all_inputs[gid] = (home_in, away_in)

    submit_label = "Tallenna veikkaukset" if is_new else "Päivitä veikkaukset"
    submit = st.form_submit_button(submit_label, type="primary")

# ── Handle group-stage submission ─────────────────────────────────────────────
if submit:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parsed: dict[int, tuple] = {}
    skipped: list[str] = []

    for gid, (h_str, a_str) in all_inputs.items():
        h_s = h_str.strip() if h_str else ""
        a_s = a_str.strip() if a_str else ""
        if not h_s and not a_s:
            parsed[gid] = (None, None)
            skipped.append(schedule_df[schedule_df["ID"] == gid].iloc[0]["MATCH"])
        else:
            try:
                h, a = int(h_s), int(a_s)
                if not (0 <= h <= 20 and 0 <= a <= 20):
                    raise ValueError
                parsed[gid] = (h, a)
            except (ValueError, AttributeError):
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


with st.form("playoff_form"):
    # ── Lohkovoittajat ja kakkoset (per group) ──────────────────────────
    st.markdown("**Lohkovoittajat ja kakkoset**")
    st.caption("Valitse kullekin lohkolle voittaja ja kakkonen (3 p + 3 p / lohko).")

    group_picks: dict[str, tuple[str, str]] = {}
    for letter in _GROUP_LETTERS:
        teams = GROUPS[letter]
        opts = ["—"] + teams
        with st.expander(f"Lohko {letter}: {', '.join(teams)}", expanded=False):
            c1, c2 = st.columns(2)
            w_key = f"GROUP_{letter}_WINNER"
            r_key = f"GROUP_{letter}_RUNNERUP"
            w = c1.selectbox(
                "Voittaja", options=opts,
                index=_sel_default(w_key, opts),
                key=f"sel_{w_key}",
            )
            r = c2.selectbox(
                "Kakkonen", options=opts,
                index=_sel_default(r_key, opts),
                key=f"sel_{r_key}",
            )
            group_picks[letter] = (w, r)

    # ── Parhaat kolmoset (8 best third-placed) ──────────────────────────
    st.markdown("**Parhaat kolmoset – valitse 8 joukkuetta**")
    st.caption("8 lohkokolmosta etenee R32-vaiheeseen (1 p / kpl).")
    third_teams = st.multiselect(
        "Parhaat kolmoset",
        options=TEAMS, default=_ms_defaults("THIRD", 8),
        max_selections=8, key="ms_third", label_visibility="collapsed",
    )

    # ── R16-jatkajat (16 teams advancing from R32) ──────────────────────
    st.markdown("**R16-jatkajat – valitse 16 joukkuetta**")
    st.caption("R32-vaiheen voittajat etenevät kuudentoista joukkoon (2 p / kpl).")
    r16_teams = st.multiselect(
        "R16-jatkajat",
        options=TEAMS, default=_ms_defaults("R16", 16),
        max_selections=16, key="ms_r16", label_visibility="collapsed",
    )

    # ── Puolivälierät ───────────────────────────────────────────────────
    st.markdown("**Puolivälierät – valitse 8 joukkuetta**")
    st.caption("R16-voittajat puolivälieriin (3 p / kpl).")
    qf_teams = st.multiselect(
        "Puolivälieräjoukkueet",
        options=TEAMS, default=_ms_defaults("QF", 8),
        max_selections=8, key="ms_qf", label_visibility="collapsed",
    )

    # ── Välierät ────────────────────────────────────────────────────────
    st.markdown("**Välierät – valitse 4 joukkuetta**")
    st.caption("Puolivälierien voittajat välieriin (5 p / kpl).")
    sf_teams = st.multiselect(
        "Välieräjoukkueet",
        options=TEAMS, default=_ms_defaults("SF", 4),
        max_selections=4, key="ms_sf", label_visibility="collapsed",
    )

    # ── Finalistit ──────────────────────────────────────────────────────
    st.markdown("**Finalistit – valitse 2 joukkuetta**")
    st.caption("+10 p / kpl välieräpaikan päälle.")
    f_teams = st.multiselect(
        "Finalistit",
        options=TEAMS, default=_ms_defaults("FINALIST", 2),
        max_selections=2, key="ms_f", label_visibility="collapsed",
    )

    # ── Mestari ─────────────────────────────────────────────────────────
    st.markdown("**Mestari**")
    st.caption("+20 p finalistipisteen päälle.")
    champ_opts = ["—"] + TEAMS
    champion = st.selectbox(
        "Mestari", options=champ_opts,
        index=_sel_default("CHAMPION", champ_opts),
        key="sel_champion", label_visibility="collapsed",
    )

    # ── Erikoisveikkaukset ──────────────────────────────────────────────
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
        key="sel_darkhorse",
        help="15 p jos valitsemasi joukkue selviää puolivälieriin asti.",
    )

    _po_label = "Tallenna pudotuspeliveikkaukset" if playoff_new else "Päivitä pudotuspeliveikkaukset"
    playoff_submit = st.form_submit_button(_po_label, type="primary")

# ── Handle playoff submission ─────────────────────────────────────────────────
if playoff_submit:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _s(v) -> str:
        if not v or v == "—":
            return "NULL"
        return "'" + str(v).replace("'", "''") + "'"

    third_v = (list(third_teams) + [None] * 8)[:8]
    r16_v   = (list(r16_teams)   + [None] * 16)[:16]
    qf_v    = (list(qf_teams)    + [None] * 8)[:8]
    sf_v    = (list(sf_teams)    + [None] * 4)[:4]
    fi_v    = (list(f_teams)     + [None] * 2)[:2]

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
        st.rerun()
    except Exception as e:
        st.error(f"Virhe pudotuspeliveikkausten tallennuksessa: {e}")
