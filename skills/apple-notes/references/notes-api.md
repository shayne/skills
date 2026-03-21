# Notes API

## Core Behavior

- Apple Notes exposes `plaintext` as read-only plain text.
- Apple Notes exposes `body` as writable HTML.
- In practice, replacing `body` rewrites the note content, so callers must choose a content mode explicitly.

## Creation And Updates

- Creating a note with `body` HTML works reliably.
- Updating a note by setting `body` works reliably for replace and append flows.
- Folder creation works at the default account root and under an existing folder.
- Moving a note to another folder works through AppleScript.

## Protected Notes

- Password-protected note metadata is visible.
- Content access or mutations may fail on protected notes. Surface that failure directly.
