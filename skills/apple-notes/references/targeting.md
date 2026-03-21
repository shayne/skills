# Targeting

## Notes

- Prefer note IDs for `read-note`, `update-note`, `delete-note`, `move-note`, and attachment commands.
- Use note titles only when the title resolves to exactly one note.
- If multiple notes match a title or search query, stop and ask for disambiguation.

## Folders

- Prefer folder IDs for rename, delete, and move destinations.
- Support folder paths like `Parent/Child` for discovery and human-friendly targeting.
- If multiple folders share the same name in different branches, require a folder ID or full path.
