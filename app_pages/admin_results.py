import streamlit as st
import pandas as pd

from app_pages._theme import apply_theme

apply_theme()

# ── Access control ────────────────────────────────────────────────────────────
ADMIN_EMAILS = {
    "mika.heino@recordlydata.com",
    "mikko.sulonen@recordlydata.com",
    "marko.laitinen@recordlydata.com",
}

user_email = st.session_state.get("user_email", "")
if user_email not in ADMIN_EMAILS:
    st.error("Ei oikeuksia.")
    st.stop()

session = st.session_state.snowpark_session
SCHEMA = "FIFA_VEIKKAUS"
SCHEDULE_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_SCHEDULE"
RESULTS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_RESULTS"
PLAYOFF_RESULTS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PLAYOFF_RESULTS"

# ── Groups + teams (loaded from data/schedule_2026.json) ─────────────────────
from schedule_data import GROUPS, TEAMS, FLAGS as _FLAGS, GROUP_LETTERS as _GROUP_LETTERS

_GROUP_POS_COLS = (
    [f"GROUP_{L}_WINNER"   for L in _GROUP_LETTERS] +
    [f"GROUP_{L}_RUNNERUP" for L in _GROUP_LETTERS]
)
_THIRD_COLS    = [f"THIRD_{i}" for i in range(1, 9)]
_R16_COLS      = [f"R16_{i}"   for i in range(1, 17)]
_QF_COLS       = [f"QF_{i}"    for i in range(1, 9)]
_SF_COLS       = [f"SF_{i}"    for i in range(1, 5)]
_FINALIST_COLS = ["FINALIST_1", "FINALIST_2"]
_RESULT_COLS = (
    _GROUP_POS_COLS + _THIRD_COLS + _R16_COLS + _QF_COLS + _SF_COLS +
    _FINALIST_COLS + ["CHAMPION", "TOP_SCORER"]
)

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


st.title("Syötä tulokset")

# ── Load schedule + current results ──────────────────────────────────────────
data_df = session.sql(
    f"""
    SELECT s.ID, s.MATCH_DAY, s.MATCH,
           r.HOME_TEAM_GOALS, r.AWAY_TEAM_GOALS
    FROM {SCHEDULE_TABLE} s
    LEFT JOIN {RESULTS_TABLE} r ON s.ID = r.ID
    ORDER BY s.ID
    """
).to_pandas()

total = len(data_df)
filled = int(data_df["HOME_TEAM_GOALS"].notna().sum())

col1, col2 = st.columns([4, 1])
with col1:
    st.progress(filled / total if total > 0 else 0)
with col2:
    st.caption(f"{filled} / {total} tulosta syötetty")

# ── Group-stage results editor ────────────────────────────────────────────────
st.subheader("Alkulohkon tulokset")
st.caption("Syötä jokaisen ottelun lopputulos (koti – vieras).")

dates = sorted(data_df["MATCH_DAY"].unique())
game_inputs: dict[int, tuple] = {}

with st.form("results_form"):
    for date in dates:
        day_df = data_df[data_df["MATCH_DAY"] == date].copy()

        day_complete = day_df["HOME_TEAM_GOALS"].notna().all()
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
                try:
                    h_def = "" if pd.isna(row["HOME_TEAM_GOALS"]) else str(int(row["HOME_TEAM_GOALS"]))
                except (ValueError, TypeError):
                    h_def = ""
                try:
                    a_def = "" if pd.isna(row["AWAY_TEAM_GOALS"]) else str(int(row["AWAY_TEAM_GOALS"]))
                except (ValueError, TypeError):
                    a_def = ""
                c1, c2, c3 = st.columns([5, 1, 1])
                c1.write(flagged(row["MATCH"]))
                home = c2.text_input("H", value=h_def, key=f"rh_{gid}",
                                     label_visibility="collapsed")
                away = c3.text_input("A", value=a_def, key=f"ra_{gid}",
                                     label_visibility="collapsed")
                game_inputs[gid] = (home, away)

    submit = st.form_submit_button("Tallenna tulokset", type="primary")

# ── Handle group-stage submission ─────────────────────────────────────────────
if submit:
    parsed: dict[int, tuple] = {}
    for gid, (h_str, a_str) in game_inputs.items():
        try:
            h, a = int(h_str.strip()), int(a_str.strip())
            if not (0 <= h <= 20 and 0 <= a <= 20):
                raise ValueError
            parsed[gid] = (h, a)
        except (ValueError, AttributeError):
            pass
    if not parsed:
        st.warning("Ei tallennettavia tuloksia – syötä pisteet numeroina 0–20.")
    else:
        try:
            for gid, (home, away) in parsed.items():
                session.sql(
                    f"MERGE INTO {RESULTS_TABLE} t "
                    f"USING (SELECT {gid} AS ID, {home} AS HOME_TEAM_GOALS, {away} AS AWAY_TEAM_GOALS) s "
                    f"ON t.ID = s.ID "
                    f"WHEN MATCHED THEN UPDATE SET t.HOME_TEAM_GOALS = s.HOME_TEAM_GOALS, t.AWAY_TEAM_GOALS = s.AWAY_TEAM_GOALS "
                    f"WHEN NOT MATCHED THEN INSERT (ID, HOME_TEAM_GOALS, AWAY_TEAM_GOALS) VALUES (s.ID, s.HOME_TEAM_GOALS, s.AWAY_TEAM_GOALS)"
                ).collect()
            st.success(f"{len(parsed)} tulosta tallennettu.")
            st.rerun()
        except Exception as e:
            st.error(f"Virhe tallennuksessa: {e}")

