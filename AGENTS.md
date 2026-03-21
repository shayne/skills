# Repository Guidelines

## Project Structure & Module Organization
This repository is a collection of reusable Codex skills. Each skill lives under `skills/<skill-name>/` and must expose a top-level `SKILL.md`. Keep supporting material next to the skill that uses it: Python helpers in `scripts/`, reference docs in `references/`, tests in `tests/`, and agent metadata in `agents/openai.yaml` when needed. Root files such as `README.md` and this guide document repository-wide conventions.

## Build, Test, and Development Commands
There is no global build step. Work from the repository root and validate the specific skill you changed.

- `find skills -maxdepth 2 -name SKILL.md | sort` lists registered skill entrypoints.
- `python3 -m unittest discover -s skills/<skill-name>/tests -p 'test_*.py'` runs a skill’s automated tests.
- `python3 skills/apple-notes/scripts/notes_cli.py --help` is a useful smoke test for CLI-based skills.
- `git diff --check` catches trailing whitespace and malformed patches before review.

## Coding Style & Naming Conventions
Use kebab-case for skill directories such as `apple-notes` and keep the entry file name exactly `SKILL.md`. Follow existing Python style in this repo: 4-space indentation, standard-library imports first, `snake_case` for modules and functions, and `test_*.py` for test files. No repo-wide formatter is configured, so match the surrounding code and keep Markdown concise and task-oriented.

## Testing Guidelines
Add or update tests whenever you change Python helpers or command behavior. Co-locate tests under the owning skill, for example `skills/terminal-controller/tests/test_tmux_control.py`. Prefer focused unit tests with `unittest` and `unittest.mock`; avoid tests that depend on live system state when a mock covers the behavior. For documentation-only changes, at minimum run `git diff --check`.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit subjects, optionally scoped by skill: `apple-notes: add Apple Notes skill`. Keep commits focused on one skill or one documentation change. Pull requests should summarize the change, list affected paths, and include the exact verification commands you ran. Screenshots are usually unnecessary unless the change affects rendered documentation or another visual artifact.
