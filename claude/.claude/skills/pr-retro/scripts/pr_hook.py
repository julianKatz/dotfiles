#!/usr/bin/env python3
"""Claude Code PostToolUse hook: after a PR is opened or merged from Bash, tell Claude to start its retro.

Fires on `gh pr create` and `gh pr merge` run in a folder under ~/dev-applied-agents (PR_RETRO_ROOT
overrides), when the command didn't fail. Example context it adds:

    PR opened (https://github.com/AppliedAgents/sellside/pull/112). Julian's standing rule: start the PR
    retro now in its own local session ... prompt "/pr-retro https://github.com/.../pull/112 open".

Merges done another way (the app's merge button, GitHub's site) are covered by the rule in
~/dev-applied-agents/CLAUDE.md and by `/pr-retro` with no argument, which catches up.
Never blocks: any error means no output and exit 0.
"""
import json
import os
import re
import sys

COMMAND = re.compile(r"(?:^|[;&|(]\s*|\s)gh\s+pr\s+(create|merge)\b([^;&|]*)")
PR_URL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")


def under(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def target(rest):
    """The PR named on a merge command: a number, URL or branch; '' means the current branch's PR."""
    for word in rest.split():
        if not word.startswith("-"):
            return word
        if "=" in word:
            continue
    return ""


def decide(payload, root):
    """The context to add, or None when the hook shouldn't fire."""
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd")
    match = COMMAND.search(command)
    if not match or not cwd or not under(cwd, root):
        return None
    response = payload.get("tool_response") or {}
    if not isinstance(response, dict):
        response = {"stdout": str(response)}
    stdout, stderr = response.get("stdout") or "", response.get("stderr") or ""
    if response.get("interrupted") or (not stdout.strip() and re.search(r"error|failed", stderr, re.I)):
        return None
    action = match.group(1)
    if action == "merge" and re.search(r"(^|\s)--(auto|disable-auto)\b", match.group(2)):
        return None  # only queues (or un-queues) a merge; the retro waits for the real one
    stage = "open" if action == "create" else "merge"
    url = PR_URL.search(stdout) or PR_URL.search(stderr)
    pr = url.group(0) if url else target(match.group(2)) or "the current branch's PR"
    return (f"PR {'opened' if stage == 'open' else 'merged'} ({pr}). Julian's standing rule: start the PR "
            f"retro now in its own session with mcp__ccd_session__start_session (initiation user_asked, "
            f"context fresh, local not cloud because it reads transcripts on this machine, use_worktree "
            f"false) and the prompt \"/pr-retro {pr} {stage}\" (resolve the PR to owner/repo#number first if "
            f"it isn't a URL). Don't wait for it; carry on with your task.")


def main():
    try:
        payload = json.load(sys.stdin)
        root = os.environ.get("PR_RETRO_ROOT") or os.path.expanduser("~/dev-applied-agents")
        text = decide(payload, root)
        if text:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
