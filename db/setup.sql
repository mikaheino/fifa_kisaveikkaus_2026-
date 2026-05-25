/* ──────────────────────────────────────────────────────────────────────────
   FIFA-veikkaus 2026 — Snowflake bootstrap
   Run start-to-finish as ACCOUNTADMIN. Idempotent: re-running is safe,
   it will not duplicate rows or overwrite results.

   Creates:
     - warehouse  FIFA_VEIKKAUS_WH                  (XS, auto-suspend 60s)
     - database   STREAMLIT_APPS                    (shared with other apps)
     - schema     STREAMLIT_APPS.FIFA_VEIKKAUS
     - tables     FIFA_VEIKKAUS_SCHEDULE,
                  FIFA_VEIKKAUS_RESULTS,
                  FIFA_VEIKKAUS_PREDICTIONS,
                  FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS,
                  FIFA_VEIKKAUS_PLAYOFF_RESULTS
     - view       FIFA_VEIKKAUS_RESULTS_V           (schedule × results)
     - stage      FIFA_VEIKKAUS_STAGE               (app source files)
     - roles      FIFA_VEIKKAUS_PLAYER_ROLE         (read all, write own preds)
                  FIFA_VEIKKAUS_ADMIN_ROLE          (full DML)
     - app        FIFA_VEIKKAUS_APP                 (Streamlit, last)
     - seed       72-row group-stage schedule (idempotent MERGE)
   ────────────────────────────────────────────────────────────────────────── */

USE ROLE ACCOUNTADMIN;

/* ── 1. Warehouse ─────────────────────────────────────────────────────── */
CREATE WAREHOUSE IF NOT EXISTS FIFA_VEIKKAUS_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Compute for the FIFA-veikkaus 2026 Streamlit app';

/* ── 2. Database + schema ────────────────────────────────────────────── */
CREATE DATABASE IF NOT EXISTS STREAMLIT_APPS
    COMMENT = 'Shared host for internal Streamlit apps';

CREATE SCHEMA IF NOT EXISTS STREAMLIT_APPS.FIFA_VEIKKAUS
    COMMENT = 'FIFA-veikkaus 2026 — tables, stage and Streamlit object';

USE DATABASE STREAMLIT_APPS;
USE SCHEMA   FIFA_VEIKKAUS;
USE WAREHOUSE FIFA_VEIKKAUS_WH;

/* ── 3. Roles ─────────────────────────────────────────────────────────
   Two account-level roles:
     - FIFA_VEIKKAUS_PLAYER_ROLE: granted to every veikkaus participant.
       Can read all reference data + every player's predictions, and can
       write/update only its own predictions (filtered by USER_EMAIL =
       CURRENT_USER() in the app code; we don't enforce row-level security
       at the table layer to keep the SQL simple — RBAC is in the app).
     - FIFA_VEIKKAUS_ADMIN_ROLE: superset of player — can also write the
       admin tables (RESULTS, PLAYOFF_RESULTS).
   Admin role inherits player role so admins also see the player tables.
   ──────────────────────────────────────────────────────────────────── */
CREATE ROLE IF NOT EXISTS FIFA_VEIKKAUS_PLAYER_ROLE
    COMMENT = 'FIFA-veikkaus 2026 — participant role';
CREATE ROLE IF NOT EXISTS FIFA_VEIKKAUS_ADMIN_ROLE
    COMMENT = 'FIFA-veikkaus 2026 — admin role (enters results)';

GRANT ROLE FIFA_VEIKKAUS_PLAYER_ROLE TO ROLE FIFA_VEIKKAUS_ADMIN_ROLE;
GRANT ROLE FIFA_VEIKKAUS_ADMIN_ROLE  TO ROLE SYSADMIN;

/* Warehouse usage for both roles */
GRANT USAGE, OPERATE ON WAREHOUSE FIFA_VEIKKAUS_WH
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* Database + schema usage */
GRANT USAGE ON DATABASE STREAMLIT_APPS
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;
GRANT USAGE ON SCHEMA STREAMLIT_APPS.FIFA_VEIKKAUS
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* ── 4. Tables ────────────────────────────────────────────────────────
   Match strings stored as "Home vs Away" in Finnish (e.g. "Saksa vs Norja").
   Goals are NUMBER(2,0) — NULL until the admin enters a result.
   Playoff tables are wide single-row-per-user (admin row count == 1).
   ──────────────────────────────────────────────────────────────────── */

