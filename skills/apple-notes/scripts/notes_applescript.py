import html
import json
import subprocess
import time
from pathlib import Path


APPLESCRIPT_JSON_HELPERS = """
on replaceText(findText, replaceText, sourceText)
\tset AppleScript's text item delimiters to findText
\tset parts to text items of sourceText
\tset AppleScript's text item delimiters to replaceText
\tset outputText to parts as text
\tset AppleScript's text item delimiters to ""
\treturn outputText
end replaceText

on jsonString(valueText)
\tif valueText is missing value then return "null"
\tset sourceText to valueText as text
\tset sourceText to my replaceText("\\\\", "\\\\\\\\", sourceText)
\tset sourceText to my replaceText("\\"", "\\\\\\"", sourceText)
\tset sourceText to my replaceText(return, "\\\\n", sourceText)
\tset sourceText to my replaceText(linefeed, "\\\\n", sourceText)
\tset sourceText to my replaceText(tab, "\\\\t", sourceText)
\treturn "\\"" & sourceText & "\\""
end jsonString

on joinList(itemList, delimiterText)
\tset AppleScript's text item delimiters to delimiterText
\tset outputText to itemList as text
\tset AppleScript's text item delimiters to ""
\treturn outputText
end joinList

on pad2(numberValue)
\tif numberValue < 10 then
\t\treturn "0" & (numberValue as text)
\tend if
\treturn numberValue as text
end pad2

on monthNumber(monthValue)
\tset monthNames to {January, February, March, April, May, June, July, August, September, October, November, December}
\trepeat with i from 1 to count monthNames
\t\tif item i of monthNames is monthValue then return i
\tend repeat
\treturn 1
end monthNumber

on isoDate(dateValue)
\tif dateValue is missing value then return "null"
\tset yearValue to year of dateValue as integer
\tset monthValue to my monthNumber(month of dateValue)
\tset dayValue to day of dateValue as integer
\tset timeValue to time of dateValue
\tset hourValue to timeValue div hours
\tset minuteValue to (timeValue mod hours) div minutes
\tset secondValue to timeValue mod minutes
\treturn my jsonString((yearValue as text) & "-" & my pad2(monthValue) & "-" & my pad2(dayValue) & "T" & my pad2(hourValue) & ":" & my pad2(minuteValue) & ":" & my pad2(secondValue))
end isoDate
"""


class AppleScriptError(RuntimeError):
    pass


TRANSIENT_APPLESCRIPT_ERROR_FRAGMENTS = (
    "connection is invalid",
    "(-609)",
)


def quote_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _is_transient_applescript_error(message: str) -> bool:
    lowered = message.lower()
    return any(fragment in lowered for fragment in TRANSIENT_APPLESCRIPT_ERROR_FRAGMENTS)


