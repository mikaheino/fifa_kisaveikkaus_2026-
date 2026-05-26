"""Click-to-pick group winner + runner-up — CCv2 component.

Replaces the two ``st.selectbox`` widgets per group with two rows of 4 team
chips. Click a chip in the ``🥇 Voittaja`` row to set the winner; click in the
``🥈 Kakkonen`` row to set the runner-up. The team already picked as winner
is disabled in the runner-up row (and vice versa) so the same team can't be
picked twice.

State written to ``st.session_state[key]`` as
``{"winner": str | None, "runnerup": str | None}``.
"""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st

_HTML = """<div class="gp-root">
  <div class="gp-row" data-slot="winner">
    <div class="gp-label gp-label-w">🥇 Voittaja</div>
    <div class="gp-chips"></div>
  </div>
  <div class="gp-row" data-slot="runnerup">
    <div class="gp-label gp-label-r">🥈 Kakkonen</div>
    <div class="gp-chips"></div>
  </div>
</div>"""

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bungee&display=swap');

.gp-root {
  font-family: 'Roboto', Arial, sans-serif;
  color: #f5e8c8;
  padding: 4px 0;
}
.gp-row {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 10px;
  align-items: stretch;
  margin-bottom: 6px;
}
.gp-label {
  font-family: 'Bungee', 'Impact', sans-serif;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  padding: 0 8px;
  color: #1a1408;
  border: 2px solid #0a0a0a;
  box-shadow: inset 1px 1px rgba(255,230,180,0.55), inset -1px -1px rgba(80,50,15,0.7);
}
.gp-label-w { background: linear-gradient(180deg, #ffd95c, #b8862a); }
.gp-label-r { background: linear-gradient(180deg, #d9d9d9, #888888); }

.gp-chips {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}
.gp-chip {
  display: block;
  width: 100%;
  text-align: center;
  font-family: inherit;
  font-size: 0.82rem;
  line-height: 1.15;
  padding: 8px 6px;
  border: none;
  border-radius: 0;
  background: rgba(60, 42, 18, 0.85);
  color: #d4b878;
  cursor: pointer;
  box-shadow: inset 1px 1px rgba(0,0,0,0.5), inset -1px -1px rgba(245,200,80,0.2);
  transition: background 0.1s, color 0.1s, transform 0.05s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gp-chip:hover:not(.disabled) {
  background: rgba(100, 70, 25, 0.95);
  color: #f5e8c8;
}
.gp-chip.selected {
  background: rgba(180, 130, 35, 0.95);
  color: #1a1408;
  font-weight: 700;
  box-shadow:
    inset 1px 1px rgba(255,230,180,0.7),
    inset -1px -1px rgba(80,50,15,0.85),
    0 0 6px rgba(245, 200, 80, 0.55);
}
.gp-row[data-slot="runnerup"] .gp-chip.selected {
  background: linear-gradient(180deg, #e6e6e6, #999999);
  box-shadow:
    inset 1px 1px rgba(255,255,255,0.7),
    inset -1px -1px rgba(60,60,60,0.85),
    0 0 6px rgba(220, 220, 220, 0.5);
}
.gp-chip.disabled {
  opacity: 0.30;
  cursor: not-allowed;
  background: rgba(40, 28, 12, 0.85);
  color: #6e5a36;
  box-shadow: inset 1px 1px rgba(0,0,0,0.5);
}
.gp-chip.flash { animation: gp-flash 0.32s ease-out; }
@keyframes gp-flash {
  0% { background: rgba(170, 60, 40, 0.95); transform: translateX(0); }
  25% { transform: translateX(-3px); }
  75% { transform: translateX(3px); }
  100% { transform: translateX(0); }
}
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component;

  function broadcast(winner, runnerup) {
    try {
      const bc = new BroadcastChannel('fifa-picks');
      bc.postMessage({
        type: 'group',
        letter: String(data?.letter ?? ''),
        winner: winner || null,
        runnerup: runnerup || null,
      });
      bc.close();
    } catch (_) {}
  }

  const teams = Array.isArray(data?.teams) ? [...data.teams] : [];
  const labels = (data && typeof data.team_labels === "object" && data.team_labels) || {};
  const labelFor = (t) => labels[t] || t;

  let winner   = teams.includes(data?.winner)   ? data.winner   : null;
  let runnerup = teams.includes(data?.runnerup) ? data.runnerup : null;
  if (winner && winner === runnerup) runnerup = null;

  const rowW = parentElement.querySelector('.gp-row[data-slot="winner"] .gp-chips');
  const rowR = parentElement.querySelector('.gp-row[data-slot="runnerup"] .gp-chips');

  function buildRow(rowEl, slot) {
    rowEl.innerHTML = "";
    teams.forEach((team) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "gp-chip";
      chip.dataset.team = team;
      chip.dataset.slot = slot;
      chip.textContent = labelFor(team);
      chip.title = labelFor(team);
      chip.onclick = () => handle(team, slot, chip);
      rowEl.appendChild(chip);
    });
  }

  function paint() {
    parentElement.querySelectorAll(".gp-chip").forEach((c) => {
      c.classList.remove("selected", "disabled");
      const team = c.dataset.team;
      const slot = c.dataset.slot;
      if (slot === "winner" && team === winner)   c.classList.add("selected");
      if (slot === "runnerup" && team === runnerup) c.classList.add("selected");
      // Disable the W team in R-row and vice versa.
      if (slot === "winner"   && team === runnerup) c.classList.add("disabled");
      if (slot === "runnerup" && team === winner)   c.classList.add("disabled");
    });
  }

  function flash(chip) {
    chip.classList.remove("flash");
    void chip.offsetWidth;
    chip.classList.add("flash");
  }

  function handle(team, slot, chip) {
    if (chip.classList.contains("disabled")) { flash(chip); return; }
    if (slot === "winner") {
      winner = (winner === team) ? null : team;
      if (winner && winner === runnerup) runnerup = null;
    } else {
      runnerup = (runnerup === team) ? null : team;
      if (runnerup && runnerup === winner) winner = null;
    }
    paint();
    setStateValue("pick", { winner, runnerup });
    broadcast(winner, runnerup);
  }

  // First-mount only — chip text doesn't change between renders.
  if (!parentElement._gp_initialized) {
    parentElement._gp_initialized = true;
    buildRow(rowW, "winner");
    buildRow(rowR, "runnerup");
  }
  paint();
}
"""

_GP_COMPONENT = st.components.v2.component(
    "fifa_group_picker",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def group_picker(
    *,
    teams: list[str],
    team_labels: dict[str, str] | None = None,
    winner: str | None = None,
    runnerup: str | None = None,
    key: str,
    letter: str | None = None,
    on_change: Callable[[], None] | None = None,
) -> dict:
    """Render a 2-row click picker. Returns ``{"winner": ..., "runnerup": ...}``."""
    prior = st.session_state.get(key)
    prior_pick = getattr(prior, "pick", None) if prior is not None else None
    if isinstance(prior_pick, dict):
        w_data = prior_pick.get("winner")
        r_data = prior_pick.get("runnerup")
    else:
        w_data = winner
        r_data = runnerup
    if w_data not in teams: w_data = None
    if r_data not in teams: r_data = None
    if w_data is not None and w_data == r_data: r_data = None

    result = _GP_COMPONENT(
        key=key,
        data={
            "teams": list(teams),
            "team_labels": dict(team_labels or {}),
            "winner": w_data,
            "runnerup": r_data,
            "letter": (letter or key.split("_")[-1]),
        },
        on_pick_change=on_change or (lambda: None),
    )
    pick = getattr(result, "pick", None)
    if isinstance(pick, dict):
        w = pick.get("winner") if pick.get("winner") in teams else None
        r = pick.get("runnerup") if pick.get("runnerup") in teams else None
        if w is not None and w == r: r = None
        return {"winner": w, "runnerup": r}
    return {"winner": w_data, "runnerup": r_data}