CREATE TABLE IF NOT EXISTS FIFA_VEIKKAUS_SCHEDULE (
    ID            NUMBER(3,0)   NOT NULL,
    MATCH_DAY     DATE          NOT NULL,
    GROUP_LETTER  VARCHAR(1)    NOT NULL,
    MATCH         VARCHAR(64)   NOT NULL,
    CONSTRAINT PK_FIFA_VEIKKAUS_SCHEDULE PRIMARY KEY (ID)
);

CREATE TABLE IF NOT EXISTS FIFA_VEIKKAUS_RESULTS (
    ID                NUMBER(3,0)  NOT NULL,
    HOME_TEAM_GOALS   NUMBER(2,0),
    AWAY_TEAM_GOALS   NUMBER(2,0),
    UPDATED           TIMESTAMP_NTZ,
    CONSTRAINT PK_FIFA_VEIKKAUS_RESULTS PRIMARY KEY (ID)
);

CREATE TABLE IF NOT EXISTS FIFA_VEIKKAUS_PREDICTIONS (
    USER_EMAIL        VARCHAR(255) NOT NULL,
    ID                NUMBER(3,0)  NOT NULL,
    MATCH_DAY         DATE,
    MATCH             VARCHAR(64),
    HOME_TEAM_GOALS   NUMBER(2,0),
    AWAY_TEAM_GOALS   NUMBER(2,0),
    INSERTED          TIMESTAMP_NTZ,
    CONSTRAINT PK_FIFA_VEIKKAUS_PREDICTIONS PRIMARY KEY (USER_EMAIL, ID)
);

/* Helper view: schedule LEFT JOIN results with derived WINNER column.
   Used by the standings calculation in the app. */
CREATE OR REPLACE VIEW FIFA_VEIKKAUS_RESULTS_V AS
SELECT
    s.ID,
    s.MATCH_DAY,
    s.GROUP_LETTER,
    s.MATCH,
    r.HOME_TEAM_GOALS,
    r.AWAY_TEAM_GOALS,
    CASE
        WHEN r.HOME_TEAM_GOALS IS NULL OR r.AWAY_TEAM_GOALS IS NULL THEN NULL
        WHEN r.HOME_TEAM_GOALS  > r.AWAY_TEAM_GOALS THEN SPLIT_PART(s.MATCH, ' vs ', 1)
        WHEN r.HOME_TEAM_GOALS  < r.AWAY_TEAM_GOALS THEN SPLIT_PART(s.MATCH, ' vs ', 2)
        ELSE 'DRAW'
    END AS WINNER
FROM FIFA_VEIKKAUS_SCHEDULE s
LEFT JOIN FIFA_VEIKKAUS_RESULTS r ON r.ID = s.ID;

