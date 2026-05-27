import streamlit as st
import pandas as pd

# Shared connection — every query runs inside `conn.safe_session()` (thread-safe
# lock) because all viewers share one container instance. See AGENTS.md.
conn = st.session_state.snowpark_conn

SCHEMA = "FIFA_VEIKKAUS"
PREDICTIONS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PREDICTIONS"
RESULTS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_RESULTS"
PLAYOFF_PRED_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS"
PLAYOFF_RESULTS_TABLE = f"{SCHEMA}.FIFA_VEIKKAUS_PLAYOFF_RESULTS"

from schedule_data import FLAGS as _FLAGS, GROUP_LETTERS as _GROUP_LETTERS
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


from app_pages._theme import apply_theme
apply_theme()

st.title("Tilanne")


def get_players() -> list[str]:
    with conn.safe_session() as session:
        rows = session.sql(
            f"SELECT DISTINCT USER_EMAIL FROM {PREDICTIONS_TABLE} ORDER BY USER_EMAIL"
        ).collect()
    return [row["USER_EMAIL"] for row in rows]


def compute_player_points(player_email: str) -> pd.DataFrame:
    """5/3/1 scoring: 5 exact, 3 same goal-difference (incl. matching draws),
    1 correct winner/draw outcome only, 0 wrong."""
    # Drive from PREDICTIONS (LEFT JOIN RESULTS) so a player's picks render even
    # before any results are entered — RESULTS is empty until admin fills it, and
    # it has no MATCH column, so MATCH/MATCH_DAY come from the predictions row.
    # POINTS stays NULL until the matching result exists.
    sql = f"""
    SELECT
        p.ID,
        p.MATCH,
        p.MATCH_DAY,
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
    LEFT JOIN {RESULTS_TABLE} r ON p.ID = r.ID
    WHERE p.USER_EMAIL = '{player_email}'
    ORDER BY p.ID
    """
    with conn.safe_session() as session:
        return session.sql(sql).to_pandas()


def _load_playoff_results() -> dict:
    try:
        with conn.safe_session() as session:
            df = session.sql(f"SELECT * FROM {PLAYOFF_RESULTS_TABLE}").to_pandas()
        if len(df) == 0:
            return {}
        row = df.iloc[0]
        return {k: (None if pd.isna(row[k]) else row[k]) for k in row.index}
    except Exception:
        return {}


def _load_user_playoff(email: str) -> dict:
    try:
        with conn.safe_session() as session:
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

with conn.safe_session() as session:
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
_player_match_dfs: dict[str, pd.DataFrame] = {}
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
        _player_match_dfs[email_to_display_name(player_email)] = df
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

# ── Pisteet ajan myötä ───────────────────────────────────────────────────────
# Cumulative group-stage points per player over the tournament days. Bracket
# points are tournament-end-only and not folded in here — the chart shows the
# day-by-day momentum during group play.
_day_frames = []
for name, df in _player_match_dfs.items():
    if df.empty or "MATCH_DAY" not in df.columns:
        continue
    by_day = (
        df.dropna(subset=["POINTS"])
          .groupby("MATCH_DAY", as_index=True)["POINTS"]
          .sum()
          .rename(name)
    )
    if not by_day.empty:
        _day_frames.append(by_day)

