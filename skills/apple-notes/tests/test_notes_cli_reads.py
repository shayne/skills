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


class NotesCliReadTests(unittest.TestCase):
    @mock.patch("notes_cli.notes_applescript.list_folders")
    def test_list_folders_prints_json(self, list_folders_mock):
        list_folders_mock.return_value = [{"id": "folder-1", "name": "Notes", "shared": False}]

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["list-folders"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            [{"id": "folder-1", "name": "Notes", "shared": False}],
        )

    @mock.patch("notes_cli.notes_applescript.find_notes_by_title")
    @mock.patch("notes_cli.notes_applescript.get_note_by_id")
    def test_read_note_prefers_id_over_title(self, get_note_by_id_mock, find_notes_by_title_mock):
        get_note_by_id_mock.return_value = {"id": "note-1", "name": "Target", "plaintext": "hello"}

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["read-note", "--id", "note-1", "--title", "Target"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["id"], "note-1")
        get_note_by_id_mock.assert_called_once_with("note-1")
        find_notes_by_title_mock.assert_not_called()

    @mock.patch("notes_cli.notes_applescript.list_notes")
    def test_list_notes_prints_json(self, list_notes_mock):
        list_notes_mock.return_value = [{"id": "note-1", "name": "Target", "plaintext": "hello"}]

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["list-notes"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            [{"id": "note-1", "name": "Target", "plaintext": "hello"}],
        )

    @mock.patch("notes_cli.notes_applescript.search_notes")
    def test_search_note_rejects_ambiguous_matches(self, search_notes_mock):
        search_notes_mock.return_value = [
            {"id": "note-1", "name": "Target"},
            {"id": "note-2", "name": "Target"},
        ]

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["search-notes", "--query", "Target", "--expect-one"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": 'Multiple notes matched query "Target". Provide a note id.'},
        )


if __name__ == "__main__":
    unittest.main()
