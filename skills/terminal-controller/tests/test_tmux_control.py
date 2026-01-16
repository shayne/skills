import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/tmux_control.py"


def load_tmux_control():
    spec = importlib.util.spec_from_file_location("tmux_control", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunTmuxTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_run_tmux_builds_command(self):
        with mock.patch.object(self.tmux_control.subprocess, "run") as run:
            self.tmux_control.run_tmux(["list-sessions"], capture_output=True)

        run.assert_called_once()
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["tmux", "list-sessions"])
        self.assertTrue(kwargs["capture_output"])
        self.assertTrue(kwargs["text"])


class CaptureTextTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_capture_text_history(self):
        result = mock.Mock(stdout="output")
        with mock.patch.object(self.tmux_control, "run_tmux", return_value=result) as run_tmux:
            text = self.tmux_control.capture_text("sess:0.0", history=True)

        self.assertEqual(text, "output")
        run_tmux.assert_called_once_with(
            ["capture-pane", "-t", "sess:0.0", "-p", "-S", "-"],
            capture_output=True,
        )

    def test_capture_text_lines(self):
        result = mock.Mock(stdout="output")
        with mock.patch.object(self.tmux_control, "run_tmux", return_value=result) as run_tmux:
            self.tmux_control.capture_text("sess:0.0", lines=50)

        run_tmux.assert_called_once_with(
            ["capture-pane", "-t", "sess:0.0", "-p", "-S", "-50"],
            capture_output=True,
        )


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_has_session_true(self):
        result = mock.Mock(returncode=0)
        with mock.patch.object(self.tmux_control.subprocess, "run", return_value=result):
            self.assertTrue(self.tmux_control.has_session("codex"))

    def test_has_session_false(self):
        result = mock.Mock(returncode=1)
        with mock.patch.object(self.tmux_control.subprocess, "run", return_value=result):
            self.assertFalse(self.tmux_control.has_session("codex"))

    def test_get_active_window_uses_tmux(self):
        result = mock.Mock(stdout="work:2\n")
        with mock.patch.object(self.tmux_control, "run_tmux", return_value=result):
            self.assertEqual(self.tmux_control.get_active_window("work"), "work:2")

    def test_get_active_window_fallback(self):
        with mock.patch.object(
            self.tmux_control,
            "run_tmux",
            side_effect=self.tmux_control.subprocess.CalledProcessError(1, ["tmux"]),
        ):
            self.assertEqual(self.tmux_control.get_active_window("work"), "work:0")

    def test_create_session_existing_no_force(self):
        with mock.patch.object(self.tmux_control, "has_session", return_value=True), \
            mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = self.tmux_control.create_session(
                    "work",
                    cwd="/tmp",
                    force=False,
                    width=80,
                    height=24,
                    no_resize=False,
                )

        self.assertEqual(result, 1)
        self.assertIn("already exists", stderr.getvalue())
        run_tmux.assert_not_called()

    def test_create_session_force(self):
        calls = []

        def fake_run_tmux(args, check=True, capture_output=False):
            calls.append((args, check))

        with mock.patch.object(self.tmux_control, "has_session", return_value=True), \
            mock.patch.object(self.tmux_control, "run_tmux", side_effect=fake_run_tmux):
            result = self.tmux_control.create_session(
                "work",
                cwd="/tmp",
                force=True,
                width=120,
                height=40,
                no_resize=False,
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            calls,
            [
                (["kill-session", "-t", "work"], False),
                (["new-session", "-d", "-s", "work", "-c", "/tmp"], True),
                (["resize-window", "-t", "work:0", "-x", "120", "-y", "40"], True),
            ],
        )


class SendTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_send_text_with_enter(self):
        with mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            self.tmux_control.send_text("sess:0.0", "ls", enter=True)

        self.assertEqual(
            run_tmux.call_args_list,
            [
                mock.call(["send-keys", "-t", "sess:0.0", "-l", "ls"]),
                mock.call(["send-keys", "-t", "sess:0.0", "Enter"]),
            ],
        )

    def test_send_keys(self):
        with mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            self.tmux_control.send_keys("sess:0.0", ["C-c", "Up"])

        run_tmux.assert_called_once_with(["send-keys", "-t", "sess:0.0", "C-c", "Up"])


class CaptureAndStepTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_capture_outputs_text(self):
        with mock.patch.object(self.tmux_control, "capture_text", return_value="hello"):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = self.tmux_control.capture("sess:0.0", lines=10, history=False)

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "hello")

    def test_step_and_capture_order(self):
        run_calls = []

        def fake_run_tmux(args, check=True, capture_output=False):
            run_calls.append(args)

        with mock.patch.object(self.tmux_control, "run_tmux", side_effect=fake_run_tmux), \
            mock.patch.object(self.tmux_control, "capture", return_value=0) as capture, \
            mock.patch.object(self.tmux_control.time, "sleep") as sleep:
            result = self.tmux_control.step_and_capture(
                "sess:0.0",
                text="echo hi",
                enter=True,
                keys=["C-c"],
                sleep_ms=50,
                lines=5,
                history=False,
            )

        self.assertEqual(result, 0)
        self.assertEqual(
            run_calls,
            [
                ["send-keys", "-t", "sess:0.0", "-l", "echo hi"],
                ["send-keys", "-t", "sess:0.0", "C-c"],
                ["send-keys", "-t", "sess:0.0", "Enter"],
            ],
        )
        sleep.assert_called_once()
        capture.assert_called_once_with("sess:0.0", 5, False)


class ResizeAndFitTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_resize(self):
        with mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            result = self.tmux_control.resize("sess:0", 100, 40)

        self.assertEqual(result, 0)
        run_tmux.assert_called_once_with(["resize-window", "-t", "sess:0", "-x", "100", "-y", "40"])

    def test_fit_to_client_no_clients(self):
        result = mock.Mock(stdout="")
        with mock.patch.object(self.tmux_control, "run_tmux", return_value=result):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = self.tmux_control.fit_to_client("sess", None)

        self.assertEqual(code, 1)
        self.assertIn("No attached tmux clients", stderr.getvalue())

    def test_fit_to_client_invalid_size(self):
        result = mock.Mock(stdout="oops\n")
        with mock.patch.object(self.tmux_control, "run_tmux", return_value=result):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = self.tmux_control.fit_to_client("sess", None)

        self.assertEqual(code, 1)
        self.assertIn("Unable to parse client size", stderr.getvalue())

    def test_fit_to_client_resizes(self):
        result = mock.Mock(stdout="120 40\n")
        run_calls = []

        def fake_run_tmux(args, check=True, capture_output=False):
            run_calls.append(args)
            return result

        with mock.patch.object(self.tmux_control, "run_tmux", side_effect=fake_run_tmux), \
            mock.patch.object(self.tmux_control, "get_active_window", return_value="sess:3"):
            code = self.tmux_control.fit_to_client("sess", None)

        self.assertEqual(code, 0)
        self.assertEqual(
            run_calls,
            [
                ["list-clients", "-t", "sess", "-F", "#{client_width} #{client_height}"],
                ["resize-window", "-t", "sess:3", "-x", "120", "-y", "40"],
            ],
        )


class ListTests(unittest.TestCase):
    def setUp(self):
        self.tmux_control = load_tmux_control()

    def test_list_sessions(self):
        with mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            self.tmux_control.list_sessions()

        run_tmux.assert_called_once_with(["list-sessions"], check=False)

    def test_list_windows(self):
        with mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            self.tmux_control.list_windows("sess")

        run_tmux.assert_called_once_with(["list-windows", "-t", "sess"], check=False)

    def test_list_panes(self):
        with mock.patch.object(self.tmux_control, "run_tmux") as run_tmux:
            self.tmux_control.list_panes("sess:0")

        run_tmux.assert_called_once_with(
            [
                "list-panes",
                "-t",
                "sess:0",
                "-F",
                "#{session_name}:#{window_index}.#{pane_index} #{pane_id} #{pane_title}",
            ],
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
