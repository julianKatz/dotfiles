#!/usr/bin/env python3
"""Claude Code Stop hook: after a long turn, have Claude close with a /tldr.

Measures the turn that just ended from the hook payload and transcript. If it
left a wall of text, blocks the stop once with a reason telling Claude to run
the tldr skill. Claude Code sets stop_hook_active on the follow-up stop, so
this fires at most once per turn. Bad input or any error allows the stop.
"""
import json
import re
import sys
import time
from datetime import datetime

# Thresholds calibrated on past transcripts: fires on ~1 in 5 finished turns
# and never on quick back-and-forth, where long answers are what was asked for.
CLOSING_WORDS = 200    # about half a laptop screen of closing message
TOOL_CALLS = 8         # Claude went off and worked
AWAY_MINUTES = 10      # or the user has likely stepped away (background work)


def parse_time(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()


def is_human(entry):
    return entry.get("type") == "user" and (entry.get("origin") or {}).get("kind") == "human"


def scan(lines, prompt_id):
    """Walk the transcript backwards.

    Returns (tool calls this turn, closing text, time of the user's last message,
    whether the turn was started by the user, a background task or another
    session). The turn is every entry after the last user entry from an earlier
    prompt.
    """
    tool_calls = 0
    has_origin = False
    closing = []
    after_last_tool = True
    in_turn = True
    human_at = None
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(entry, dict):
            continue
        kind = entry.get("type")
        if in_turn and kind == "user" and entry.get("promptId") not in (None, prompt_id):
            in_turn = False
        if in_turn and kind == "user" and entry.get("origin"):
            has_origin = True
        if in_turn and kind == "assistant":
            message = entry.get("message") or {}
            if message.get("model") != "<synthetic>":
                for block in reversed(message.get("content") or []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        tool_calls += 1
                        after_last_tool = False
                    elif block.get("type") == "text" and after_last_tool:
                        closing.append(block.get("text") or "")
        if human_at is None and is_human(entry) and entry.get("timestamp"):
            human_at = parse_time(entry["timestamp"])
        if not in_turn and human_at is not None:
            break
    return tool_calls, "\n".join(reversed(closing)), human_at, has_origin


def is_tldr(text):
    return all(re.search(r"\*\*%s\b" % label, text) for label in ("Goal", "Found", "Next"))


def decide(payload, lines, now):
    """The block reason if this turn needs a tl;dr, else None."""
    if payload.get("stop_hook_active"):
        return None
    tool_calls, closing, human_at, has_origin = scan(lines, payload.get("prompt_id"))
    # Headless runs (claude -p, Agent SDK) print only the final message, so a
    # recap there would replace the real result. Their prompts carry no origin.
    if not has_origin:
        return None
    if isinstance(payload.get("last_assistant_message"), str):
        closing = payload["last_assistant_message"]
    words = len(closing.split())
    away = (now - human_at) / 60 if human_at else 0
    if is_tldr(closing) or words < CLOSING_WORDS:
        return None
    if tool_calls < TOOL_CALLS and away < AWAY_MINUTES:
        return None
    return (
        "Long turn (%d tool call%s, %d-word closing message, %d min since the "
        "user's last message). Close it out: run the tldr skill now and reply "
        "with only its recap." % (tool_calls, "" if tool_calls == 1 else "s", words, away)
    )


def main():
    payload = json.load(sys.stdin)
    with open(payload["transcript_path"], "rb") as f:
        lines = f.read().splitlines()
    reason = decide(payload, lines, time.time())
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