def run_applescript(source: str) -> str:
    for attempt in range(3):
        completed = subprocess.run(
            ["osascript", "-"],
            input=source,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            return completed.stdout.strip()

        message = (completed.stderr or completed.stdout or "AppleScript failed").strip()
        if attempt < 2 and _is_transient_applescript_error(message):
            time.sleep(0.25 * (attempt + 1))
            continue
        raise AppleScriptError(message)


def _load_json(source: str):
    return json.loads(run_applescript(source))


def _json_script(body: str) -> str:
    return APPLESCRIPT_JSON_HELPERS + "\n" + body


def _note_reference(note_id: str) -> str:
    return f"note id {quote_text(note_id)}"


def _folder_reference_by_id(folder_id: str) -> str:
    return f"folder id {quote_text(folder_id)}"


def _text_to_html(value: str) -> str:
    lines = value.splitlines() or [value]
    return "".join(f"<div>{html.escape(line) if line else '<br>'}</div>" for line in lines)


def _build_note_body(*, title: str, text: str | None = None, html_body: str | None = None) -> str:
    title_html = f"<div>{html.escape(title)}</div>"
    if html_body is not None:
        return title_html + html_body.replace("\r", "").replace("\n", "")
    return title_html + _text_to_html(text or "")


def _normalize_folder_paths(folders):
    folder_by_id = {folder["id"]: folder for folder in folders}

    def folder_path(folder):
        parent_id = folder.get("container_id")
        if not parent_id or parent_id not in folder_by_id:
            return folder["name"]
        return f'{folder_path(folder_by_id[parent_id])}/{folder["name"]}'

    for folder in folders:
        folder["path"] = folder_path(folder)
    return folders


def build_folder_tree(folders):
    folders = [dict(folder) for folder in folders]
    nodes = {folder["id"]: {**folder, "children": []} for folder in folders}
    roots = []
    for folder in folders:
        node = nodes[folder["id"]]
        parent_id = folder.get("container_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


def list_folders():
    script = _json_script(
        """
tell application "Notes"
\tset defaultAccount to default account
\tset folderJson to {}
\trepeat with f in every folder of defaultAccount
\t\ttry
\t\t\tset parentId to missing value
\t\t\tset parentName to missing value
\t\t\tset parentContainer to container of f
\t\t\tif class of parentContainer is folder then
\t\t\t\tset parentId to id of parentContainer
\t\t\t\tset parentName to name of parentContainer
\t\t\tend if
\t\t\tset end of folderJson to "{" & "\\"id\\":" & my jsonString(id of f) & "," & "\\"name\\":" & my jsonString(name of f) & "," & "\\"shared\\":" & ((shared of f) as text) & "," & "\\"container_id\\":" & my jsonString(parentId) & "," & "\\"container_name\\":" & my jsonString(parentName) & "," & "\\"note_count\\":" & (count of notes of f) & "}"
\t\ton error errMsg number errNum
\t\t\t-- Skip stale folder references that appear briefly after moving folders to Trash.
\t\tend try
\tend repeat
\treturn "[" & my joinList(folderJson, ",") & "]"
end tell
"""
    )
    return _normalize_folder_paths(_load_json(script))


def resolve_folder(folder_id: str | None = None, path: str | None = None, name: str | None = None):
    folders = list_folders()
    if folder_id:
        matches = [folder for folder in folders if folder["id"] == folder_id]
    elif path:
        matches = [folder for folder in folders if folder.get("path") == path]
    elif name:
        matches = [folder for folder in folders if folder.get("name") == name]
    else:
        return None
    if not matches:
        return None
    if len(matches) > 1:
        label = path or name or folder_id
        raise AppleScriptError(f'Multiple folders matched "{label}". Provide a folder id.')
    return matches[0]


def list_notes(folder: str | None = None):
    script = _json_script(
        """
tell application "Notes"
\tset noteJson to {}
\trepeat with n in every note of default account
\t\tset noteFolder to container of n
\t\tset notePlaintext to missing value
\t\tset noteBody to missing value
\t\ttry
\t\t\tset notePlaintext to plaintext of n
\t\tend try
\t\ttry
\t\t\tset noteBody to body of n
\t\tend try
\t\tset end of noteJson to "{" & "\\"id\\":" & my jsonString(id of n) & "," & "\\"name\\":" & my jsonString(name of n) & "," & "\\"folder_id\\":" & my jsonString(id of noteFolder) & "," & "\\"folder_name\\":" & my jsonString(name of noteFolder) & "," & "\\"plaintext\\":" & my jsonString(notePlaintext) & "," & "\\"body_html\\":" & my jsonString(noteBody) & "," & "\\"creation_date\\":" & my isoDate(creation date of n) & "," & "\\"modification_date\\":" & my isoDate(modification date of n) & "," & "\\"password_protected\\":" & ((password protected of n) as text) & "," & "\\"shared\\":" & ((shared of n) as text) & "}"
\tend repeat
\treturn "[" & my joinList(noteJson, ",") & "]"
end tell
"""
    )
    notes = _load_json(script)
    if folder is None:
        return notes
    resolved_folder = resolve_folder(folder_id=folder) or resolve_folder(path=folder) or resolve_folder(name=folder)
    if not resolved_folder:
        raise AppleScriptError(f'Folder "{folder}" not found.')
    return [note for note in notes if note.get("folder_id") == resolved_folder["id"]]


def get_note_by_id(note_id: str):
    for note in list_notes():
        if note.get("id") == note_id:
            return note
    return None


def find_notes_by_title(title: str):
    return [note for note in list_notes() if note.get("name") == title]


def search_notes(query: str):
    needle = query.casefold()
    return [
        note
        for note in list_notes()
        if needle in (note.get("name") or "").casefold() or needle in (note.get("plaintext") or "").casefold()
    ]


def create_folder(*, name: str, parent_id: str | None = None, parent_path: str | None = None):
    parent_folder = resolve_folder(folder_id=parent_id, path=parent_path) if (parent_id or parent_path) else None
    target = _folder_reference_by_id(parent_folder["id"]) if parent_folder else "default account"
    script = f"""
tell application "Notes"
\tset newFolder to make new folder at {target} with properties {{name:{quote_text(name)}}}
\treturn id of newFolder
end tell
"""
    folder_id = run_applescript(script)
    time.sleep(0.1)
    return resolve_folder(folder_id=folder_id) or {"id": folder_id, "name": name}


def rename_folder(*, folder_id: str | None = None, path: str | None = None, name: str):
    folder = resolve_folder(folder_id=folder_id, path=path)
    if not folder:
        raise AppleScriptError("Folder not found.")
    script = f"""
tell application "Notes"
\tset name of {_folder_reference_by_id(folder["id"])} to {quote_text(name)}
\treturn id of {_folder_reference_by_id(folder["id"])}
end tell
"""
    run_applescript(script)
    time.sleep(0.1)
    return resolve_folder(folder_id=folder["id"]) or {"id": folder["id"], "name": name}


def delete_folder(*, folder_id: str | None = None, path: str | None = None):
    folder = resolve_folder(folder_id=folder_id, path=path)
    if not folder:
        raise AppleScriptError("Folder not found.")
    script = f"""
tell application "Notes"
\tset trashFolder to folder "Trash"
\tmove {_folder_reference_by_id(folder["id"])} to trashFolder
\treturn "ok"
end tell
"""
    run_applescript(script)
    return {"id": folder["id"], "path": folder.get("path"), "deleted": True}


def create_note(*, folder=None, title: str, text=None, html=None):
    target_folder = None
    if folder:
        target_folder = resolve_folder(folder_id=folder) or resolve_folder(path=folder) or resolve_folder(name=folder)
        if not target_folder:
            raise AppleScriptError(f'Folder "{folder}" not found.')
    target = _folder_reference_by_id(target_folder["id"]) if target_folder else "default folder of default account"
    body_html = _build_note_body(title=title, text=text, html_body=html)
    script = f"""
tell application "Notes"
\tset newNote to make new note at {target} with properties {{body:{quote_text(body_html)}}}
\treturn id of newNote
end tell
"""
    note_id = run_applescript(script)
    time.sleep(0.1)
    return get_note_by_id(note_id) or {"id": note_id}


def update_note(*, note_id: str, operation: str, value: str):
    current_note = get_note_by_id(note_id)
    if not current_note:
        raise AppleScriptError(f'Note "{note_id}" not found.')

    if operation == "replace-text":
        body_html = _build_note_body(title=current_note.get("name") or "", text=value)
    elif operation == "replace-html":
        body_html = value.replace("\r", "").replace("\n", "")
    elif operation == "append-text":
        existing_body = current_note.get("body_html") or _build_note_body(
            title=current_note.get("name") or "",
            text=current_note.get("plaintext") or "",
        )
        body_html = existing_body + _text_to_html(value)
    else:
        raise AppleScriptError(f'Unsupported update operation "{operation}".')

    script = f"""
tell application "Notes"
\tset body of {_note_reference(note_id)} to {quote_text(body_html)}
\treturn id of {_note_reference(note_id)}
end tell
"""
    run_applescript(script)
    time.sleep(0.1)
    return get_note_by_id(note_id) or {"id": note_id}


def delete_note(note_id: str):
    script = f"""
tell application "Notes"
\tdelete {_note_reference(note_id)}
\treturn "ok"
end tell
"""
    run_applescript(script)
    return {"id": note_id, "deleted": True}


def move_note(*, note_id: str, folder_id: str | None = None, folder_path: str | None = None):
    folder = resolve_folder(folder_id=folder_id, path=folder_path)
    if not folder:
        raise AppleScriptError("Destination folder not found.")
    script = f"""
tell application "Notes"
\tmove {_note_reference(note_id)} to {_folder_reference_by_id(folder["id"])}
\treturn id of {_note_reference(note_id)}
end tell
"""
    run_applescript(script)
    time.sleep(0.1)
    return get_note_by_id(note_id) or {"id": note_id, "folder_id": folder["id"]}


def list_attachments(note_id: str):
    script = _json_script(
        """
tell application "Notes"
\tset theNote to __NOTE_REFERENCE__
\tset attachmentJson to {}
\trepeat with a in attachments of theNote
\t\tset attachmentUrl to missing value
\t\ttry
\t\t\tset attachmentUrl to URL of a
\t\tend try
\t\tset end of attachmentJson to "{" & "\\"id\\":" & my jsonString(id of a) & "," & "\\"name\\":" & my jsonString(name of a) & "," & "\\"note_id\\":" & my jsonString(id of theNote) & "," & "\\"url\\":" & my jsonString(attachmentUrl) & "," & "\\"creation_date\\":" & my isoDate(creation date of a) & "," & "\\"modification_date\\":" & my isoDate(modification date of a) & "," & "\\"shared\\":" & ((shared of a) as text) & "}"
\tend repeat
\treturn "[" & my joinList(attachmentJson, ",") & "]"
end tell
""".replace("__NOTE_REFERENCE__", _note_reference(note_id))
    )
    return _load_json(script)


def attachment_operation_supported(operation: str) -> bool:
    return operation == "add"


def add_attachment(*, note_id: str, file_path: str):
    absolute_path = str(Path(file_path).expanduser().resolve())
    script = f"""
tell application "Notes"
\tset theNote to {_note_reference(note_id)}
\tset theFile to POSIX file {quote_text(absolute_path)}
\tset newAttachment to make new attachment at theNote with data theFile
\treturn id of newAttachment
end tell
"""
    attachment_id = run_applescript(script)
    time.sleep(0.1)
    for attachment in list_attachments(note_id):
        if attachment.get("id") == attachment_id:
            return attachment
    return {"id": attachment_id, "note_id": note_id, "name": Path(absolute_path).name}


def remove_attachment(*, note_id: str, name: str):
    raise AppleScriptError("Attachment remove is not supported by the current Notes AppleScript interface.")