/* Wide playoff tables.
   Predictions: one row per user. Results: one row total (admin-filled).
   Column order matches _PLAYOFF_COLS / _RESULT_COLS in the Python code.
*/
CREATE TABLE IF NOT EXISTS FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS (
    USER_EMAIL           VARCHAR(255) NOT NULL,
    GROUP_A_WINNER       VARCHAR(64),
    GROUP_B_WINNER       VARCHAR(64),
    GROUP_C_WINNER       VARCHAR(64),
    GROUP_D_WINNER       VARCHAR(64),
    GROUP_E_WINNER       VARCHAR(64),
    GROUP_F_WINNER       VARCHAR(64),
    GROUP_G_WINNER       VARCHAR(64),
    GROUP_H_WINNER       VARCHAR(64),
    GROUP_I_WINNER       VARCHAR(64),
    GROUP_J_WINNER       VARCHAR(64),
    GROUP_K_WINNER       VARCHAR(64),
    GROUP_L_WINNER       VARCHAR(64),
    GROUP_A_RUNNERUP     VARCHAR(64),
    GROUP_B_RUNNERUP     VARCHAR(64),
    GROUP_C_RUNNERUP     VARCHAR(64),
    GROUP_D_RUNNERUP     VARCHAR(64),
    GROUP_E_RUNNERUP     VARCHAR(64),
    GROUP_F_RUNNERUP     VARCHAR(64),
    GROUP_G_RUNNERUP     VARCHAR(64),
    GROUP_H_RUNNERUP     VARCHAR(64),
    GROUP_I_RUNNERUP     VARCHAR(64),
    GROUP_J_RUNNERUP     VARCHAR(64),
    GROUP_K_RUNNERUP     VARCHAR(64),
    GROUP_L_RUNNERUP     VARCHAR(64),
    THIRD_1              VARCHAR(64),
    THIRD_2              VARCHAR(64),
    THIRD_3              VARCHAR(64),
    THIRD_4              VARCHAR(64),
    THIRD_5              VARCHAR(64),
    THIRD_6              VARCHAR(64),
    THIRD_7              VARCHAR(64),
    THIRD_8              VARCHAR(64),
    R16_1                VARCHAR(64),
    R16_2                VARCHAR(64),
    R16_3                VARCHAR(64),
    R16_4                VARCHAR(64),
    R16_5                VARCHAR(64),
    R16_6                VARCHAR(64),
    R16_7                VARCHAR(64),
    R16_8                VARCHAR(64),
    R16_9                VARCHAR(64),
    R16_10               VARCHAR(64),
    R16_11               VARCHAR(64),
    R16_12               VARCHAR(64),
    R16_13               VARCHAR(64),
    R16_14               VARCHAR(64),
    R16_15               VARCHAR(64),
    R16_16               VARCHAR(64),
    QF_1                 VARCHAR(64),
    QF_2                 VARCHAR(64),
    QF_3                 VARCHAR(64),
    QF_4                 VARCHAR(64),
    QF_5                 VARCHAR(64),
    QF_6                 VARCHAR(64),
    QF_7                 VARCHAR(64),
    QF_8                 VARCHAR(64),
    SF_1                 VARCHAR(64),
    SF_2                 VARCHAR(64),
    SF_3                 VARCHAR(64),
    SF_4                 VARCHAR(64),
    FINALIST_1           VARCHAR(64),
    FINALIST_2           VARCHAR(64),
    CHAMPION             VARCHAR(64),
    TOP_SCORER           VARCHAR(128),
    DARK_HORSE           VARCHAR(64),
    INSERTED             TIMESTAMP_NTZ,
    CONSTRAINT PK_FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS PRIMARY KEY (USER_EMAIL)
);

CREATE TABLE IF NOT EXISTS FIFA_VEIKKAUS_PLAYOFF_RESULTS (
    GROUP_A_WINNER       VARCHAR(64),
    GROUP_B_WINNER       VARCHAR(64),
    GROUP_C_WINNER       VARCHAR(64),
    GROUP_D_WINNER       VARCHAR(64),
    GROUP_E_WINNER       VARCHAR(64),
    GROUP_F_WINNER       VARCHAR(64),
    GROUP_G_WINNER       VARCHAR(64),
    GROUP_H_WINNER       VARCHAR(64),
    GROUP_I_WINNER       VARCHAR(64),
    GROUP_J_WINNER       VARCHAR(64),
    GROUP_K_WINNER       VARCHAR(64),
    GROUP_L_WINNER       VARCHAR(64),
    GROUP_A_RUNNERUP     VARCHAR(64),
    GROUP_B_RUNNERUP     VARCHAR(64),
    GROUP_C_RUNNERUP     VARCHAR(64),
    GROUP_D_RUNNERUP     VARCHAR(64),
    GROUP_E_RUNNERUP     VARCHAR(64),
    GROUP_F_RUNNERUP     VARCHAR(64),
    GROUP_G_RUNNERUP     VARCHAR(64),
    GROUP_H_RUNNERUP     VARCHAR(64),
    GROUP_I_RUNNERUP     VARCHAR(64),
    GROUP_J_RUNNERUP     VARCHAR(64),
    GROUP_K_RUNNERUP     VARCHAR(64),
    GROUP_L_RUNNERUP     VARCHAR(64),
    THIRD_1              VARCHAR(64),
    THIRD_2              VARCHAR(64),
    THIRD_3              VARCHAR(64),
    THIRD_4              VARCHAR(64),
    THIRD_5              VARCHAR(64),
    THIRD_6              VARCHAR(64),
    THIRD_7              VARCHAR(64),
    THIRD_8              VARCHAR(64),
    R16_1                VARCHAR(64),
    R16_2                VARCHAR(64),
    R16_3                VARCHAR(64),
    R16_4                VARCHAR(64),
    R16_5                VARCHAR(64),
    R16_6                VARCHAR(64),
    R16_7                VARCHAR(64),
    R16_8                VARCHAR(64),
    R16_9                VARCHAR(64),
    R16_10               VARCHAR(64),
    R16_11               VARCHAR(64),
    R16_12               VARCHAR(64),
    R16_13               VARCHAR(64),
    R16_14               VARCHAR(64),
    R16_15               VARCHAR(64),
    R16_16               VARCHAR(64),
    QF_1                 VARCHAR(64),
    QF_2                 VARCHAR(64),
    QF_3                 VARCHAR(64),
    QF_4                 VARCHAR(64),
    QF_5                 VARCHAR(64),
    QF_6                 VARCHAR(64),
    QF_7                 VARCHAR(64),
    QF_8                 VARCHAR(64),
    SF_1                 VARCHAR(64),
    SF_2                 VARCHAR(64),
    SF_3                 VARCHAR(64),
    SF_4                 VARCHAR(64),
    FINALIST_1           VARCHAR(64),
    FINALIST_2           VARCHAR(64),
    CHAMPION             VARCHAR(64),
    TOP_SCORER           VARCHAR(128),
    UPDATED              TIMESTAMP_NTZ
);

