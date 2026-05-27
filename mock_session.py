"""
Mock Snowpark session for local development without a Snowflake connection.
Schedule + groups load from ``schedule_data`` (single source of truth backed
by ``data/schedule_2026.json``); this module adds in-memory predictions and
results storage on top so all UI features can be exercised locally.
"""
import pandas as pd
from contextlib import contextmanager
from typing import Optional

from schedule_data import GROUPS, TEAMS as ALL_TEAMS, SCHEDULE_MATCHES


# ── Schedule: 72 real group-stage games (Jun 11–27, 2026) ─────────────────────
SCHEDULE_DF = pd.DataFrame([
    {**m, "HOME_TEAM_GOALS": None, "AWAY_TEAM_GOALS": None}
    for m in SCHEDULE_MATCHES
])

# Results for the first ~8 match days so the standings line chart has shape.
def _seed_results() -> dict[int, tuple[int, int]]:
    import random
    rng = random.Random(2026)
    out = {}
    for i in range(1, 36):  # ~half the group stage
        # Reasonable football scorelines: most teams score 0-3.
        h, a = rng.randint(0, 3), rng.randint(0, 3)
        out[i] = (h, a)
    return out

_RESULTS = _seed_results()

RESULTS_DF = SCHEDULE_DF[["ID"]].copy()
RESULTS_DF["HOME_TEAM_GOALS"] = RESULTS_DF["ID"].map(lambda i: _RESULTS.get(i, (None, None))[0])
RESULTS_DF["AWAY_TEAM_GOALS"] = RESULTS_DF["ID"].map(lambda i: _RESULTS.get(i, (None, None))[1])
RESULTS_DF["MATCH"] = SCHEDULE_DF["MATCH"]


# ── Playoff predictions table ────────────────────────────────────────────────
#
# Per user (single row): group winners + runners-up, 8 best third-placed,
# 16 R16 advancers, 8 QF, 4 SF, 2 finalists, champion, top scorer, dark horse.

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
# Predictions include user-only fields (DARK_HORSE); results omit them.
_PREDICTION_BRACKET_COLS = (
    _GROUP_POS_COLS + _THIRD_COLS + _R16_COLS + _QF_COLS + _SF_COLS +
    _FINALIST_COLS + ["CHAMPION", "TOP_SCORER", "DARK_HORSE"]
)
_RESULT_BRACKET_COLS = (
    _GROUP_POS_COLS + _THIRD_COLS + _R16_COLS + _QF_COLS + _SF_COLS +
    _FINALIST_COLS + ["CHAMPION", "TOP_SCORER"]
)

_PLAYOFF_DF = pd.DataFrame(columns=["USER_EMAIL"] + _PREDICTION_BRACKET_COLS + ["INSERTED"])
_PLAYOFF_RESULTS_DF = pd.DataFrame(columns=_RESULT_BRACKET_COLS + ["UPDATED"])


# ── Seed: "Germany wins it all" sample prediction ────────────────────────────
# Pre-populates the current mock user's bracket so the predictions page loads
# with a full R32 pool and Saksa advancing through R16 → QF → SF → Final → 🏆.

_DEMO_GROUP_W = {
    "A": "Meksiko",   "B": "Kanada",    "C": "Brasilia",   "D": "Yhdysvallat",
    "E": "Saksa",     "F": "Alankomaat","G": "Belgia",     "H": "Espanja",
    "I": "Ranska",    "J": "Argentiina","K": "Portugali",  "L": "Englanti",
}
_DEMO_GROUP_R = {
    "A": "Etelä-Korea",       "B": "Sveitsi",         "C": "Marokko",        "D": "Paraguay",
    "E": "Norsunluurannikko", "F": "Japani",          "G": "Egypti",         "H": "Uruguay",
    "I": "Senegal",           "J": "Itävalta",        "K": "Uzbekistan",     "L": "Kroatia",
}
_DEMO_THIRDS = [
    "Tšekki", "Bosnia", "Skotlanti", "Australia",
    "Ecuador", "Ruotsi", "Norja", "Kolumbia",
]
# Bracket advancers — Saksa shows up in every round.
_DEMO_R16 = [
    "Saksa", "Brasilia", "Argentiina", "Ranska", "Espanja", "Portugali",
    "Alankomaat", "Englanti", "Belgia", "Meksiko", "Kanada", "Marokko",
    "Kroatia", "Etelä-Korea", "Uruguay", "Senegal",
]
_DEMO_QF        = ["Saksa", "Brasilia", "Argentiina", "Ranska", "Espanja", "Portugali", "Englanti", "Belgia"]
_DEMO_SF        = ["Saksa", "Brasilia", "Ranska", "Argentiina"]
_DEMO_FINALISTS = ["Saksa", "Brasilia"]
_DEMO_CHAMPION  = "Saksa"