# ── Playoff results section ───────────────────────────────────────────────────
st.divider()
st.subheader("Pudotuspelien tulokset")
st.caption(
    "Täytä bracket sitä mukaa kun otteluita pelataan. "
    "Tyhjäksi jätetyt kentät tallentuvat NULL-arvoina ja "
    "korvataan kun seuraavan kierroksen tulokset ratkeavat."
)

playoff_existing: dict = {}
try:
    pp_df = session.sql(f"SELECT * FROM {PLAYOFF_RESULTS_TABLE}").to_pandas()
    if len(pp_df) > 0:
        for k in _RESULT_COLS:
            if k not in pp_df.columns:
                continue
            v = pp_df.iloc[0][k]
            if v is not None and not (isinstance(v, float) and pd.isna(v)) and v != "":
                playoff_existing[k] = v
except Exception:
    pass


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


with st.form("playoff_results_form"):
    # ── Lohkovoittajat ja kakkoset ─────────────────────────────────────
    st.markdown("**Lohkovoittajat ja kakkoset**")
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
                key=f"res_sel_{w_key}",
            )
            r = c2.selectbox(
                "Kakkonen", options=opts,
                index=_sel_default(r_key, opts),
                key=f"res_sel_{r_key}",
            )
            group_picks[letter] = (w, r)

    st.markdown("**Parhaat kolmoset – 8 joukkuetta**")
    third_teams = st.multiselect(
        "Parhaat kolmoset", options=TEAMS,
        default=_ms_defaults("THIRD", 8), max_selections=8,
        key="ms_res_third", label_visibility="collapsed",
    )

    st.markdown("**R16-jatkajat – 16 joukkuetta**")
    r16_teams = st.multiselect(
        "R16-jatkajat", options=TEAMS,
        default=_ms_defaults("R16", 16), max_selections=16,
        key="ms_res_r16", label_visibility="collapsed",
    )

    st.markdown("**Puolivälierissä – 8 joukkuetta**")
    qf_teams = st.multiselect(
        "Puolivälierissä", options=TEAMS,
        default=_ms_defaults("QF", 8), max_selections=8,
        key="ms_res_qf", label_visibility="collapsed",
    )

    st.markdown("**Välierissä – 4 joukkuetta**")
    sf_teams = st.multiselect(
        "Välierissä", options=TEAMS,
        default=_ms_defaults("SF", 4), max_selections=4,
        key="ms_res_sf", label_visibility="collapsed",
    )

    st.markdown("**Finalistit – 2 joukkuetta**")
    f_teams = st.multiselect(
        "Finalistit", options=TEAMS,
        default=_ms_defaults("FINALIST", 2), max_selections=2,
        key="ms_res_f", label_visibility="collapsed",
    )

    st.markdown("**Mestari**")
    champ_opts = ["—"] + TEAMS
    champion = st.selectbox(
        "Mestari", options=champ_opts,
        index=_sel_default("CHAMPION", champ_opts),
        key="sel_res_champion", label_visibility="collapsed",
    )

    st.markdown("**Maalikuningas**")
    top_scorer = st.text_input(
        "Maalikuningas (pelaajan nimi)",
        value=_str_default("TOP_SCORER"),
        key="ti_res_scorer",
    )

    playoff_submit = st.form_submit_button("Tallenna pudotuspelien tulokset", type="primary")

# ── Handle playoff results submission ─────────────────────────────────────────
if playoff_submit:
    from datetime import datetime
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

    values: list[str] = []
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
    values.append(f"'{now_str}'")

    col_list = ", ".join(_RESULT_COLS) + ", UPDATED"
    val_list = ", ".join(values)

    try:
        session.sql(f"DELETE FROM {PLAYOFF_RESULTS_TABLE}").collect()
        session.sql(
            f"INSERT INTO {PLAYOFF_RESULTS_TABLE} ({col_list}) VALUES ({val_list})"
        ).collect()
        st.success("Pudotuspelien tulokset tallennettu.")
        st.rerun()
    except Exception as e:
        st.error(f"Virhe pudotuspelien tulosten tallennuksessa: {e}")
