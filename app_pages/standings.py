import base64
import os
import streamlit as st
import pandas as pd

session = st.session_state.snowpark_session

SCHEMA = "FIFA_VEIKKAUS"
PREDICTIONS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PREDICTIONS"
RESULTS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_RESULTS"
PLAYOFF_PRED_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS"
PLAYOFF_RESULTS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PLAYOFF_RESULTS"

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

_GROUP_LETTERS = list("ABCDEFGHIJKL")
_GROUP_POS_COLS = (
    [f"GROUP_{L}_WINNER"   for L in _GROUP_LETTERS] +
    [f"GROUP_{L}_RUNNERUP" for L in _GROUP_LETTERS]
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


def email_to_display_name(email: str) -> str:
    local = email.split("@")[0]
    parts = local.replace(".", " ").split()
    return " ".join(p.capitalize() for p in parts)


# ── Background image ──────────────────────────────────────────────────────────
_img_path = os.path.join(os.path.dirname(__file__), "..", "assets", "maradona.gif")
if os.path.exists(_img_path):
    _b64 = base64.b64encode(open(_img_path, "rb").read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/gif;base64,{_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(20, 14, 8, 0.72);
            pointer-events: none;
            z-index: 0;
        }}
        div[data-baseweb="select"] span {{
            color: #ffffff !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("Tilanne")


def get_players() -> list[str]:
    rows = session.sql(
        f"SELECT DISTINCT USER_EMAIL FROM {PREDICTIONS_TABLE} ORDER BY USER_EMAIL"
    ).collect()
    return [row["USER_EMAIL"] for row in rows]


def compute_player_points(player_email: str) -> pd.DataFrame:
    """5/3/1 scoring: 5 exact, 3 same goal-difference (incl. matching draws),
    1 correct winner/draw outcome only, 0 wrong."""
    sql = f"""
    SELECT
        r.ID,
        r.MATCH,
        r.HOME_TEAM_GOALS AS RESULT_HOME,
        r.AWAY_TEAM_GOALS AS RESULT_AWAY,
        p.HOME_TEAM_GOALS AS PRED_HOME,
        p.AWAY_TEAM_GOALS AS PRED_AWAY,
        CASE
            WHEN r.HOME_TEAM_GOALS IS NULL OR p.HOME_TEAM_GOALS IS NULL THEN NULL
            WHEN p.HOME_TEAM_GOALS = r.HOME_TEAM_GOALS
                 AND p.AWAY_TEAM_GOALS = r.AWAY_TEAM_GOALS THEN 5
            WHEN (p.HOME_TEAM_GOALS - p.AWAY_TEAM_GOALS)
                 = (r.HOME_TEAM_GOALS - r.AWAY_TEAM_GOALS) THEN 3
            WHEN (p.HOME_TEAM_GOALS > p.AWAY_TEAM_GOALS
                  AND r.HOME_TEAM_GOALS > r.AWAY_TEAM_GOALS)
              OR (p.HOME_TEAM_GOALS < p.AWAY_TEAM_GOALS
                  AND r.HOME_TEAM_GOALS < r.AWAY_TEAM_GOALS)
              OR (p.HOME_TEAM_GOALS = p.AWAY_TEAM_GOALS
                  AND r.HOME_TEAM_GOALS = r.AWAY_TEAM_GOALS) THEN 1
            ELSE 0
        END AS POINTS
    FROM {PREDICTIONS_TABLE} p
    INNER JOIN {RESULTS_TABLE} r ON p.ID = r.ID
    WHERE p.USER_EMAIL = '{player_email}'
      AND r.MATCH IS NOT NULL
    ORDER BY r.ID
    """
    return session.sql(sql).to_pandas()


def _load_playoff_results() -> dict:
    try:
        df = session.sql(f"SELECT * FROM {PLAYOFF_RESULTS_TABLE}").to_pandas()
        if len(df) == 0:
            return {}
        row = df.iloc[0]
        return {k: (None if pd.isna(row[k]) else row[k]) for k in row.index}
    except Exception:
        return {}


def _load_user_playoff(email: str) -> dict:
    try:
        df = session.sql(
            f"SELECT * FROM {PLAYOFF_PRED_TABLE} WHERE USER_EMAIL = '{email}'"
        ).to_pandas()
        if len(df) == 0:
            return {}
        row = df.iloc[0]
        return {k: (None if pd.isna(row[k]) else row[k]) for k in row.index}
    except Exception:
        return {}


def _clean(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def compute_bracket_points(user_pred: dict, results: dict) -> int:
    if not results or not user_pred:
        return 0
    total = 0

    # Group winners + runners-up: 3 pts each
    for col in _GROUP_POS_COLS:
        u, r = _clean(user_pred.get(col)), _clean(results.get(col))
        if u and r and u == r:
            total += 3

    def _set(prefix: str, n: int, src: dict) -> set[str]:
        s = set()
        for i in range(1, n + 1):
            v = _clean(src.get(f"{prefix}_{i}"))
            if v:
                s.add(v)
        return s

    # Third placed: 1 pt each
    total += 1 * len(_set("THIRD", 8, user_pred) & _set("THIRD", 8, results))
    # R16: 2 pts each
    total += 2 * len(_set("R16", 16, user_pred) & _set("R16", 16, results))
    # QF: 3 pts each
    real_qf = _set("QF", 8, results)
    total += 3 * len(_set("QF", 8, user_pred) & real_qf)
    # SF: 5 pts each
    total += 5 * len(_set("SF", 4, user_pred) & _set("SF", 4, results))
    # Finalists: +10 each (on top of SF)
    total += 10 * len(_set("FINALIST", 2, user_pred) & _set("FINALIST", 2, results))
    # Champion: +20
    u_ch, r_ch = _clean(user_pred.get("CHAMPION")), _clean(results.get("CHAMPION"))
    if u_ch and r_ch and u_ch == r_ch:
        total += 20
    # Top scorer: 15 (case-insensitive)
    u_ts = _clean(user_pred.get("TOP_SCORER")).lower()
    r_ts = _clean(results.get("TOP_SCORER")).lower()
    if u_ts and u_ts == r_ts:
        total += 15
    # Dark horse: 15 if pick reaches QF
    dh = _clean(user_pred.get("DARK_HORSE"))
    if dh and dh in real_qf:
        total += 15

    return total


players = get_players()

if not players:
    st.info("Ei veikkauksia vielä.")
    st.stop()

scored_count = session.sql(
    f"SELECT COUNT(*) AS N FROM {RESULTS_TABLE} WHERE HOME_TEAM_GOALS IS NOT NULL"
).collect()[0]["N"]
total_games = session.sql(
    f"SELECT COUNT(*) AS N FROM {SCHEMA}.FIFA_VEIKKAUS_SCHEDULE"
).collect()[0]["N"]
st.caption(f"Otteluja tuloksilla: **{scored_count} / {total_games}**")

# ── Pistetaulukko ─────────────────────────────────────────────────────────────
st.subheader("Pistetaulukko")
st.caption(
    "Sija lasketaan ottelukohtaisista pisteistä (5 = täysosuma, 3 = sama maaliero, "
    "1 = oikea voittaja) plus bracket-pisteistä."
)

current_user = st.session_state.get("user_email", "")
playoff_results = _load_playoff_results()

leaderboard_rows = []
for player_email in players:
    try:
        df = compute_player_points(player_email)
        group_pts = int(df["POINTS"].dropna().sum())
        bracket_pts = compute_bracket_points(_load_user_playoff(player_email), playoff_results)
        leaderboard_rows.append({
            "email": player_email,
            "name": email_to_display_name(player_email),
            "group_pts": group_pts,
            "bracket_pts": bracket_pts,
            "points": group_pts + bracket_pts,
        })
    except Exception:
        pass

if leaderboard_rows:
    leaderboard_rows.sort(key=lambda r: r["points"], reverse=True)
    rank_html_parts = []
    for i, row in enumerate(leaderboard_rows, start=1):
        is_me = row["email"] == current_user
        bg = "rgba(160, 110, 30, 0.92)" if is_me else "rgba(80, 55, 15, 0.85)"
        marker = " <span style='color:#f5c842;font-size:0.78rem;'>(sinä)</span>" if is_me else ""
        breakdown = ""
        if row["bracket_pts"]:
            breakdown = (
                f"<span style='color:#d4b878;font-size:0.75rem;margin-right:0.6rem;'>"
                f"alkulohko {row['group_pts']} + bracket {row['bracket_pts']}</span>"
            )
        rank_html_parts.append(
            f"<div style=\"display:flex;align-items:center;justify-content:space-between;"
            f"padding:8px 14px;margin-bottom:4px;background:{bg};"
            f"box-shadow:inset -1px -1px rgba(0,0,0,0.85),inset 1px 1px rgba(170,200,255,0.55),"
            f"inset -2px -2px rgba(0,0,20,0.55),inset 2px 2px rgba(140,175,255,0.28);"
            f"color:#f5e8c8;font-family:'Roboto',Arial,sans-serif;\">"
            f"<span><span style='display:inline-block;width:2.2rem;color:#f5c842;font-weight:700;'>"
            f"{i}.</span>{row['name']}{marker}</span>"
            f"<span>{breakdown}"
            f"<span style='font-weight:700;font-variant-numeric:tabular-nums;'>{row['points']} p</span>"
            f"</span></div>"
        )
    st.markdown("".join(rank_html_parts), unsafe_allow_html=True)
else:
    st.info("Tuloksia ei vielä saatavilla.")

# ── Ottelutiedot ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("Ottelutiedot")
st.caption("Valitse pelaaja nähdäksesi hänen veikkauksensa ottelukohtaisesti.")

player_display_names = [email_to_display_name(e) for e in players]
email_by_display = dict(zip(player_display_names, players))

default_idx = 0
if current_user:
    me_display = email_to_display_name(current_user)
    if me_display in player_display_names:
        default_idx = player_display_names.index(me_display)

selected_display = st.selectbox(
    "Pelaaja",
    options=player_display_names,
    index=default_idx,
    label_visibility="collapsed",
)

if selected_display:
    player_email = email_by_display[selected_display]
    try:
        detail_df = compute_player_points(player_email)
    except Exception as e:
        st.error(f"Tietojen lataus epäonnistui ({selected_display}): {e}")
        detail_df = None

    if detail_df is not None and len(detail_df) > 0:
        sched_df = session.sql(
            f"SELECT ID, MATCH_DAY FROM {SCHEMA}.FIFA_VEIKKAUS_SCHEDULE ORDER BY ID"
        ).to_pandas()[["ID", "MATCH_DAY"]]
        merged = detail_df.merge(sched_df, on="ID", how="left")
        merged = merged.sort_values("ID")

        total_pts = int(merged["POINTS"].dropna().sum())
        st.caption(f"**{selected_display}** – alkulohko **{total_pts}** pistettä.")

        dates = sorted(merged["MATCH_DAY"].dropna().unique())
        for d in dates:
            day_rows = merged[merged["MATCH_DAY"] == d]
            day_pts = int(day_rows["POINTS"].dropna().sum())
            scored = int(day_rows["POINTS"].notna().sum())
            total = len(day_rows)
            date_label = _fi_date(d)
            label = f"{date_label} — {scored}/{total} ottelua tuloksella · {day_pts} p"
            with st.expander(label, expanded=False):
                hdr1, hdr2, hdr3, hdr4 = st.columns([5, 2, 2, 1])
                hdr2.caption("Veikkaus")
                hdr3.caption("Tulos")
                hdr4.caption("Pisteet")
                for _, row in day_rows.iterrows():
                    c1, c2, c3, c4 = st.columns([5, 2, 2, 1])
                    c1.write(flagged(row["MATCH"]))

                    ph, pa = row["PRED_HOME"], row["PRED_AWAY"]
                    pred_str = (
                        f"{int(ph)} – {int(pa)}"
                        if not pd.isna(ph) and not pd.isna(pa)
                        else "–"
                    )
                    c2.write(pred_str)

                    rh, ra = row["RESULT_HOME"], row["RESULT_AWAY"]
                    if not pd.isna(rh) and not pd.isna(ra):
                        c3.write(f"{int(rh)} – {int(ra)}")
                    else:
                        c3.write("—")

                    pts = row["POINTS"]
                    if pd.isna(pts):
                        badge = "<span style='color:#aa9466;'>—</span>"
                    else:
                        pts_int = int(pts)
                        if pts_int == 5:
                            bg = "rgba(40,160,80,0.85)"; fg = "#f5e8c8"
                        elif pts_int == 3:
                            bg = "rgba(80,140,200,0.85)"; fg = "#f5e8c8"
                        elif pts_int == 1:
                            bg = "rgba(200,160,40,0.85)"; fg = "#1a1408"
                        else:
                            bg = "rgba(120,40,40,0.75)"; fg = "#f5e8c8"
                        badge = (
                            f"<span style='background:{bg};color:{fg};"
                            f"padding:2px 8px;font-weight:700;'>{pts_int}</span>"
                        )
                    c4.markdown(badge, unsafe_allow_html=True)
    elif detail_df is not None:
        st.info("Pelaajalla ei ole vielä veikkauksia tuloksellisiin otteluihin.")
