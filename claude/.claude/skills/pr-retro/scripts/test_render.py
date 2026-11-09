"""Tests for render.py. Run from this directory: python3 -B -m unittest test_render"""
import json
import os
import tempfile
import unittest

import render

PR = {"number": 112, "title": "APP-287", "url": "https://github.com/o/r/pull/112", "state": "MERGED",
      "createdAt": "2026-11-06T21:41:03Z", "mergedAt": "2026-11-07T00:26:29Z", "additions": 10,
      "deletions": 2, "changedFiles": 3, "commits": [{}, {}],
      "statusCheckRollup": [{"conclusion": "FAILURE"}, {"conclusion": "SUCCESS"}]}


def session(sid, why, last, **m):
    return {"session_id": sid, "title": sid, "why": why, "path": f"/t/{sid}.jsonl", "last_ts": last,
            "metrics": dict({"human_prompts": 0, "peer_messages": 0, "tool_errors": 0, "subagents": 0,
                             "workflows": 0, "wall_hours": 1.0}, **m)}


MANIFEST = {"repo": "o/r", "sessions": [session("worker", ["pr-link"], "2026-11-06T22:00:00Z", human_prompts=3),
                                        session("boss", ["parent"], "2026-11-07T01:00:00Z", human_prompts=99)]}


def finding(title, severity="medium"):
    return {"title": title, "what_happened": "x", "refs": ["worker:L1"], "cost": "c", "severity": severity,
            "better_way": "b", "root_cause": "judgment", "proposed_change": {"target": "none", "text": ""},
            "actor": "claude", "category": "rework"}


def result(*findings, headline="h"):
    return {"missing_lenses": [], "retro": {"headline": headline, "scores": {"rework": 3}, "findings": list(findings),
                                            "went_well": ["w"], "dropped": []}}


class Build(unittest.TestCase):
    def test_open_stage_record(self):
        r = render.build(None, PR, MANIFEST, result(finding("a", "low"), finding("b", "high")), "open", "now")
        self.assertEqual([f["title"] for f in r["findings"]], ["b", "a"])  # high first
        self.assertTrue(all(f["stage"] == "open" for f in r["findings"]))
        self.assertEqual(r["checks_failed"], 1)
        self.assertEqual(r["size"]["commits"], 2)
        self.assertEqual(r["stages"]["open"]["covered_until"], "2026-11-07T01:00:00Z")

    def test_parent_metrics_are_left_out(self):
        r = render.build(None, PR, MANIFEST, result(), "open", "now")
        self.assertEqual(r["metrics"]["human_prompts"], 3)
        self.assertEqual(r["metrics"]["sessions"], 2)

    def test_merge_stage_keeps_open_findings_and_headline(self):
        first = render.build(None, PR, MANIFEST, result(finding("a"), headline="open h"), "open", "t1")
        r = render.build(first, PR, MANIFEST, result(finding("m", "high"), headline="merge h"), "merge", "t2")
        self.assertEqual([(f["title"], f["stage"]) for f in r["findings"]], [("a", "open"), ("m", "merge")])
        self.assertEqual(r["stages"]["open"]["headline"], "open h")
        self.assertEqual(r["stages"]["merge"]["headline"], "merge h")

    def test_rerun_of_a_stage_replaces_only_that_stage(self):
        first = render.build(None, PR, MANIFEST, result(finding("a")), "open", "t1")
        second = render.build(first, PR, MANIFEST, result(finding("m")), "merge", "t2")
        again = render.build(second, PR, MANIFEST, result(finding("a2")), "open", "t3")
        self.assertEqual(sorted(f["title"] for f in again["findings"]), ["a2", "m"])

    def test_null_retro_still_renders(self):
        r = render.build(None, PR, MANIFEST, {"retro": None, "missing_lenses": ["rework"]}, "open", "now")
        self.assertEqual(r["findings"], [])
        self.assertIn("no result from rework", render.markdown(r))

    def test_unwraps_task_output_file(self):
        bare = result(finding("a"))
        self.assertIs(render.unwrap(bare), bare)
        self.assertEqual(render.unwrap({"summary": "s", "result": bare}), bare)
        self.assertEqual(render.unwrap({"summary": "s", "result": json.dumps(bare)}), bare)

    def test_bad_refs_lists_only_missing_rows(self):
        work = tempfile.mkdtemp()
        os.makedirs(os.path.join(work, "digests"))
        with open(os.path.join(work, "digests", "abcdef12-rest.md"), "w") as f:
            f.write("# t\n\nL5 10:00 JULIAN: hi\nL12 TOOL Bash: ls\n")
        f = finding("a")
        f["refs"] = ["abcdef12:L5", "abcdef12:L12", "abcdef12:L6", "00000000:L5", "pr:body"]
        self.assertEqual(render.bad_refs([f], work), ["abcdef12:L6", "00000000:L5"])

    def test_name_uses_opened_date_and_repo(self):
        self.assertEqual(render.base_name("o/sellside", PR), "2026-11-06-sellside-pr112")

    def test_markdown_shows_change_only_when_targeted(self):
        f = finding("t")
        f["proposed_change"] = {"target": "memory", "text": "remember X"}
        md = render.markdown(render.build(None, PR, MANIFEST, result(f, finding("u")), "open", "now"))
        self.assertIn("**Change (memory):** remember X", md)
        self.assertEqual(md.count("**Change"), 1)


if __name__ == "__main__":
    unittest.main()
