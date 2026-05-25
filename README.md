# FIFA-veikkaus 2026

Internal football prediction pool for the **2026 FIFA World Cup** (USA / Canada / Mexico, June 11 – July 19, 2026). Runs as a Streamlit-in-Snowflake **container-runtime** app on the `FIFA_VEIKKAUS_POOL` compute pool, auto-suspended by `FIFA_VEIKKAUS_AUTOSTOP_TASK` after 60 minutes of viewer idle (~60-90s cold start on next visit).

- **Veikkausaika lukittuu:** 11.6.2026 klo 19:00 (Helsinki) – juuri ennen avausottelua.
- **Ennustettavaa:** 72 alkulohko-ottelua + koko pudotuspelibracket + maalikuningas + oma musta hevonen.

## Pisteytys lyhyesti

| | Pisteet |
|---|---|
| Alkulohko-ottelu (täysosuma) | 5 p |
| Alkulohko-ottelu (sama maaliero & voittaja) | 3 p |
| Alkulohko-ottelu (oikea voittaja) | 1 p |
| Lohkovoittaja / -kakkonen | 3 p / kpl |
| Paras kolmonen (8 kpl) | 1 p / kpl |
| R16-jatkaja (16 kpl) | 2 p / kpl |
| Puolivälieräpaikka (8 kpl) | 3 p / kpl |
| Välieräpaikka (4 kpl) | 5 p / kpl |
| Finalisti | +10 p / kpl |
| Mestari | +20 p |
| Maalikuningas | 15 p |
| Musta hevonen (puolivälieriin) | 15 p |

Tarkka kuvaus ja esimerkit löytyvät sovelluksen **Säännöt**-sivulta.

## Repo layout

Katso `AGENTS.md` täydelliset ohjeet tiedostorakenteesta, Snowflake-skeema-asetuksista, deployaamisesta ja kehittäjälle olennaisista konventioista.

```
streamlit_app.py            # Production entry (Snowflake)
streamlit_app_local.py      # Local dev (MockSession, no Snowflake)
mock_session.py             # In-memory Snowpark mock
app_pages/                  # my_predictions, standings, rules, admin_results
tests/                      # pytest (pure Python)
assets/                     # logo + background images
environment.yml             # SiS dependency manifest (Anaconda channel; pip allowed on container runtime)
pyproject.toml              # Local dev deps (uv)
AGENTS.md                   # Full project docs
CLAUDE.md                   # Brief Claude Code instructions
RELEASE_NOTES.md            # Release + migration history
```

## Local development

```bash
python3 -m streamlit run streamlit_app_local.py --server.port 8501 --server.headless true
```

`MockSession` simulates the Snowflake tables in memory — no connection needed.

## Tests

```bash
python3 -m pytest tests/ -v
```

## Production

See `AGENTS.md` → **Snowflake-Specific Settings** for `PUT` commands and migrations.
