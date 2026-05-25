"""Single source of truth for tournament reference data.

Loads ``data/schedule_2026.json`` and exposes Finnish-keyed views used by
both ``mock_session.py`` (local) and every page in ``app_pages/``.

In production this file is uploaded alongside the JSON to
``@FIFA_VEIKKAUS_STAGE/`` (see AGENTS.md → "Deploying files after
changes"), so Snowflake-side imports resolve the same way.
"""
from __future__ import annotations

import json
import os
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH = os.path.join(_HERE, "data", "schedule_2026.json")

with open(_JSON_PATH, encoding="utf-8") as _f:
    _DATA = json.load(_f)

# English → Finnish lookup, used when translating ad-hoc strings.
EN_TO_FI: dict[str, str] = {en: info["fi"] for en, info in _DATA["teams"].items()}

# Finnish team name → flag emoji.
FLAGS: dict[str, str] = {info["fi"]: info["flag"] for info in _DATA["teams"].values()}

# Group letter → list of 4 Finnish team names (host listed first).
GROUPS: dict[str, list[str]] = {
    letter: [EN_TO_FI[en] for en in team_ens]
    for letter, team_ens in _DATA["groups"].items()
}

GROUP_LETTERS: list[str] = sorted(GROUPS.keys())

# Alphabetised flat list of all 48 Finnish team names — for selectbox options.
TEAMS: list[str] = sorted({t for ts in GROUPS.values() for t in ts})


def _parse_date(s: str) -> date:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


# Group-stage match rows in the shape mock_session and the app pages expect.
SCHEDULE_MATCHES: list[dict] = []
for _m in _DATA["matches"]:
    if _m["stage"] != "group":
        continue
    _home_fi = EN_TO_FI[_m["home"]]
    _away_fi = EN_TO_FI[_m["away"]]
    SCHEDULE_MATCHES.append({
        "ID": _m["id"],
        "MATCH_DAY": _parse_date(_m["date"]),
        "GROUP_LETTER": _m["group"],
        "MATCH": f"{_home_fi} vs {_away_fi}",
    })

# Knockout matches (for future use — playoff bracket UI, results entry).
KNOCKOUT_MATCHES: list[dict] = [m for m in _DATA["matches"] if m["stage"] != "group"]

assert len(GROUPS) == 12 and len(TEAMS) == 48
assert len(SCHEDULE_MATCHES) == 72
assert len(KNOCKOUT_MATCHES) == 32
