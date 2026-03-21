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


class NotesCliAttachmentTests(unittest.TestCase):
    @mock.patch("notes_cli.notes_applescript.list_attachments")
    def test_list_attachments_returns_metadata(self, list_attachments_mock):
        list_attachments_mock.return_value = [
            {"id": "att-1", "name": "sample-attachment.txt", "note_id": "note-1"}
        ]

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(["list-attachments", "--id", "note-1"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            [{"id": "att-1", "name": "sample-attachment.txt", "note_id": "note-1"}],
        )

    @mock.patch("notes_cli.notes_applescript.attachment_operation_supported")
    def test_add_attachment_reports_unsupported_when_capability_check_fails(
        self, attachment_operation_supported_mock
    ):
        attachment_operation_supported_mock.return_value = False

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(
                ["add-attachment", "--id", "note-1", "--file", "/tmp/sample-attachment.txt"]
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": "Attachment add is not supported by the current Notes AppleScript interface."},
        )

    @mock.patch("notes_cli.notes_applescript.attachment_operation_supported")
    def test_remove_attachment_reports_unsupported_when_capability_check_fails(
        self, attachment_operation_supported_mock
    ):
        attachment_operation_supported_mock.return_value = False

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = notes_cli.main(
                ["remove-attachment", "--id", "note-1", "--name", "sample-attachment.txt"]
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {"error": "Attachment remove is not supported by the current Notes AppleScript interface."},
        )


if __name__ == "__main__":
    unittest.main()
