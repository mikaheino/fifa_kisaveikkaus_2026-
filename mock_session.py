"""
Mock Snowpark session for local development without a Snowflake connection.
Provides sample schedule data, fake results for the opening days, and
in-memory predictions in a single shared table so all UI features can be tested.
"""
import pandas as pd
from datetime import date, timedelta
from itertools import combinations
from typing import Optional

# ── Sample groups (placeholder — admin replaces with actual draw via SQL) ─────
#
# 48 teams across 12 groups of 4. Hosts pre-allocated:
#   Mexico → A, Canada → B, USA → D.
# Remaining teams distributed as a plausible spread of qualified nations from
# the 2026 cycle. Replace with the real draw output in production.

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

ALL_TEAMS: list[str] = sorted({t for teams in GROUPS.values() for t in teams})
assert len(ALL_TEAMS) == 48, f"expected 48 teams, got {len(ALL_TEAMS)}"


# ── Schedule: 72 group-stage games across Jun 11–27, 2026 ─────────────────────

_GROUP_STAGE_START = date(2026, 6, 11)
_GROUP_STAGE_DAYS = 17  # Jun 11 → Jun 27 inclusive

def _build_schedule() -> pd.DataFrame:
    """Round-robin matchups for all 12 groups, spread across 17 days."""
    all_matches: list[tuple[str, str, str]] = []
    for letter in sorted(GROUPS.keys()):
        for home, away in combinations(GROUPS[letter], 2):
            all_matches.append((letter, home, away))
    assert len(all_matches) == 72

    rows = []
    for i, (group_letter, home, away) in enumerate(all_matches):
        day_offset = i * _GROUP_STAGE_DAYS // len(all_matches)
        match_day = _GROUP_STAGE_START + timedelta(days=day_offset)
        rows.append({
            "ID": i + 1,
            "MATCH_DAY": match_day,
            "GROUP_LETTER": group_letter,
            "MATCH": f"{home} vs {away}",
            "HOME_TEAM_GOALS": None,
            "AWAY_TEAM_GOALS": None,
        })
    return pd.DataFrame(rows)

SCHEDULE_DF = _build_schedule()

# Results for the first few games (opening days)
_RESULTS = {
    1: (1, 0), 2: (2, 1), 3: (0, 0), 4: (3, 2),
    5: (1, 1), 6: (2, 2), 7: (0, 1), 8: (1, 3),
}

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


# ── Shared predictions table ─────────────────────────────────────────────────

MOCK_CURRENT_USER = "mika.heino@recordlydata.com"

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
    _make_predictions("matti.test@recordlydata.com", 42, complete_days=2),
    _make_predictions("liisa.test@recordlydata.com", 7),
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
    """Mimics the subset of Snowpark Session API used by the app."""

    def sql(self, query: str) -> _MockResult:
        global _PREDICTIONS_DF, _PLAYOFF_DF, _PLAYOFF_RESULTS_DF
        q = query.upper()

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
            ][["ID", "HOME_TEAM_GOALS", "AWAY_TEAM_GOALS"]]

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
            })[["ID", "MATCH", "RESULT_HOME", "RESULT_AWAY", "PRED_HOME", "PRED_AWAY", "POINTS"]]
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
