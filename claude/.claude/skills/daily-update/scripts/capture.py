#!/usr/bin/env python3
"""Claude Code Stop hook: keep a short note of each finished turn for /daily-update.

Appends one JSON line to ~/.claude/daily-log/<local date>.jsonl for every turn
that Julian started or that ended with a wrap-up: the thread's title, branch and
PRs, the prompt that started the work, and what came of it (the wrap-up recap,
else the start of the closing message). Stop can fire twice for one turn (when
another Stop hook blocks once), so a turn may appear twice; readers keep the
last line per (transcript, prompt_id). Keeps today and the 6 days before, so
it's a rolling week, not memory. Never blocks: errors are swallowed, nothing
is printed.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta

LOG_DIR = os.environ.get("DAILY_LOG_DIR") or os.path.expanduser("~/.claude/daily-log")
KEEP_DAYS = 7
PROMPT_CHARS = 240
CLOSING_CHARS = 400
WRAP_UP = "mcp__ccd_turn__wrap_up"
DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})\b")


def parse(lines):
    for raw in lines:
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if isinstance(entry, dict):
            yield entry


def cut(text, limit):
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def prompt_text(content):
    """The user's own words: no system reminders, pastes and shell output collapsed."""
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content
                          if isinstance(b, dict) and b.get("type") == "text")
    text = content or ""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"<pasted_content\b[^>]*>.*?</pasted_content>", "[pasted]", text, flags=re.S)
    text = re.sub(r"<bash-input>(.*?)</bash-input>", r"[shell: \1]", text, flags=re.S)
    text = re.sub(r"<bash-(stdout|stderr)>.*?</bash-\1>", "", text, flags=re.S)
    return cut(text, PROMPT_CHARS)


def is_human(entry):
    return entry.get("type") == "user" and (entry.get("origin") or {}).get("kind") == "human"


def extract(payload, lines):
    """This turn's log entry, or None if the turn was neither Julian's nor wrapped up.

    User entries (prompts and tool results) carry the turn's promptId; assistant
    entries don't, so an assistant entry belongs to the turn of the user entry
    before it. Without a prompt_id in the payload, the turn is the last one.
    """
    entries = list(parse(lines))
    prompt_id = payload.get("prompt_id") or next(
        (e.get("promptId") for e in reversed(entries) if e.get("type") == "user" and e.get("promptId")),
        None)
    title = branch = None
    prs = []
    prompt = earlier_prompt = ""
    wrap = None
    closing = []
    in_turn = False
    for entry in entries:
        kind = entry.get("type")
        if kind == "custom-title":
            title = entry.get("customTitle") or title
        elif kind == "pr-link" and entry.get("prUrl") and entry["prUrl"] not in prs:
            prs.append(entry["prUrl"])
        if entry.get("gitBranch"):
            branch = entry["gitBranch"]
        if kind == "user" and entry.get("promptId"):
            in_turn = entry["promptId"] == prompt_id
        if not in_turn:
            if is_human(entry):
                earlier_prompt = prompt_text((entry.get("message") or {}).get("content"))
            continue
        if is_human(entry) and not prompt:
            prompt = prompt_text((entry.get("message") or {}).get("content"))
        if kind == "assistant":
            for block in (entry.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    closing = []
                    if block.get("name") == WRAP_UP and (block.get("input") or {}).get("recap"):
                        wrap = block
                elif block.get("type") == "text":
                    closing.append(block.get("text") or "")
    if not prompt and not wrap:
        return None
    carried = not prompt and bool(earlier_prompt)
    return {
        "session_id": payload.get("session_id"),
        "transcript": payload.get("transcript_path"),
        "prompt_id": prompt_id,
        "title": title,
        "cwd": payload.get("cwd"),
        "branch": branch,
        "prs": prs,
        "prompt": prompt or earlier_prompt,
        "prompt_carried": carried,
        "recap": wrap["input"]["recap"] if wrap else cut("\n".join(closing), CLOSING_CHARS),
        "recap_from": "wrap_up" if wrap else "closing",
    }


def record(entry, log_dir, now):
    """Append entry to today's file; delete dated files older than the week."""
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, now.strftime("%Y-%m-%d") + ".jsonl")
    entry = dict(entry, logged_at=now.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    cutoff = (now - timedelta(days=KEEP_DAYS - 1)).strftime("%Y-%m-%d")
    for name in os.listdir(log_dir):
        m = DATED.match(name)
        if m and m.group(1) < cutoff:
            os.remove(os.path.join(log_dir, name))


def main():
    payload = json.load(sys.stdin)
    with open(payload["transcript_path"], "rb") as f:
        lines = f.read().splitlines()
    entry = extract(payload, lines)
    if entry:
        record(entry, LOG_DIR, datetime.now())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
