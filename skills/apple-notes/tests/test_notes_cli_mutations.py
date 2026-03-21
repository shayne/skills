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


class NotesCliMutationTests(unittest.TestCase):
    def test_create_note_requires_title_and_content(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["create-note", "--folder", "Notes", "--title", "Draft"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": "create-note requires --title and one content flag."},
        )

    def test_update_note_requires_explicit_content_mode(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["update-note", "--id", "note-1"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": "update-note requires exactly one content operation."},
        )

    @mock.patch("notes_cli.notes_applescript.find_notes_by_title")
    def test_delete_note_rejects_ambiguous_title_lookup(self, find_notes_by_title_mock):
        find_notes_by_title_mock.return_value = [
            {"id": "note-1", "name": "Draft"},
            {"id": "note-2", "name": "Draft"},
        ]

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["delete-note", "--title", "Draft"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": 'Multiple notes matched title "Draft". Provide a note id.'},
        )


if __name__ == "__main__":
    unittest.main()