if _day_frames:
    import altair as alt
    points_wide = pd.concat(_day_frames, axis=1).sort_index().fillna(0).cumsum()
    points_wide.index = pd.to_datetime(points_wide.index)
    st.divider()
    st.subheader("Pisteet ajan myötä")
    st.caption(
        "Kumulatiiviset alkulohkopisteet ottelupäivän mukaan. "
        "Bracket-pisteet lisätään turnauksen päätteeksi."
    )
    chart_df = (
        points_wide.reset_index()
        .rename(columns={"index": "Päivä", "MATCH_DAY": "Päivä"})
        .melt(id_vars="Päivä", var_name="Pelaaja", value_name="Pisteet")
    )
    # 90s-arcade palette — saturated neon over a transparent panel.
    _PALETTE = ["#ff7e1c", "#5fc879", "#4a9eff", "#ffd95c", "#ff5cb8", "#a259ff", "#fff5d0"]
    base = alt.Chart(chart_df).encode(
        x=alt.X(
            "Päivä:T",
            title=None,
            axis=alt.Axis(
                format="%d.%m",
                labelColor="#f5e8c8",
                labelFontSize=12,
                labelFont="VT323",
                tickColor="#f5c842",
                domainColor="#f5c842",
                grid=False,
            ),
        ),
        y=alt.Y(
            "Pisteet:Q",
            title=None,
            axis=alt.Axis(
                labelColor="#f5e8c8",
                labelFontSize=12,
                labelFont="VT323",
                tickColor="#f5c842",
                domainColor="#f5c842",
                gridColor="rgba(245, 200, 80, 0.12)",
                gridDash=[2, 4],
            ),
        ),
        color=alt.Color(
            "Pelaaja:N",
            scale=alt.Scale(range=_PALETTE),
            legend=alt.Legend(
                orient="bottom",
                labelColor="#f5e8c8",
                labelFont="Bungee",
                labelFontSize=11,
                titleColor="#ffd95c",
                title=None,
                symbolType="square",
                symbolSize=140,
            ),
        ),
    )
    chart = (
        (base.mark_line(strokeWidth=3, interpolate="step-after")
            + base.mark_point(size=70, filled=True, opacity=0.95))
        .properties(height=340, background="transparent")
        .configure_view(fill=None, stroke="#f5c842", strokeWidth=2)
        .configure(background="transparent")
    )
    # Wrap the chart in a panel that matches the prediction-page scoreboard look.
    st.markdown(
        """
        <style>
        .stMainBlockContainer div[data-testid="stVegaLiteChart"] {
            background: linear-gradient(180deg, rgba(10, 31, 18, 0.85), rgba(6, 19, 8, 0.85));
            border: 2px solid #f5c842;
            box-shadow: 4px 4px 0 #000, inset 0 0 0 1px rgba(0,0,0,0.7),
                        inset 0 2px 0 rgba(255,230,180,0.18);
            padding: 6px;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(
        "💡 Klikkaa kuvaajan oikeasta yläkulmasta laajenna-kuvaketta nähdäksesi "
        "kuvaajan koko ruudulla — paremmin luettavissa kun pelaajia on paljon."
    )

# ── Pelaajan veikkaukset ─────────────────────────────────────────────────────
# Single-player view — with 20+ users the all-columns table doesn't fit.
st.divider()
st.subheader("Pelaajan veikkaukset")
st.caption("Valitse pelaaja nähdäksesi kaikki hänen ottelukohtaiset veikkauksensa. "
           "Värikoodi: vihreä = 5 p (täysosuma), sininen = 3 p, keltainen = 1 p, punainen = 0 p.")

_indexed_dfs = {
    name: df.set_index("ID")
    for name, df in _player_match_dfs.items()
    if df is not None and not df.empty
}
if _indexed_dfs:
    _all_names = sorted(_indexed_dfs.keys())

    # Default to the current user if present, otherwise the first player.
    _me_display = email_to_display_name(current_user) if current_user else ""
    _default_idx = _all_names.index(_me_display) if _me_display in _all_names else 0

    _selected = st.selectbox(
        "Pelaaja",
        options=_all_names,
        index=_default_idx,
        key="preds_filter",
    )
    _names = [_selected]

    _base_name = _all_names[0]
    _schedule_df = _indexed_dfs[_base_name].reset_index().sort_values(["MATCH_DAY", "ID"])

    st.markdown(
        """
        <style>
        table.all-preds {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Roboto', Arial, sans-serif;
            font-size: 0.82rem;
            color: #f5e8c8;
            background: rgba(6, 19, 8, 0.65);
        }
        table.all-preds th {
            background: linear-gradient(180deg, #ffd95c, #b8862a);
            color: #1a1408;
            font-family: 'Bungee', 'Impact', sans-serif;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 7px 10px;
            border: 1px solid #0a0a0a;
            position: sticky;
            top: 0;
            text-align: left;
        }
        table.all-preds th.center { text-align: center; }
        table.all-preds tbody tr.alt td { background-color: rgba(245, 200, 80, 0.04); }
        table.all-preds tbody tr.day-start td {
            border-top: 2px solid rgba(245, 200, 80, 0.55);
        }
        table.all-preds td {
            padding: 6px 10px;
            border-bottom: 1px solid rgba(245, 200, 80, 0.10);
            vertical-align: middle;
            font-variant-numeric: tabular-nums;
        }
        table.all-preds td.num {
            color: #aa9466;
            font-family: 'VT323', monospace;
            font-size: 0.95rem;
            text-align: right;
            width: 36px;
        }
        table.all-preds td.day {
            font-family: 'VT323', monospace;
            color: #d4b878;
            font-size: 1.0rem;
            white-space: nowrap;
            width: 200px;
        }
        table.all-preds td.day.empty-day { color: transparent; }
        table.all-preds td.match { font-weight: 500; white-space: nowrap; min-width: 240px; }
        table.all-preds td.result {
            font-family: 'VT323', monospace;
            font-size: 1.15rem;
            color: #ff7e1c;
            text-shadow: 0 0 4px #ff7e1c;
            text-align: center;
            background: #050505 !important;
            min-width: 64px;
            width: 64px;
        }
        table.all-preds td.result.pending { color: #553a18; text-shadow: none; }
        table.all-preds td.pred {
            text-align: center;
            font-weight: 600;
            min-width: 78px;
        }
        table.all-preds td.pred .pts {
            display: inline-block;
            font-size: 0.7rem;
            opacity: 0.85;
            margin-left: 4px;
        }
        table.all-preds td.p5 { background-color: rgba(40,160,80,0.55) !important; color: #fff; font-weight: 700; }
        table.all-preds td.p3 { background-color: rgba(80,140,200,0.55) !important; color: #fff; }
        table.all-preds td.p1 { background-color: rgba(200,160,40,0.55) !important; color: #1a1408; }
        table.all-preds td.p0 { background-color: rgba(170,50,50,0.55) !important; color: #fff; }
        table.all-preds td.empty { color: #5a4a30; text-align: center; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _html: list[str] = [
        "<div style='overflow-x:auto;border:2px solid #f5c842;box-shadow:4px 4px 0 #000;'>",
        "<table class='all-preds'><thead><tr>",
        "<th>#</th><th>Pvm</th><th>Ottelu</th><th class='center'>Tulos</th>",
    ]
    for n in _names:
        _html.append(f"<th class='center'>{n}</th>")
    _html.append("</tr></thead><tbody>")

    prev_day = None
    for i, (_, row) in enumerate(_schedule_df.iterrows(), start=1):
        mid = int(row["ID"])
        day_changed = row["MATCH_DAY"] != prev_day
        d_label = _fi_date(row["MATCH_DAY"]) if day_changed else ""
        day_cls = "day" if day_changed else "day empty-day"
        prev_day = row["MATCH_DAY"]

        row_classes = []
        if day_changed: row_classes.append("day-start")
        if i % 2 == 0:  row_classes.append("alt")
        row_cls = f" class='{' '.join(row_classes)}'" if row_classes else ""

        match_str = flagged(row["MATCH"])
        rh, ra = row["RESULT_HOME"], row["RESULT_AWAY"]
        if not pd.isna(rh) and not pd.isna(ra):
            res_cell = f"<td class='result'>{int(rh)}–{int(ra)}</td>"
        else:
            res_cell = "<td class='result pending'>—</td>"

        _html.append(
            f"<tr{row_cls}>"
            f"<td class='num'>{i}</td>"
            f"<td class='{day_cls}'>{d_label or '·'}</td>"
            f"<td class='match'>{match_str}</td>"
            f"{res_cell}"
        )
        for n in _names:
            df = _indexed_dfs[n]
            if mid not in df.index:
                _html.append("<td class='empty'>—</td>")
                continue
            prow = df.loc[mid]
            ph, pa, pts = prow["PRED_HOME"], prow["PRED_AWAY"], prow["POINTS"]
            if pd.isna(ph) or pd.isna(pa):
                _html.append("<td class='empty'>—</td>")
                continue
            pred = f"{int(ph)}–{int(pa)}"
            cls = ""
            pts_html = ""
            if not pd.isna(pts):
                pts_int = int(pts)
                cls = f"p{pts_int}"
                pts_html = f"<span class='pts'>{pts_int}p</span>"
            _html.append(f"<td class='pred {cls}'>{pred}{pts_html}</td>")
        _html.append("</tr>")
    _html.append("</tbody></table></div>")
    st.markdown("".join(_html), unsafe_allow_html=True)
else:
    st.info("Veikkauksia ei vielä saatavilla.")
