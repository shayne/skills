#!/usr/bin/env python3
"""Extract usable context from a Codex session rollout JSONL file."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any


DEFAULT_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_MEMORY_INDEX = Path.home() / ".codex" / "memories" / "MEMORY.md"


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_number, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def resolve_rollout_path(
    session_or_path: str,
    sessions_root: Path = DEFAULT_SESSIONS_ROOT,
    memory_index: Path = DEFAULT_MEMORY_INDEX,
) -> Path:
    candidate = Path(session_or_path).expanduser()
    if candidate.exists():
        return candidate.resolve()

    if memory_index.exists():
        match = find_rollout_in_memory(session_or_path, memory_index)
        if match:
            return match

    if sessions_root.exists():
        matches = sorted(sessions_root.rglob(f"*{session_or_path}*.jsonl"))
        if matches:
            return matches[-1].resolve()

    raise FileNotFoundError(f"could not resolve session id or rollout path: {session_or_path}")


def find_rollout_in_memory(session_id: str, memory_index: Path) -> Path | None:
    rollout_re = re.compile(r"rollout_path=([^,)]+)")
    for line in memory_index.read_text(encoding="utf-8").splitlines():
        if session_id not in line:
            continue
        match = rollout_re.search(line)
        if not match:
            continue
        path = Path(match.group(1).strip()).expanduser()
        if path.exists():
            return path.resolve()
    return None


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        for key in ("text", "input_text", "output_text"):
            value = item.get(key)
            if isinstance(value, str):
                parts.append(value)
                break
    return "\n".join(parts).strip()


def compact_text(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def extract_context(
    path: Path,
    max_tail_events: int = 180,
    max_history_messages: int = 120,
    text_limit: int = 1200,
) -> dict[str, Any]:
    path = path.expanduser().resolve()
    session: dict[str, Any] = {"rollout_path": str(path)}
    type_counts: Counter[str] = Counter()
    response_item_counts: Counter[str] = Counter()
    compactions: list[dict[str, Any]] = []
    latest_compacted_timestamp: str | None = None
    latest_replacement_history: list[dict[str, Any]] = []
    tail_candidates: list[dict[str, Any]] = []

    for line_number, row in iter_jsonl(path):
        row_type = row.get("type", "")
        payload = row.get("payload") or {}
        timestamp = row.get("timestamp", "")
        type_counts[row_type] += 1

        if row_type == "session_meta":
            meta = payload if isinstance(payload, dict) else {}
            session.update(
                {
                    "id": meta.get("id", session.get("id")),
                    "cwd": meta.get("cwd", session.get("cwd")),
                    "timestamp": meta.get("timestamp", session.get("timestamp")),
                    "model": meta.get("model", session.get("model")),
                }
            )
            continue

        if row_type == "response_item":
            item_type = payload.get("type") if isinstance(payload, dict) else None
            if item_type:
                response_item_counts[item_type] += 1

        if row_type == "compacted":
            latest_compacted_timestamp = timestamp
            latest_replacement_history = payload.get("replacement_history") or []
            compactions.append(summarize_compaction(timestamp, payload, line_number))
            continue

        tail_entry = summarize_tail_row(row, text_limit=text_limit)
        if tail_entry:
            tail_candidates.append(tail_entry)

    if latest_compacted_timestamp:
        tail_candidates = [
            entry for entry in tail_candidates if entry.get("timestamp", "") > latest_compacted_timestamp
        ]

    latest_compaction = summarize_latest_compaction(
        compactions[-1] if compactions else None,
        latest_replacement_history,
        max_history_messages=max_history_messages,
        text_limit=text_limit,
    )

    return {
        "session": session,
        "counts": {
            "top_level": dict(type_counts),
            "response_items": dict(response_item_counts),
        },
        "compactions": compactions,
        "latest_compaction": latest_compaction,
        "tail": tail_candidates[-max_tail_events:],
    }


def summarize_compaction(timestamp: str, payload: dict[str, Any], line_number: int) -> dict[str, Any]:
    replacement_history = payload.get("replacement_history") or []
    message_count = sum(1 for item in replacement_history if item.get("type") == "message")
    encrypted_count = sum(
        1
        for item in replacement_history
        if item.get("type") in {"compaction", "reasoning"} and item.get("encrypted_content")
    )
    return {
        "timestamp": timestamp,
        "line": line_number,
        "window_number": payload.get("window_number"),
        "window_id": payload.get("window_id"),
        "replacement_history_count": len(replacement_history),
        "message_count": message_count,
        "encrypted_compaction_count": encrypted_count,
    }


def summarize_latest_compaction(
    summary: dict[str, Any] | None,
    replacement_history: list[dict[str, Any]],
    max_history_messages: int,
    text_limit: int,
) -> dict[str, Any] | None:
    if summary is None:
        return None

    messages: list[dict[str, str]] = []
    encrypted_count = 0
    for item in replacement_history:
        item_type = item.get("type")
        if item_type == "message":
            text = compact_text(text_from_content(item.get("content")), text_limit)
            if text:
                messages.append({"role": item.get("role", "?"), "text": text})
        elif item.get("encrypted_content"):
            encrypted_count += 1

    result = dict(summary)
    omitted_message_count = max(0, len(messages) - max_history_messages)
    if omitted_message_count:
        messages = messages[-max_history_messages:]
    result["messages"] = messages
    result["omitted_message_count"] = omitted_message_count
    result["encrypted_compaction_count"] = encrypted_count
    return result


def summarize_tail_row(row: dict[str, Any], text_limit: int) -> dict[str, Any] | None:
    timestamp = row.get("timestamp", "")
    row_type = row.get("type", "")
    payload = row.get("payload") or {}

    if row_type == "event_msg":
        event_type = payload.get("type")
        if event_type not in {"agent_message", "user_message"}:
            return None
        return {
            "timestamp": timestamp,
            "kind": event_type,
            "message": compact_text(payload.get("message", ""), text_limit),
        }

    if row_type != "response_item":
        return None

    item_type = payload.get("type")
    if item_type == "message":
        text = compact_text(text_from_content(payload.get("content")), text_limit)
        if not text:
            return None
        return {
            "timestamp": timestamp,
            "kind": f"message:{payload.get('role', '?')}",
            "message": text,
        }

    if item_type == "function_call":
        command = command_from_function_call(payload)
        return {
            "timestamp": timestamp,
            "kind": f"tool:{payload.get('name', '?')}",
            "command": compact_text(command, text_limit),
        }

    return None


def command_from_function_call(payload: dict[str, Any]) -> str:
    arguments = payload.get("arguments")
    if isinstance(arguments, str):
        try:
            decoded = json.loads(arguments)
        except json.JSONDecodeError:
            return arguments
    elif isinstance(arguments, dict):
        decoded = arguments
    else:
        return ""

    if isinstance(decoded, dict):
        return decoded.get("cmd") or decoded.get("chars") or json.dumps(decoded, sort_keys=True)
    return str(decoded)


def render_markdown(report: dict[str, Any]) -> str:
    session = report["session"]
    lines = [
        "# Loaded Session Context",
        "",
        f"- Source: `{session.get('rollout_path')}`",
        f"- Session id: `{session.get('id') or 'unknown'}`",
        f"- CWD: `{session.get('cwd') or 'unknown'}`",
        "",
        "## Availability",
        "",
        "- Plain user/assistant messages, status events, and command calls are readable.",
        "- Encrypted reasoning and encrypted compaction payloads cannot be reconstructed from JSONL.",
        "",
        "## Counts",
        "",
    ]

    for key, value in sorted(report["counts"]["top_level"].items()):
        lines.append(f"- `{key}`: {value}")

    if report["counts"]["response_items"]:
        lines.extend(["", "Response item types:"])
        for key, value in sorted(report["counts"]["response_items"].items()):
            lines.append(f"- `{key}`: {value}")

    compactions = report["compactions"]
    lines.extend(["", "## Compaction Windows", ""])
    if not compactions:
        lines.append("No compaction windows found.")
    else:
        for item in compactions[-12:]:
            lines.append(
                "- "
                f"`{item['timestamp']}` window `{item.get('window_number')}` "
                f"messages={item['message_count']} "
                f"encrypted={item['encrypted_compaction_count']} "
                f"line={item['line']}"
            )

    latest = report["latest_compaction"]
    lines.extend(["", "## Latest Replacement History", ""])
    if not latest:
        lines.append("No replacement history found.")
    else:
        lines.append(
            f"Window `{latest.get('window_number')}` / `{latest.get('window_id')}` "
            f"at `{latest.get('timestamp')}`."
        )
        if latest.get("encrypted_compaction_count"):
            lines.append(f"Encrypted entries in replacement history: {latest['encrypted_compaction_count']}.")
        if latest.get("omitted_message_count"):
            lines.append(f"Older readable messages omitted: {latest['omitted_message_count']}.")
        lines.append("")
        for message in latest.get("messages", []):
            lines.append(f"- **{message['role']}**: {message['text']}")

    lines.extend(["", "## Un-Compacted Tail", ""])
    if not report["tail"]:
        lines.append("No readable tail events found after the latest compaction.")
    else:
        for item in report["tail"]:
            if "command" in item:
                lines.append(f"- `{item['timestamp']}` {item['kind']}: `{item['command']}`")
            else:
                lines.append(f"- `{item['timestamp']}` {item['kind']}: {item['message']}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_or_path", help="Codex session id or rollout JSONL path")
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS_ROOT)
    parser.add_argument("--memory-index", type=Path, default=DEFAULT_MEMORY_INDEX)
    parser.add_argument("--max-tail-events", type=int, default=180)
    parser.add_argument("--max-history-messages", type=int, default=120)
    parser.add_argument("--text-limit", type=int, default=1200)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    rollout = resolve_rollout_path(args.session_or_path, args.sessions_root, args.memory_index)
    report = extract_context(
        rollout,
        max_tail_events=args.max_tail_events,
        max_history_messages=args.max_history_messages,
        text_limit=args.text_limit,
    )

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
