#!/usr/bin/env python3
"""Fill a work folder for one PR's retro: the PR's facts, its sessions, and a digest of each.

    python3 prepare.py AppliedAgents/sellside 112 --work /tmp/retro-112
    -> /tmp/retro-112/pr.json, manifest.json, digests/<session_id>.md

manifest.json lists each session with how it was found (pr-link, branch or parent), its raw transcript
path, and its digest metrics. Prints the manifest's summary so the caller can see what was found.
"""
import argparse
import json
import os

from digest import digest, read_lines
from find_work import PROJECTS, find_transcripts, pr_facts


def prepare(repo, number, work, projects=PROJECTS, facts=None):
    pr = facts if facts is not None else pr_facts(repo, number)
    found = find_transcripts(projects, repo, number, pr.get("headRefName"))
    os.makedirs(os.path.join(work, "digests"), exist_ok=True)
    sessions = []
    for t in found:
        text, metrics = digest(read_lines(t["path"]), t["path"][:-6])
        out = os.path.join(work, "digests", f"{t['session_id']}.md")
        with open(out, "w") as f:
            f.write(text)
        sessions.append(dict(t, digest=out, digest_bytes=len(text.encode()), metrics=metrics))
    manifest = {"repo": repo, "number": number, "sessions": sessions}
    with open(os.path.join(work, "pr.json"), "w") as f:
        json.dump(pr, f, indent=1)
    with open(os.path.join(work, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo")
    ap.add_argument("number", type=int)
    ap.add_argument("--work", required=True)
    ap.add_argument("--projects", default=PROJECTS)
    args = ap.parse_args()
    m = prepare(args.repo, args.number, args.work, args.projects)
    for s in m["sessions"]:
        print(f"{s['session_id'][:8]} {','.join(s['why']):16} {s['digest_bytes'] // 1024:>4} KB  {s['title']}")
    if not m["sessions"]:
        print("no sessions found")


if __name__ == "__main__":
    main()
