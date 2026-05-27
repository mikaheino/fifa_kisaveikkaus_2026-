"""Group-organised best-third-placed picker — CCv2 component.

Replaces the flat "pick any 8" grid for ``Parhaat lohkokolmoset``. One card per
group (A–L). Each card shows **all four** group teams: the already-chosen 🥇
winner and 🥈 runner-up are rendered locked (for context — you read at a glance
how tough the group was), and the two remaining teams are clickable chips. Click
one to mark it as that group's advancing third placer; its sibling dims to the
4th-place / out state. At most one third per group, and a global cap of 8 (the
real format: 8 of 12 third-placed teams advance).

State written to ``st.session_state[key].selected`` as a ``list[str]`` — the
same shape the old ``team_grid_picker`` emitted, so the THIRD_1..8 save path,
the R32 pool, and the live counter all keep working unchanged.
"""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st

_HTML = """<div class="tp-root">
  <div class="tp-bar">
    <span class="tp-count"></span>
    <button type="button" class="tp-clear">Tyhjennä</button>
  </div>
  <div class="tp-grid"></div>
  <div class="tp-hint">Klikkaa lohkon kahdesta jäljellä olevasta joukkueesta toista = sen lohkon 3. sija. Toinen jää neljänneksi. Max 1 / lohko, yhteensä 8 etenijää.</div>
</div>"""

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bungee&display=swap');