/* ── 5. Stage (Streamlit source files live here) ────────────────────── */
CREATE STAGE IF NOT EXISTS FIFA_VEIKKAUS_STAGE
    DIRECTORY = ( ENABLE = TRUE )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
    COMMENT = 'Source files for FIFA_VEIKKAUS_APP — see AGENTS.md PUT block';

/* ── 6. Grants ────────────────────────────────────────────────────────
   PLAYER: read everything, write own group-stage predictions and own
           playoff predictions (RBAC at app level is by USER_EMAIL).
   ADMIN:  full DML on results tables.
   ──────────────────────────────────────────────────────────────────── */

/* Player: SELECT on all tables (incl. each other's predictions for the
   public leaderboard / per-player view). */
GRANT SELECT ON ALL TABLES    IN SCHEMA FIFA_VEIKKAUS TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA FIFA_VEIKKAUS TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;
GRANT SELECT ON ALL VIEWS     IN SCHEMA FIFA_VEIKKAUS TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA FIFA_VEIKKAUS TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* Player: write own predictions (filtered by USER_EMAIL in app code). */
GRANT INSERT, UPDATE, DELETE ON TABLE FIFA_VEIKKAUS_PREDICTIONS
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;
GRANT INSERT, UPDATE, DELETE ON TABLE FIFA_VEIKKAUS_PLAYOFF_PREDICTIONS
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* Player: read the stage so the Streamlit app's files can be served. */
GRANT READ, USAGE ON STAGE FIFA_VEIKKAUS_STAGE
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* Admin: results tables (filling in actual outcomes). */
GRANT INSERT, UPDATE, DELETE ON TABLE FIFA_VEIKKAUS_RESULTS
    TO ROLE FIFA_VEIKKAUS_ADMIN_ROLE;
GRANT INSERT, UPDATE, DELETE ON TABLE FIFA_VEIKKAUS_PLAYOFF_RESULTS
    TO ROLE FIFA_VEIKKAUS_ADMIN_ROLE;

/* Admin: write to stage (uploading new source-file versions). */
GRANT WRITE ON STAGE FIFA_VEIKKAUS_STAGE
    TO ROLE FIFA_VEIKKAUS_ADMIN_ROLE;

/* ── 7. Seed: 72-game group-stage schedule (real FIFA 2026 draw) ──────
   Generated from data/schedule_2026.json — the canonical source of truth.
   To regenerate after a schedule correction, re-run the snippet in
   data/build_schedule_2026.py and re-emit the VALUES block.

   MERGE includes WHEN MATCHED THEN UPDATE so re-running the bootstrap on
   a DB that was previously seeded with placeholder data corrects the rows
   in place. Idempotent: re-running on already-correct data is a no-op.
   ──────────────────────────────────────────────────────────────────── */
