#!/bin/bash
# Playwright smoke test fired by Claude Code's PostToolUse hook (Edit|Write).
#
# Flow:
#   1. Read the hook's stdin JSON and extract tool_input.file_path.
#   2. Skip unless the edited file is part of the Streamlit UI.
#   3. Skip if Streamlit isn't running on :8501 (no server to smoke).
#   4. Drive Chromium via Playwright: load `/`, screenshot, capture errors.
#   5. Exit 2 if the page raised a JS error or Streamlit rendered a Python
#      traceback — code 2 surfaces the failure back to the model.
#
# Logs + screenshots: /tmp/claude-smoke/
set -uo pipefail

SMOKE_DIR=/tmp/claude-smoke
LOG="$SMOKE_DIR/log.txt"
mkdir -p "$SMOKE_DIR"

INPUT=$(cat)

# Extract the changed file path. python3 is used instead of jq so the hook
# has no external deps; swap to `jq -r '.tool_input.file_path // ""'` once
# jq is installed if you prefer.
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or '')" \
  2>/dev/null || echo "")

# Skip if the edit wasn't to a UI file
if [[ ! "$FILE_PATH" =~ (app_pages/.*\.py|streamlit_app.*\.py|assets/.*\.(css|html)|\.cortex/.*\.sh)$ ]]; then
  exit 0
fi

# Skip if no Streamlit dev server is up — nothing to smoke
if ! curl -fsS -o /dev/null --max-time 2 http://localhost:8501/ 2>/dev/null; then
  echo "[$(date '+%H:%M:%S')] $FILE_PATH — no server on :8501, skipping" >> "$LOG"
  exit 0
fi

# Run the actual smoke test
exec /usr/bin/python3 - <<'PY'
import os, sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

SMOKE_DIR = Path("/tmp/claude-smoke")
LOG = SMOKE_DIR / "log.txt"
URL = "http://localhost:8501/"
TS = time.strftime("%Y%m%d-%H%M%S")

errors: list[str] = []
console_errors: list[str] = []

def log(msg: str) -> None:
    with LOG.open("a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(msg)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(f"{m.type}: {m.text}")
                if m.type == "error" else None)
        page.goto(URL, wait_until="networkidle", timeout=20000)
        # Streamlit renders progressively; wait for the script to settle.
        try:
            page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        # Streamlit renders Python tracebacks as visible text on the page.
        # Detect the standard error banner / "Traceback" text.
        body_text = page.inner_text("body").lower()
        page_traceback = "traceback" in body_text and "most recent call last" in body_text

        shot = SMOKE_DIR / f"smoke-{TS}.png"
        page.screenshot(path=str(shot), full_page=True)
        ctx.close()
        browser.close()

    if errors or console_errors or page_traceback:
        log(f"FAIL → {shot}")
        for e in errors:         log(f"  pageerror: {e}")
        for e in console_errors: log(f"  console: {e}")
        if page_traceback:       log("  python traceback rendered on page")
        sys.exit(2)
    log(f"OK   → {shot}")
    sys.exit(0)
except Exception as e:
    log(f"smoke crashed: {e}")
    sys.exit(0)  # don't block edits if Playwright itself fails
PY
