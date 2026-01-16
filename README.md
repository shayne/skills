# Codex Skills

This repo contains reusable Codex skills.

## Skills
- `crossword-solver` - Solve crossword puzzles in .puz format using the cursewords terminal app. Use when asked to open, navigate, solve, check, or fill crossword grids in cursewords, or when clues need to be listed/parsed from a .puz file.
- `terminal-controller` - Programmatically control tmux sessions and panes: create sessions/windows, send keys/text, capture pane output, resize to client dimensions, and stream pane output. Use when asked to automate or interact with terminal sessions via tmux.

Example prompt:
`use $terminal-controller and $crossword-solver to solve the puz file`

## Install in Codex
Codex loads skills from these locations (higher precedence first):

- `$CWD/.codex/skills`
- `$CWD/../.codex/skills`
- `$REPO_ROOT/.codex/skills`
- `$CODEX_HOME/skills` (default `~/.codex/skills` on macOS/Linux)
- `/etc/codex/skills`

To install from this repo, copy or symlink a skill folder into any of those locations, for example:

```sh
mkdir -p .codex/skills
ln -s "$(pwd)/skills/crossword-solver" .codex/skills/crossword-solver
```

For GitHub installs, use `$skill-installer` in Codex with a folder URL, for example:

```sh
$skill-installer install https://github.com/shayne/skills/tree/main/skills/crossword-solver
```

After installing skills, restart Codex to pick them up.