def _build_demo_playoff_row(email: str) -> dict:
    row = {"USER_EMAIL": email}
    for L in _GROUP_LETTERS:
        row[f"GROUP_{L}_WINNER"]   = _DEMO_GROUP_W[L]
        row[f"GROUP_{L}_RUNNERUP"] = _DEMO_GROUP_R[L]
    for i, t in enumerate(_DEMO_THIRDS,    1): row[f"THIRD_{i}"]    = t
    for i, t in enumerate(_DEMO_R16,       1): row[f"R16_{i}"]      = t
    for i, t in enumerate(_DEMO_QF,        1): row[f"QF_{i}"]       = t
    for i, t in enumerate(_DEMO_SF,        1): row[f"SF_{i}"]       = t
    for i, t in enumerate(_DEMO_FINALISTS, 1): row[f"FINALIST_{i}"] = t
    row["CHAMPION"]   = _DEMO_CHAMPION
    row["TOP_SCORER"] = "Florian Wirtz"
    row["DARK_HORSE"] = "Marokko"
    row["INSERTED"]   = "2026-05-23 22:00:00"
    return row


# ── Shared predictions table ─────────────────────────────────────────────────

MOCK_CURRENT_USER = "mika.heino@recordlydata.com"

# Seed the demo playoff row for the current mock user so the bracket loads
# fully populated.
_PLAYOFF_DF = pd.DataFrame([_build_demo_playoff_row(MOCK_CURRENT_USER)])

def _make_predictions(email: str, seed: int, complete_days: Optional[int] = None) -> pd.DataFrame:
    import random
    rng = random.Random(seed)
    dates = sorted(SCHEDULE_DF["MATCH_DAY"].unique())
    done_dates = set(dates[:complete_days]) if complete_days else set(dates)
    rows = []
    for _, row in SCHEDULE_DF.iterrows():
        filled = row["MATCH_DAY"] in done_dates
        rows.append({
            "USER_EMAIL": email,
            "ID": row["ID"],
            "MATCH_DAY": row["MATCH_DAY"],
            "MATCH": row["MATCH"],
            "HOME_TEAM_GOALS": rng.randint(0, 4) if filled else None,
            "AWAY_TEAM_GOALS": rng.randint(0, 4) if filled else None,
            "INSERTED": "2026-05-20 10:00:00",
        })
    return pd.DataFrame(rows)

_PREDICTIONS_DF = pd.concat([
    _make_predictions("matti.test@recordlydata.com", 42),
    _make_predictions("liisa.test@recordlydata.com", 7),
    _make_predictions("pekka.test@recordlydata.com", 99),
    _make_predictions(MOCK_CURRENT_USER, 1337),
], ignore_index=True)


# ── Mock row / result helpers ─────────────────────────────────────────────────

class _MockRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

class _MockResult:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def to_pandas(self) -> pd.DataFrame:
        return self._df.copy()

    def collect(self) -> "list[_MockRow]":
        return [_MockRow(r) for r in self._df.to_dict(orient="records")]


# ── Mock session ──────────────────────────────────────────────────────────────