.tp-root {
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
.tp-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(245, 200, 80, 0.25);
}
.tp-count {
  font-family: 'Bungee', 'Impact', sans-serif;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #ffd95c;
  font-size: 0.9rem;
}
.tp-count.full { color: #5fc879; }
.tp-clear {
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
.tp-clear:hover { color: #f5e8c8; border-color: #ffd95c; }
.tp-clear:disabled { opacity: 0.4; cursor: not-allowed; }

.tp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}
.tp-card {
  background: rgba(30, 20, 8, 0.45);
  border: 1px solid rgba(245, 200, 80, 0.18);
  box-shadow: inset 1px 1px rgba(0,0,0,0.55), inset -1px -1px rgba(245,200,80,0.15);
  padding: 6px 6px 8px;
}
.tp-card.tp-has-pick { border-color: rgba(245, 200, 80, 0.5); }
.tp-card-title {
  font-family: 'Bungee', 'Impact', sans-serif;
  text-align: center;
  letter-spacing: 2px;
  font-size: 0.82rem;
  color: #ffd95c;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(245, 200, 80, 0.25);
  padding-bottom: 4px;
}
.tp-locked { display: flex; flex-direction: column; gap: 3px; }
.tp-lock {
  font-size: 0.78rem;
  line-height: 1.15;
  padding: 4px 6px;
  color: #8c7a52;
  background: rgba(40, 28, 12, 0.6);
  box-shadow: inset 1px 1px rgba(0,0,0,0.4);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}
.tp-lock-w { color: #c9a85f; }
.tp-lock-r { color: #b9bcc2; }
.tp-sep {
  height: 1px;
  background: rgba(245, 200, 80, 0.25);
  margin: 6px 2px;
}
.tp-cands { display: flex; flex-direction: column; gap: 3px; }
.tp-chip {
  display: block;
  width: 100%;
  text-align: left;
  font-family: inherit;
  font-size: 0.82rem;
  line-height: 1.15;
  padding: 6px 8px;
  border: none;
  border-radius: 0;
  background: rgba(60, 42, 18, 0.85);
  color: #d4b878;
  cursor: pointer;
  box-shadow: inset 1px 1px rgba(0,0,0,0.5), inset -1px -1px rgba(245,200,80,0.2);
  transition: background 0.1s, color 0.1s, transform 0.05s, opacity 0.1s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tp-chip:hover { background: rgba(100, 70, 25, 0.95); color: #f5e8c8; }
.tp-chip.selected {
  background: rgba(180, 130, 35, 0.95);
  color: #1a1408;
  font-weight: 700;
  box-shadow:
    inset 1px 1px rgba(255,230,180,0.7),
    inset -1px -1px rgba(80,50,15,0.85),
    0 0 6px rgba(245, 200, 80, 0.55);
}
.tp-chip.selected:hover { background: rgba(220, 165, 45, 0.95); }
/* Sibling of a picked third = 4th place / out: dimmed but still clickable
   (clicking it switches the group's pick). */
.tp-chip.fourth { opacity: 0.32; }
.tp-chip.fourth:hover { opacity: 0.6; }
.tp-chip.flash { animation: tp-flash 0.32s ease-out; }
.tp-chip.pulse { animation: tp-pulse 0.45s ease-out; }
.tp-chip.entering { animation: tp-slide-in 0.28s cubic-bezier(0.18, 0.89, 0.32, 1.28) both; }
@keyframes tp-flash {
  0% { background: rgba(170, 60, 40, 0.95); transform: translateX(0); }
  25% { transform: translateX(-3px); }
  75% { transform: translateX(3px); }
  100% { transform: translateX(0); }
}
@keyframes tp-pulse {
  0%   { transform: scale(1);    filter: brightness(1)   drop-shadow(0 0 0 rgba(245,200,80,0)); }
  40%  { transform: scale(1.06); filter: brightness(1.25) drop-shadow(0 0 8px rgba(245,200,80,0.85)); }
  100% { transform: scale(1);    filter: brightness(1)   drop-shadow(0 0 0 rgba(245,200,80,0)); }
}
@keyframes tp-slide-in {
  0%   { opacity: 0; transform: scale(0.85); }
  60%  { opacity: 1; transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}
.tp-hint {
  text-align: center;
  font-size: 0.72rem;
  color: #aa9466;
  margin-top: 8px;
}
"""

_JS = r"""
export default function (component) {
  const { data, parentElement, setStateValue } = component;

  const groups = Array.isArray(data?.groups) ? data.groups : [];
  const labels = (data && typeof data.team_labels === "object" && data.team_labels) || {};
  const cap = Number.isFinite(data?.max_selected) ? data.max_selected : 8;
  const labelFor = (t) => labels[t] || t;

  // team -> group letter, for the one-per-group rule and validity checks.
  const groupOf = {};
  const candidateSet = new Set();
  groups.forEach((g) => {
    (g.candidates || []).forEach((t) => {
      groupOf[t] = g.letter;
      candidateSet.add(t);
    });
  });

  // Hydrate from session_state via data.selected. Keep only valid candidates,
  // enforce one-per-group (first wins), and cap.
  const seenGroups = new Set();
  const selected = [];
  (Array.isArray(data?.selected) ? data.selected : []).forEach((t) => {
    if (!candidateSet.has(t)) return;
    const L = groupOf[t];
    if (seenGroups.has(L)) return;
    if (selected.length >= cap) return;
    seenGroups.add(L);
    selected.push(t);
  });
  const selectedSet = new Set(selected);

  const grid = parentElement.querySelector(".tp-grid");
  const countEl = parentElement.querySelector(".tp-count");
  const clearBtn = parentElement.querySelector(".tp-clear");

  function pickInGroup(letter) {
    const g = groups.find((x) => x.letter === letter);
    if (!g) return null;
    return (g.candidates || []).find((t) => selectedSet.has(t)) || null;
  }

  function updateCount() {
    countEl.textContent = `${selectedSet.size} / ${cap} valittu`;
    countEl.classList.toggle("full", selectedSet.size === cap);
    clearBtn.disabled = selectedSet.size === 0;
  }

  function paint() {
    grid.querySelectorAll(".tp-card").forEach((card) => {
      const letter = card.dataset.letter;
      const hasPick = pickInGroup(letter) !== null;
      card.classList.toggle("tp-has-pick", hasPick);
      card.querySelectorAll(".tp-chip").forEach((chip) => {
        const team = chip.dataset.team;
        const isSel = selectedSet.has(team);
        chip.classList.toggle("selected", isSel);
        // Sibling of a picked team = 4th place (group has a pick, this isn't it).
        chip.classList.toggle("fourth", hasPick && !isSel);
      });
    });
  }

  function flash(chip) {
    chip.classList.remove("flash");
    void chip.offsetWidth;
    chip.classList.add("flash");
  }
  function pulse(chip) {
    chip.classList.remove("pulse");
    void chip.offsetWidth;
    chip.classList.add("pulse");
  }

  function emit() {
    setStateValue("selected", [...selected]);
    try {
      const bc = new BroadcastChannel('fifa-picks');
      bc.postMessage({ type: 'thirds', teams: [...selected] });
      bc.close();
    } catch (_) {}
  }

  function removeTeam(team) {
    const i = selected.indexOf(team);
    if (i !== -1) selected.splice(i, 1);
    selectedSet.delete(team);
  }

  function handle(team, chip) {
    const letter = groupOf[team];
    if (selectedSet.has(team)) {
      // Toggle off — frees this group.
      removeTeam(team);
    } else {
      const existing = pickInGroup(letter);
      if (existing) {
        // Switch within the group: replace sibling, count unchanged.
        removeTeam(existing);
        selected.push(team);
        selectedSet.add(team);
      } else {
        // New group entry — respect the global cap.
        if (selectedSet.size >= cap) { flash(chip); return; }
        selected.push(team);
        selectedSet.add(team);
        pulse(chip);
      }
    }
    paint();
    updateCount();
    emit();
  }

  // Build cards once; the group/team structure is stable across reruns.
  const sig = groups.map((g) =>
    `${g.letter}:${g.winner}|${g.runnerup}|${(g.candidates || []).join(",")}`
  ).join(";");
  if (parentElement._tp_sig !== sig) {
    parentElement._tp_sig = sig;
    grid.innerHTML = "";
    groups.forEach((g) => {
      const card = document.createElement("div");
      card.className = "tp-card";
      card.dataset.letter = g.letter;

      const title = document.createElement("div");
      title.className = "tp-card-title";
      title.textContent = g.letter;
      card.appendChild(title);

      const locked = document.createElement("div");
      locked.className = "tp-locked";
      const mk = (cls, medal, team) => {
        const el = document.createElement("div");
        el.className = `tp-lock ${cls}`;
        el.textContent = `${medal} ${labelFor(team)}`;
        el.title = labelFor(team);
        return el;
      };
      if (g.winner)   locked.appendChild(mk("tp-lock-w", "🥇", g.winner));
      if (g.runnerup) locked.appendChild(mk("tp-lock-r", "🥈", g.runnerup));
      card.appendChild(locked);

      const sep = document.createElement("div");
      sep.className = "tp-sep";
      card.appendChild(sep);

      const cands = document.createElement("div");
      cands.className = "tp-cands";
      (g.candidates || []).forEach((team) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "tp-chip";
        chip.dataset.team = team;
        chip.dataset.letter = g.letter;
        chip.textContent = labelFor(team);
        chip.title = labelFor(team);
        chip.onclick = () => handle(team, chip);
        cands.appendChild(chip);
      });
      card.appendChild(cands);

      grid.appendChild(card);
    });
  }

  paint();
  updateCount();

  clearBtn.onclick = () => {
    if (selectedSet.size === 0) return;
    selected.length = 0;
    selectedSet.clear();
    paint();
    updateCount();
    emit();
  };
}
"""

_TP_COMPONENT = st.components.v2.component(
    "fifa_third_place_picker",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def third_place_picker(
    *,
    groups: list[dict],
    team_labels: dict[str, str] | None = None,
    selected: list[str] | None = None,
    max_selected: int = 8,
    key: str = "grid_third",
    on_change: Callable[[], None] | None = None,
) -> list[str]:
    """Render the group-organised best-third picker. Returns selected teams.

    ``groups`` is an ordered list of
    ``{"letter": str, "winner": str, "runnerup": str, "candidates": [t1, t2]}``.
    Only the two ``candidates`` per group are selectable; winner/runner-up are
    shown locked for context. Output is a flat list (≤ ``max_selected``) with at
    most one team per group, in selection order.
    """
    # team -> letter, plus the valid candidate pool, for server-side pruning.
    group_of: dict[str, str] = {}
    candidate_pool: set[str] = set()
    for g in groups:
        for t in g.get("candidates", []):
            group_of[t] = g["letter"]
            candidate_pool.add(t)

    # On rerun, prefer session_state over the caller's `selected` so the
    # component doesn't snap back to a stale initial value.
    prior = st.session_state.get(key)
    prior_selected = getattr(prior, "selected", None) if prior is not None else None
    raw = list(prior_selected) if prior_selected is not None else list(selected or [])

    # Keep only valid candidates, one per group (first wins), capped.
    seen_groups: set[str] = set()
    initial_selected: list[str] = []
    for t in raw:
        if t not in candidate_pool:
            continue
        letter = group_of[t]
        if letter in seen_groups:
            continue
        if len(initial_selected) >= max_selected:
            break
        seen_groups.add(letter)
        initial_selected.append(t)

    result = _TP_COMPONENT(
        key=key,
        data={
            "groups": [
                {
                    "letter": g["letter"],
                    "winner": g.get("winner"),
                    "runnerup": g.get("runnerup"),
                    "candidates": list(g.get("candidates", [])),
                }
                for g in groups
            ],
            "team_labels": dict(team_labels or {}),
            "selected": initial_selected,
            "max_selected": int(max_selected),
        },
        on_selected_change=on_change or (lambda: None),
    )
    out = getattr(result, "selected", None)
    if not isinstance(out, list):
        return list(initial_selected)

    # Re-apply the same invariants to whatever the component emitted.
    seen_groups = set()
    cleaned: list[str] = []
    for t in out:
        if t not in candidate_pool:
            continue
        letter = group_of[t]
        if letter in seen_groups:
            continue
        if len(cleaned) >= max_selected:
            break
        seen_groups.add(letter)
        cleaned.append(t)
    return cleaned
