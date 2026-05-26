"""Fetch Twemoji SVG flags for every team in schedule_2026.json.

Each team has a flag emoji (e.g. 🇲🇽), made of two Regional Indicator Symbols
that encode the ISO 3166-1 alpha-2 code (M=1F1F2, X=1F1FD). Twemoji ships
each emoji as ``assets/svg/<codepoint-codepoint>.svg``.

Run once, then check ``assets/flags/<iso2>.svg`` into git. The slider reads
those files as base64 at module-import time so Snowflake CSP (no external
URLs) stays happy.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JSON_PATH = os.path.join(ROOT, "data", "schedule_2026.json")
OUT_DIR = os.path.join(ROOT, "assets", "flags")

# Twemoji svg endpoint (jdecked fork — current upstream after Twitter handoff).
URL = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/{cp}.svg"


def emoji_to_iso2(flag: str) -> str:
    """🇲🇽 → 'mx'.  Each char is a Regional Indicator Symbol; subtract base."""
    if len(flag) < 2:
        return ""
    a = ord(flag[0]) - 0x1F1E6  # 'A' base
    b = ord(flag[1]) - 0x1F1E6
    if not (0 <= a < 26 and 0 <= b < 26):
        return ""
    return chr(ord("a") + a) + chr(ord("a") + b)


def emoji_to_codepoint(flag: str) -> str:
    return "-".join(f"{ord(c):x}" for c in flag)


# Flat 4:3 flags fetched from flag-icons instead of Twemoji: their equal
# horizontal bands cropped to a single color when rendered as a waving Twemoji
# illustration. The slider stretch-fills these (see _STRETCH_FILL_ISO in
# app_pages/_momentum_slider.py).
FLAG_ICONS_URL = "https://cdn.jsdelivr.net/gh/lipis/flag-icons@7/flags/4x3/{iso}.svg"
FLAG_ICONS_ISO = {"de", "at"}


def main() -> int:
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)
    fetched: list[str] = []
    failed: list[str] = []
    for en, info in data["teams"].items():
        flag = info.get("flag", "")
        iso = emoji_to_iso2(flag)
        if not iso:
            failed.append(f"{en}: no ISO from {flag!r}")
            continue
        out_path = os.path.join(OUT_DIR, f"{iso}.svg")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            continue
        if iso in FLAG_ICONS_ISO:
            url = FLAG_ICONS_URL.format(iso=iso)
        else:
            url = URL.format(cp=emoji_to_codepoint(flag))
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                svg = r.read()
            if not svg.startswith(b"<"):
                failed.append(f"{en} ({iso}): non-SVG response")
                continue
            # Flag-icons flags stretch-fill the slider's wide-short box end, so
            # they must NOT preserve their 4:3 aspect (default would letterbox
            # the flag and leave transparent margins). Force full stretch.
            if iso in FLAG_ICONS_ISO and b"preserveAspectRatio" not in svg:
                svg = svg.replace(b"<svg ", b'<svg preserveAspectRatio="none" ', 1)
            with open(out_path, "wb") as fout:
                fout.write(svg)
            fetched.append(f"{en} → {iso}.svg ({len(svg)} B)")
        except Exception as e:
            failed.append(f"{en} ({iso}): {e}")
    print(f"Fetched {len(fetched)}:")
    for line in fetched:
        print(f"  {line}")
    if failed:
        print(f"\nFailed {len(failed)}:", file=sys.stderr)
        for line in failed:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
