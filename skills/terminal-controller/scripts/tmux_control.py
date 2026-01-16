#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time


def run_tmux(args, check=True, capture_output=False):
    cmd = ["tmux"] + args
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=True)


def capture_text(target, lines=None, history=False):
    args = ["capture-pane", "-t", target, "-p"]
    if history:
        args += ["-S", "-"]
    elif lines is not None:
        args += ["-S", f"-{lines}"]
    result = run_tmux(args, capture_output=True)
    return result.stdout


def has_session(name):
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def get_active_window(session):
    try:
        result = run_tmux(
            ["display-message", "-p", "-t", session, "#{session_name}:#{window_index}"],
            capture_output=True,
        )
        value = result.stdout.strip()
        return value or f"{session}:0"
    except subprocess.CalledProcessError:
        return f"{session}:0"


def create_session(name, cwd, force, width, height, no_resize):
    if has_session(name):
        if not force:
            print(f"Session '{name}' already exists. Use --force to recreate.", file=sys.stderr)
            return 1
        run_tmux(["kill-session", "-t", name], check=False)
    args = ["new-session", "-d", "-s", name]
    if cwd:
        args += ["-c", cwd]
    run_tmux(args)
    if not no_resize:
        run_tmux(["resize-window", "-t", f"{name}:0", "-x", str(width), "-y", str(height)])
    print(f"Created tmux session '{name}'.")
    return 0


def send_text(target, text, enter):
    run_tmux(["send-keys", "-t", target, "-l", text])
    if enter:
        run_tmux(["send-keys", "-t", target, "Enter"])
    return 0


def send_keys(target, keys):
    run_tmux(["send-keys", "-t", target] + keys)
    return 0


def capture(target, lines, history):
    sys.stdout.write(capture_text(target, lines=lines, history=history))
    return 0


def step_and_capture(target, text, enter, keys, sleep_ms, lines, history):
    if text:
        run_tmux(["send-keys", "-t", target, "-l", text])
    if keys:
        run_tmux(["send-keys", "-t", target] + keys)
    if enter:
        run_tmux(["send-keys", "-t", target, "Enter"])
    if sleep_ms:
        time.sleep(sleep_ms / 1000.0)
    return capture(target, lines, history)


def resize(target, width, height):
    run_tmux(["resize-window", "-t", target, "-x", str(width), "-y", str(height)])
    return 0


def fit_to_client(session, target):
    result = run_tmux(
        ["list-clients", "-t", session, "-F", "#{client_width} #{client_height}"],
        capture_output=True,
    )
    line = result.stdout.strip().splitlines()
    if not line:
        print(f"No attached tmux clients for session '{session}'.", file=sys.stderr)
        return 1
    try:
        width, height = [int(x) for x in line[0].split()[:2]]
    except ValueError:
        print(f"Unable to parse client size: {line[0]!r}", file=sys.stderr)
        return 1
    window_target = target or get_active_window(session)
    run_tmux(["resize-window", "-t", window_target, "-x", str(width), "-y", str(height)])
    print(f"Resized {window_target} to {width}x{height}.")
    return 0




def list_sessions():
    run_tmux(["list-sessions"], check=False)
    return 0


def list_windows(session):
    run_tmux(["list-windows", "-t", session], check=False)
    return 0


