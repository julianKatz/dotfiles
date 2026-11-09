"""Tests for pr_hook.py, written from the spec. Run from this directory: python3 -B -m unittest test_pr_hook"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import pr_hook

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr_hook.py")
URL = "https://github.com/AppliedAgents/sellside/pull/112"


def payload(command, cwd, stdout="", stderr="", tool="Bash", **response):
    resp = {"stdout": stdout, "stderr": stderr}
    resp.update(response)
    return {"tool_name": tool, "tool_input": {"command": command}, "tool_response": resp, "cwd": cwd}


class Decide(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp())
        self.cwd = os.path.join(self.root, "sellside", ".claude", "worktrees", "wt")
        os.makedirs(self.cwd)

    def decide(self, *a, **k):
        return pr_hook.decide(payload(*a, **k), self.root)

    def test_pr_create_fires_with_open_stage_and_url(self):
        text = self.decide("gh pr create --title T --body B", self.cwd, stdout=URL + "\n")
        self.assertIsInstance(text, str)
        self.assertIn("open", text)
        self.assertIn(URL, text)

    def test_pr_create_inside_compound_command_fires(self):
        text = self.decide("git push -u origin HEAD && gh pr create --fill", self.cwd, stdout=URL)
        self.assertIsNotNone(text)
        self.assertIn(URL, text)

    def test_pr_merge_fires_with_merge_stage_and_number(self):
        text = self.decide("gh pr merge 112 --squash", self.cwd, stdout="")
        self.assertIsNotNone(text)
        self.assertIn("merge", text)
        self.assertIn("112", text)

    def test_pr_merge_by_branch_names_the_branch(self):
        text = self.decide("gh pr merge claude/zones --squash --delete-branch", self.cwd)
        self.assertIsNotNone(text)
        self.assertIn("claude/zones", text)

    def test_other_gh_pr_commands_do_not_fire(self):
        for cmd in ["gh pr view 112", "gh pr list --state open", "git push", "gh pr checks 112"]:
            self.assertIsNone(self.decide(cmd, self.cwd, stdout=URL), cmd)

    def test_auto_merge_only_queues_so_does_not_fire(self):
        # --auto merges later, when checks pass; the retro waits for the real merge.
        for cmd in ["gh pr merge 112 --auto --squash", "gh pr merge --squash --auto"]:
            self.assertIsNone(self.decide(cmd, self.cwd, stdout="Pull request #112 will be automatically merged"), cmd)

    def test_disable_auto_does_not_fire(self):
        self.assertIsNone(self.decide("gh pr merge 112 --disable-auto", self.cwd, stdout="ok"))

    def test_non_bash_tool_does_not_fire(self):
        self.assertIsNone(self.decide("gh pr create --fill", self.cwd, stdout=URL, tool="Read"))

    def test_cwd_outside_root_does_not_fire(self):
        outside = os.path.realpath(tempfile.mkdtemp())
        self.assertIsNone(self.decide("gh pr create --fill", outside, stdout=URL))

    def test_sibling_folder_sharing_root_prefix_does_not_fire(self):
        sibling = self.root + "-other"
        os.makedirs(sibling)
        self.assertIsNone(self.decide("gh pr create --fill", sibling, stdout=URL))

    def test_failed_command_does_not_fire(self):
        self.assertIsNone(self.decide("gh pr create --fill", self.cwd, stdout="",
                                      stderr="pull request create failed: GraphQL: No commits"))
        self.assertIsNone(self.decide("gh pr merge 112 --squash", self.cwd, stdout="",
                                      stderr="X Pull request is not mergeable: error"))

    def test_interrupted_command_does_not_fire(self):
        self.assertIsNone(self.decide("gh pr create --fill", self.cwd, stdout=URL, interrupted=True))

    def test_stderr_noise_with_stdout_still_fires(self):
        text = self.decide("gh pr create --fill", self.cwd, stdout=URL,
                           stderr="Warning: 1 uncommitted change; error reporting disabled")
        self.assertIsNotNone(text)
        self.assertIn(URL, text)

    def test_incomplete_payloads_do_not_fire_or_crash(self):
        for p in [{}, {"tool_name": "Bash"}, {"tool_name": "Bash", "tool_input": {}, "cwd": self.cwd},
                  {"tool_name": "Bash", "tool_input": {"command": "gh pr create"}}]:
            self.assertIsNone(pr_hook.decide(p, self.root), p)


class AsAHook(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp())
        self.cwd = os.path.join(self.root, "sellside")
        os.makedirs(self.cwd)

    def run_hook(self, stdin, env_extra=None):
        env = dict(os.environ, PR_RETRO_ROOT=self.root)
        env.update(env_extra or {})
        return subprocess.run([sys.executable, "-B", HOOK], input=stdin, env=env,
                              capture_output=True, text=True, timeout=10)

    def test_fires_with_post_tool_use_json(self):
        p = payload("gh pr create --fill", self.cwd, stdout=URL)
        out = self.run_hook(json.dumps(p))
        self.assertEqual(out.returncode, 0, out.stderr)
        body = json.loads(out.stdout)
        hso = body["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PostToolUse")
        self.assertEqual(hso["additionalContext"], pr_hook.decide(p, self.root))
        self.assertIn(URL, hso["additionalContext"])

    def test_no_fire_prints_nothing(self):
        out = self.run_hook(json.dumps(payload("gh pr view 112", self.cwd, stdout=URL)))
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout, "")

    def test_bad_input_never_blocks_or_errors(self):
        for stdin in ["", "not json", "[]", "null", "42", json.dumps({"tool_name": "Bash"})]:
            out = self.run_hook(stdin)
            self.assertEqual(out.returncode, 0, stdin)
            self.assertEqual(out.stdout, "", stdin)

    def test_default_root_is_dev_applied_agents_under_home(self):
        home = os.path.realpath(tempfile.mkdtemp())
        cwd = os.path.join(home, "dev-applied-agents", "sellside")
        os.makedirs(cwd)
        env = {k: v for k, v in os.environ.items() if k != "PR_RETRO_ROOT"}
        env["HOME"] = home
        p = payload("gh pr merge 112 --squash", cwd)
        out = subprocess.run([sys.executable, "-B", HOOK], input=json.dumps(p), env=env,
                             capture_output=True, text=True, timeout=10)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("112", json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
