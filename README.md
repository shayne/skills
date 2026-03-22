# Codex Skills

This repo contains reusable Codex skills. Each skill lives in `skills/<skill-name>/` with a `SKILL.md` entrypoint and any supporting scripts, references, or tests that skill needs.

## Skills
- `apple-notes` - Read, search, create, update, delete, organize, and move content in local Apple Notes on macOS through tested helper scripts.
- `crossword-solver` - Solve crossword puzzles in .puz format using the cursewords terminal app. Use when asked to open, navigate, solve, check, or fill crossword grids in cursewords, or when clues need to be listed/parsed from a .puz file.
- `gh-draft-release` - Draft a user-facing GitHub release for an explicit version or a patch, minor, or major bump request.
- `install-system-package` - Declaratively install missing or useful packages on macOS hosts managed by nix-darwin, preferring Nix packages first and confirming scope before editing config.
- `terminal-controller` - Programmatically control tmux sessions and panes: create sessions/windows, send keys/text, capture pane output, resize to client dimensions, and stream pane output. Use when asked to automate or interact with terminal sessions via tmux.

Example prompts:
- `use $apple-notes to move my meeting notes into the Projects/Planning folder`
- `use $gh-draft-release to prepare the next patch release draft`
- `use $install-system-package to add ripgrep declaratively on this Mac`
- `use $terminal-controller and $crossword-solver to solve the puz file`

## Install in Codex
Codex loads skills from these locations (higher precedence first):

- `$CWD/.codex/skills`
- `$CWD/../.codex/skills`
- `$REPO_ROOT/.codex/skills`
- `$CODEX_HOME/skills` (default `~/.codex/skills` on macOS/Linux)
- `/etc/codex/skills`

To install from this repo, copy or symlink any skill folder into one of those locations. For example:

```sh
SKILL_NAME=apple-notes
mkdir -p .codex/skills
ln -s "$(pwd)/skills/$SKILL_NAME" ".codex/skills/$SKILL_NAME"
```

For GitHub installs, use `$skill-installer` in Codex with the specific skill folder URL:

```sh
$skill-installer install https://github.com/shayne/skills/tree/main/skills/<skill-name>
```

After installing skills, restart Codex to pick them up.