MERGE INTO FIFA_VEIKKAUS_SCHEDULE t
USING (
    SELECT column1 AS ID, column2::DATE AS MATCH_DAY,
           column3 AS GROUP_LETTER, column4 AS MATCH
    FROM VALUES
        (1,  '2026-06-11', 'A', 'Meksiko vs Etelä-Afrikka'),
        (2,  '2026-06-11', 'A', 'Etelä-Korea vs Tšekki'),
        (3,  '2026-06-12', 'B', 'Kanada vs Bosnia'),
        (4,  '2026-06-12', 'D', 'Yhdysvallat vs Paraguay'),
        (5,  '2026-06-13', 'C', 'Haiti vs Skotlanti'),
        (6,  '2026-06-13', 'D', 'Australia vs Turkki'),
        (7,  '2026-06-13', 'C', 'Brasilia vs Marokko'),
        (8,  '2026-06-13', 'B', 'Qatar vs Sveitsi'),
        (9,  '2026-06-14', 'E', 'Norsunluurannikko vs Ecuador'),
        (10, '2026-06-14', 'E', 'Saksa vs Curaçao'),
        (11, '2026-06-14', 'F', 'Alankomaat vs Japani'),
        (12, '2026-06-14', 'F', 'Ruotsi vs Tunisia'),
        (13, '2026-06-15', 'H', 'Saudi-Arabia vs Uruguay'),
        (14, '2026-06-15', 'H', 'Espanja vs Kap Verde'),
        (15, '2026-06-15', 'G', 'Iran vs Uusi-Seelanti'),
        (16, '2026-06-15', 'G', 'Belgia vs Egypti'),
        (17, '2026-06-16', 'I', 'Ranska vs Senegal'),
        (18, '2026-06-16', 'I', 'Irak vs Norja'),
        (19, '2026-06-16', 'J', 'Argentiina vs Algeria'),
        (20, '2026-06-16', 'J', 'Itävalta vs Jordania'),
        (21, '2026-06-17', 'L', 'Ghana vs Panama'),
        (22, '2026-06-17', 'L', 'Englanti vs Kroatia'),
        (23, '2026-06-17', 'K', 'Portugali vs Kongon DT'),
        (24, '2026-06-17', 'K', 'Uzbekistan vs Kolumbia'),
        (25, '2026-06-18', 'A', 'Tšekki vs Etelä-Afrikka'),
        (26, '2026-06-18', 'B', 'Sveitsi vs Bosnia'),
        (27, '2026-06-18', 'B', 'Kanada vs Qatar'),
        (28, '2026-06-18', 'A', 'Meksiko vs Etelä-Korea'),
        (29, '2026-06-19', 'C', 'Brasilia vs Haiti'),
        (30, '2026-06-19', 'C', 'Skotlanti vs Marokko'),
        (31, '2026-06-19', 'D', 'Turkki vs Paraguay'),
        (32, '2026-06-19', 'D', 'Yhdysvallat vs Australia'),
        (33, '2026-06-20', 'E', 'Saksa vs Norsunluurannikko'),
        (34, '2026-06-20', 'E', 'Ecuador vs Curaçao'),
        (35, '2026-06-20', 'F', 'Alankomaat vs Ruotsi'),
        (36, '2026-06-20', 'F', 'Tunisia vs Japani'),
        (37, '2026-06-21', 'H', 'Uruguay vs Kap Verde'),
        (38, '2026-06-21', 'H', 'Espanja vs Saudi-Arabia'),
        (39, '2026-06-21', 'G', 'Belgia vs Iran'),
        (40, '2026-06-21', 'G', 'Uusi-Seelanti vs Egypti'),
        (41, '2026-06-22', 'I', 'Norja vs Senegal'),
        (42, '2026-06-22', 'I', 'Ranska vs Irak'),
        (43, '2026-06-22', 'J', 'Argentiina vs Itävalta'),
        (44, '2026-06-22', 'J', 'Jordania vs Algeria'),
        (45, '2026-06-23', 'L', 'Englanti vs Ghana'),
        (46, '2026-06-23', 'L', 'Panama vs Kroatia'),
        (47, '2026-06-23', 'K', 'Portugali vs Uzbekistan'),
        (48, '2026-06-23', 'K', 'Kolumbia vs Kongon DT'),
        (49, '2026-06-24', 'C', 'Skotlanti vs Brasilia'),
        (50, '2026-06-24', 'C', 'Marokko vs Haiti'),
        (51, '2026-06-24', 'B', 'Sveitsi vs Kanada'),
        (52, '2026-06-24', 'B', 'Bosnia vs Qatar'),
        (53, '2026-06-24', 'A', 'Tšekki vs Meksiko'),
        (54, '2026-06-24', 'A', 'Etelä-Afrikka vs Etelä-Korea'),
        (55, '2026-06-25', 'E', 'Curaçao vs Norsunluurannikko'),
        (56, '2026-06-25', 'E', 'Ecuador vs Saksa'),
        (57, '2026-06-25', 'F', 'Japani vs Ruotsi'),
        (58, '2026-06-25', 'F', 'Tunisia vs Alankomaat'),
        (59, '2026-06-25', 'D', 'Turkki vs Yhdysvallat'),
        (60, '2026-06-25', 'D', 'Paraguay vs Australia'),
        (61, '2026-06-26', 'I', 'Norja vs Ranska'),
        (62, '2026-06-26', 'I', 'Senegal vs Irak'),
        (63, '2026-06-26', 'G', 'Egypti vs Iran'),
        (64, '2026-06-26', 'G', 'Uusi-Seelanti vs Belgia'),
        (65, '2026-06-26', 'H', 'Kap Verde vs Saudi-Arabia'),
        (66, '2026-06-26', 'H', 'Uruguay vs Espanja'),
        (67, '2026-06-27', 'L', 'Panama vs Englanti'),
        (68, '2026-06-27', 'L', 'Kroatia vs Ghana'),
        (69, '2026-06-27', 'J', 'Algeria vs Itävalta'),
        (70, '2026-06-27', 'J', 'Jordania vs Argentiina'),
        (71, '2026-06-27', 'K', 'Kolumbia vs Portugali'),
        (72, '2026-06-27', 'K', 'Kongon DT vs Uzbekistan')
) s
ON s.ID = t.ID
WHEN MATCHED AND (
        t.MATCH_DAY    <> s.MATCH_DAY
     OR t.GROUP_LETTER <> s.GROUP_LETTER
     OR t.MATCH        <> s.MATCH
   ) THEN
    UPDATE SET t.MATCH_DAY    = s.MATCH_DAY,
               t.GROUP_LETTER = s.GROUP_LETTER,
               t.MATCH        = s.MATCH
