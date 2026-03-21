import argparse
import json

import notes_applescript


def emit_json(data) -> None:
    print(json.dumps(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes_cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_folders_parser = subparsers.add_parser("list-folders")
    list_folders_parser.add_argument("--tree", action="store_true")

    create_folder_parser = subparsers.add_parser("create-folder")
    create_folder_parser.add_argument("--name")
    create_folder_parser.add_argument("--parent-id")
    create_folder_parser.add_argument("--parent-path")

    rename_folder_parser = subparsers.add_parser("rename-folder")
    rename_folder_parser.add_argument("--id")
    rename_folder_parser.add_argument("--path")
    rename_folder_parser.add_argument("--name")

    delete_folder_parser = subparsers.add_parser("delete-folder")
    delete_folder_parser.add_argument("--id")
    delete_folder_parser.add_argument("--path")

    move_note_parser = subparsers.add_parser("move-note")
    move_note_parser.add_argument("--id")
    move_note_parser.add_argument("--title")
    move_note_parser.add_argument("--folder-id")
    move_note_parser.add_argument("--folder-path")

    subparsers.add_parser("list-notes")

    read_note_parser = subparsers.add_parser("read-note")
    read_note_parser.add_argument("--id")
    read_note_parser.add_argument("--title")

    search_notes_parser = subparsers.add_parser("search-notes")
    search_notes_parser.add_argument("--query", required=True)
    search_notes_parser.add_argument("--expect-one", action="store_true")

    create_note_parser = subparsers.add_parser("create-note")
    create_note_parser.add_argument("--folder")
    create_note_parser.add_argument("--title")
    create_note_parser.add_argument("--text")
    create_note_parser.add_argument("--html")

    update_note_parser = subparsers.add_parser("update-note")
    update_note_parser.add_argument("--id")
    update_note_parser.add_argument("--replace-text")
    update_note_parser.add_argument("--replace-html")
    update_note_parser.add_argument("--append-text")

    delete_note_parser = subparsers.add_parser("delete-note")
    delete_note_parser.add_argument("--id")
    delete_note_parser.add_argument("--title")

    list_attachments_parser = subparsers.add_parser("list-attachments")
    list_attachments_parser.add_argument("--id")
    list_attachments_parser.add_argument("--title")

    add_attachment_parser = subparsers.add_parser("add-attachment")
    add_attachment_parser.add_argument("--id")
    add_attachment_parser.add_argument("--title")
    add_attachment_parser.add_argument("--file")

    remove_attachment_parser = subparsers.add_parser("remove-attachment")
    remove_attachment_parser.add_argument("--id")
    remove_attachment_parser.add_argument("--title")
    remove_attachment_parser.add_argument("--name")

    return parser


def emit_error(message: str) -> int:
    emit_json({"error": message})
    return 1


def resolve_note_id(*, note_id: str | None = None, title: str | None = None):
    if note_id:
        return note_id
    matches = notes_applescript.find_notes_by_title(title)
    if len(matches) != 1:
        raise notes_applescript.AppleScriptError(f'Multiple notes matched title "{title}". Provide a note id.')
    return matches[0]["id"]


def main(argv=None) -> int:
    try:
        args = build_parser().parse_args(argv)

        if args.command == "list-folders":
            folders = notes_applescript.list_folders()
            emit_json(notes_applescript.build_folder_tree(folders) if args.tree else folders)
            return 0

        if args.command == "create-folder":
            if not args.name:
                return emit_error("create-folder requires --name.")
            emit_json(
                notes_applescript.create_folder(
                    name=args.name,
                    parent_id=args.parent_id,
                    parent_path=args.parent_path,
                )
            )
            return 0

        if args.command == "rename-folder":
            if not args.name or (not args.id and not args.path):
                return emit_error("rename-folder requires --id or --path, plus --name.")
            emit_json(notes_applescript.rename_folder(folder_id=args.id, path=args.path, name=args.name))
            return 0

        if args.command == "delete-folder":
            if not args.id and not args.path:
                return emit_error("delete-folder requires --id or --path.")
            emit_json(notes_applescript.delete_folder(folder_id=args.id, path=args.path))
            return 0

        if args.command == "move-note":
            if (not args.id and not args.title) or (not args.folder_id and not args.folder_path):
                return emit_error("move-note requires a note identifier and a destination folder identifier.")
            emit_json(
                notes_applescript.move_note(
                    note_id=resolve_note_id(note_id=args.id, title=args.title),
                    folder_id=args.folder_id,
                    folder_path=args.folder_path,
                )
            )
            return 0

        if args.command == "list-notes":
            emit_json(notes_applescript.list_notes())
            return 0

        if args.command == "read-note":
            emit_json(notes_applescript.get_note_by_id(resolve_note_id(note_id=args.id, title=args.title)))
            return 0

        if args.command == "search-notes":
            matches = notes_applescript.search_notes(args.query)
            if args.expect_one and len(matches) != 1:
                return emit_error(f'Multiple notes matched query "{args.query}". Provide a note id.')
            emit_json(matches)
            return 0

        if args.command == "create-note":
            if not args.title or (not args.text and not args.html):
                return emit_error("create-note requires --title and one content flag.")
            emit_json(
                notes_applescript.create_note(
                    folder=args.folder,
                    title=args.title,
                    text=args.text,
                    html=args.html,
                )
            )
            return 0

        if args.command == "update-note":
            operations = {
                "replace-text": args.replace_text,
                "replace-html": args.replace_html,
                "append-text": args.append_text,
            }
            selected = [(name, value) for name, value in operations.items() if value is not None]
            if not args.id or len(selected) != 1:
                return emit_error("update-note requires exactly one content operation.")
            operation, value = selected[0]
            emit_json(notes_applescript.update_note(note_id=args.id, operation=operation, value=value))
            return 0

        if args.command == "delete-note":
            emit_json(notes_applescript.delete_note(resolve_note_id(note_id=args.id, title=args.title)))
            return 0

        if args.command == "list-attachments":
            emit_json(notes_applescript.list_attachments(resolve_note_id(note_id=args.id, title=args.title)))
            return 0

        if args.command == "add-attachment":
            if not notes_applescript.attachment_operation_supported("add"):
                return emit_error("Attachment add is not supported by the current Notes AppleScript interface.")
            emit_json(
                notes_applescript.add_attachment(
                    note_id=resolve_note_id(note_id=args.id, title=args.title),
                    file_path=args.file,
                )
            )
            return 0

        if args.command == "remove-attachment":
            if not notes_applescript.attachment_operation_supported("remove"):
                return emit_error("Attachment remove is not supported by the current Notes AppleScript interface.")
            emit_json(
                notes_applescript.remove_attachment(
                    note_id=resolve_note_id(note_id=args.id, title=args.title),
                    name=args.name,
                )
            )
            return 0

        return emit_error(f"Unsupported command: {args.command}")
    except notes_applescript.AppleScriptError as exc:
        return emit_error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
