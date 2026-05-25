"""Saksa / Yhdysvallat prediction celebration — full-screen Pirlo overlay.

Wired into the prediction page via :func:`maybe_celebrate` (call from inside
the per-match fragment after the slider renders). When the user commits a
score on a group-stage match featuring either Saksa or Yhdysvallat, the
helper stashes the team name in session_state and triggers a full-app
rerun; on the rerun :func:`consume_pending` emits the CSS-driven overlay,
which fades itself out after ~5 seconds.

Fires at most once per target match per session — so 6 max in this slate
(Saksa plays 3 group games, Yhdysvallat plays 3).
"""
from __future__ import annotations

import base64
import os

import streamlit as st

from schedule_data import SCHEDULE_MATCHES

def _asset_b64(name: str) -> str:
    p = os.path.join(os.path.dirname(__file__), "..", "assets", name)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return ""
    return base64.b64encode(open(p, "rb").read()).decode()


_PIRLO_B64 = _asset_b64("pirlo.gif")
_DIEGO_B64 = _asset_b64("diego.gif")
_GOAL_B64 = _asset_b64("goal.gif")


def _gif_duration_ms(name: str, fallback: int) -> int:
    p = os.path.join(os.path.dirname(__file__), "..", "assets", name)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return fallback
    try:
        from PIL import Image, ImageSequence
        im = Image.open(p)
        return sum(f.info.get("duration", 70) for f in ImageSequence.Iterator(im))
    except Exception:
        return fallback


_GOAL_MS = _gif_duration_ms("goal.gif", 10000)

_TARGET_TEAMS = {"Saksa", "Yhdysvallat"}


def _target_match_team() -> dict[int, str]:
    """Map ``match_id -> celebrated team`` for every group game featuring
    one of the target teams."""
    out: dict[int, str] = {}
    for m in SCHEDULE_MATCHES:
        home, _, away = m["MATCH"].partition(" vs ")
        home, away = home.strip(), away.strip()
        if home in _TARGET_TEAMS:
            out[int(m["ID"])] = home
        elif away in _TARGET_TEAMS:
            out[int(m["ID"])] = away
    return out


_MATCH_TO_TEAM = _target_match_team()


def maybe_celebrate() -> None:
    """Fire the overlay any time a Saksa/USA pick is committed or edited.

    We track the *score we last celebrated for each match* (not just the
    set of match-ids we've ever celebrated), so a new commit on any
    target match re-fires the overlay — covers both first picks and
    later edits, for every Saksa/USA group game.
    """
    last: dict[int, tuple[int, int]] = st.session_state.setdefault(
        "last_celebrated_scores", {}
    )
    for gid, team in _MATCH_TO_TEAM.items():
        state = st.session_state.get(f"mom_{gid}")
        score = getattr(state, "score", None) if state is not None else None
        if not (isinstance(score, dict) and "home" in score and "away" in score):
            continue
        key = (int(score["home"]), int(score["away"]))
        if last.get(gid) == key:
            continue
        last[gid] = key
        st.session_state["pending_celebrate"] = team.upper()
        st.rerun(scope="app")
        return


def maybe_celebrate_groups_complete(group_picks: dict) -> None:
    """Fire the Diego overlay once when all 12 group winner+runnerup picks are set.

    Re-fires if the user clears a pick and re-completes the set (e.g.
    edits a group then re-fills it).
    """
    if not _DIEGO_B64:
        return
    all_filled = bool(group_picks) and all(
        w and w != "—" and r and r != "—" for (w, r) in group_picks.values()
    )
    already = bool(st.session_state.get("groups_complete_celebrated"))
    if all_filled and not already:
        st.session_state["groups_complete_celebrated"] = True
        st.session_state["pending_celebrate_groups"] = True
        st.rerun(scope="app")
    elif not all_filled and already:
        st.session_state["groups_complete_celebrated"] = False


def trigger_submit_celebrate() -> None:
    """Queue the goal-clip overlay; consumed on the next page render."""
    if _GOAL_B64:
        st.session_state["pending_celebrate_submit"] = True


