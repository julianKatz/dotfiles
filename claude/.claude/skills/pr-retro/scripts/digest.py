#!/usr/bin/env python3
"""Turn one Claude Code transcript into a short, readable timeline for a PR retro.

A raw transcript is 5-12 MB of JSON lines; a reviewer can't read it. The digest keeps what shows how
the work went and drops the rest. Example rows:

    L812 19:41 JULIAN: no, the zone should come from the requester's calendar, not the MD's
    L815 19:42 TOOL Bash: uv run pytest -q 01-scheduling
    L816 19:43 ERROR Bash: Exit code 1 ... 3 failed
    L990 20:10 RECAP: PR #112 open; 412 tests pass; live eval not run.

`L<n>` is the line in the transcript, so a finding can cite it and a checker can open that line.
Usage: python3 digest.py <transcript.jsonl> [--out FILE]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

WRAP_UP = "mcp__ccd_turn__wrap_up"
LIMITS = {"JULIAN": 2000, "CLAUDE": 600, "TOOL": 200, "ERROR": 300, "PEER": 1200, "NOTICE": 200,
          "RECAP": 600}
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
# Prompts written by another session, not by Julian: a relayed message, a subagent's hand-back, or the
# brief a parent session started this one with.
RELAYED = re.compile(r"\s*(<cross-session-message|<agent-message|Another Claude session sent a message"
                     r"|Background \(from the session that started this one\))")


def parse(lines):
    """(line number, entry) for each line that is a JSON object; bad lines are skipped."""
    for n, raw in enumerate(lines, 1):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if isinstance(entry, dict):
            yield n, entry


def flat(text):
    return " ".join((text or "").split())


def cut(text, limit):
    text = flat(text)
    if len(text) > limit:
        return f"{text[:limit]} [+{len(text) - limit} chars]"
    return text


def block_text(content):
    """Text of a message content that is either a string or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text") or "" for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def clean_prompt(text):
    """The human's own words: system reminders out, a slash command shown by name."""
    text = REMINDER.sub("", text or "")
    command = re.search(r"<command-name>(.*?)</command-name>", text)
    if command:
        args = re.search(r"<command-args>(.*?)</command-args>", text, re.S)
        return f"[ran {command.group(1)}] {args.group(1) if args else ''}".strip()
    return text.strip()


def hhmm(entry):
    ts = entry.get("timestamp")
    return ts[11:16] if isinstance(ts, str) and len(ts) >= 16 else None


def tool_summary(name, inp):
    """One line saying what a tool call did, e.g. the Bash command or the file edited."""
    inp = inp if isinstance(inp, dict) else {}
    if name == "Bash":
        return inp.get("command", "")
    if name in ("Edit", "Write", "Read", "NotebookEdit"):
        return inp.get("file_path", "")
    if name == "Agent":
        return f"{inp.get('description', '')} (model {inp.get('model') or 'default'})"
    if name == "Skill":
        return f"{inp.get('skill', '')} {inp.get('args', '')}"
    if name == "Workflow":
        return inp.get("scriptPath") or inp.get("name") or "inline script"
    for key in ("description", "title", "prompt", "query", "url", "message", "pattern"):
        if isinstance(inp.get(key), str):
            return inp[key]
    return json.dumps(inp)[:400]


def result_text(block):
    content = block.get("content")
    return block_text(content) if isinstance(content, list) else str(content or "")