WHEN NOT MATCHED THEN
    INSERT (ID, MATCH_DAY, GROUP_LETTER, MATCH)
    VALUES (s.ID, s.MATCH_DAY, s.GROUP_LETTER, s.MATCH);

/* ── 7b. Compute pool for container-runtime Streamlit ────────────────
   The container runtime is required because Snowflake's warehouse
   runtime frontend strips st.components.v2.component (used by the
   bracket / momentum / group / team-grid pickers). XS pool, single
   node. AUTO_RESUME brings it back when a viewer hits the app.
   ──────────────────────────────────────────────────────────────────── */
CREATE COMPUTE POOL IF NOT EXISTS FIFA_VEIKKAUS_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 300
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'FIFA-veikkaus 2026 — Streamlit container compute pool';

GRANT USAGE, MONITOR ON COMPUTE POOL FIFA_VEIKKAUS_POOL
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* ── 7c. Activity log + activity-driven auto-suspend Task ────────────
   Streamlit's built-in pool auto-suspend only fires after 3 days of
   viewer inactivity, which never happens during the tournament. The
   Task below polls every 30 min: if FIFA_VEIKKAUS_ACTIVITY has no row
   in the last 60 min, it stops all services and suspends the pool.
   Auto-resume on the pool brings it back on the next viewer hit
   (cold start ≈ 60-90s).
   ──────────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS FIFA_VEIKKAUS_ACTIVITY (
    TS         TIMESTAMP_NTZ NOT NULL,
    USER_EMAIL VARCHAR
);

GRANT INSERT, SELECT ON FIFA_VEIKKAUS_ACTIVITY
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

