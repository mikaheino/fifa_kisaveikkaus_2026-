"""Click-to-pick team grid — CCv2 component for picking N teams from a list.

Replaces a Streamlit multiselect with a chip grid: each team is a clickable
button, click to toggle, cap enforced. Selected chips glow gold; trying to
exceed the cap flashes the chip red.

State written to ``st.session_state[key].selected`` as a ``list[str]``.
"""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st

_HTML = """<div class="tg-root">
  <div class="tg-bar">
    <span class="tg-count"></span>
    <button type="button" class="tg-clear">Tyhjennä</button>
  </div>
  <div class="tg-grid"></div>
</div>"""

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bungee&display=swap');

.tg-root {
  font-family: 'Roboto', Arial, sans-serif;
  color: #f5e8c8;
  background: linear-gradient(180deg, #0a1f12 0%, #061308 100%);
  border: 2px solid #f5c842;
  box-shadow:
    4px 4px 0 #000,
    inset 0 0 0 1px rgba(0,0,0,0.7),
    inset 0 2px 0 rgba(255,230,180,0.18);
  padding: 10px;
  margin-bottom: 12px;
}
.tg-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(245, 200, 80, 0.25);
}
.tg-count {
  font-family: 'Bungee', 'Impact', sans-serif;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #ffd95c;
  font-size: 0.9rem;
}
.tg-count.full { color: #5fc879; }
.tg-clear {
  font-family: 'Bungee', 'Impact', sans-serif;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.72rem;
  color: #d4b878;
  background: transparent;
  border: 1px solid #b8862a;
  padding: 3px 8px;
  cursor: pointer;
}
.tg-clear:hover { color: #f5e8c8; border-color: #ffd95c; }
.tg-clear:disabled { opacity: 0.4; cursor: not-allowed; }

.tg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 6px;
}
.tg-chip {
  display: block;
  width: 100%;
  text-align: left;
  font-family: inherit;
  font-size: 0.84rem;
  line-height: 1.15;
  padding: 8px 10px;
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
.tg-chip:hover {
  background: rgba(100, 70, 25, 0.95);
  color: #f5e8c8;
}
.tg-chip.selected {
  background: rgba(180, 130, 35, 0.95);
  color: #1a1408;
  font-weight: 700;
  box-shadow:
    inset 1px 1px rgba(255,230,180,0.7),
    inset -1px -1px rgba(80,50,15,0.85),
    0 0 6px rgba(245, 200, 80, 0.55);
}
.tg-chip.selected:hover { background: rgba(220, 165, 45, 0.95); }
.tg-chip.flash { animation: tg-flash 0.32s ease-out; }
.tg-chip.entering { animation: tg-slide-in 0.28s cubic-bezier(0.18, 0.89, 0.32, 1.28) both; }
@keyframes tg-flash {
  0% { background: rgba(170, 60, 40, 0.95); transform: translateX(0); }
  25% { transform: translateX(-3px); }
  75% { transform: translateX(3px); }
  100% { transform: translateX(0); }
}
@keyframes tg-slide-in {
  0%   { opacity: 0; transform: scale(0.85); }
  60%  { opacity: 1; transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component;

  const teams = Array.isArray(data?.teams) ? [...data.teams] : [];
  const labels = (data && typeof data.team_labels === "object" && data.team_labels) || {};
  const cap = Number.isFinite(data?.max_selected) ? data.max_selected : 8;

  // Hydrate from session_state via data.selected on every run.
  const initialSelected = Array.isArray(data?.selected)
    ? data.selected.filter((t) => teams.includes(t)).slice(0, cap)
    : [];
  const selected = new Set(initialSelected);

  const grid = parentElement.querySelector(".tg-grid");
  const countEl = parentElement.querySelector(".tg-count");
  const clearBtn = parentElement.querySelector(".tg-clear");
  const labelFor = (t) => labels[t] || t;

  function updateCount() {
    countEl.textContent = `${selected.size} / ${cap} valittu`;
    countEl.classList.toggle("full", selected.size === cap);
    clearBtn.disabled = selected.size === 0;
  }

  function paintChip(chip) {
    if (selected.has(chip.dataset.team)) chip.classList.add("selected");
    else chip.classList.remove("selected");
  }

  function flash(chip) {
    chip.classList.remove("flash");
    void chip.offsetWidth;
    chip.classList.add("flash");
  }

  function emit() {
    setStateValue("selected", [...selected]);
  }

  // First-mount: build chips. Subsequent reruns: reuse them.
  const firstRender = !parentElement._tg_initialized;
  if (firstRender) {
    parentElement._tg_initialized = true;
    teams.forEach((team) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "tg-chip";
      chip.dataset.team = team;
      chip.textContent = labelFor(team);
      chip.title = labelFor(team);
      chip.onclick = () => {
        if (selected.has(team)) {
          selected.delete(team);
        } else {
          if (selected.size >= cap) { flash(chip); return; }
          selected.add(team);
        }
        paintChip(chip);
        updateCount();
        emit();
      };
      grid.appendChild(chip);
    });
  }

  // Re-sync visual state from selected set (handles reruns where data.selected
  // changed externally, e.g. parent pruned options).
  grid.querySelectorAll(".tg-chip").forEach(paintChip);
  updateCount();

  clearBtn.onclick = () => {
    if (selected.size === 0) return;
    selected.clear();
    grid.querySelectorAll(".tg-chip").forEach(paintChip);
    updateCount();
    emit();
  };
}
"""

_TG_COMPONENT = st.components.v2.component(
    "fifa_team_grid_picker",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def team_grid_picker(
    *,
    teams: list[str],
    selected: list[str] | None = None,
    team_labels: dict[str, str] | None = None,
    max_selected: int = 8,
    key: str = "team_grid",
    on_change: Callable[[], None] | None = None,
) -> list[str]:
    """Render a click-to-pick chip grid. Returns the list of selected teams."""
    # On rerun, prefer session_state over the caller's `selected` so the
    # component doesn't snap back to a stale initial value.
    prior = st.session_state.get(key)
    prior_selected = getattr(prior, "selected", None) if prior is not None else None
    initial_selected = (
        list(prior_selected) if prior_selected is not None else list(selected or [])
    )
    # Keep only teams that are still valid options.
    initial_selected = [t for t in initial_selected if t in teams][:max_selected]

    result = _TG_COMPONENT(
        key=key,
        data={
            "teams": list(teams),
            "team_labels": dict(team_labels or {}),
            "selected": initial_selected,
            "max_selected": int(max_selected),
        },
        on_selected_change=on_change or (lambda: None),
    )
    out = getattr(result, "selected", None)
    if not isinstance(out, list):
        return list(initial_selected)
    return [t for t in out if t in teams][:max_selected]
