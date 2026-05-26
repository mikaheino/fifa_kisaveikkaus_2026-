"""Two-thumb football slider — CCv2 component for single-match score picking.

One horizontal track with a kickoff line at center. Each team gets its own
``⚽`` thumb: home drags leftward (0–10 goals), away drags rightward (0–10
goals). Both can reach 10 independently, so 10–10 is a valid pick.

The component writes its picked score to ``st.session_state[key].score`` as a
dict ``{"home": int, "away": int}`` whenever a thumb is released.

Each end of the slider box renders the team's flag as a Twemoji SVG fading
toward center. Flags live in ``assets/flags/<iso2>.svg`` and are loaded as
base64 at module import time (Snowflake CSP blocks external URLs).
"""
from __future__ import annotations

import base64
import os
from collections.abc import Callable

import streamlit as st

from schedule_data import FLAGS as _FLAGS

_FLAGS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "flags")

# Subnational flags whose emoji is a tag sequence rather than two Regional
# Indicator Symbols — handled by hardcoded ISO codes.
_TAG_FLAG_ISO = {
    "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f": "gb-sct",  # Scotland
    "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f": "gb-eng",  # England
}


def _emoji_to_iso2(flag: str) -> str:
    """🇲🇽 → 'mx'. Returns "" if emoji isn't a regional-indicator pair."""
    if flag in _TAG_FLAG_ISO:
        return _TAG_FLAG_ISO[flag]
    if len(flag) < 2:
        return ""
    a = ord(flag[0]) - 0x1F1E6
    b = ord(flag[1]) - 0x1F1E6
    if not (0 <= a < 26 and 0 <= b < 26):
        return ""
    return chr(ord("a") + a) + chr(ord("a") + b)


# Flat flags whose three equal horizontal bands get cropped to a single color
# by ``background-size: cover``. Horizontal stripes are immune to horizontal
# stretching (a third stays a third), so these stretch-fill the box end
# instead. Other flags (incl. Spain, whose emblem must NOT be stretched) keep
# the default ``cover`` render.
_STRETCH_FILL_ISO = {"de", "at"}


def _load_flag_b64(iso: str) -> str:
    """Return base64-encoded SVG for the given ISO code, or '' if missing."""
    if not iso:
        return ""
    p = os.path.join(_FLAGS_DIR, f"{iso}.svg")
    if not os.path.exists(p):
        return ""
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


# Finnish team name → base64 SVG. Built once at import. Missing flags map to
# "" so the slider falls back to a flag-less render gracefully.
_FLAG_B64_BY_TEAM: dict[str, str] = {
    team_fi: _load_flag_b64(_emoji_to_iso2(emoji))
    for team_fi, emoji in _FLAGS.items()
}

# Finnish team name → "stretch" | "cover" background-fit hint for the flag.
_FLAG_FIT_BY_TEAM: dict[str, str] = {
    team_fi: ("stretch" if _emoji_to_iso2(emoji) in _STRETCH_FILL_ISO else "cover")
    for team_fi, emoji in _FLAGS.items()
}


def flag_b64_for(team_fi: str) -> str:
    """Public helper for callers that want to pass the flag explicitly."""
    return _FLAG_B64_BY_TEAM.get(team_fi, "")


def flag_fit_for(team_fi: str) -> str:
    """Background-size hint ('stretch' or 'cover') for a team's flag."""
    return _FLAG_FIT_BY_TEAM.get(team_fi, "cover")

_HTML = """<div class="mom-root">
  <div class="mom-flag mom-flag-home"></div>
  <div class="mom-flag mom-flag-away"></div>
  <div class="mom-teams">
    <span class="mom-home"></span>
    <span class="mom-score">—</span>
    <span class="mom-away"></span>
  </div>
  <div class="mom-track">
    <div class="mom-fill mom-fill-home"></div>
    <div class="mom-fill mom-fill-away"></div>
    <div class="mom-ticks"></div>
    <div class="mom-kickoff"></div>
    <button class="mom-thumb mom-thumb-home" type="button" aria-label="raahaa kotijoukkueen jalkapalloa">⚽</button>
    <button class="mom-thumb mom-thumb-away" type="button" aria-label="raahaa vierasjoukkueen jalkapalloa">⚽</button>
  </div>
</div>"""

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Bungee&display=swap');