def list_panes(target):
    run_tmux([
        "list-panes",
        "-t",
        target,
        "-F",
        "#{session_name}:#{window_index}.#{pane_index} #{pane_id} #{pane_title}",
    ], check=False)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Create and control tmux sessions.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create a tmux session.")
    p_create.add_argument("--name", default="codex", help="Session name.")
    p_create.add_argument("--cwd", default=None, help="Working directory for the session.")
    p_create.add_argument("--force", action="store_true", help="Recreate if session exists.")
    p_create.add_argument("--width", type=int, default=100, help="Window width in columns.")
    p_create.add_argument("--height", type=int, default=40, help="Window height in rows.")
    p_create.add_argument(
        "--no-resize",
        action="store_true",
        help="Do not resize the window after creating the session.",
    )

    p_send = sub.add_parser("send", help="Send literal text to a pane.")
    p_send.add_argument("--target", default="codex:0.0", help="Target pane (session:window.pane).")
    p_send.add_argument("--text", required=True, help="Text to send.")
    p_send.add_argument("--enter", action="store_true", help="Press Enter after text.")

    p_keys = sub.add_parser("keys", help="Send raw keys to a pane.")
    p_keys.add_argument("--target", default="codex:0.0", help="Target pane.")
    p_keys.add_argument("keys", nargs=argparse.REMAINDER, help="Keys to send (e.g., C-c Up).")

    p_cap = sub.add_parser("capture", help="Capture pane contents.")
    p_cap.add_argument("--target", default="codex:0.0", help="Target pane.")
    p_cap.add_argument("--lines", type=int, default=None, help="Number of lines from bottom.")
    p_cap.add_argument("--history", action="store_true", help="Capture full scrollback.")

    p_step = sub.add_parser("step", help="Send input, optionally sleep, then capture.")
    p_step.add_argument("--target", default="codex:0.0", help="Target pane.")
    p_step.add_argument("--text", default=None, help="Literal text to send.")
    p_step.add_argument("--enter", action="store_true", help="Press Enter after sending.")
    p_step.add_argument(
        "--keys",
        nargs="+",
        help="Raw keys to send after text (e.g., C-g Down). Use -- before keys starting with '-'.",
    )
    p_step.add_argument(
        "--sleep-ms",
        type=int,
        default=0,
        help="Pause in milliseconds before capturing.",
    )
    p_step.add_argument(
        "--lines",
        type=int,
        default=200,
        help="Number of lines from bottom to capture.",
    )
    p_step.add_argument("--history", action="store_true", help="Capture full scrollback.")

    p_resize = sub.add_parser("resize", help="Resize a tmux window.")
    p_resize.add_argument("--target", default="codex:0", help="Target window (session:window).")
    p_resize.add_argument("--width", type=int, required=True, help="Columns.")
    p_resize.add_argument("--height", type=int, required=True, help="Rows.")

    p_fit = sub.add_parser("fit", help="Resize a window to match the first client size.")
    p_fit.add_argument("--session", default="codex", help="Session name.")
    p_fit.add_argument("--target", default=None, help="Target window (session:window).")

    p_list = sub.add_parser("list", help="List sessions, windows, or panes.")
    p_list.add_argument("--sessions", action="store_true", help="List sessions.")
    p_list.add_argument("--windows", metavar="SESSION", help="List windows for session.")
    p_list.add_argument("--panes", metavar="TARGET", help="List panes for target session/window.")

    args = parser.parse_args()

    if args.cmd == "create":
        return create_session(args.name, args.cwd, args.force, args.width, args.height, args.no_resize)
    if args.cmd == "send":
        return send_text(args.target, args.text, args.enter)
    if args.cmd == "keys":
        if not args.keys:
            print("No keys provided.", file=sys.stderr)
            return 2
        return send_keys(args.target, args.keys)
    if args.cmd == "capture":
        return capture(args.target, args.lines, args.history)
    if args.cmd == "step":
        keys = args.keys if args.keys else []
        return step_and_capture(
            args.target,
            args.text,
            args.enter,
            keys,
            args.sleep_ms,
            args.lines,
            args.history,
        )
    if args.cmd == "resize":
        return resize(args.target, args.width, args.height)
    if args.cmd == "fit":
        return fit_to_client(args.session, args.target)
    if args.cmd == "list":
        if args.sessions:
            return list_sessions()
        if args.windows:
            return list_windows(args.windows)
        if args.panes:
            return list_panes(args.panes)
        print("Specify one of --sessions, --windows, or --panes.", file=sys.stderr)
        return 2

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
