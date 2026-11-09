#!/usr/bin/env python3
"""Find every Claude Code transcript that worked on one PR, plus the PR's facts from GitHub.

A transcript belongs to the PR when it links the PR (a `pr-link` entry, written when a session opens or
binds it) or ran on the PR's head branch (`gitBranch` on its entries). Example:

    python3 find_work.py AppliedAgents/sellside 112
    -> {"pr": {"number": 112, "headRefName": "claude/callie-project-match-9cc1f6", ...},
        "transcripts": [{"path": ".../02f5f82e-....jsonl", "why": ["pr-link", "branch"], ...}]}

Sessions that only mention the PR (a daily update, an orchestrator) are left out on purpose: they did
not do the work. An orchestrator's instructions still show up, as PEER rows in the worker's digest.
"""
import argparse
import glob
import json
import os
import re
import subprocess

PROJECTS = os.path.expanduser("~/.claude/projects")
PR_FIELDS = ("number,title,url,state,headRefName,baseRefName,createdAt,mergedAt,closedAt,author,"
             "additions,deletions,changedFiles,commits,reviews,comments,statusCheckRollup,body")


def pr_facts(repo, number):
    """The PR as GitHub sees it (gh must be logged in to an account that can read the repo)."""
    out = subprocess.run(["gh", "pr", "view", str(number), "--repo", repo, "--json", PR_FIELDS],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def scan(path, repo, number, branch, force=False):
    """Facts about one transcript if it is tied to the PR (or `force`), else None."""
    with open(path, "rb") as f:
        data = f.read()
    # Cheap byte check first: most transcripts mention neither, and parsing 10 MB of JSON is slow.
    # Tolerates either JSON spacing ("prNumber":112 or "prNumber": 112); a false hit is fine, parsing decides.
    if not force and not re.search(rb'"prNumber":\s*%d\b' % number, data) and \
            (not branch or not re.search(rb'"gitBranch":\s*' + re.escape(json.dumps(branch).encode()), data)):
        return None
    why, title, first, last, lines = set(), None, None, None, 0
    for raw in data.splitlines():
        lines += 1
        try:
            e = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if e.get("type") == "pr-link" and e.get("prNumber") == number \
                and str(e.get("prRepository", "")).lower() == repo.lower():
            why.add("pr-link")
        if branch and e.get("gitBranch") == branch:
            why.add("branch")
        if e.get("type") == "custom-title":
            title = e.get("customTitle") or title
        ts = e.get("timestamp")
        if isinstance(ts, str) and e.get("type") in ("user", "assistant"):
            first, last = first or ts, ts
    if not why and not force:
        return None
    # The file is named by its session id; entries can carry other ids (a forked or relayed session).
    return {"path": path, "session_id": os.path.basename(path)[:-6],
            "why": sorted(why), "title": title, "first_ts": first, "last_ts": last, "lines": lines}


def keep_longest(hits):
    """One hit per session. A session that moved folders leaves a shorter prefix copy behind."""
    best = {}
    for hit in hits:
        if hit["session_id"] not in best or hit["lines"] > best[hit["session_id"]]["lines"]:
            best[hit["session_id"]] = hit
    return list(best.values())


SENDER = re.compile(r'from-name="([^"]*)"')


def senders(path):
    """Titles of the other sessions that messaged this one, e.g. an orchestrator that started it.

    Subagent hand-backs also arrive as peer messages; they are this session's own helpers, so skipped.
    """
    names = set()
    with open(path, "rb") as f:
        for raw in f:
            if b'"peer"' not in raw and b"from-name=" not in raw:
                continue
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(e, dict) or e.get("type") != "user":
                continue
            origin = e.get("origin") if isinstance(e.get("origin"), dict) else {}
            text = json.dumps((e.get("message") or {}).get("content"))
            if "agent-message" in text:
                continue
            if origin.get("kind") == "peer" and origin.get("name"):
                names.add(origin["name"])
            names.update(SENDER.findall(text.replace('\\"', '"')))
    return names


def titled(path, names):
    """True if the transcript was ever titled one of `names` (sessions get renamed as work moves)."""
    with open(path, "rb") as f:
        data = f.read()
    return any(f'"customTitle":{json.dumps(n)}'.encode() in data for n in names)


def find_transcripts(projects_dir, repo, number, branch):
    """Transcripts that worked on the PR, then the sessions that directed them; oldest first.

    `why` says how each was found: "pr-link" or "branch" for the workers, "parent" for a session that
    messaged a worker (an orchestrator). A parent covers many PRs; readers look only at its parts
    about this one.
    """
    paths = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
    workers = keep_longest(h for h in (scan(p, repo, number, branch) for p in paths) if h)
    names = set().union(*(senders(w["path"]) for w in workers)) if workers else set()
    taken = {w["session_id"] for w in workers}
    parents = []
    for p in paths if names else []:
        if titled(p, names):
            hit = scan(p, repo, -1, None, force=True)
            if hit["session_id"] not in taken:
                parents.append(dict(hit, why=["parent"]))
    return sorted(workers + keep_longest(parents), key=lambda h: h["first_ts"] or "")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", help="owner/name, e.g. AppliedAgents/sellside")
    ap.add_argument("number", type=int)
    ap.add_argument("--projects", default=PROJECTS)
    ap.add_argument("--branch", help="head branch; skips the GitHub lookup when given")
    args = ap.parse_args()
    pr = {"number": args.number, "headRefName": args.branch} if args.branch else pr_facts(args.repo, args.number)
    found = find_transcripts(args.projects, args.repo, args.number, pr.get("headRefName"))
    print(json.dumps({"pr": pr, "transcripts": found}, indent=1))


if __name__ == "__main__":
    main()
