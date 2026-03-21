import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import notes_cli  # noqa: E402


class NotesCliFolderTests(unittest.TestCase):
    @mock.patch("notes_cli.notes_applescript.create_folder")
    def test_create_folder_accepts_parent_path(self, create_folder_mock):
        create_folder_mock.return_value = {"id": "folder-2", "path": "Parent/Child"}

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["create-folder", "--name", "Child", "--parent-path", "Parent"])

        self.assertEqual(exit_code, 0)
        create_folder_mock.assert_called_once_with(name="Child", parent_id=None, parent_path="Parent")
        self.assertEqual(json.loads(stdout.getvalue())["path"], "Parent/Child")

    def test_rename_folder_requires_identifier(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["rename-folder", "--name", "Renamed"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": "rename-folder requires --id or --path, plus --name."},
        )

    @mock.patch("notes_cli.notes_applescript.delete_folder")
    def test_delete_folder_allows_non_empty_folder(self, delete_folder_mock):
        delete_folder_mock.return_value = {"id": "folder-1", "deleted": True}

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["delete-folder", "--id", "folder-1"])

        self.assertEqual(exit_code, 0)
        delete_folder_mock.assert_called_once_with(folder_id="folder-1", path=None)
        self.assertTrue(json.loads(stdout.getvalue())["deleted"])

    @mock.patch("notes_cli.notes_applescript.move_note")
    def test_move_note_requires_note_and_folder_identifiers(self, move_note_mock):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["move-note", "--id", "note-1"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": "move-note requires a note identifier and a destination folder identifier."},
        )
        move_note_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
