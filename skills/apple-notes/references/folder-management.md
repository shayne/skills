# Folder Management

## Scope

- Limit folder mutations to the default Notes account.
- Support nested folders.
- Support flat listing and tree listing.

## Supported Operations

- Create a root folder.
- Create a child folder under a parent folder path or ID.
- Rename a folder by ID or path.
- Delete a folder by ID or path.
- Move a note between folders by note ID and folder ID or path.

## Delete Semantics

- Delete non-empty folders by moving them to the built-in `Trash` folder when the target is unambiguous.
- Do not add a confirmation prompt at the skill layer unless the user asks for one.
- Prefer the `Trash` move over raw `delete folder ...`, which is not reliable in Notes AppleScript.
