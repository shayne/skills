---
name: crossword-solver
description: Solve crossword puzzles in .puz format using the cursewords terminal app. Use when asked to open, navigate, solve, check, or fill crossword grids in cursewords, or when clues need to be listed/parsed from a .puz file.
---

# Crossword Solver

## Overview
Use cursewords to open a .puz file, read the on-screen clue, and fill answers in the terminal. Solve in the interactive TUI one clue at a time, driven by what is currently shown on screen; do not pre-solve a list of answers or batch-fill.

## Quick Start
- Open the puzzle: `uvx cursewords <puzzle.puz>` (or `cursewords <puzzle.puz>` if installed).
- Downs-only mode: `uvx cursewords --downs-only <puzzle.puz>`.
- If the terminal size changes, quit and reopen; cursewords does not adapt well to resizing.

## Workflow
1. Open the puzzle interactively with `uvx cursewords <puzzle.puz>`.
2. Immediately read the current clue displayed in the TUI (usually 1-Across).
3. Solve that clue from the on-screen prompt and type the answer directly into the grid.
4. After typing the full answer, check the cursor (block) position. Cursewords typically auto-advances to the next clue when the word is fully filled, so do **not** press `Tab` unless the cursor did not advance.
5. Use `Ctrl+G` only when you need to jump to a specific number, not as the default flow. If you trigger the prompt, enter the number + Enter promptly or the input may go into the grid.
6. Use crosses to verify uncertain entries and keep going one clue at a time.
7. After any input, capture the TUI screen so the next clue is visible before acting again.
8. When the TUI shows the completion message, confirm success and stop. Do not save or quit unless the user explicitly asks.

## Fast Entry (still using cursewords UI)
Only use batch entry if the user explicitly asks for batch entry. If the user asks to solve in the TUI clue-by-clue, do not use batch entry.

## Keybindings (cursewords)
- `Tab` / `Shift+Tab`: move to the next/previous clue in the current direction (in tmux, use `BTab` for Shift+Tab).
- Arrow keys: move the cursor; moving perpendicular will usually switch direction.
- `Space`: toggle Across/Down at the current square.
- `Enter`: toggle Across/Down at the current square.
- `Shift+Arrow`: move perpendicular to the current direction.
- `Page Up` / `Page Down`: jump between words.
- `[` / `{`: move perpendicular backward; `{` skips to the previous blank.
- `]` / `}`: move perpendicular forward; `}` skips to the next blank.
- `Ctrl+G`: go to a numbered square (type number, press Enter).
- `Ctrl+C`: check square/word/puzzle.
- `Ctrl+R`: reveal square/word/puzzle.
- `Ctrl+X`: clear all entries.
- `Ctrl+Z`: reset puzzle state.
- `Ctrl+P`: pause/unpause the puzzle.
- `Ctrl+S`: save.
- `Ctrl+Q`: quit.

## Solving Guidance
- Fill the easiest Across/Down entries first to build cross letters.
- Use crossings to confirm proper nouns and abbreviations.
- Keep answers in all caps; cursewords expects letters only.
- `Space` is the quickest way to verify direction: it flips the clue line between ACROSS/DOWN for the current square.
- `Tab`/`BTab` behavior depends on the current cell: from a blank it jumps to the next word, from a filled cell it moves within the word to the next blank.
- Overwrite behavior (from source):
  - Typing over a filled square turns on overwrite mode and advances within the word, cycling through already-filled squares and wrapping if needed.
  - When not overwriting, letter entry skips filled squares and advances to the next blank in the current word; if no blanks remain, it jumps to the next word.
  - `Backspace` clears the current cell and retreats within the word (or to the previous word end); `Delete` clears and advances within the word.
- Avoid typing digits unless the `Ctrl+G` prompt is active; numbers will be entered into the grid.
- Do not use `Ctrl+C` (check) or any check/reveal functionality; solve without assistance.
- Do not pre-compute or list all answers outside the TUI when the request is to solve one clue at a time.
- Do not try to install parsing libraries or write custom scripts when the request is to use cursewords via `uvx`.
- Avoid leaving the TUI idle after launch; always act on the displayed clue.
- Treat `Ctrl+Z` as destructive: it resets the puzzle. Only use it if explicitly asked to reset.
- Backspace behavior can be unreliable in tmux; prefer overwriting letters or use `Ctrl+X` only if you intend to clear the entire puzzle.
- tmux + automation caveat: when driving cursewords via tmux tooling, `Ctrl+G`, `Backspace`, and `Delete` can misfire and inject digits/garbage into the grid. If go-to fails, navigate with arrow keys and overwrite with letters; do not quit or restart due to corruption.
- Corruption recovery (do this instead of quitting):
  - Identify the corrupted word from the visible clue or by moving to the word start with arrow keys.
  - Re-enter the correct answer by typing the full word to overwrite the bad cells (overwrite mode will advance).
  - If only a single cell is wrong, move to it and type the correct letter to overwrite.
  - If the direction is wrong, use `Space` once to toggle, then overwrite the word again.
  - After cleanup, capture the screen and continue with the next clue.
- `Ctrl+G` uses a digit-only prompt (`Enter` or any non-digit immediately cancels). It reads with a timeout, so if you don't see the "Enter square number:" prompt, the digits will spill into the grid. In tmux automation, add a short delay between `C-g` and digits to let the prompt appear. Example: `tmux_control.py keys --target <pane> C-g; sleep 0.05; tmux_control.py send --target <pane> --text \"54\" --enter`. Sending everything at once can be too fast; waiting too long can time out the prompt.
- When using `tmux_control.py step --keys`, add `--` if you need to send keys that start with `-`, or split the `keys`/`capture` calls; otherwise option-looking tokens (like `--lines 200`) can be mis-sent to the grid.
- Direction hygiene: after a go-to, read the clue line to confirm Across/Down; do not tap `Space` unless you must change direction. Toggling blindly can overwrite filled across entries when you start typing a down answer (or vice versa).
- Cross-reference handling: when a clue says "See X-Down/Across," use cursewords go-to (`Ctrl+G`, number, `Enter`) to jump to that referenced clue, read/solve it, then go back to the original clue and fill the answer.
