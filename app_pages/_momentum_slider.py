"""Trophy-drag momentum slider — CCv2 component for single-match score picking.

Drag the trophy thumb left (away wins) or right (home wins). 21 discrete stops
map to a curated score grid: 0-10 ... 0-1, 0-0 (draw), 1-0 ... 10-0.

The component writes its picked score to ``st.session_state[key].score`` as a
dict ``{"home": int, "away": int}`` whenever the user releases the thumb.
"""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st

_HTML = """<div class="mom-root">
  <div class="mom-teams">
    <span class="mom-home"></span>
    <span class="mom-score">—</span>
    <span class="mom-away"></span>
  </div>
  <div class="mom-track">
    <div class="mom-fill"></div>
    <div class="mom-ticks"></div>
    <button class="mom-thumb" type="button" aria-label="raahaa pokaalia">🏆</button>
  </div>
</div>"""

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Bungee&display=swap');

.mom-root {
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
.mom-teams {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.mom-home { text-align: left;  flex: 1; color: #ffd95c; text-shadow: 2px 2px 0 #1a1408; }
.mom-away { text-align: right; flex: 1; color: #ffd95c; text-shadow: 2px 2px 0 #1a1408; }
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
.mom-thumb {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
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
  animation: mom-trophy-glow 1.4s ease-in-out infinite alternate;
}
@keyframes mom-trophy-glow {
  0%   { filter: drop-shadow(0 0 2px #ffd95c) drop-shadow(0 0 6px rgba(255,126,28,0.55)); }
  100% { filter: drop-shadow(0 0 5px #ffd95c) drop-shadow(0 0 14px rgba(255,126,28,0.95)); }
}
.mom-thumb:active { cursor: grabbing; }
.mom-thumb:focus { outline: 2px solid #ff7e1c; outline-offset: 4px; }
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component;

  // 21 stops: away by 10 → draw (1-1) → home by 10.
  const MAX_DIFF = 10;
  const N = 2 * MAX_DIFF + 1;
  const DRAW_IDX = MAX_DIFF;
  const POSITIONS = Array.from({ length: N }, (_, i) => {
    const diff = i - MAX_DIFF;
    if (diff === 0) return { home: 0, away: 0 };
    if (diff > 0) return { home: diff, away: 0 };
    return { home: 0, away: -diff };
  });

  // First-mount setup: populate team names and tick marks.
  if (!parentElement._mom_initialized) {
    parentElement._mom_initialized = true;
    const homeEl = parentElement.querySelector(".mom-home");
    const awayEl = parentElement.querySelector(".mom-away");
    homeEl.textContent = data?.home_team ?? "";
    awayEl.textContent = data?.away_team ?? "";
    // Render 5 reference ticks (0%, 25%, 50%, 75%, 100%) — not one per stop.
    const ticks = parentElement.querySelector(".mom-ticks");
    for (let i = 0; i < 5; i++) ticks.appendChild(document.createElement("span"));
  }

  const track = parentElement.querySelector(".mom-track");
  const thumb = parentElement.querySelector(".mom-thumb");
  const scoreEl = parentElement.querySelector(".mom-score");
  const fillEl = parentElement.querySelector(".mom-fill");

  function scoreToIdx(s) {
    if (!s || s.home == null || s.away == null) return null;
    const diff = s.home - s.away;
    if (diff === 0) return DRAW_IDX;
    return Math.max(0, Math.min(N - 1, DRAW_IDX + diff));
  }

  // Hydrate from Python data on every run; only overwrite local UI if not dragging.
  let idx = scoreToIdx(data?.score);

  function paint(i) {
    if (i == null) {
      thumb.style.left = "50%";
      fillEl.style.left = "50%";
      fillEl.style.width = "0%";
      scoreEl.textContent = "—";
      scoreEl.classList.add("unset");
      return;
    }
    const pct = (i / (N - 1)) * 100;
    thumb.style.left = `${pct}%`;
    // Fill grows outward from the 50% midpoint toward the thumb side.
    if (pct >= 50) {
      fillEl.style.left = "50%";
      fillEl.style.width = `${pct - 50}%`;
    } else {
      fillEl.style.left = `${pct}%`;
      fillEl.style.width = `${50 - pct}%`;
    }
    const s = POSITIONS[i];
    scoreEl.textContent = `${s.home} – ${s.away}`;
    scoreEl.classList.remove("unset");
  }

  if (!parentElement._mom_dragging) paint(idx);

  function xToIdx(clientX) {
    const r = track.getBoundingClientRect();
    let t = (clientX - r.left) / r.width;
    t = Math.max(0, Math.min(1, t));
    return Math.round(t * (N - 1));
  }

  function commit(newIdx) {
    idx = newIdx;
    paint(idx);
    setStateValue("score", POSITIONS[idx]);
  }

  // Attach handlers fresh each run (idempotent — we overwrite the same props).
  thumb.onpointerdown = (e) => {
    parentElement._mom_dragging = true;
    try { thumb.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  };
  thumb.onpointermove = (e) => {
    if (!parentElement._mom_dragging) return;
    const next = xToIdx(e.clientX);
    idx = next;
    paint(idx);
  };
  thumb.onpointerup = (e) => {
    if (!parentElement._mom_dragging) return;
    parentElement._mom_dragging = false;
    try { thumb.releasePointerCapture(e.pointerId); } catch (_) {}
    commit(idx);
  };
  thumb.onkeydown = (e) => {
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
      commit(Math.max(0, (idx ?? DRAW_IDX) - 1));
      e.preventDefault();
    } else if (e.key === "ArrowRight" || e.key === "ArrowUp") {
      commit(Math.min(N - 1, (idx ?? DRAW_IDX) + 1));
      e.preventDefault();
    } else if (e.key === "Home") {
      commit(0);
      e.preventDefault();
    } else if (e.key === "End") {
      commit(N - 1);
      e.preventDefault();
    }
  };
  track.onclick = (e) => {
    if (e.target === thumb) return;
    commit(xToIdx(e.clientX));
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
    default_score: tuple[int, int] | None = None,
    on_change: Callable[[], None] | None = None,
) -> tuple[int, int] | None:
    """Render one match-prediction trophy slider. Returns the picked score or None."""
    key = f"mom_{match_id}"
    score_payload = (
        {"home": int(default_score[0]), "away": int(default_score[1])}
        if default_score is not None
        else None
    )
    result = _MOM_COMPONENT(
        key=key,
        data={
            "home_team": home_team,
            "away_team": away_team,
            "score": score_payload,
        },
        on_score_change=on_change or (lambda: None),
    )
    score = getattr(result, "score", None)
    if isinstance(score, dict) and "home" in score and "away" in score:
        return (int(score["home"]), int(score["away"]))
    return None