class Timeline:
    def __init__(self):
        self.rows = []
        self.tools = {}  # tool_use id -> name
        self.m = {"human_prompts": 0, "peer_messages": 0, "assistant_messages": 0,
                  "tool_calls": Counter(), "tool_errors": 0, "compactions": 0,
                  "first_ts": None, "last_ts": None, "prs": [], "title": None}

    def row(self, n, entry, kind, text):
        time = hhmm(entry)
        label = kind.split(" ", 1)[0]
        self.rows.append(f"L{n}{' ' + time if time else ''} {kind}: {cut(text, LIMITS.get(label, 300))}")

    def add(self, n, entry):
        kind = entry.get("type")
        ts = entry.get("timestamp")
        if isinstance(ts, str) and kind in ("user", "assistant"):
            self.m["first_ts"] = self.m["first_ts"] or ts
            self.m["last_ts"] = ts
        if kind == "user":
            self.user(n, entry)
        elif kind == "assistant":
            self.assistant(n, entry)
        elif kind == "pr-link" and entry.get("prUrl") and entry["prUrl"] not in self.m["prs"]:
            self.m["prs"].append(entry["prUrl"])
            self.row(n, entry, "PR", entry["prUrl"])
        elif kind == "custom-title" and entry.get("customTitle") \
                and entry["customTitle"] != self.m["title"]:
            self.m["title"] = entry["customTitle"]
            self.row(n, entry, "TITLE", entry["customTitle"])
        elif kind == "system" and entry.get("subtype") == "compact_boundary":
            self.m["compactions"] += 1
            self.rows.append(f"L{n} COMPACT: context was summarized here")

    def user(self, n, entry):
        content = (entry.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                self.m["tool_errors"] += 1
                name = self.tools.get(block.get("tool_use_id"), "tool")
                self.row(n, entry, f"ERROR {name}", result_text(block))
        origin = entry.get("origin") or {}
        source = origin.get("kind") if isinstance(origin, dict) else None
        if source == "peer":
            self.m["peer_messages"] += 1
            body = "\n".join(m.get("body", "") for m in origin.get("members") or [] if isinstance(m, dict))
            body = body or block_text(content)
            label = "SUBAGENT" if "<agent-message" in body else \
                f"PEER {flat(origin.get('name') or origin.get('from') or '?')}"
            self.row(n, entry, label, body)
            return
        text = clean_prompt(block_text(content))
        if not text or entry.get("isMeta"):
            return
        relayed = RELAYED.match(text)
        if relayed:
            # Another session's words arriving as a plain prompt: not Julian's, so not his correction.
            self.m["peer_messages"] += 1
            sender = re.search(r'from-name="([^"]*)"', text)
            label = "SUBAGENT" if "agent-message" in relayed.group(0) else \
                f"PEER {sender.group(1) if sender else 'parent session'}"
            self.row(n, entry, label, text)
            return
        if source == "task-notification":
            self.row(n, entry, "NOTICE", text)
        elif source in (None, "human"):
            self.m["human_prompts"] += 1
            self.row(n, entry, "JULIAN", text)

    def assistant(self, n, entry):
        blocks = (entry.get("message") or {}).get("content") or []
        if any(isinstance(b, dict) and b.get("type") == "text" for b in blocks):
            self.m["assistant_messages"] += 1
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and (block.get("text") or "").strip():
                self.row(n, entry, "CLAUDE", block["text"])
            elif block.get("type") == "tool_use":
                name = block.get("name") or "?"
                self.tools[block.get("id")] = name
                self.m["tool_calls"][name] += 1
                inp = block.get("input") or {}
                if name == WRAP_UP:
                    ask = f" | ASK: {inp['ask']}" if inp.get("ask") else ""
                    self.row(n, entry, "RECAP", f"{inp.get('recap', '')}{ask}")
                else:
                    self.row(n, entry, f"TOOL {name}", tool_summary(name, inp))


def read_lines(path):
    with open(path, "rb") as f:
        return f.read().splitlines()


def subagents(session_dir):
    """One block per subagent: what it was asked, what it answered."""
    folder = os.path.join(session_dir, "subagents")
    if not os.path.isdir(folder):
        return []
    out = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".jsonl"):
            continue
        meta = {}
        try:
            with open(os.path.join(folder, name[:-6] + ".meta.json")) as f:
                meta = json.load(f)
        except (OSError, ValueError):
            pass
        prompt = answer = ""
        for _, entry in parse(read_lines(os.path.join(folder, name))):
            text = block_text((entry.get("message") or {}).get("content"))
            if entry.get("type") == "user" and not prompt and text.strip():
                prompt = REMINDER.sub("", text)
            elif entry.get("type") == "assistant" and text.strip():
                answer = text
        out.append(f"- **{flat(meta.get('description') or name)}** "
                   f"(model {meta.get('model') or 'default'}, {meta.get('agentType') or 'agent'})\n"
                   f"  - asked: {cut(prompt, 300)}\n  - answered: {cut(answer, 500)}")
    return out


def workflows(session_dir):
    folder = os.path.join(session_dir, "workflows", "scripts")
    if not os.path.isdir(folder):
        return []
    return [f"- {name}" for name in sorted(os.listdir(folder)) if name.endswith(".js")]


def hours(first, last):
    try:
        a, b = (datetime.fromisoformat(t.replace("Z", "+00:00")) for t in (first, last))
    except (TypeError, ValueError, AttributeError):
        return None
    return round((b - a).total_seconds() / 3600, 1)


def digest(lines, session_dir=None):
    """(markdown timeline, metrics dict) for one transcript's raw lines."""
    t = Timeline()
    for n, entry in parse(lines):
        t.add(n, entry)
    m = t.m
    m["tool_calls"] = dict(m["tool_calls"])
    m["wall_hours"] = hours(m["first_ts"], m["last_ts"])
    parts = [f"# {m['title'] or 'Untitled session'}", "", "## Timeline (UTC)", "", *t.rows]
    agents = subagents(session_dir) if session_dir else []
    flows = workflows(session_dir) if session_dir else []
    m["subagents"], m["workflows"] = len(agents), len(flows)
    if agents:
        parts += ["", "## Subagents", "", *agents]
    if flows:
        parts += ["", "## Workflows", "", *flows]
    return "\n".join(parts) + "\n", m


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("transcript")
    ap.add_argument("--out")
    args = ap.parse_args()
    session_dir = args.transcript[:-6] if args.transcript.endswith(".jsonl") else None
    text, metrics = digest(read_lines(args.transcript), session_dir)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(json.dumps(metrics))
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
