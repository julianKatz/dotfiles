"""Tests for find_work.find_transcripts, written from the spec. Run from this directory:
python3 -B -m unittest test_find_work"""
import json
import os
import tempfile
import unittest

import find_work

REPO = "AppliedAgents/sellside"


def user(ts, branch="main", text="hi"):
    return {"type": "user", "timestamp": ts, "gitBranch": branch, "origin": {"kind": "human"},
            "message": {"role": "user", "content": text}}


def pr(n=112, repo=REPO):
    return {"type": "pr-link", "prNumber": n, "prUrl": f"https://github.com/{repo}/pull/{n}",
            "prRepository": repo, "sessionId": "x"}


def title(text):
    return {"type": "custom-title", "customTitle": text}


class FindTranscripts(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def write(self, project, sid, *entries, raw=None):
        d = os.path.join(self.root, project)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, sid + ".jsonl")
        body = raw if raw is not None else [json.dumps(e) for e in entries]
        with open(path, "w") as f:
            f.write("\n".join(body) + "\n")
        return path

    def find(self, number=112, branch="claude/zones", repo=REPO):
        return find_work.find_transcripts(self.root, repo, number, branch)

    def test_pr_link_match_reports_path_id_title_times_and_lines(self):
        path = self.write("proj-a", "s1",
                          user("2026-11-06T19:00:00.000Z"), title("Callie zones"), pr(112),
                          user("2026-11-06T21:00:00.000Z"))
        found = self.find()
        self.assertEqual(len(found), 1)
        t = found[0]
        self.assertEqual(t["path"], path)
        self.assertEqual(t["session_id"], "s1")
        self.assertEqual(t["why"], ["pr-link"])
        self.assertEqual(t["title"], "Callie zones")
        self.assertTrue(t["first_ts"].startswith("2026-11-06T19:00"))
        self.assertTrue(t["last_ts"].startswith("2026-11-06T21:00"))
        self.assertEqual(t["lines"], 4)

    def test_branch_match_alone(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z", branch="claude/zones"))
        found = self.find()
        self.assertEqual([t["why"] for t in found], [["branch"]])

    def test_both_reasons(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z", branch="claude/zones"), pr(112))
        self.assertEqual(set(self.find()[0]["why"]), {"pr-link", "branch"})

    def test_unrelated_transcript_is_excluded(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z", branch="claude/other"), pr(90))
        self.assertEqual(self.find(), [])

    def test_pr_number_must_match_exactly(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z"), pr(112))
        self.write("proj-a", "s2", user("2026-11-06T19:00:00.000Z"), pr(1120))
        self.assertEqual(self.find(number=11, branch="claude/none"), [])
        self.assertEqual([t["session_id"] for t in self.find(number=112, branch="claude/none")], ["s1"])

    def test_same_number_in_another_repo_does_not_match(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z"), pr(112, repo="AppliedAgents/other"))
        self.assertEqual(self.find(branch="claude/none"), [])

    def test_repo_match_is_case_insensitive(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z"), pr(112, repo="appliedagents/SELLSIDE"))
        self.assertEqual(len(self.find(branch="claude/none")), 1)

    def test_subagent_transcripts_are_not_scanned(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z"))
        sub = os.path.join(self.root, "proj-a", "s1", "subagents")
        os.makedirs(sub)
        with open(os.path.join(sub, "agent-a1.jsonl"), "w") as f:
            f.write(json.dumps(pr(112)) + "\n" + json.dumps(user("2026-11-06T19:05:00.000Z", "claude/zones")))
        self.assertEqual(self.find(), [])

    def test_session_in_two_folders_keeps_the_longer_copy(self):
        entries = [user("2026-11-06T19:00:00.000Z", "claude/zones"), pr(112),
                   user("2026-11-06T20:00:00.000Z", "claude/zones")]
        self.write("proj-old", "s1", *entries[:2])
        longer = self.write("proj-new", "s1", *entries, user("2026-11-06T21:00:00.000Z", "claude/zones"))
        found = self.find()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["path"], longer)
        self.assertEqual(found[0]["lines"], 4)

    def test_sorted_by_first_timestamp(self):
        self.write("proj-a", "late", user("2026-11-07T09:00:00.000Z", "claude/zones"))
        self.write("proj-b", "early", user("2026-11-05T09:00:00.000Z", "claude/zones"))
        self.write("proj-a", "middle", user("2026-11-06T09:00:00.000Z"), pr(112))
        self.assertEqual([t["session_id"] for t in self.find()], ["early", "middle", "late"])

    def test_malformed_lines_are_skipped(self):
        self.write("proj-a", "s1", raw=["{broken", json.dumps(pr(112)), "", "not json at all",
                                        json.dumps(user("2026-11-06T19:00:00.000Z"))])
        found = self.find(branch="claude/none")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["why"], ["pr-link"])

    def test_no_branch_still_matches_on_pr_link(self):
        self.write("proj-a", "s1", user("2026-11-06T19:00:00.000Z"), pr(112))
        self.write("proj-a", "s2", user("2026-11-06T19:00:00.000Z", branch="claude/zones"))
        self.assertEqual([t["session_id"] for t in self.find(branch=None)], ["s1"])

    def test_empty_projects_dir(self):
        self.assertEqual(self.find(), [])


if __name__ == "__main__":
    unittest.main()