CREATE OR REPLACE PROCEDURE FIFA_VEIKKAUS_AUTOSTOP_SP()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    last_activity TIMESTAMP_NTZ;
BEGIN
    SELECT MAX(TS) INTO :last_activity FROM FIFA_VEIKKAUS_ACTIVITY;
    IF (last_activity IS NULL OR last_activity < DATEADD(minute, -60, CURRENT_TIMESTAMP())) THEN
        EXECUTE IMMEDIATE 'ALTER COMPUTE POOL FIFA_VEIKKAUS_POOL STOP ALL';
        EXECUTE IMMEDIATE 'ALTER COMPUTE POOL FIFA_VEIKKAUS_POOL SUSPEND';
        RETURN 'suspended';
    END IF;
    RETURN 'active';
END;
$$;

CREATE OR REPLACE TASK FIFA_VEIKKAUS_AUTOSTOP_TASK
    WAREHOUSE = FIFA_VEIKKAUS_WH
    SCHEDULE = '30 MINUTE'
AS
    CALL FIFA_VEIKKAUS_AUTOSTOP_SP();

ALTER TASK FIFA_VEIKKAUS_AUTOSTOP_TASK RESUME;

/* ── 8. Streamlit app object ─────────────────────────────────────────
   Run AFTER uploading source files to FIFA_VEIKKAUS_STAGE (see AGENTS.md
   "Deploying files after changes"). Container runtime requires the FROM
   syntax (not ROOT_LOCATION) and ADD LIVE VERSION to activate the app.

   Container runtime: needs RUNTIME_NAME + COMPUTE_POOL. QUERY_WAREHOUSE
   is still used for Snowpark SQL queries (separate from the container
   compute pool, which only hosts the Streamlit process itself).

   On a fresh setup, upload the files first via PUT, then run this block.

   NOTE: CREATE STREAMLIT ... FROM copies files into an embedded versioned
   stage inside the app object. After updating source files on the stage,
   run ALTER STREAMLIT ... ADD LIVE VERSION FROM LAST to pick up changes.
   ──────────────────────────────────────────────────────────────────── */
CREATE STREAMLIT IF NOT EXISTS FIFA_VEIKKAUS_APP
    FROM '@STREAMLIT_APPS.FIFA_VEIKKAUS.FIFA_VEIKKAUS_STAGE'
    MAIN_FILE     = 'streamlit_app.py'
    RUNTIME_NAME  = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
    COMPUTE_POOL  = FIFA_VEIKKAUS_POOL
    QUERY_WAREHOUSE = 'FIFA_VEIKKAUS_WH'
    COMMENT = 'FIFA-veikkaus 2026 — production app (container runtime)';

ALTER STREAMLIT FIFA_VEIKKAUS_APP ADD LIVE VERSION FROM LAST;

GRANT USAGE ON STREAMLIT FIFA_VEIKKAUS_APP
    TO ROLE FIFA_VEIKKAUS_PLAYER_ROLE;

/* ── 9. Grant the roles to real humans ────────────────────────────────
   Customise to the participating accounts. The role-as-default makes
   the SiS app open under the right role automatically.
   ──────────────────────────────────────────────────────────────────── */
-- GRANT ROLE FIFA_VEIKKAUS_ADMIN_ROLE  TO USER "MIKA.HEINO";
-- ALTER USER "MIKA.HEINO" SET DEFAULT_ROLE = FIFA_VEIKKAUS_ADMIN_ROLE;
--
-- GRANT ROLE FIFA_VEIKKAUS_PLAYER_ROLE TO USER "PLAYER.ONE";
-- ALTER USER "PLAYER.ONE" SET DEFAULT_ROLE = FIFA_VEIKKAUS_PLAYER_ROLE;
-- ... etc.

/* ── 10. Sanity checks ────────────────────────────────────────────────
   All should return the expected counts after a successful bootstrap.
   ──────────────────────────────────────────────────────────────────── */
SELECT 'schedule rows (expect 72)' AS check_name, COUNT(*) AS n
FROM FIFA_VEIKKAUS_SCHEDULE
UNION ALL
SELECT 'distinct match days (expect 17)', COUNT(DISTINCT MATCH_DAY)
FROM FIFA_VEIKKAUS_SCHEDULE
UNION ALL
SELECT 'distinct groups (expect 12)', COUNT(DISTINCT GROUP_LETTER)
FROM FIFA_VEIKKAUS_SCHEDULE
UNION ALL
SELECT 'results rows (expect 0 on fresh setup)', COUNT(*)
FROM FIFA_VEIKKAUS_RESULTS;
