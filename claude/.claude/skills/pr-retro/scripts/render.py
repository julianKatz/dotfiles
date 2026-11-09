#!/usr/bin/env python3
"""Write one PR's retro from the workflow's result: a .json for the later meta-analysis, a .md for people.

    python3 render.py --work /tmp/retro-112 --result result.json --stage open --out ~/dev-applied-agents/retros

Files are named <opened date>-<repo>-pr<N>.json/.md, one pair per PR. The open stage writes them; the merge
stage adds its findings (stage "merge") and its own headline and scores, keeping the open stage's.
Schema of the .json (version 1):
    repo, number, title, url, state, opened_at, merged_at, closed_at,
    size: {additions, deletions, files, commits}, checks_failed,
    sessions: [{id, title, why, transcript}],
    metrics: {sessions, human_prompts, peer_messages, tool_errors, subagents, workflows, wall_hours},
    stages: {open|merge: {run_at, covered_until, headline, scores, went_well, dropped, missing_lenses}},
    findings: [{category, stage, title, what_happened, refs, cost, severity, better_way, root_cause,
                proposed_change: {target, text}, actor}]
"""
import argparse
import json
import os
from datetime import datetime, timezone

SCHEMA = 1
SEVERITY = {"high": 0, "medium": 1, "low": 2}


def base_name(repo, pr):
    day = (pr.get("createdAt") or datetime.now(timezone.utc).isoformat())[:10]
    return f"{day}-{repo.split('/')[-1]}-pr{pr['number']}"


def metrics(sessions):
    total = {"sessions": len(sessions), "human_prompts": 0, "peer_messages": 0, "tool_errors": 0,
             "subagents": 0, "workflows": 0, "wall_hours": 0.0}
    for s in sessions:
        if "parent" in s["why"]:
            continue  # an orchestrator's numbers cover many PRs, so they'd swamp this one's
        for key in ("human_prompts", "peer_messages", "tool_errors", "subagents", "workflows"):
            total[key] += s["metrics"].get(key) or 0
        total["wall_hours"] += s["metrics"].get("wall_hours") or 0
    total["wall_hours"] = round(total["wall_hours"], 1)
    return total


def build(previous, pr, manifest, result, stage, now):
    """The retro record: the previous one (if any) with this stage's result merged in."""
    retro = result.get("retro") or {}
    sessions = manifest["sessions"]
    checks = pr.get("statusCheckRollup") or []
    record = dict(previous or {})
    record.update({
        "schema": SCHEMA, "repo": manifest["repo"], "number": pr["number"], "title": pr.get("title"),
        "url": pr.get("url"), "state": pr.get("state"), "opened_at": pr.get("createdAt"),
        "merged_at": pr.get("mergedAt"), "closed_at": pr.get("closedAt"),
        "size": {"additions": pr.get("additions"), "deletions": pr.get("deletions"),
                 "files": pr.get("changedFiles"), "commits": len(pr.get("commits") or [])},
        "checks_failed": sum(1 for c in checks if (c.get("conclusion") or "").upper() == "FAILURE"),
        "sessions": [{"id": s["session_id"], "title": s["title"], "why": s["why"], "transcript": s["path"]}
                     for s in sessions],
        "metrics": metrics(sessions),
    })
    last = max((s["last_ts"] for s in sessions if s.get("last_ts")), default=None)
    stages = dict(record.get("stages") or {})
    stages[stage] = {"run_at": now, "covered_until": last, "headline": retro.get("headline"),
                     "scores": retro.get("scores"), "went_well": retro.get("went_well") or [],
                     "dropped": retro.get("dropped") or [], "missing_lenses": result.get("missing_lenses") or []}
    record["stages"] = stages
    kept = [f for f in record.get("findings") or [] if f.get("stage") != stage]  # a re-run replaces its stage
    new = [dict(f, stage=stage) for f in retro.get("findings") or []]
    record["findings"] = sorted(kept + new, key=lambda f: (f["stage"] != "open", SEVERITY.get(f.get("severity"), 3)))
    return record


def markdown(r):
    size = r["size"]
    m = r["metrics"]
    lines = [f"# PR retro: {r['title']}", "",
             f"[{r['repo']}#{r['number']}]({r['url']}) · {r['state']} · opened {(r['opened_at'] or '')[:10]}"
             f"{' · merged ' + r['merged_at'][:10] if r.get('merged_at') else ''} · "
             f"+{size['additions']}/-{size['deletions']} in {size['files']} files, {size['commits']} commits", "",
             "## At a glance", ""]
    for stage, s in r["stages"].items():
        scores = ", ".join(f"{k} {v}" for k, v in (s.get("scores") or {}).items())
        lines.append(f"- **{stage}:** {s.get('headline') or '(no headline)'}" + (f" Scores (1-5): {scores}." if scores else ""))
    lines += [f"- {m['sessions']} sessions, {m['human_prompts']} prompts from Julian, {m['peer_messages']} from "
              f"other sessions, {m['tool_errors']} tool errors, {m['subagents']} subagents, "
              f"~{m['wall_hours']} h of session time; {r['checks_failed']} failed checks.", ""]
    for i, f in enumerate(r["findings"], 1):
        change = f["proposed_change"]
        lines += [f"## {i}. {f['title']}", "",
                  f"*{f['category']} · {f['severity']} · {f['stage']} stage · {f['actor']} · {f['root_cause']}*", "",
                  f"- **What happened:** {f['what_happened']}",
                  f"- **Cost:** {f['cost']}",
                  f"- **Better:** {f['better_way']}"]
        if change.get("target") != "none" and change.get("text"):
            lines.append(f"- **Change ({change['target']}):** {change['text']}")
        lines += [f"- Evidence: {', '.join(f['refs'])}", ""]
    went = [w for s in r["stages"].values() for w in s.get("went_well") or []]
    if went:
        lines += ["## Went well", "", *[f"- {w}" for w in went], ""]
    lines += ["<details><summary>Sessions read, and findings dropped</summary>", ""]
    lines += [f"- `{s['id'][:8]}` {s['title']} ({', '.join(s['why'])})" for s in r["sessions"]]
    for stage, s in r["stages"].items():
        for d in s.get("dropped") or []:
            lines.append(f"- dropped ({stage}): {d}")
        if s.get("missing_lenses"):
            lines.append(f"- {stage}: no result from {', '.join(s['missing_lenses'])}")
    lines += ["", "</details>", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--work", required=True)
    ap.add_argument("--result", required=True, help="the workflow's return value, saved as JSON")
    ap.add_argument("--stage", choices=["open", "merge"], required=True)
    ap.add_argument("--out", default=os.path.expanduser("~/dev-applied-agents/retros"))
    args = ap.parse_args()
    load = lambda p: json.load(open(p))
    pr, manifest, result = load(os.path.join(args.work, "pr.json")), load(os.path.join(args.work, "manifest.json")), load(args.result)
    path = os.path.join(args.out, base_name(manifest["repo"], pr))
    previous = load(path + ".json") if os.path.exists(path + ".json") else None
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = build(previous, pr, manifest, result, args.stage, now)
    os.makedirs(args.out, exist_ok=True)
    with open(path + ".json", "w") as f:
        json.dump(record, f, indent=1)
    with open(path + ".md", "w") as f:
        f.write(markdown(record))
    print(path + ".md")


if __name__ == "__main__":
    main()