def _emit_overlay(
    b64: str,
    cls_prefix: str,
    alt: str,
    *,
    fade: bool = True,
    img_size_css: str = "width: 25vmin; max-width: 240px; height: auto;",
    duration_ms: int = 2000,
) -> None:
    counter = int(st.session_state.get("celebrate_counter", 0)) + 1
    st.session_state["celebrate_counter"] = counter
    cls = f"{cls_prefix}-{counter}"
    anim = f"{cls_prefix}-anim-{counter}"
    fade_rules = (
        f"animation: {anim} {duration_ms}ms ease-in-out forwards;"
        if fade
        else f"animation: {anim} {duration_ms}ms linear forwards;"
    )
    keyframes = (
        f"""@keyframes {anim} {{
            0%   {{ opacity: 0; transform: scale(0.88); }}
            10%  {{ opacity: 1; transform: scale(1.04); }}
            18%  {{ transform: scale(1.00); }}
            82%  {{ opacity: 1; transform: scale(1.00); }}
            100% {{ opacity: 0; transform: scale(1.10); visibility: hidden; }}
        }}"""
        if fade
        else f"""@keyframes {anim} {{
            0%, 99%   {{ opacity: 1; }}
            100%      {{ opacity: 0; visibility: hidden; }}
        }}"""
    )
    st.markdown(
        f"""
        <div class="cele-overlay {cls}">
          <img src="data:image/gif;base64,{b64}" alt="{alt}"/>
        </div>
        <style>
        .{cls} {{
            position: fixed;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
            z-index: 9999;
            background: radial-gradient(
                ellipse at center,
                rgba(8, 24, 14, 0.55) 0%,
                rgba(2, 8, 5, 0.0)  70%
            );
            {fade_rules}
        }}
        .{cls} img {{
            {img_size_css}
            filter: drop-shadow(0 14px 32px rgba(0, 0, 0, 0.75));
        }}
        {keyframes}
        </style>
        """,
        unsafe_allow_html=True,
    )


_THANKS_MS = 5_000
_GOAL_PLAY_MS = _GOAL_MS


def _emit_thanks_then_goal() -> None:
    counter = int(st.session_state.get("celebrate_counter", 0)) + 1
    st.session_state["celebrate_counter"] = counter
    cls = f"goal-cele-{counter}"
    total = _THANKS_MS + _GOAL_PLAY_MS
    text_pct = _THANKS_MS / total * 100
    img_pct = text_pct + 0.5  # tiny gap so text snaps off before img snaps on
    gif_url = f'url("data:image/gif;base64,{_GOAL_B64}")'
    st.markdown(
        f"""
        <div class="{cls}">
          <div class="{cls}-text">
            Kiitoksia että jaksoit täyttää kaikki kohdat!<br/>
            Tässä palkintona jaksamisesta mestarin taidonnäyte.
          </div>
          <div class="{cls}-img"></div>
        </div>
        <style>
        .{cls} {{
            position: fixed;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
            z-index: 9999;
            background: radial-gradient(
                ellipse at center,
                rgba(8, 24, 14, 0.75) 0%,
                rgba(2, 8, 5, 0.0)  75%
            );
            animation: {cls}-bg {total}ms linear forwards;
        }}
        .{cls}-text {{
            position: absolute;
            max-width: 80vmin;
            text-align: center;
            font-family: 'Bungee', 'Impact', sans-serif;
            font-size: clamp(1.1rem, 2.6vmin, 1.9rem);
            line-height: 1.4;
            color: #ffd95c;
            text-shadow: 2px 2px 0 #1a1408, 0 0 12px rgba(255,126,28,0.55);
            opacity: 1;
            animation: {cls}-text {total}ms linear forwards;
        }}
        .{cls}-img {{
            position: absolute;
            width: 480px;
            height: 270px;
            background-image: none;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            filter: drop-shadow(0 14px 32px rgba(0, 0, 0, 0.75));
            animation: {cls}-img {total}ms linear forwards;
        }}
        @keyframes {cls}-bg {{
            0%, 99% {{ opacity: 1; }}
            100%    {{ opacity: 0; visibility: hidden; }}
        }}
        @keyframes {cls}-text {{
            0%              {{ opacity: 1; }}
            {text_pct:.3f}% {{ opacity: 1; }}
            {img_pct:.3f}%  {{ opacity: 0; }}
            100%            {{ opacity: 0; }}
        }}
        @keyframes {cls}-img {{
            0%              {{ background-image: none; }}
            {text_pct:.3f}% {{ background-image: none; }}
            {img_pct:.3f}%  {{ background-image: {gif_url}; }}
            100%            {{ background-image: {gif_url}; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def consume_pending() -> None:
    """Render any queued overlay, then clear the flag.

    Each emission carries a unique counter so Streamlit's markdown diff
    treats it as a new element — otherwise back-to-back celebrations would
    reuse the previous DOM node and the CSS animation wouldn't replay.
    """
    team = st.session_state.pop("pending_celebrate", None)
    if team and _PIRLO_B64:
        _emit_overlay(_PIRLO_B64, "pirlo-cele", "Pirlo celebrates")

    if st.session_state.pop("pending_celebrate_groups", False) and _DIEGO_B64:
        _emit_overlay(_DIEGO_B64, "diego-cele", "Diego celebrates")

    if st.session_state.pop("pending_celebrate_submit", False) and _GOAL_B64:
        _emit_thanks_then_goal()