class MockSession:
    """Mimics the subset of Snowpark Session API used by the app.

    Doubles as a stand-in for ``st.connection("snowflake")``: ``safe_session()``
    yields the mock itself, mirroring SnowflakeConnection's thread-safe context
    manager so page code can use the same ``with conn.safe_session()`` pattern
    locally and in production.
    """

    @contextmanager
    def safe_session(self):
        yield self

    def sql(self, query: str) -> _MockResult:
        global _PREDICTIONS_DF, _PLAYOFF_DF, _PLAYOFF_RESULTS_DF
        q = query.upper()

        # Activity-log INSERT used by streamlit_app.py for the auto-suspend
        # Task in production. Must be checked before CURRENT_USER because the
        # INSERT statement itself contains CURRENT_USER().
        if "FIFA_VEIKKAUS_ACTIVITY" in q:
            return _MockResult(pd.DataFrame({"rows_inserted": [0]}))

        if "CURRENT_USER" in q:
            return _MockResult(pd.DataFrame({"CURRENT_USER()": [MOCK_CURRENT_USER]}))

        if "SHOW TABLES" in q:
            table_names = [
                "FIFA_VEIKKAUS_RESULTS",
                "FIFA_VEIKKAUS_SCHEDULE",
                "FIFA_VEIKKAUS_PREDICTIONS",
                "FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS",
                "FIFA_VEIKKAUS_PLAYOFF_RESULTS",
            ]
            if "LIKE '" in query:
                like_val = query.split("LIKE '")[1].split("'")[0]
                like_val = like_val.replace("%", "").upper()
                table_names = [n for n in table_names if like_val in n.upper()]
            return _MockResult(pd.DataFrame({"name": table_names}))

        # ── Playoff results ─────────────────────────────────────────────
        if "DELETE" in q and "PLAYOFF_RESULTS" in q:
            _PLAYOFF_RESULTS_DF = _PLAYOFF_RESULTS_DF.iloc[0:0].copy()
            return _MockResult(pd.DataFrame({"rows_deleted": [0]}))

        if "INSERT" in q and "PLAYOFF_RESULTS" in q:
            import re
            cols_str = query.split("(", 1)[1].split(")", 1)[0]
            cols = [c.strip() for c in cols_str.split(",")]
            values_str = query.split("VALUES", 1)[1]
            tuples = re.findall(r"\(([^)]+)\)", values_str)
            new_rows = []
            for t in tuples:
                parts = [p.strip().strip("'") for p in t.split(",")]
                row_dict = {}
                for idx, col in enumerate(cols):
                    row_dict[col] = None if parts[idx].upper() == "NULL" else parts[idx]
                new_rows.append(row_dict)
            _PLAYOFF_RESULTS_DF = pd.concat(
                [_PLAYOFF_RESULTS_DF, pd.DataFrame(new_rows)], ignore_index=True
            )
            return _MockResult(pd.DataFrame({"rows_inserted": [len(new_rows)]}))

        if "PLAYOFF_RESULTS" in q:
            return _MockResult(_PLAYOFF_RESULTS_DF.copy())

        # ── Playoff predictions ─────────────────────────────────────────
        if "DELETE" in q and "PLAYOFF_PREDICTIONS" in q:
            email = query.split("'")[1].lower()
            _PLAYOFF_DF = _PLAYOFF_DF[_PLAYOFF_DF["USER_EMAIL"] != email].reset_index(drop=True)
            return _MockResult(pd.DataFrame({"rows_deleted": [0]}))

        if "INSERT" in q and "PLAYOFF_PREDICTIONS" in q:
            import re
            cols_str = query.split("(")[1].split(")")[0]
            cols = [c.strip() for c in cols_str.split(",")]
            values_str = query.split("VALUES")[1]
            tuples = re.findall(r"\(([^)]+)\)", values_str)
            new_rows = []
            for t in tuples:
                parts = [p.strip().strip("'") for p in t.split(",")]
                row_dict = {}
                for idx, col in enumerate(cols):
                    row_dict[col] = None if parts[idx].upper() == "NULL" else parts[idx]
                new_rows.append(row_dict)
            _PLAYOFF_DF = pd.concat(
                [_PLAYOFF_DF, pd.DataFrame(new_rows)], ignore_index=True
            )
            return _MockResult(pd.DataFrame({"rows_inserted": [len(new_rows)]}))

        if "PLAYOFF_PREDICTIONS" in q:
            email = query.split("'")[1].lower() if "'" in query else MOCK_CURRENT_USER
            filtered = _PLAYOFF_DF[_PLAYOFF_DF["USER_EMAIL"] == email]
            return _MockResult(filtered.copy())

        # ── Group-stage predictions ─────────────────────────────────────
        if "DELETE" in q and "FIFA_VEIKKAUS_PREDICTIONS" in q:
            email = query.split("'")[1].lower()
            _PREDICTIONS_DF = _PREDICTIONS_DF[
                _PREDICTIONS_DF["USER_EMAIL"] != email
            ].reset_index(drop=True)
            return _MockResult(pd.DataFrame({"rows_deleted": [0]}))

        if "INSERT" in q and "FIFA_VEIKKAUS_PREDICTIONS" in q:
            values_str = query.split("VALUES")[1]
            import re
            tuples = re.findall(r"\(([^)]+)\)", values_str)
            new_rows = []
            for t in tuples:
                parts = [p.strip().strip("'") for p in t.split(",")]
                new_rows.append({
                    "USER_EMAIL": parts[0],
                    "ID": int(parts[1]),
                    "MATCH_DAY": parts[2],
                    "MATCH": parts[3],
                    "HOME_TEAM_GOALS": None if parts[4].upper() == "NULL" else int(parts[4]),
                    "AWAY_TEAM_GOALS": None if parts[5].upper() == "NULL" else int(parts[5]),
                    "INSERTED": parts[6],
                })
            _PREDICTIONS_DF = pd.concat(
                [_PREDICTIONS_DF, pd.DataFrame(new_rows)], ignore_index=True
            )
            return _MockResult(pd.DataFrame({"rows_inserted": [len(new_rows)]}))

        if "DISTINCT" in q and "USER_EMAIL" in q:
            emails = sorted(_PREDICTIONS_DF["USER_EMAIL"].unique())
            return _MockResult(pd.DataFrame({"USER_EMAIL": emails}))

        if "COUNT" in q and "FIFA_VEIKKAUS_RESULTS" in q:
            n = int(RESULTS_DF["HOME_TEAM_GOALS"].notna().sum())
            return _MockResult(pd.DataFrame({"N": [n]}))

        if "COUNT" in q and "FIFA_VEIKKAUS_SCHEDULE" in q:
            return _MockResult(pd.DataFrame({"N": [len(SCHEDULE_DF)]}))

        # Schedule LEFT JOIN Results (admin page)
        if "FIFA_VEIKKAUS_SCHEDULE" in q and "FIFA_VEIKKAUS_RESULTS" in q:
            df = SCHEDULE_DF[["ID", "MATCH_DAY", "MATCH"]].merge(
                RESULTS_DF[["ID", "HOME_TEAM_GOALS", "AWAY_TEAM_GOALS"]],
                on="ID", how="left",
            )
            return _MockResult(df)

        if "FIFA_VEIKKAUS_SCHEDULE" in q:
            return _MockResult(SCHEDULE_DF[["ID", "MATCH_DAY", "MATCH"]].copy())

        # Player points JOIN (5/3/1 scoring)
        if "FIFA_VEIKKAUS_PREDICTIONS" in q and "FIFA_VEIKKAUS_RESULTS" in q:
            email = query.split("'")[1].lower() if "'" in query else MOCK_CURRENT_USER
            player_preds = _PREDICTIONS_DF[
                _PREDICTIONS_DF["USER_EMAIL"] == email
            ][["ID", "MATCH_DAY", "HOME_TEAM_GOALS", "AWAY_TEAM_GOALS"]]

            merged = player_preds.merge(
                RESULTS_DF[["ID", "MATCH", "HOME_TEAM_GOALS", "AWAY_TEAM_GOALS"]],
                on="ID", suffixes=("_PRED", "_RESULT"),
            )

            def _pts(row):
                rh, ra = row["HOME_TEAM_GOALS_RESULT"], row["AWAY_TEAM_GOALS_RESULT"]
                ph, pa = row["HOME_TEAM_GOALS_PRED"],   row["AWAY_TEAM_GOALS_PRED"]
                if pd.isna(rh) or pd.isna(ph):
                    return None
                if ph == rh and pa == ra:
                    return 5
                if (ph - pa) == (rh - ra):
                    return 3
                if (ph > pa and rh > ra) or (ph < pa and rh < ra) or (ph == pa and rh == ra):
                    return 1
                return 0

            merged["POINTS"] = merged.apply(_pts, axis=1)
            result = merged.rename(columns={
                "HOME_TEAM_GOALS_RESULT": "RESULT_HOME",
                "AWAY_TEAM_GOALS_RESULT": "RESULT_AWAY",
                "HOME_TEAM_GOALS_PRED":   "PRED_HOME",
                "AWAY_TEAM_GOALS_PRED":   "PRED_AWAY",
            })[["ID", "MATCH", "MATCH_DAY", "RESULT_HOME", "RESULT_AWAY", "PRED_HOME", "PRED_AWAY", "POINTS"]]
            return _MockResult(result)

        if "FIFA_VEIKKAUS_PREDICTIONS" in q:
            email = query.split("'")[1].lower() if "'" in query else MOCK_CURRENT_USER
            filtered = _PREDICTIONS_DF[
                _PREDICTIONS_DF["USER_EMAIL"] == email
            ][["ID", "HOME_TEAM_GOALS", "AWAY_TEAM_GOALS"]]
            return _MockResult(filtered.copy())

        if "FIFA_VEIKKAUS_RESULTS" in q:
            return _MockResult(RESULTS_DF.copy())

        return _MockResult(pd.DataFrame())

    def write_pandas(self, df: pd.DataFrame, table_name: str, **kwargs):
        global _PREDICTIONS_DF
        print(f"[mock] write_pandas → {table_name} ({len(df)} rows)")
