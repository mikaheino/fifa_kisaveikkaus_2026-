"""Visual playoff-bracket picker — CCv2 component.

6 columns left-to-right: R32 → R16 → QF → SF → Final → Champion. Click any
chip to toggle its advancement to the next column (caps enforced: 16, 8, 4,
2, 1). Advanced chips glow gold; chips that didn't advance stay dim. A chip
appears in every column it has reached, so the user reads the whole bracket
in one glance.

State written to ``st.session_state[key].picks`` as
``{"r16": [...], "qf": [...], "sf": [...], "finalists": [...], "champion": str | None}``.
"""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st

_HTML = """<div class="bp-root">
  <div class="bp-grid"></div>
  <div class="bp-hint">Klikkaa joukkuetta nostaaksesi seuraavaan vaiheeseen. Klikkaa uudelleen pudottaaksesi. Jokainen kierros tarvitsee kaksi joukkuetta per ottelu seuraavalle kierrokselle.</div>
</div>"""

_CSS = """
.bp-root {
  color: #f5e8c8;
  font-family: 'Roboto', Arial, sans-serif;
  padding: 8px 0;
}
.bp-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
  align-items: start;
}
.bp-col {
  background: rgba(30, 20, 8, 0.45);
  border: 1px solid rgba(245, 200, 80, 0.18);
  box-shadow: inset 1px 1px rgba(0,0,0,0.55), inset -1px -1px rgba(245,200,80,0.15);
  padding: 6px 4px 8px;
  min-height: 80px;
}
.bp-col-title {
  text-align: center;
  font-weight: 700;
  font-size: 0.78rem;
  color: #d4b878;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(245, 200, 80, 0.25);
  padding-bottom: 4px;
}
.bp-col-title .bp-count {
  display: block;
  font-size: 0.7rem;
  font-weight: 400;
  color: #aa9466;
  letter-spacing: 0;
  text-transform: none;
}
.bp-col.bp-full .bp-col-title .bp-count { color: #5fc879; }
.bp-chips {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.bp-chip {
  display: block;
  width: 100%;
  text-align: left;
  font-family: inherit;
  font-size: 0.78rem;
  line-height: 1.15;
  padding: 5px 6px;
  border: none;
  border-radius: 0;
  background: rgba(60, 42, 18, 0.85);
  color: #d4b878;
  cursor: pointer;
  box-shadow: inset 1px 1px rgba(0,0,0,0.5), inset -1px -1px rgba(245,200,80,0.2);
  transition: background 0.1s, color 0.1s, box-shadow 0.1s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bp-chip:hover {
  background: rgba(100, 70, 25, 0.95);
  color: #f5e8c8;
}
.bp-chip.advanced {
  background: rgba(180, 130, 35, 0.95);
  color: #1a1408;
  font-weight: 700;
  box-shadow:
    inset 1px 1px rgba(255,230,180,0.7),
    inset -1px -1px rgba(80,50,15,0.85),
    0 0 6px rgba(245, 200, 80, 0.55);
}
.bp-chip.advanced:hover { background: rgba(220, 165, 45, 0.95); }
.bp-chip.terminal { cursor: default; }
.bp-chip.terminal:hover { background: rgba(180, 130, 35, 0.95); color: #1a1408; }
.bp-chip.flash {
  animation: bp-flash 0.32s ease-out;
}
@keyframes bp-flash {
  0% { background: rgba(170, 60, 40, 0.95); transform: translateX(0); }
  20% { transform: translateX(-3px); }
  40% { transform: translateX(3px); }
  60% { transform: translateX(-2px); }
  80% { transform: translateX(2px); }
  100% { transform: translateX(0); }
}
.bp-chip.entering {
  animation: bp-slide-in 0.32s cubic-bezier(0.18, 0.89, 0.32, 1.28) both;
}
@keyframes bp-slide-in {
  0%   { opacity: 0; transform: translateX(-14px) scale(0.85); }
  60%  { opacity: 1; transform: translateX(2px)   scale(1.04); }
  100% { opacity: 1; transform: translateX(0)     scale(1); }
}
.bp-chip.pulse {
  animation: bp-pulse 0.45s ease-out;
}
@keyframes bp-pulse {
  0%   { transform: scale(1);    filter: brightness(1)   drop-shadow(0 0 0 rgba(245,200,80,0)); }
  40%  { transform: scale(1.07); filter: brightness(1.25) drop-shadow(0 0 8px rgba(245,200,80,0.85)); }
  100% { transform: scale(1);    filter: brightness(1)   drop-shadow(0 0 0 rgba(245,200,80,0)); }
}
.bp-chip.champion-bob {
  animation: bp-bob 0.9s ease-out;
}
@keyframes bp-bob {
  0%   { transform: translateY(0)    scale(1); }
  20%  { transform: translateY(-7px) scale(1.10); }
  40%  { transform: translateY(0)    scale(1); }
  55%  { transform: translateY(-3px) scale(1.04); }
  70%  { transform: translateY(0)    scale(1); }
  100% { transform: translateY(0)    scale(1); }
}
.bp-col { position: relative; overflow: hidden; }
.bp-confetti-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
}
.bp-confetti {
  position: absolute;
  left: 50%;
  top: 32%;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  opacity: 0;
  animation: bp-burst 0.95s cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
}
@keyframes bp-burst {
  0%   { opacity: 1; transform: translate(-50%, -50%) scale(0.4); }
  15%  { opacity: 1; }
  100% {
    opacity: 0;
    transform:
      translate(calc(-50% + var(--dx)), calc(-50% + var(--dy)))
      scale(1.1) rotate(var(--rot));
  }
}
.bp-hint {
  text-align: center;
  font-size: 0.72rem;
  color: #aa9466;
  margin-top: 8px;
}
.bp-empty {
  text-align: center;
  font-size: 0.7rem;
  color: #7a6244;
  padding: 12px 4px;
  font-style: italic;
}
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component;

  // Stages: 0=R32 (input pool), 1=R16, 2=QF, 3=SF, 4=Final, 5=Champion
  const STAGES = [
    { id: 0, label: "R32", cap: 32, key: null },
    { id: 1, label: "R16", cap: 16, key: "r16" },
    { id: 2, label: "QF",  cap: 8,  key: "qf" },
    { id: 3, label: "SF",  cap: 4,  key: "sf" },
    { id: 4, label: "Final", cap: 2, key: "finalists" },
    { id: 5, label: "🏆",   cap: 1,  key: "champion_list" },
  ];

  const teamsR32 = Array.isArray(data?.teams_r32) ? [...data.teams_r32] : [];
  const teamLabels = (data && typeof data.team_labels === "object" && data.team_labels) || {};
  const labelFor = (t) => teamLabels[t] || t;

  // Local mutable state per non-R32 stage; preserves user-chosen order.
  const initialPicks = data?.picks ?? {};
  const state = {
    1: Array.isArray(initialPicks.r16) ? initialPicks.r16.filter((t) => teamsR32.includes(t)) : [],
    2: Array.isArray(initialPicks.qf)  ? initialPicks.qf.filter((t) => teamsR32.includes(t))  : [],
    3: Array.isArray(initialPicks.sf)  ? initialPicks.sf.filter((t) => teamsR32.includes(t))  : [],
    4: Array.isArray(initialPicks.finalists) ? initialPicks.finalists.filter((t) => teamsR32.includes(t)) : [],
    5: initialPicks.champion && teamsR32.includes(initialPicks.champion) ? [initialPicks.champion] : [],
  };

  // Enforce nested-subset invariant: state[L+1] ⊆ state[L].
  for (let L = 2; L <= 5; L++) {
    state[L] = state[L].filter((t) => state[L - 1].includes(t));
  }

  const grid = parentElement.querySelector(".bp-grid");

  function listForStage(s) {
    if (s === 0) return teamsR32;
    return state[s];
  }

  function isAdvanced(team, stage) {
    if (stage === 5) return true; // champion is terminal
    return state[stage + 1].includes(team);
  }

  // Per-column previous lists survive across reruns so we can detect which
  // chips are newly added and animate only those (not every existing chip).
  if (!parentElement._bp_prev) parentElement._bp_prev = {0: null, 1: [], 2: [], 3: [], 4: [], 5: []};

  function render() {
    grid.innerHTML = "";
    STAGES.forEach((stage) => {
      const list = listForStage(stage.id);
      const prev = parentElement._bp_prev[stage.id];
      const prevSet = new Set(prev || []);
      // First-render of column 0 (R32 input pool): don't slide-in every team;
      // only the truly new ones across subsequent renders should animate.
      const firstRender = prev === null;

      const col = document.createElement("div");
      col.className = "bp-col";
      col.dataset.stageId = String(stage.id);
      if (stage.id > 0 && list.length === stage.cap) col.classList.add("bp-full");

      const title = document.createElement("div");
      title.className = "bp-col-title";
      const cnt =
        stage.id === 0
          ? `${list.length}`
          : `${list.length} / ${stage.cap}`;
      title.innerHTML = `${stage.label}<span class="bp-count">${cnt}</span>`;
      col.appendChild(title);

      const chips = document.createElement("div");
      chips.className = "bp-chips";
      if (list.length === 0 && stage.id > 0) {
        const empty = document.createElement("div");
        empty.className = "bp-empty";
        empty.textContent = "—";
        chips.appendChild(empty);
      } else {
        list.forEach((team, i) => {
          const chip = document.createElement("button");
          chip.type = "button";
          chip.className = "bp-chip";
          chip.dataset.team = team;
          chip.dataset.stage = String(stage.id);
          chip.textContent = labelFor(team);
          chip.title = labelFor(team);
          if (isAdvanced(team, stage.id)) chip.classList.add("advanced");
          if (stage.id === 5) chip.classList.add("terminal");
          if (!firstRender && !prevSet.has(team)) {
            chip.classList.add("entering");
            chip.style.animationDelay = `${i * 30}ms`;
          }
          chip.onclick = (e) => handleClick(team, stage.id, chip);
          chips.appendChild(chip);
        });
      }
      col.appendChild(chips);

      // Confetti burst on first time a champion appears in stage 5.
      if (stage.id === 5 && !firstRender && list.length === 1 && (!prev || prev.length === 0)) {
        const layer = document.createElement("div");
        layer.className = "bp-confetti-layer";
        const COLORS = ["#f5c842", "#f5e8c8", "#d4b878", "#ffeaa7", "#b8862a", "#ffd95c"];
        for (let i = 0; i < 16; i++) {
          const dot = document.createElement("div");
          dot.className = "bp-confetti";
          const angle = (Math.PI * 2 * i) / 16 + (Math.random() - 0.5) * 0.4;
          const dist = 55 + Math.random() * 35;
          dot.style.setProperty("--dx", `${Math.cos(angle) * dist}px`);
          dot.style.setProperty("--dy", `${Math.sin(angle) * dist}px`);
          dot.style.setProperty("--rot", `${Math.random() * 360}deg`);
          dot.style.background = COLORS[i % COLORS.length];
          dot.style.animationDelay = `${i * 12}ms`;
          layer.appendChild(dot);
        }
        col.appendChild(layer);
        setTimeout(() => layer.remove(), 1100);
        // Bob the new champion chip once.
        const championChip = chips.querySelector(".bp-chip");
        if (championChip) {
          championChip.classList.add("champion-bob");
          setTimeout(() => championChip.classList.remove("champion-bob"), 950);
        }
      }

      grid.appendChild(col);
      parentElement._bp_prev[stage.id] = [...list];
    });
  }

  function flash(chip) {
    chip.classList.remove("flash");
    void chip.offsetWidth; // force reflow to restart animation
    chip.classList.add("flash");
  }

  function stageCount(level) {
    return level === 0 ? teamsR32.length : state[level].length;
  }

  function handleClick(team, stage, chip) {
    if (stage === 5) return; // can't advance past champion
    const nextLevel = stage + 1;
    const cap = STAGES[nextLevel].cap;
    let advancing = false;

    if (state[nextLevel].includes(team)) {
      // Demote from nextLevel and every higher level (always allowed).
      for (let L = nextLevel; L <= 5; L++) {
        state[L] = state[L].filter((t) => t !== team);
      }
    } else {
      if (state[nextLevel].length >= cap) {
        flash(chip);
        return;
      }
      // Branching-factor rule: each match in stage N+1 needs 2 teams from
      // stage N. So after this advance, stageCount(stage) >= 2*(N+1 count).
      // This prevents the "single team marches to Champion" bug (Champion
      // needs Final >= 2) while still letting users fill rounds in any
      // order they like.
      const nextCountAfter = state[nextLevel].length + 1;
      if (stageCount(stage) < 2 * nextCountAfter) {
        flash(chip);
        return;
      }
      state[nextLevel].push(team);
      advancing = true;
    }
    // Pulse the source chip before re-render (re-render rebuilds DOM, so we
    // also re-apply pulse to the recreated chip after render).
    if (advancing) {
      chip.classList.remove("pulse");
      void chip.offsetWidth;
      chip.classList.add("pulse");
    }
    emit();
    render();
    if (advancing) {
      // Find the rebuilt chip in the same column and pulse it too — it's now
      // a fresh DOM node, but the visual continuity reads as one effect.
      const rebuilt = grid.querySelector(
        `[data-stage-id="${stage}"] .bp-chip[data-team="${CSS.escape(team)}"]`
      );
      if (rebuilt) {
        rebuilt.classList.add("pulse");
        setTimeout(() => rebuilt.classList.remove("pulse"), 470);
      }
    }
  }

  function emit() {
    setStateValue("picks", {
      r16: [...state[1]],
      qf: [...state[2]],
      sf: [...state[3]],
      finalists: [...state[4]],
      champion: state[5][0] ?? null,
    });
  }

  // Only re-emit when normalization actually changed the picks (e.g. dropped
  // teams that are no longer in the R32 pool). Otherwise emitting on every
  // mount would risk a callback loop.
  function picksEqual(a, b) {
    const fields = ["r16", "qf", "sf", "finalists"];
    for (const f of fields) {
      const aa = (a && a[f]) || [];
      const bb = (b && b[f]) || [];
      if (aa.length !== bb.length) return false;
      for (let i = 0; i < aa.length; i++) if (aa[i] !== bb[i]) return false;
    }
    return (a?.champion ?? null) === (b?.champion ?? null);
  }
  const normalized = {
    r16: state[1], qf: state[2], sf: state[3], finalists: state[4],
    champion: state[5][0] ?? null,
  };
  if (!picksEqual(initialPicks, normalized)) emit();
  render();
}
"""

