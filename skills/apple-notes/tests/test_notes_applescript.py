import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import notes_applescript  # noqa: E402


class RunAppleScriptTests(unittest.TestCase):
    @mock.patch("notes_applescript.subprocess.run")
    def test_run_applescript_returns_stdout_on_success(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess(
            args=["osascript", "-e", 'return "ok"'],
            returncode=0,
            stdout="ok\n",
            stderr="",
        )

        result = notes_applescript.run_applescript('return "ok"')

        self.assertEqual(result, "ok")
        run_mock.assert_called_once()

    @mock.patch("notes_applescript.subprocess.run")
    def test_run_applescript_raises_with_stderr_on_failure(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess(
            args=["osascript", "-e", 'error "boom"'],
            returncode=1,
            stdout="",
            stderr="boom\n",
        )

        with self.assertRaises(notes_applescript.AppleScriptError) as exc_info:
            notes_applescript.run_applescript('error "boom"')

        self.assertIn("boom", str(exc_info.exception))

    @mock.patch("notes_applescript.time.sleep")
    @mock.patch("notes_applescript.subprocess.run")
    def test_run_applescript_retries_transient_connection_invalid_errors(self, run_mock, sleep_mock):
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                args=["osascript", "-"],
                returncode=1,
                stdout="",
                stderr="Notes got an error: Connection is invalid. (-609)\n",
            ),
            subprocess.CompletedProcess(
                args=["osascript", "-"],
                returncode=0,
                stdout="ok\n",
                stderr="",
            ),
        ]

        result = notes_applescript.run_applescript('return "ok"')

        self.assertEqual(result, "ok")
        self.assertEqual(run_mock.call_count, 2)
        sleep_mock.assert_called_once()

    @mock.patch("notes_applescript.time.sleep")
    @mock.patch("notes_applescript.subprocess.run")
    def test_run_applescript_raises_after_retry_budget_exhausted(self, run_mock, sleep_mock):
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                args=["osascript", "-"],
                returncode=1,
                stdout="",
                stderr="Notes got an error: Connection is invalid. (-609)\n",
            ),
            subprocess.CompletedProcess(
                args=["osascript", "-"],
                returncode=1,
                stdout="",
                stderr="Notes got an error: Connection is invalid. (-609)\n",
            ),
            subprocess.CompletedProcess(
                args=["osascript", "-"],
                returncode=1,
                stdout="",
                stderr="Notes got an error: Connection is invalid. (-609)\n",
            ),
        ]

        with self.assertRaises(notes_applescript.AppleScriptError) as exc_info:
            notes_applescript.run_applescript('return "still broken"')

        self.assertIn("Connection is invalid", str(exc_info.exception))
        self.assertEqual(run_mock.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 2)

    def test_quote_text_escapes_backslashes_and_quotes(self):
        value = 'one "two" \\ three'

        quoted = notes_applescript.quote_text(value)

        self.assertEqual(quoted, '"one \\"two\\" \\\\ three"')

    @mock.patch("notes_applescript.run_applescript")
    def test_list_folders_parses_json_from_applescript(self, run_applescript_mock):
        run_applescript_mock.return_value = '[{"id":"folder-1","name":"Notes","shared":false}]'

        result = notes_applescript.list_folders()

        self.assertEqual(result[0]["id"], "folder-1")
        self.assertEqual(result[0]["name"], "Notes")
        self.assertEqual(result[0]["shared"], False)
        self.assertEqual(result[0]["path"], "Notes")

    @mock.patch("notes_applescript.run_applescript")
    def test_list_folders_script_skips_broken_folder_references(self, run_applescript_mock):
        run_applescript_mock.return_value = "[]"

        notes_applescript.list_folders()

        script = run_applescript_mock.call_args.args[0]
        self.assertIn("on error errMsg number errNum", script)
        self.assertIn("repeat with f in every folder of defaultAccount", script)

    @mock.patch("notes_applescript.list_notes")
    def test_find_notes_by_title_matches_exact_name(self, list_notes_mock):
        list_notes_mock.return_value = [
            {"id": "note-1", "name": "Target", "plaintext": "hello"},
            {"id": "note-2", "name": "Other", "plaintext": "Target inside body"},
        ]

        result = notes_applescript.find_notes_by_title("Target")

        self.assertEqual(result, [{"id": "note-1", "name": "Target", "plaintext": "hello"}])

    @mock.patch("notes_applescript.list_notes")
    def test_search_notes_matches_name_and_plaintext_case_insensitively(self, list_notes_mock):
        list_notes_mock.return_value = [
            {"id": "note-1", "name": "Travel", "plaintext": "Pack passport"},
            {"id": "note-2", "name": "Groceries", "plaintext": "milk"},
        ]

        result = notes_applescript.search_notes("PASSPORT")

        self.assertEqual(result, [{"id": "note-1", "name": "Travel", "plaintext": "Pack passport"}])

    @mock.patch("notes_applescript.resolve_folder")
    @mock.patch("notes_applescript.get_note_by_id")
    @mock.patch("notes_applescript.run_applescript")
    def test_create_note_returns_created_note_lookup(
        self,
        run_applescript_mock,
        get_note_by_id_mock,
        resolve_folder_mock,
    ):
        run_applescript_mock.return_value = "note-1"
        get_note_by_id_mock.return_value = {"id": "note-1", "name": "Draft", "plaintext": "Draft\nhello"}
        resolve_folder_mock.return_value = {"id": "folder-1", "name": "Notes", "path": "Notes"}

        result = notes_applescript.create_note(folder="Notes", title="Draft", text="hello")

        self.assertEqual(result["id"], "note-1")
        self.assertIn("<div>Draft</div>", run_applescript_mock.call_args.args[0])
        self.assertIn("<div>hello</div>", run_applescript_mock.call_args.args[0])

    @mock.patch("notes_applescript.get_note_by_id")
    @mock.patch("notes_applescript.run_applescript")
    def test_update_note_appends_text_to_existing_body_html(self, run_applescript_mock, get_note_by_id_mock):
        get_note_by_id_mock.side_effect = [
            {"id": "note-1", "body_html": "<div>Draft</div><div>hello</div>"},
            {"id": "note-1", "body_html": "<div>Draft</div><div>hello</div><div>updated</div>"},
        ]

        result = notes_applescript.update_note(
            note_id="note-1",
            operation="append-text",
            value="updated",
        )

        self.assertEqual(result["id"], "note-1")
        self.assertIn("<div>updated</div>", run_applescript_mock.call_args.args[0])

    @mock.patch("notes_applescript.run_applescript")
    def test_list_attachments_parses_json_from_applescript(self, run_applescript_mock):
        run_applescript_mock.return_value = '[{"id":"att-1","name":"sample.txt","note_id":"note-1"}]'

        result = notes_applescript.list_attachments("note-1")

        self.assertEqual(result, [{"id": "att-1", "name": "sample.txt", "note_id": "note-1"}])

    def test_attachment_operation_supported_allows_add_but_not_remove(self):
        self.assertTrue(notes_applescript.attachment_operation_supported("add"))
        self.assertFalse(notes_applescript.attachment_operation_supported("remove"))

    @mock.patch("notes_applescript.resolve_folder")
    @mock.patch("notes_applescript.run_applescript")
    def test_delete_folder_moves_folder_to_trash(self, run_applescript_mock, resolve_folder_mock):
        resolve_folder_mock.return_value = {"id": "folder-1", "path": "Parent"}

        result = notes_applescript.delete_folder(folder_id="folder-1")

        self.assertEqual(result, {"id": "folder-1", "path": "Parent", "deleted": True})
        script = run_applescript_mock.call_args.args[0]
        self.assertIn('set trashFolder to folder "Trash"', script)
        self.assertIn('move folder id "folder-1" to trashFolder', script)


if __name__ == "__main__":
    unittest.main()