.mom-root {
  position: relative;
  overflow: hidden;
  font-family: 'Bungee', 'Impact', sans-serif;
  color: #f5e8c8;
  padding: 10px 8px 14px;
  background:
    linear-gradient(180deg, #0a1f12 0%, #061308 100%);
  border: 2px solid #f5c842;
  box-shadow:
    4px 4px 0 #000,
    inset 0 0 0 1px rgba(0,0,0,0.7),
    inset 0 2px 0 rgba(255,230,180,0.18);
  margin-bottom: 12px;
}
.mom-flag {
  position: absolute;
  top: 0; bottom: 0;
  width: 50%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
  z-index: 0;
}
.mom-flag-home {
  left: 0;
  -webkit-mask-image: linear-gradient(90deg, #000 0%, #000 40%, transparent 100%);
          mask-image: linear-gradient(90deg, #000 0%, #000 40%, transparent 100%);
}
.mom-flag-away {
  right: 0;
  -webkit-mask-image: linear-gradient(270deg, #000 0%, #000 40%, transparent 100%);
          mask-image: linear-gradient(270deg, #000 0%, #000 40%, transparent 100%);
}
.mom-teams {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
/* Heavy drop-shadow so team names stay legible on bright/light flag areas
   (yellow on Germany, white stripes on USA, etc.). */
.mom-home, .mom-away {
  flex: 1;
  color: #ffd95c;
  text-shadow:
    0 0 6px rgba(0,0,0,0.95),
    0 0 12px rgba(0,0,0,0.85),
    2px 2px 0 #1a1408;
}
.mom-home { text-align: left; }
.mom-away { text-align: right; }
.mom-score {
  font-family: 'VT323', 'Courier New', monospace;
  background: #0a0a0a;
  color: #ff7e1c;
  font-weight: 400;
  padding: 2px 16px;
  font-variant-numeric: tabular-nums;
  font-size: 1.7rem;
  letter-spacing: 4px;
  line-height: 1;
  border: 2px solid #4a3010;
  text-shadow:
    0 0 4px #ff7e1c,
    0 0 8px rgba(255,126,28,0.6);
  box-shadow:
    inset 0 0 8px rgba(0,0,0,0.95),
    inset 0 2px 0 rgba(255,126,28,0.1),
    0 0 6px rgba(255,126,28,0.25);
  min-width: 88px;
  text-align: center;
}
.mom-score.unset { color: #553a18; text-shadow: none; box-shadow: inset 0 0 8px rgba(0,0,0,0.95); }
.mom-track {
  position: relative;
  z-index: 1;
  height: 20px;
  background: #050505;
  margin: 0 22px;
  cursor: pointer;
  border: 2px solid #f5c842;
  box-shadow:
    inset 0 2px 0 rgba(0,0,0,0.85),
    inset 0 -2px 0 rgba(245,200,80,0.35),
    3px 3px 0 rgba(0,0,0,0.85);
  touch-action: none;
}
.mom-fill {
  position: absolute;
  top: 0; bottom: 0;
  background:
    repeating-linear-gradient(
      90deg,
      #ff7e1c 0px, #ff7e1c 6px,
      #ffd95c 6px, #ffd95c 12px
    );
  pointer-events: none;
  box-shadow: 0 0 8px rgba(255,126,28,0.6);
}
.mom-ticks {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: space-between;
  padding: 0;
  pointer-events: none;
}
.mom-ticks span {
  width: 2px;
  background: rgba(0,0,0,0.85);
  box-shadow: 1px 0 0 rgba(245,232,200,0.3);
}
.mom-kickoff {
  position: absolute;
  top: -4px;
  bottom: -4px;
  left: 50%;
  width: 2px;
  margin-left: -1px;
  background: rgba(245,232,200,0.85);
  box-shadow:
    0 0 4px rgba(255,230,180,0.6),
    0 0 8px rgba(255,126,28,0.35);
  pointer-events: none;
}
.mom-thumb {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 38px;
  height: 38px;
  border: none;
  background: transparent;
  font-size: 1.7rem;
  line-height: 1;
  padding: 0;
  cursor: grab;
  touch-action: none;
  user-select: none;
  filter:
    drop-shadow(0 0 3px #ffd95c)
    drop-shadow(0 0 8px rgba(255,126,28,0.7));
  text-shadow: 2px 2px 0 #000;
  animation: mom-ball-glow 1.4s ease-in-out infinite alternate;
}
/* Nudge the resting (0–0) thumbs ~14px away from the kickoff line so they
   never overlap at center. The translate keeps them visually offset from
   their nominal track position. */
.mom-thumb-home { transform: translate(calc(-50% - 14px), -50%); }
.mom-thumb-away { transform: translate(calc(-50% + 14px), -50%); }
@keyframes mom-ball-glow {
  0%   { filter: drop-shadow(0 0 2px #ffd95c) drop-shadow(0 0 6px rgba(255,126,28,0.55)); }
  100% { filter: drop-shadow(0 0 5px #ffd95c) drop-shadow(0 0 14px rgba(255,126,28,0.95)); }
}
.mom-thumb:active { cursor: grabbing; }
.mom-thumb:focus { outline: 2px solid #ff7e1c; outline-offset: 4px; }
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component;

  // Counter live-updates: every commit also broadcasts so the floating
  // progress counter recounts client-side (no Python rerun needed).
  function broadcast(filled) {
    try {
      const bc = new BroadcastChannel('fifa-picks');
      bc.postMessage({
        type: 'match',
        id: Number(data?.match_id),
        filled: !!filled,
      });
      bc.close();
    } catch (_) {}
  }

  // Two independent thumbs, each with 11 stops (0..10). Home thumb extends
  // leftward from the kickoff line, away thumb extends rightward. Both can
  // independently reach 10, so 10–10 is reachable.
  const MAX = 10;

  // First-mount setup: populate team names, flag backgrounds, and tick marks.
  if (!parentElement._mom_initialized) {
    parentElement._mom_initialized = true;
    const homeEl = parentElement.querySelector(".mom-home");
    const awayEl = parentElement.querySelector(".mom-away");
    homeEl.textContent = data?.home_team ?? "";
    awayEl.textContent = data?.away_team ?? "";
    // Flag backgrounds (base64 SVG passed from Python). Skip if empty so we
    // don't render a broken image for teams without a bundled flag.
    const homeFlag = parentElement.querySelector(".mom-flag-home");
    const awayFlag = parentElement.querySelector(".mom-flag-away");
    // Stretch flags (equal horizontal-band flags like DE/AT) fill the box
    // end edge-to-center: 100% 100% scaling plus a mask that stays solid most
    // of the way and fades only near the kickoff line, so the full tricolor
    // reads clearly instead of fading out at 40%.
    const STRETCH_MASK_HOME = "linear-gradient(90deg, #000 0%, #000 80%, transparent 100%)";
    const STRETCH_MASK_AWAY = "linear-gradient(270deg, #000 0%, #000 80%, transparent 100%)";
    if (data?.home_flag_b64) {
      homeFlag.style.backgroundImage = `url("data:image/svg+xml;base64,${data.home_flag_b64}")`;
      if (data?.home_flag_fit === "stretch") {
        homeFlag.style.backgroundSize = "100% 100%";
        homeFlag.style.webkitMaskImage = STRETCH_MASK_HOME;
        homeFlag.style.maskImage = STRETCH_MASK_HOME;
      }
    }
    if (data?.away_flag_b64) {
      awayFlag.style.backgroundImage = `url("data:image/svg+xml;base64,${data.away_flag_b64}")`;
      if (data?.away_flag_fit === "stretch") {
        awayFlag.style.backgroundSize = "100% 100%";
        awayFlag.style.webkitMaskImage = STRETCH_MASK_AWAY;
        awayFlag.style.maskImage = STRETCH_MASK_AWAY;
      }
    }
    // Render 5 reference ticks (0%, 25%, 50%, 75%, 100%).
    const ticks = parentElement.querySelector(".mom-ticks");
    for (let i = 0; i < 5; i++) ticks.appendChild(document.createElement("span"));
  }

  const track = parentElement.querySelector(".mom-track");
  const homeThumb = parentElement.querySelector(".mom-thumb-home");
  const awayThumb = parentElement.querySelector(".mom-thumb-away");
  const homeFill = parentElement.querySelector(".mom-fill-home");
  const awayFill = parentElement.querySelector(".mom-fill-away");
  const scoreEl = parentElement.querySelector(".mom-score");

  // Hydrate from Python data. A null/missing score means "untouched" and the
  // display stays as "—" even though both thumbs render at center.
  let homeIdx = 0;
  let awayIdx = 0;
  let touched = false;
  if (data?.score && data.score.home != null && data.score.away != null) {
    homeIdx = Math.max(0, Math.min(MAX, Number(data.score.home) | 0));
    awayIdx = Math.max(0, Math.min(MAX, Number(data.score.away) | 0));
    touched = true;
  }

  function paint() {
    // Home thumb track position: 0% (idx=MAX) … 50% (idx=0). Symmetric for away.
    const homePct = (1 - homeIdx / MAX) * 50;
    const awayPct = 50 + (awayIdx / MAX) * 50;
    homeThumb.style.left = `${homePct}%`;
    awayThumb.style.left = `${awayPct}%`;
    // Home fill grows leftward from kickoff (50%) to home thumb.
    homeFill.style.left = `${homePct}%`;
    homeFill.style.width = `${50 - homePct}%`;
    // Away fill grows rightward from kickoff (50%) to away thumb.
    awayFill.style.left = "50%";
    awayFill.style.width = `${awayPct - 50}%`;
    if (!touched) {
      scoreEl.textContent = "—";
      scoreEl.classList.add("unset");
    } else {
      scoreEl.textContent = `${homeIdx} – ${awayIdx}`;
      scoreEl.classList.remove("unset");
    }
  }

  if (!parentElement._mom_dragging_home && !parentElement._mom_dragging_away) {
    paint();
  }

  function xToHomeIdx(clientX) {
    const r = track.getBoundingClientRect();
    let t = (clientX - r.left) / r.width;
    t = Math.max(0, Math.min(0.5, t));
    // t in [0, 0.5] → idx in [MAX, 0]
    return Math.round((0.5 - t) * 2 * MAX);
  }

  function xToAwayIdx(clientX) {
    const r = track.getBoundingClientRect();
    let t = (clientX - r.left) / r.width;
    t = Math.max(0.5, Math.min(1, t));
    // t in [0.5, 1] → idx in [0, MAX]
    return Math.round((t - 0.5) * 2 * MAX);
  }

  function commit() {
    touched = true;
    paint();
    setStateValue("score", { home: homeIdx, away: awayIdx });
    broadcast(true);
  }

  // ── Home thumb drag ─────────────────────────────────────────────────────
  homeThumb.onpointerdown = (e) => {
    parentElement._mom_dragging_home = true;
    try { homeThumb.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  };
  homeThumb.onpointermove = (e) => {
    if (!parentElement._mom_dragging_home) return;
    homeIdx = xToHomeIdx(e.clientX);
    touched = true;
    paint();
  };
  homeThumb.onpointerup = (e) => {
    if (!parentElement._mom_dragging_home) return;
    parentElement._mom_dragging_home = false;
    try { homeThumb.releasePointerCapture(e.pointerId); } catch (_) {}
    commit();
  };
  homeThumb.onkeydown = (e) => {
    // Left/down = more home goals (thumb slides further left).
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      homeIdx = Math.min(MAX, homeIdx + 1);
      commit();
      e.preventDefault();
    } else if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      homeIdx = Math.max(0, homeIdx - 1);
      commit();
      e.preventDefault();
    } else if (e.key === "Home") {
      homeIdx = 0;
      commit();
      e.preventDefault();
    } else if (e.key === "End") {
      homeIdx = MAX;
      commit();
      e.preventDefault();
    }
  };

  // ── Away thumb drag ─────────────────────────────────────────────────────
  awayThumb.onpointerdown = (e) => {
    parentElement._mom_dragging_away = true;
    try { awayThumb.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  };
  awayThumb.onpointermove = (e) => {
    if (!parentElement._mom_dragging_away) return;
    awayIdx = xToAwayIdx(e.clientX);
    touched = true;
    paint();
  };
  awayThumb.onpointerup = (e) => {
    if (!parentElement._mom_dragging_away) return;
    parentElement._mom_dragging_away = false;
    try { awayThumb.releasePointerCapture(e.pointerId); } catch (_) {}
    commit();
  };
  awayThumb.onkeydown = (e) => {
    // Right/up = more away goals.
    if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      awayIdx = Math.min(MAX, awayIdx + 1);
      commit();
      e.preventDefault();
    } else if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      awayIdx = Math.max(0, awayIdx - 1);
      commit();
      e.preventDefault();
    } else if (e.key === "Home") {
      awayIdx = 0;
      commit();
      e.preventDefault();
    } else if (e.key === "End") {
      awayIdx = MAX;
      commit();
      e.preventDefault();
    }
  };

  // Click on the track (not on a thumb) jumps the nearer thumb to that point.
  track.onclick = (e) => {
    if (e.target === homeThumb || e.target === awayThumb) return;
    const r = track.getBoundingClientRect();
    const t = (e.clientX - r.left) / r.width;
    if (t < 0.5) {
      homeIdx = xToHomeIdx(e.clientX);
    } else {
      awayIdx = xToAwayIdx(e.clientX);
    }
    commit();
  };
}
"""

_MOM_COMPONENT = st.components.v2.component(
    "fifa_momentum_slider",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def momentum_slider(
    *,
    match_id: int,
    home_team: str,
    away_team: str,
    home_flag_b64: str | None = None,
    away_flag_b64: str | None = None,
    default_score: tuple[int, int] | None = None,
    on_change: Callable[[], None] | None = None,
) -> tuple[int, int] | None:
    """Render one match-prediction football slider. Returns the picked score or None.

    Pass plain team names (no emoji prefix); the giant flag in each end of
    the box visually replaces the emoji. ``home_flag_b64`` / ``away_flag_b64``
    are base64-encoded SVG strings — when omitted, the slider falls back to
    :func:`flag_b64_for` to look them up by Finnish team name.
    """
    if home_flag_b64 is None:
        home_flag_b64 = flag_b64_for(home_team)
    if away_flag_b64 is None:
        away_flag_b64 = flag_b64_for(away_team)
    home_flag_fit = flag_fit_for(home_team)
    away_flag_fit = flag_fit_for(away_team)
    key = f"mom_{match_id}"
    # On reruns the user's most recent pick lives in session_state[key].score —
    # that's the source of truth and must be fed back as `data` so the slider
    # doesn't visually snap back to the original DB default after a rerun.
    prior = st.session_state.get(key)
    prior_score = getattr(prior, "score", None) if prior is not None else None
    if isinstance(prior_score, dict) and "home" in prior_score and "away" in prior_score:
        score_payload = {
            "home": int(prior_score["home"]),
            "away": int(prior_score["away"]),
        }
    elif default_score is not None:
        score_payload = {"home": int(default_score[0]), "away": int(default_score[1])}
    else:
        score_payload = None
    result = _MOM_COMPONENT(
        key=key,
        data={
            "match_id": int(match_id),
            "home_team": home_team,
            "away_team": away_team,
            "home_flag_b64": home_flag_b64 or "",
            "away_flag_b64": away_flag_b64 or "",
            "home_flag_fit": home_flag_fit,
            "away_flag_fit": away_flag_fit,
            "score": score_payload,
        },
        on_score_change=on_change or (lambda: None),
    )
    score = getattr(result, "score", None)
    if isinstance(score, dict) and "home" in score and "away" in score:
        return (int(score["home"]), int(score["away"]))
    return None
