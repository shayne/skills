---
name: apple-notes
description: Read, search, create, update, delete, organize, and move content in local Apple Notes on macOS through tested helper scripts. Use when Codex needs to work with notes, folders, nested folders, note attachments, or note metadata without relying on browser session data.
---

# Apple Notes

## Overview

Use the helper CLI in `scripts/notes_cli.py` instead of writing ad hoc AppleScript. The CLI handles JSON output, ambiguity checks, folder-path resolution, and known Notes API limits.

## Workflow

1. Start with discovery commands.
2. Prefer note IDs and folder IDs for mutations.
3. Use note titles or folder paths only for discovery or when the match is unique.
4. If a title or path matches multiple objects, stop and ask for disambiguation.
5. Keep folder mutations inside the default Notes account.

## Commands

Use these commands directly:

- `python3 scripts/notes_cli.py list-folders`
- `python3 scripts/notes_cli.py list-folders --tree`
- `python3 scripts/notes_cli.py create-folder --name "Parent"`
- `python3 scripts/notes_cli.py create-folder --name "Child" --parent-path "Parent"`
- `python3 scripts/notes_cli.py rename-folder --id "<folder-id>" --name "Renamed"`
- `python3 scripts/notes_cli.py delete-folder --id "<folder-id>"`
- `python3 scripts/notes_cli.py list-notes`
- `python3 scripts/notes_cli.py read-note --id "<note-id>"`
- `python3 scripts/notes_cli.py search-notes --query "keyword"`
- `python3 scripts/notes_cli.py create-note --folder "Parent/Child" --title "Draft" --text "hello"`
- `python3 scripts/notes_cli.py update-note --id "<note-id>" --append-text "more text"`
- `python3 scripts/notes_cli.py move-note --id "<note-id>" --folder-id "<folder-id>"`
- `python3 scripts/notes_cli.py delete-note --id "<note-id>"`
- `python3 scripts/notes_cli.py list-attachments --id "<note-id>"`
- `python3 scripts/notes_cli.py add-attachment --id "<note-id>" --file /path/to/file`

## Mutation Rules

- Prefer `--id` for note and folder mutations.
- Allow folder paths like `Parent/Child` for discovery and human-friendly targeting.
- Support note body updates through exactly one content mode at a time.
- Delete non-empty folders without prompting if the target is unambiguous.
- Do not try to unlock password-protected notes.
- Do not fall back to UI scripting for unsupported attachment operations.

## References

- Read `references/notes-api.md` for Notes-specific behavior such as `body` vs `plaintext`.
- Read `references/targeting.md` for ambiguity and ID-first rules.
- Read `references/folder-management.md` for default-account folder scope and nested path behavior.
- Read `references/attachment-caveats.md` for current attachment support limits.
