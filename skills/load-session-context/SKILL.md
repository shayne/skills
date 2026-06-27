---
name: load-session-context
description: Use when asked to load, restore, resume, reconstruct, or summarize usable context from a prior Codex session, thread id, or rollout JSONL, especially when the session is large, compacted, or partially encrypted.
---

# Load Session Context

## Overview
Rebuild the usable LLM context from Codex rollout JSONL without dumping the whole file into the conversation. Load readable compacted replacement history, explicit compaction-window metadata, and the un-compacted tail of user/assistant/status/tool-call events.

## Workflow
1. Run the extractor from the skills repo root, passing either a session id or a rollout JSONL path:
   ```bash
   python3 skills/load-session-context/scripts/extract_session_context.py <session-id-or-rollout-path> --max-tail-events 200
   ```
2. Read the Markdown report into context. It includes session metadata, event counts, recent compaction windows, the latest readable replacement history, and the post-compaction tail.
3. If the user asks for exact evidence, query the raw JSONL by timestamp or keyword after the extractor resolves the rollout path:
   ```bash
   jq -r 'select(.timestamp >= "2026-06-27T03:39:00Z") | .' <rollout.jsonl>
   rg -n "keyword|commit|error" <rollout.jsonl>
   ```
4. State the limitation clearly: encrypted `reasoning` and encrypted `compaction` payloads cannot be recovered from the JSONL. Do not claim full raw LLM hidden context when only readable transcript layers were loaded.

## Helper Notes
- The helper resolves session ids through `~/.codex/memories/MEMORY.md` and then `~/.codex/sessions/**/<session-id>*.jsonl`.
- Use `--json` when another script should consume the extracted context.
- Use `--max-history-messages` to control how many readable messages from the latest replacement history are rendered. The default keeps the most recent 120.
- Increase `--max-tail-events` for long post-compaction work; lower `--text-limit` when command text or status messages are too large.
- Prefer this helper before `cat`, broad `jq`, or loading a huge rollout directly. Large rollouts often contain thousands of tool records and encrypted blobs that add noise without restoring usable context.

## Common Mistakes
- Treating compaction metadata as the full compacted summary. Some replacement-history entries are encrypted and intentionally unreadable.
- Loading every `function_call_output` by default. Tool outputs can be enormous; only inspect them when a specific command result matters.
- Stopping at memory summaries when the user asks for full usable conversation context. Memory is useful for orientation, but the raw rollout tail usually has the decisive status stream and command sequence.
