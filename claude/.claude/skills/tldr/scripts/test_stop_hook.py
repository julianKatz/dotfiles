"""Tests for stop_hook.py. Run from this directory: python3 -B -m unittest test_stop_hook"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import stop_hook

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stop_hook.py")
T0 = "2026-09-25T12:00:00.000Z"
NOW = stop_hook.parse_time(T0) + 60  # a minute after the prompt


def at(minutes):
    """Timestamp `minutes` after T0, in the transcript's format."""
    return T0.replace("12:00", "12:%02d" % minutes)


def human(text, pid="p1", ts=T0):
    return {"type": "user", "promptId": pid, "timestamp": ts, "origin": {"kind": "human"},
            "message": {"role": "user", "content": text}}


def notification(pid, ts=T0):
    return {"type": "user", "promptId": pid, "timestamp": ts,
            "origin": {"kind": "task-notification"},
            "message": {"role": "user", "content": "<task-notification>done</task-notification>"}}


def work(n, pid="p1", ts=T0):
    """n tool calls, each followed by its result."""
    out = []
    for _ in range(n):
        out.append({"type": "assistant", "timestamp": ts, "message": {"content": [
            {"type": "tool_use", "id": "t", "name": "Bash", "input": {}}]}})
        out.append({"type": "user", "promptId": pid, "timestamp": ts, "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t", "content": "ok"}]}})
    return out


def say(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def words(n):
    return " ".join(["word"] * n)


def decide(entries, pid="p1", now=NOW, **payload):
    payload = dict({"prompt_id": pid, "stop_hook_active": False}, **payload)
    lines = [json.dumps(e).encode() for e in entries]
    return stop_hook.decide(payload, lines, now)


class DecideTest(unittest.TestCase):
    # --- fires ---
    def test_long_closing_after_lots_of_work_fires(self):
        reason = decide([human("go"), *work(12), say(words(250))])
        self.assertIn("run the tldr skill", reason)
        self.assertIn("12 tool calls, 250-word closing message", reason)

    def test_long_report_after_user_stepped_away_fires(self):
        # A background workflow finished 40 minutes after the user's last message.
        entries = [human("kick it off"), *work(2), say("Launched."),
                   notification("p2", at(40)), *work(1, "p2", at(40)), say(words(400))]
        reason = decide(entries, pid="p2", now=stop_hook.parse_time(at(40)))
        self.assertIn("40 min since", reason)

    def test_away_time_counts_from_the_latest_human_message(self):
        entries = [human("first", "p1", at(0)), *work(1, "p1"), say("ok"),
                   human("second", "p2", at(35)), *work(1, "p2", at(35)), say("Launched."),
                   notification("p3", at(40)), *work(1, "p3", at(40)), say(words(400))]
        self.assertIsNone(decide(entries, pid="p3", now=stop_hook.parse_time(at(40))))
        entries = [human("q", "p1", at(0)), say("a"),
                   human("follow-up", "p2", at(35)), *work(1, "p2", at(35)), say(words(400))]
        self.assertIsNone(decide(entries, pid="p2", now=stop_hook.parse_time(at(40))))

    def test_threshold_is_200_words(self):
        self.assertIsNone(decide([human("go"), *work(8), say(words(199))]))
        self.assertIsNotNone(decide([human("go"), *work(8), say(words(200))]))

    def test_closing_text_comes_from_payload_when_present(self):
        entries = [human("go"), *work(10), say("short")]
        self.assertIsNotNone(decide(entries, last_assistant_message=words(300)))

    # --- stays quiet ---
    def test_long_answer_to_a_direct_question_is_quiet(self):
        self.assertIsNone(decide([human("explain X"), *work(1), say(words(700))]))

    def test_lots_of_work_but_short_closing_is_quiet(self):
        self.assertIsNone(decide([human("go"), *work(30), say(words(60))]))

    def test_second_stop_never_blocks(self):
        entries = [human("go"), *work(30), say(words(900))]
        self.assertIsNone(decide(entries, stop_hook_active=True))

    def test_closing_that_is_already_a_tldr_is_quiet(self):
        tldr = "**Goal**\n- a\n\n**Found**\n- b\n\n**Next**\n- c " + words(300)
        self.assertIsNone(decide([human("go"), *work(12), say(tldr)]))

    def test_closing_with_only_some_labels_still_fires(self):
        partial = "**Goal**\n- a\n\n**Next**\n- c " + words(300)
        self.assertIsNotNone(decide([human("go"), *work(12), say(partial)]))

    def test_headless_turn_is_quiet(self):
        # claude -p prompts carry no origin; a recap would replace the printed result.
        prompt = {"type": "user", "promptId": "p1", "timestamp": T0,
                  "message": {"role": "user", "content": "go"}}
        self.assertIsNone(decide([prompt, *work(12), say(words(300))]))

    # --- what counts as the turn ---
    def test_earlier_turns_do_not_count(self):
        entries = [human("first", "p1"), *work(25, "p1"), say(words(800)),
                   human("thanks", "p2"), *work(1, "p2"), say(words(250))]
        self.assertIsNone(decide(entries, pid="p2"))

    def test_text_before_the_last_tool_call_is_not_closing(self):
        entries = [human("go"), *work(5), say(words(500)), *work(5), say(words(40))]
        self.assertIsNone(decide(entries))

    def test_meta_entries_inside_the_turn_do_not_split_it(self):
        meta = {"type": "user", "promptId": "p1", "isMeta": True, "message": {"content": "skill"}}
        compact = {"type": "user", "promptId": "p1", "isCompactSummary": True,
                   "message": {"content": "This session is being continued..."}}
        entries = [human("go"), meta, *work(4), compact, *work(4), say(words(250))]
        self.assertIsNotNone(decide(entries))

    def test_non_message_entries_are_ignored(self):
        noise = [{"type": "attachment"}, {"type": "system", "subtype": "stop_hook_summary"},
                 {"type": "last-prompt"}, [1, 2]]
        entries = [human("go"), *work(10), say(words(250)), *noise]
        self.assertIsNotNone(decide(entries))

    def test_synthetic_assistant_text_is_ignored(self):
        synthetic = {"type": "assistant", "message": {
            "model": "<synthetic>", "content": [{"type": "text", "text": words(500)}]}}
        self.assertIsNone(decide([human("go"), *work(10), synthetic]))


class MainTest(unittest.TestCase):
    """Runs the script the way Claude Code does: payload on stdin, JSON on stdout."""

    def run_hook(self, stdin):
        proc = subprocess.run([sys.executable, HOOK], input=stdin,
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        return proc.stdout

    def payload_for(self, entries, d):
        path = os.path.join(d, "t.jsonl")
        with open(path, "w") as f:
            f.write("{not json\n")
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return json.dumps({"prompt_id": "p1", "transcript_path": path,
                           "hook_event_name": "Stop", "stop_hook_active": False})

    def test_blocks_with_decision_json(self):
        with tempfile.TemporaryDirectory() as d:
            out = json.loads(self.run_hook(self.payload_for(
                [human("go"), *work(9), say(words(300))], d)))
        self.assertEqual(out["decision"], "block")
        self.assertIn("tldr", out["reason"])

    def test_missing_transcript_allows_stop(self):
        self.assertEqual(self.run_hook(json.dumps({"transcript_path": "/nope.jsonl"})), "")

    def test_garbage_stdin_allows_stop(self):
        self.assertEqual(self.run_hook("not json"), "")


if __name__ == "__main__":
    unittest.main()