_BRACKET_COMPONENT = st.components.v2.component(
    "fifa_bracket_picker",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def bracket_picker(
    *,
    teams_r32: list[str],
    team_labels: dict[str, str] | None = None,
    initial_picks: dict | None = None,
    key: str = "bracket_picker",
    on_change: Callable[[], None] | None = None,
) -> dict:
    """Render the visual playoff bracket.

    ``teams_r32`` is the pool of 32 teams (group winners + runners-up + best
    thirds). ``initial_picks`` mirrors the dict written to session state.
    Returns the current picks dict; values are empty lists / None when unset.
    """
    initial_picks = initial_picks or {}
    # On reruns the user's edits live in session_state[key].picks; that's the
    # source of truth and must be fed back as data so the component doesn't
    # snap back to the initial state.
    prior = st.session_state.get(key)
    prior_picks = getattr(prior, "picks", None) if prior is not None else None
    picks_for_data = prior_picks if prior_picks is not None else {
        "r16": list(initial_picks.get("r16", [])),
        "qf": list(initial_picks.get("qf", [])),
        "sf": list(initial_picks.get("sf", [])),
        "finalists": list(initial_picks.get("finalists", [])),
        "champion": initial_picks.get("champion"),
    }
    result = _BRACKET_COMPONENT(
        key=key,
        data={
            "teams_r32": list(teams_r32),
            "team_labels": dict(team_labels or {}),
            "picks": picks_for_data,
        },
        on_picks_change=on_change or (lambda: None),
    )
    picks = getattr(result, "picks", None) or picks_for_data or {}
    return {
        "r16": list(picks.get("r16", []) or []),
        "qf": list(picks.get("qf", []) or []),
        "sf": list(picks.get("sf", []) or []),
        "finalists": list(picks.get("finalists", []) or []),
        "champion": picks.get("champion"),
    }
