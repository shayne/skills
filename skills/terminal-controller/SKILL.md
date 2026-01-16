---
name: terminal-controller
description: "Programmatically control tmux sessions and panes: create sessions/windows, send keys/text, capture pane output, resize to client dimensions, and stream pane output. Use when asked to automate or interact with terminal sessions via tmux."
---

# Terminal Controller

## Overview
Use tmux primitives (or the bundled helper script) to create sessions, send keystrokes, read screen contents, and resize windows/panes in a controlled, repeatable way.

## Quick Start (helper script)
Use `scripts/tmux_control.py` for common actions:
- Create session (defaults to 100x40): `python scripts/tmux_control.py create --name <session> --cwd <dir>`
- Create session without resizing: `python scripts/tmux_control.py create --name <session> --cwd <dir> --no-resize`
- Preferred (input + pause + capture in one call): `python scripts/tmux_control.py step --target <session:window.pane> --text "ls" --enter --sleep-ms 200 --lines 200`
- Control-key prompt (single send): `python scripts/tmux_control.py step --target <session:window.pane> --keys C-g 54 Enter --sleep-ms 150 --lines 200`
- Control-key prompt (split send, more reliable with TUIs that need a moment to open): `python scripts/tmux_control.py keys --target <session:window.pane> C-g; sleep 0.08; python scripts/tmux_control.py send --target <session:window.pane> --text "54" --enter`
- Control-key prompt + confirm (capture, then inspect the output text): `python scripts/tmux_control.py capture --target <session:window.pane> --lines 120`
- Send text: `python scripts/tmux_control.py send --target <session:window.pane> --text "ls" --enter`
- Send keys: `python scripts/tmux_control.py keys --target <session:window.pane> Up Enter`
- Send control/special keys: `python scripts/tmux_control.py keys --target <session:window.pane> C-g BTab`
- Capture output: `python scripts/tmux_control.py capture --target <session:window.pane> --lines 200`
- Resize window: `python scripts/tmux_control.py resize --target <session:window> --width 120 --height 40`
- Fit to client: `python scripts/tmux_control.py fit --session <session>`

## tmux Primitives (direct commands)
- Create a session: `tmux new-session -d -s <name> -c <dir>`
- List windows/panes: `tmux list-windows -t <session>`; `tmux list-panes -t <session> -F '#{pane_id} #{pane_index} #{pane_title}'`
- Send literal text: `tmux send-keys -t <session:window.pane> -l "echo hi"`
- Send special keys: `tmux send-keys -t <session:window.pane> Enter` (or `Up`, `C-c`, etc.)
- Capture output: `tmux capture-pane -t <session:window.pane> -p -S -200`
- Resize a window: `tmux resize-window -t <session:window> -x <cols> -y <rows>`
- Stream output to a file: `tmux pipe-pane -t <session:window.pane> -o 'cat >> /tmp/pane.log'`
- Stop streaming: `tmux pipe-pane -t <session:window.pane>`

## Notes and Guardrails
- Target format is usually `session:window.pane` (example: `work:0.0`).
- `capture-pane` only sees what the terminal has rendered (screen + scrollback), not hidden app state.
- For resizing to match an attached client, query it with `tmux list-clients -t <session> -F '#{client_width} #{client_height}'`.
- Session creation defaults to 100x40 unless explicitly disabled with `--no-resize`.
- If a command uses the alternate screen buffer (TUI apps), use `step` after each action to capture the updated screen and avoid frequent resizes.
- tmux key caveats: use `BTab` for Shift+Tab; `Shift+Arrow` may not always be forwarded, so prefer explicit key alternatives when available.
- Prefer `step` over `send`+`capture` combos. Only split calls when a workflow truly requires multiple discrete key presses before any capture.
- When launching a TUI, immediately capture the screen and act on the displayed prompt; do not leave the UI idle.
- `step` reduces round trips: send input, optional pause, then capture in one call.
- `step` sends `--text` before `--keys`. For sequences that must start with a control key, pass the whole sequence via `--keys` (including digits and `Enter`) so it is sent as one tmux command.
- If you need to send a key token that begins with `-` (e.g., `-` or `-1`), insert `--` after `--keys` (or after `keys`) so argparse stops parsing options.
- If you need to send key tokens that start with `-`, insert `--` after `--keys` (example: `--keys -- -`); this prevents argparse from treating them as flags.
- If you see stray digits or flags injected into a TUI, double-check the `step --keys` invocation and re-run with `--keys` plus `--` as needed.
- If a target app needs time to react to a control key (e.g., it opens a prompt and only then accepts digits), split the action into two commands with a short delay between them. This keeps tmux_control generic while allowing reliable interaction with time-sensitive UIs.
  - Example pattern: `tmux_control.py keys --target <pane> C-g; sleep 0.05; tmux_control.py send --target <pane> --text \"123\" --enter`
