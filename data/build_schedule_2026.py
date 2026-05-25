"""Build data/schedule_2026.json from the official FIFA 2026 schedule.

The canonical 104-match list is encoded as compact tuples in this script; we
hand-typed each entry once from the FIFA / Wikipedia draw. Re-run this
builder if anything ever changes (kickoff times shift, venue swap, etc.).

  python3 /tmp/build_schedule_2026.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("/Users/mika.heino/prod/fifa_kisaveikkaus_2026/data/schedule_2026.json")

TEAMS = {
    # english (canonical key) -> {fi, flag}
    "Mexico":                 {"fi": "Meksiko",        "flag": "🇲🇽"},
    "South Africa":           {"fi": "Etelä-Afrikka", "flag": "🇿🇦"},
    "South Korea":            {"fi": "Etelä-Korea",   "flag": "🇰🇷"},
    "Czech Republic":         {"fi": "Tšekki",         "flag": "🇨🇿"},
    "Canada":                 {"fi": "Kanada",         "flag": "🇨🇦"},
    "Bosnia and Herzegovina": {"fi": "Bosnia",         "flag": "🇧🇦"},
    "Qatar":                  {"fi": "Qatar",          "flag": "🇶🇦"},
    "Switzerland":            {"fi": "Sveitsi",        "flag": "🇨🇭"},
    "Brazil":                 {"fi": "Brasilia",       "flag": "🇧🇷"},
    "Morocco":                {"fi": "Marokko",        "flag": "🇲🇦"},
    "Haiti":                  {"fi": "Haiti",          "flag": "🇭🇹"},
    "Scotland":               {"fi": "Skotlanti",      "flag": "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f"},
    "United States":          {"fi": "Yhdysvallat",    "flag": "🇺🇸"},
    "Paraguay":               {"fi": "Paraguay",       "flag": "🇵🇾"},
    "Australia":              {"fi": "Australia",      "flag": "🇦🇺"},
    "Turkey":                 {"fi": "Turkki",         "flag": "🇹🇷"},
    "Germany":                {"fi": "Saksa",          "flag": "🇩🇪"},
    "Curaçao":                {"fi": "Curaçao",        "flag": "🇨🇼"},
    "Ivory Coast":            {"fi": "Norsunluurannikko", "flag": "🇨🇮"},
    "Ecuador":                {"fi": "Ecuador",        "flag": "🇪🇨"},
    "Netherlands":            {"fi": "Alankomaat",     "flag": "🇳🇱"},
    "Japan":                  {"fi": "Japani",         "flag": "🇯🇵"},
    "Sweden":                 {"fi": "Ruotsi",         "flag": "🇸🇪"},
    "Tunisia":                {"fi": "Tunisia",        "flag": "🇹🇳"},
    "Belgium":                {"fi": "Belgia",         "flag": "🇧🇪"},
    "Egypt":                  {"fi": "Egypti",         "flag": "🇪🇬"},
    "Iran":                   {"fi": "Iran",           "flag": "🇮🇷"},
    "New Zealand":            {"fi": "Uusi-Seelanti", "flag": "🇳🇿"},
    "Spain":                  {"fi": "Espanja",        "flag": "🇪🇸"},
    "Cape Verde":             {"fi": "Kap Verde",      "flag": "🇨🇻"},
    "Saudi Arabia":           {"fi": "Saudi-Arabia",   "flag": "🇸🇦"},
    "Uruguay":                {"fi": "Uruguay",        "flag": "🇺🇾"},
    "France":                 {"fi": "Ranska",         "flag": "🇫🇷"},
    "Senegal":                {"fi": "Senegal",        "flag": "🇸🇳"},
    "Iraq":                   {"fi": "Irak",           "flag": "🇮🇶"},
    "Norway":                 {"fi": "Norja",          "flag": "🇳🇴"},
    "Argentina":              {"fi": "Argentiina",     "flag": "🇦🇷"},
    "Algeria":                {"fi": "Algeria",        "flag": "🇩🇿"},
    "Austria":                {"fi": "Itävalta",       "flag": "🇦🇹"},
    "Jordan":                 {"fi": "Jordania",       "flag": "🇯🇴"},
    "Portugal":               {"fi": "Portugali",      "flag": "🇵🇹"},
    "DR Congo":               {"fi": "Kongon DT",      "flag": "🇨🇩"},
    "Uzbekistan":             {"fi": "Uzbekistan",     "flag": "🇺🇿"},
    "Colombia":               {"fi": "Kolumbia",       "flag": "🇨🇴"},
    "England":                {"fi": "Englanti",       "flag": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f"},
    "Croatia":                {"fi": "Kroatia",        "flag": "🇭🇷"},
    "Ghana":                  {"fi": "Ghana",          "flag": "🇬🇭"},
    "Panama":                 {"fi": "Panama",         "flag": "🇵🇦"},
}

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

HOST_NATIONS = ["Mexico", "Canada", "United States"]

VENUES = {
    "Estadio Azteca":          {"city": "Mexico City",       "country": "Mexico"},
    "Estadio Akron":           {"city": "Zapopan",           "country": "Mexico"},
    "Estadio BBVA":            {"city": "Guadalupe",         "country": "Mexico"},
    "BMO Field":               {"city": "Toronto",           "country": "Canada"},
    "BC Place":                {"city": "Vancouver",         "country": "Canada"},
    "SoFi Stadium":            {"city": "Inglewood",         "country": "United States"},
    "Levi's Stadium":          {"city": "Santa Clara",       "country": "United States"},
    "Lumen Field":             {"city": "Seattle",           "country": "United States"},
    "NRG Stadium":             {"city": "Houston",           "country": "United States"},
    "AT&T Stadium":            {"city": "Arlington",         "country": "United States"},
    "Arrowhead Stadium":       {"city": "Kansas City",       "country": "United States"},
    "Mercedes-Benz Stadium":   {"city": "Atlanta",           "country": "United States"},
    "Hard Rock Stadium":       {"city": "Miami Gardens",     "country": "United States"},
    "MetLife Stadium":         {"city": "East Rutherford",   "country": "United States"},
    "Gillette Stadium":        {"city": "Foxborough",        "country": "United States"},
    "Lincoln Financial Field": {"city": "Philadelphia",      "country": "United States"},
}

# Group-stage matches: (id, group, date, local_time, tz_offset, home, away, venue)
GROUP_MATCHES = [
    # ── Round 1 ──
    (1,  "A", "2026-06-11", "13:00", "-06:00", "Mexico",         "South Africa",            "Estadio Azteca"),
    (2,  "A", "2026-06-11", "20:00", "-06:00", "South Korea",    "Czech Republic",          "Estadio Akron"),
    (3,  "B", "2026-06-12", "15:00", "-04:00", "Canada",         "Bosnia and Herzegovina",  "BMO Field"),
    (4,  "D", "2026-06-12", "18:00", "-07:00", "United States",  "Paraguay",                "SoFi Stadium"),
    (5,  "C", "2026-06-13", "21:00", "-04:00", "Haiti",          "Scotland",                "Gillette Stadium"),
    (6,  "D", "2026-06-13", "21:00", "-07:00", "Australia",      "Turkey",                  "BC Place"),
    (7,  "C", "2026-06-13", "18:00", "-04:00", "Brazil",         "Morocco",                 "MetLife Stadium"),
    (8,  "B", "2026-06-13", "12:00", "-07:00", "Qatar",          "Switzerland",             "Levi's Stadium"),
    (9,  "E", "2026-06-14", "19:00", "-04:00", "Ivory Coast",    "Ecuador",                 "Lincoln Financial Field"),
    (10, "E", "2026-06-14", "12:00", "-05:00", "Germany",        "Curaçao",                 "NRG Stadium"),
    (11, "F", "2026-06-14", "15:00", "-05:00", "Netherlands",    "Japan",                   "AT&T Stadium"),
    (12, "F", "2026-06-14", "20:00", "-06:00", "Sweden",         "Tunisia",                 "Estadio BBVA"),
    (13, "H", "2026-06-15", "18:00", "-04:00", "Saudi Arabia",   "Uruguay",                 "Hard Rock Stadium"),
    (14, "H", "2026-06-15", "12:00", "-04:00", "Spain",          "Cape Verde",              "Mercedes-Benz Stadium"),
    (15, "G", "2026-06-15", "18:00", "-07:00", "Iran",           "New Zealand",             "SoFi Stadium"),
    (16, "G", "2026-06-15", "12:00", "-07:00", "Belgium",        "Egypt",                   "Lumen Field"),
    (17, "I", "2026-06-16", "15:00", "-04:00", "France",         "Senegal",                 "MetLife Stadium"),
    (18, "I", "2026-06-16", "18:00", "-04:00", "Iraq",           "Norway",                  "Gillette Stadium"),
    (19, "J", "2026-06-16", "20:00", "-05:00", "Argentina",      "Algeria",                 "Arrowhead Stadium"),
    (20, "J", "2026-06-16", "21:00", "-07:00", "Austria",        "Jordan",                  "Levi's Stadium"),
    (21, "L", "2026-06-17", "19:00", "-04:00", "Ghana",          "Panama",                  "BMO Field"),
    (22, "L", "2026-06-17", "15:00", "-05:00", "England",        "Croatia",                 "AT&T Stadium"),
    (23, "K", "2026-06-17", "12:00", "-05:00", "Portugal",       "DR Congo",                "NRG Stadium"),
    (24, "K", "2026-06-17", "20:00", "-06:00", "Uzbekistan",     "Colombia",                "Estadio Azteca"),
    # ── Round 2 ──
    (25, "A", "2026-06-18", "12:00", "-04:00", "Czech Republic",          "South Africa",            "Mercedes-Benz Stadium"),
    (26, "B", "2026-06-18", "12:00", "-07:00", "Switzerland",             "Bosnia and Herzegovina",  "SoFi Stadium"),
    (27, "B", "2026-06-18", "15:00", "-07:00", "Canada",                  "Qatar",                   "BC Place"),
    (28, "A", "2026-06-18", "19:00", "-06:00", "Mexico",                  "South Korea",             "Estadio Akron"),
    (29, "C", "2026-06-19", "20:30", "-04:00", "Brazil",                  "Haiti",                   "Lincoln Financial Field"),
    (30, "C", "2026-06-19", "18:00", "-04:00", "Scotland",                "Morocco",                 "Gillette Stadium"),
    (31, "D", "2026-06-19", "20:00", "-07:00", "Turkey",                  "Paraguay",                "Levi's Stadium"),
    (32, "D", "2026-06-19", "12:00", "-07:00", "United States",           "Australia",               "Lumen Field"),
    (33, "E", "2026-06-20", "16:00", "-04:00", "Germany",                 "Ivory Coast",             "BMO Field"),
    (34, "E", "2026-06-20", "19:00", "-05:00", "Ecuador",                 "Curaçao",                 "Arrowhead Stadium"),
    (35, "F", "2026-06-20", "12:00", "-05:00", "Netherlands",             "Sweden",                  "NRG Stadium"),
    (36, "F", "2026-06-20", "22:00", "-06:00", "Tunisia",                 "Japan",                   "Estadio BBVA"),
    (37, "H", "2026-06-21", "18:00", "-04:00", "Uruguay",                 "Cape Verde",              "Hard Rock Stadium"),
    (38, "H", "2026-06-21", "12:00", "-04:00", "Spain",                   "Saudi Arabia",            "Mercedes-Benz Stadium"),
    (39, "G", "2026-06-21", "12:00", "-07:00", "Belgium",                 "Iran",                    "SoFi Stadium"),
    (40, "G", "2026-06-21", "18:00", "-07:00", "New Zealand",             "Egypt",                   "BC Place"),
    (41, "I", "2026-06-22", "20:00", "-04:00", "Norway",                  "Senegal",                 "MetLife Stadium"),
    (42, "I", "2026-06-22", "17:00", "-04:00", "France",                  "Iraq",                    "Lincoln Financial Field"),
    (43, "J", "2026-06-22", "12:00", "-05:00", "Argentina",               "Austria",                 "AT&T Stadium"),
    (44, "J", "2026-06-22", "20:00", "-07:00", "Jordan",                  "Algeria",                 "Levi's Stadium"),
    (45, "L", "2026-06-23", "16:00", "-04:00", "England",                 "Ghana",                   "Gillette Stadium"),
    (46, "L", "2026-06-23", "19:00", "-04:00", "Panama",                  "Croatia",                 "BMO Field"),
    (47, "K", "2026-06-23", "12:00", "-05:00", "Portugal",                "Uzbekistan",              "NRG Stadium"),
    (48, "K", "2026-06-23", "20:00", "-06:00", "Colombia",                "DR Congo",                "Estadio Akron"),
    # ── Round 3 ──
    (49, "C", "2026-06-24", "18:00", "-04:00", "Scotland",                "Brazil",                  "Hard Rock Stadium"),
    (50, "C", "2026-06-24", "18:00", "-04:00", "Morocco",                 "Haiti",                   "Mercedes-Benz Stadium"),
    (51, "B", "2026-06-24", "12:00", "-07:00", "Switzerland",             "Canada",                  "BC Place"),
    (52, "B", "2026-06-24", "12:00", "-07:00", "Bosnia and Herzegovina",  "Qatar",                   "Lumen Field"),
    (53, "A", "2026-06-24", "19:00", "-06:00", "Czech Republic",          "Mexico",                  "Estadio Azteca"),
    (54, "A", "2026-06-24", "19:00", "-06:00", "South Africa",            "South Korea",             "Estadio BBVA"),
    (55, "E", "2026-06-25", "16:00", "-04:00", "Curaçao",                 "Ivory Coast",             "Lincoln Financial Field"),
    (56, "E", "2026-06-25", "16:00", "-04:00", "Ecuador",                 "Germany",                 "MetLife Stadium"),
    (57, "F", "2026-06-25", "18:00", "-05:00", "Japan",                   "Sweden",                  "AT&T Stadium"),
    (58, "F", "2026-06-25", "18:00", "-05:00", "Tunisia",                 "Netherlands",             "Arrowhead Stadium"),
    (59, "D", "2026-06-25", "19:00", "-07:00", "Turkey",                  "United States",           "SoFi Stadium"),
    (60, "D", "2026-06-25", "19:00", "-07:00", "Paraguay",                "Australia",               "Levi's Stadium"),
    (61, "I", "2026-06-26", "15:00", "-04:00", "Norway",                  "France",                  "Gillette Stadium"),
    (62, "I", "2026-06-26", "15:00", "-04:00", "Senegal",                 "Iraq",                    "BMO Field"),
    (63, "G", "2026-06-26", "20:00", "-07:00", "Egypt",                   "Iran",                    "Lumen Field"),
    (64, "G", "2026-06-26", "20:00", "-07:00", "New Zealand",             "Belgium",                 "BC Place"),
    (65, "H", "2026-06-26", "19:00", "-05:00", "Cape Verde",              "Saudi Arabia",            "NRG Stadium"),
    (66, "H", "2026-06-26", "18:00", "-06:00", "Uruguay",                 "Spain",                   "Estadio Akron"),
    (67, "L", "2026-06-27", "17:00", "-04:00", "Panama",                  "England",                 "MetLife Stadium"),
    (68, "L", "2026-06-27", "17:00", "-04:00", "Croatia",                 "Ghana",                   "Lincoln Financial Field"),
    (69, "J", "2026-06-27", "21:00", "-05:00", "Algeria",                 "Austria",                 "Arrowhead Stadium"),
    (70, "J", "2026-06-27", "21:00", "-05:00", "Jordan",                  "Argentina",               "AT&T Stadium"),
    (71, "K", "2026-06-27", "19:30", "-04:00", "Colombia",                "Portugal",                "Hard Rock Stadium"),
    (72, "K", "2026-06-27", "19:30", "-04:00", "DR Congo",                "Uzbekistan",              "Mercedes-Benz Stadium"),
]

# Knockout: home/away are placeholders until determined by group results.
# Tuple shape: (id, stage, date, local_time, tz_offset, home_placeholder,
#               away_placeholder, venue)
KO_MATCHES = [
    # ── Round of 32 (June 28 – July 3) ──
    (73,  "round_of_32", "2026-06-28", "12:00", "-07:00", "Runner-up Group A",  "Runner-up Group B",  "SoFi Stadium"),
    (74,  "round_of_32", "2026-06-29", "16:30", "-04:00", "Winner Group E",     "3rd Group A/B/C/D/F", "Gillette Stadium"),
    (75,  "round_of_32", "2026-06-29", "19:00", "-06:00", "Winner Group F",     "Runner-up Group C",  "Estadio BBVA"),
    (76,  "round_of_32", "2026-06-29", "12:00", "-05:00", "Winner Group C",     "Runner-up Group F",  "NRG Stadium"),
    (77,  "round_of_32", "2026-06-30", "17:00", "-04:00", "Winner Group I",     "3rd Group C/D/F/G/H", "MetLife Stadium"),
    (78,  "round_of_32", "2026-06-30", "12:00", "-05:00", "Runner-up Group E",  "Runner-up Group I",  "AT&T Stadium"),
    (79,  "round_of_32", "2026-06-30", "19:00", "-06:00", "Winner Group A",     "3rd Group C/E/F/H/I", "Estadio Azteca"),
    (80,  "round_of_32", "2026-07-01", "12:00", "-04:00", "Winner Group L",     "3rd Group E/H/I/J/K", "Mercedes-Benz Stadium"),
    (81,  "round_of_32", "2026-07-01", "17:00", "-07:00", "Winner Group D",     "3rd Group B/E/F/I/J", "Levi's Stadium"),
    (82,  "round_of_32", "2026-07-01", "13:00", "-07:00", "Winner Group G",     "3rd Group A/E/H/I/J", "Lumen Field"),
    (83,  "round_of_32", "2026-07-02", "19:00", "-04:00", "Runner-up Group K",  "Runner-up Group L",  "BMO Field"),
    (84,  "round_of_32", "2026-07-02", "12:00", "-07:00", "Winner Group H",     "Runner-up Group J",  "SoFi Stadium"),
    (85,  "round_of_32", "2026-07-02", "20:00", "-07:00", "Winner Group B",     "3rd Group E/F/G/I/J", "BC Place"),
    (86,  "round_of_32", "2026-07-03", "18:00", "-04:00", "Winner Group J",     "Runner-up Group H",  "Hard Rock Stadium"),
    (87,  "round_of_32", "2026-07-03", "20:30", "-05:00", "Winner Group K",     "3rd Group D/E/I/J/L", "Arrowhead Stadium"),
    (88,  "round_of_32", "2026-07-03", "13:00", "-05:00", "Runner-up Group D",  "Runner-up Group G",  "AT&T Stadium"),
    # ── Round of 16 (July 4 – 7) ──
    (89,  "round_of_16", "2026-07-04", "17:00", "-04:00", "Winner Match 74", "Winner Match 77", "Lincoln Financial Field"),
    (90,  "round_of_16", "2026-07-04", "12:00", "-05:00", "Winner Match 73", "Winner Match 75", "NRG Stadium"),
    (91,  "round_of_16", "2026-07-05", "16:00", "-04:00", "Winner Match 76", "Winner Match 78", "MetLife Stadium"),
    (92,  "round_of_16", "2026-07-05", "18:00", "-06:00", "Winner Match 79", "Winner Match 80", "Estadio Azteca"),
    (93,  "round_of_16", "2026-07-06", "14:00", "-05:00", "Winner Match 83", "Winner Match 84", "AT&T Stadium"),
    (94,  "round_of_16", "2026-07-06", "17:00", "-07:00", "Winner Match 81", "Winner Match 82", "Lumen Field"),
    (95,  "round_of_16", "2026-07-07", "12:00", "-04:00", "Winner Match 86", "Winner Match 88", "Mercedes-Benz Stadium"),
    (96,  "round_of_16", "2026-07-07", "13:00", "-07:00", "Winner Match 85", "Winner Match 87", "BC Place"),
    # ── Quarterfinals (July 9 – 11) ──
    (97,  "quarterfinal", "2026-07-09", "16:00", "-04:00", "Winner Match 89", "Winner Match 90", "Gillette Stadium"),
    (98,  "quarterfinal", "2026-07-10", "12:00", "-07:00", "Winner Match 93", "Winner Match 94", "SoFi Stadium"),
    (99,  "quarterfinal", "2026-07-11", "17:00", "-04:00", "Winner Match 91", "Winner Match 92", "Hard Rock Stadium"),
    (100, "quarterfinal", "2026-07-11", "20:00", "-05:00", "Winner Match 95", "Winner Match 96", "Arrowhead Stadium"),
    # ── Semifinals (July 14 – 15) ──
    (101, "semifinal", "2026-07-14", "14:00", "-05:00", "Winner Match 97", "Winner Match 98",  "AT&T Stadium"),
    (102, "semifinal", "2026-07-15", "15:00", "-04:00", "Winner Match 99", "Winner Match 100", "Mercedes-Benz Stadium"),
    # ── Third-place play-off (July 18) ──
    (103, "third_place", "2026-07-18", "17:00", "-04:00", "Loser Match 101",  "Loser Match 102",  "Hard Rock Stadium"),
    # ── Final (July 19) ──
    (104, "final",       "2026-07-19", "15:00", "-04:00", "Winner Match 101", "Winner Match 102", "MetLife Stadium"),
]


def build() -> dict:
    matches = []
    for (mid, grp, date, time, tz, h, a, v) in GROUP_MATCHES:
        assert h in TEAMS, h
        assert a in TEAMS, a
        assert v in VENUES, v
        assert h in GROUPS[grp] and a in GROUPS[grp], (grp, h, a)
        matches.append({
            "id": mid, "stage": "group", "group": grp,
            "date": date, "time": time, "tz": tz,
            "home": h, "away": a, "venue": v,
        })
    for (mid, stg, date, time, tz, hp, ap, v) in KO_MATCHES:
        assert v in VENUES, v
        matches.append({
            "id": mid, "stage": stg,
            "date": date, "time": time, "tz": tz,
            "home_placeholder": hp, "away_placeholder": ap,
            "venue": v,
        })

    return {
        "tournament": "FIFA World Cup 2026",
        "start_date": "2026-06-11",
        "end_date":   "2026-07-19",
        "host_nations": HOST_NATIONS,
        "teams": TEAMS,
        "groups": GROUPS,
        "venues": VENUES,
        "matches": matches,
    }


def main() -> None:
    data = build()

    # Sanity checks
    assert len(data["teams"]) == 48, len(data["teams"])
    assert sum(len(v) for v in data["groups"].values()) == 48
    assert len(data["venues"]) == 16
    assert len(data["matches"]) == 104

    by_stage = {}
    for m in data["matches"]:
        by_stage[m["stage"]] = by_stage.get(m["stage"], 0) + 1
    assert by_stage == {
        "group": 72, "round_of_32": 16, "round_of_16": 8,
        "quarterfinal": 4, "semifinal": 2, "third_place": 1, "final": 1,
    }, by_stage

    ids = [m["id"] for m in data["matches"]]
    assert ids == list(range(1, 105)), "match IDs must be 1..104"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"  {len(data['teams'])} teams, {len(data['groups'])} groups, "
          f"{len(data['venues'])} venues, {len(data['matches'])} matches")
    print(f"  stage breakdown: {by_stage}")


if __name__ == "__main__":
    main()
