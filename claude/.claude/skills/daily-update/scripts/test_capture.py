"""Tests for capture.py. Run from this directory: python3 -B -m unittest test_capture"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime

import capture

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture.py")
NOW = datetime(2026, 11, 3, 17, 30)  # 5:30 pm local


def human(text, pid="p1", ts="2026-11-04T01:00:00Z", branch="claude/x"):
    return {"type": "user", "promptId": pid, "timestamp": ts, "origin": {"kind": "human"},
            "gitBranch": branch, "message": {"role": "user", "content": text}}


def wrap(recap, tid="w1", pid="p1", ts="2026-11-04T01:05:00Z"):
    """Real transcripts: assistant entries carry no promptId; the tool result after it does."""
    return {"type": "assistant", "timestamp": ts, "message": {"content": [
        {"type": "text", "text": "done"},
        {"type": "tool_use", "id": tid, "name": "mcp__ccd_turn__wrap_up", "input": {"recap": recap}}]}}


def result(tid="w1", pid="p1"):
    return {"type": "user", "promptId": pid, "message": {"content": [
        {"type": "tool_result", "tool_use_id": tid, "content": "ok"}]}}


def title(text):
    return {"type": "custom-title", "customTitle": text}


def pr(url):
    return {"type": "pr-link", "prUrl": url, "prNumber": 73}


def payload(path, pid="p1"):
    return {"session_id": "s1", "transcript_path": path, "cwd": "/repo/wt", "prompt_id": pid}


def lines(*entries):
    return [json.dumps(e).encode() for e in entries]


def closing(text, ts="2026-11-04T01:06:00Z"):
    return {"type": "assistant", "timestamp": ts, "message": {"content": [{"type": "text", "text": text}]}}


def note(kind, pid="p1", text="background task finished"):
    return {"type": "user", "promptId": pid, "origin": {"kind": kind} if kind else None,
            "message": {"content": text}}


class ExtractTurn(unittest.TestCase):
    def test_logs_the_turns_recap_title_pr_and_prompt(self):
        entry = capture.extract(payload("t"), lines(
            title("Old name"), title("Callie CI"), pr("https://gh/pr/72"), pr("https://gh/pr/73"),
            human("Set up CI please"), wrap("CI runs on every PR now.")))
        self.assertEqual(entry["recap"], "CI runs on every PR now.")
        self.assertEqual(entry["recap_from"], "wrap_up")
        self.assertEqual(entry["title"], "Callie CI")
        self.assertEqual(entry["prs"], ["https://gh/pr/72", "https://gh/pr/73"])
        self.assertEqual(entry["prompt"], "Set up CI please")
        self.assertEqual(entry["branch"], "claude/x")
        self.assertEqual(entry["cwd"], "/repo/wt")
        self.assertEqual(entry["prompt_id"], "p1")
        self.assertEqual(entry["transcript"], "t")

    def test_turn_without_wrap_up_logs_the_closing_message(self):
        # Real work often ends without a wrap-up ("write an email to MT").
        entry = capture.extract(payload("t", pid="p2"), lines(
            human("build it"), wrap("Built."), result(),
            human("write an email to MT", pid="p2"), closing("Draft is in Gmail.")))
        self.assertEqual(entry["prompt"], "write an email to MT")
        self.assertEqual(entry["recap"], "Draft is in Gmail.")
        self.assertEqual(entry["recap_from"], "closing")

    def test_long_closing_message_is_cut(self):
        entry = capture.extract(payload("t"), lines(human("go"), closing("word " * 500)))
        self.assertLessEqual(len(entry["recap"]), capture.CLOSING_CHARS + 1)
        self.assertTrue(entry["recap"].endswith("…"))

    def test_notification_turn_without_wrap_up_logs_nothing(self):
        entry = capture.extract(payload("t", pid="p2"), lines(
            human("go"), wrap("ok"), result(), note("task-notification", pid="p2"), closing("noted")))
        self.assertIsNone(entry)

    def test_uses_the_last_wrap_up_in_the_turn(self):
        entry = capture.extract(payload("t"), lines(
            human("go"), wrap("first", tid="a"), wrap("second", tid="b")))
        self.assertEqual(entry["recap"], "second")

    def test_prompt_strips_system_reminders_and_pastes(self):
        text = [{"type": "text", "text": "<system-reminder>\nworktree stuff\n</system-reminder>\n\n"},
                {"type": "text", "text": "<pasted_content id=x>big log</pasted_content> fix this"}]
        entry = capture.extract(payload("t"), lines(human(text), wrap("Fixed.")))
        self.assertEqual(entry["prompt"], "[pasted] fix this")

    def test_shell_command_prompt_is_shown_as_shell(self):
        text = "<bash-input>cp a b</bash-input><bash-stdout>lots</bash-stdout><bash-stderr></bash-stderr>"
        entry = capture.extract(payload("t"), lines(human(text), wrap("ok")))
        self.assertEqual(entry["prompt"], "[shell: cp a b]")

    def test_long_prompt_is_cut_at_a_word_with_marker(self):
        entry = capture.extract(payload("t"), lines(human("word " * 200), wrap("ok")))
        self.assertLessEqual(len(entry["prompt"]), capture.PROMPT_CHARS + 1)
        self.assertTrue(entry["prompt"].endswith("…"))

    def test_wrap_up_after_background_work_carries_the_earlier_request(self):
        # Julian asks, Claude starts a workflow and stops; the result turn wraps up.
        for kind in ["task-notification", "peer", None]:
            entry = capture.extract(payload("t", pid="p2"), lines(
                human("review the plan"), closing("Reviewers running."),
                note(kind, pid="p2"), wrap("Plan fixed.", pid="p2")))
            self.assertEqual(entry["recap"], "Plan fixed.")
            self.assertEqual(entry["prompt"], "review the plan")
            self.assertTrue(entry["prompt_carried"])

    def test_thread_started_by_another_session_has_empty_prompt(self):
        entry = capture.extract(payload("t"), lines(note(None, text="brief"), wrap("Merged X.")))
        self.assertEqual(entry["recap"], "Merged X.")
        self.assertEqual(entry["prompt"], "")

    def test_missing_prompt_id_falls_back_to_the_last_turn(self):
        p = payload("t", pid=None)
        entry = capture.extract(p, lines(human("a"), wrap("old", tid="o"), result("o"),
                                         human("b", pid="p2"), wrap("new", tid="n", pid="p2"),
                                         result("n", pid="p2")))
        self.assertEqual(entry["recap"], "new")
        self.assertEqual(entry["prompt"], "b")

    def test_garbage_lines_are_skipped(self):
        entry = capture.extract(payload("t"), [b"not json", b"[1,2]"] + lines(human("go"), wrap("ok")))
        self.assertEqual(entry["recap"], "ok")


class WriteLog(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def read(self, name):
        with open(os.path.join(self.dir, name)) as f:
            return [json.loads(l) for l in f]

    def test_appends_to_todays_local_file(self):
        capture.record({"recap": "a"}, self.dir, NOW)
        capture.record({"recap": "b"}, self.dir, NOW)
        rows = self.read("2026-11-03.jsonl")
        self.assertEqual([r["recap"] for r in rows], ["a", "b"])
        self.assertEqual(rows[0]["logged_at"], "2026-11-03T17:30:00")

    def test_appends_even_when_todays_file_has_a_corrupt_line(self):
        with open(os.path.join(self.dir, "2026-11-03.jsonl"), "w") as f:
            f.write('{"recap": "trunc\n')
        capture.record({"recap": "a"}, self.dir, NOW)
        with open(os.path.join(self.dir, "2026-11-03.jsonl")) as f:
            self.assertEqual(json.loads(f.read().splitlines()[-1])["recap"], "a")

    def test_keeps_today_and_the_six_days_before(self):
        for name in ["2026-10-28.jsonl", "2026-10-27.jsonl", "2026-10-20-update.md", "notes.txt",
                     "coaching.md"]:
            open(os.path.join(self.dir, name), "w").close()
        capture.record({"recap": "a"}, self.dir, NOW)
        left = sorted(os.listdir(self.dir))
        # coaching.md holds the process reviews; /daily-update reads it across weeks.
        self.assertEqual(left, ["2026-10-28.jsonl", "2026-11-03.jsonl", "coaching.md", "notes.txt"])


class AsAHook(unittest.TestCase):
    def run_hook(self, stdin, logdir):
        env = dict(os.environ, DAILY_LOG_DIR=logdir)
        return subprocess.run([sys.executable, "-B", HOOK], input=stdin, env=env,
                              capture_output=True, text=True, timeout=10)

    def test_end_to_end_writes_a_line_and_prints_nothing(self):
        logdir = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile("wb", suffix=".jsonl", delete=False) as t:
            t.write(b"\n".join(lines(title("T"), human("go"), wrap("Did it."))))
        out = self.run_hook(json.dumps(payload(t.name)), logdir)
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout, "")
        files = os.listdir(logdir)
        self.assertEqual(len(files), 1)
        with open(os.path.join(logdir, files[0])) as f:
            self.assertEqual(json.loads(f.readline())["recap"], "Did it.")

    def test_bad_input_never_blocks_or_errors(self):
        for stdin in ["", "not json", json.dumps({"transcript_path": "/nope"})]:
            out = self.run_hook(stdin, tempfile.mkdtemp())
            self.assertEqual(out.returncode, 0)
            self.assertEqual(out.stdout, "")


if __name__ == "__main__":
    unittest.main()
