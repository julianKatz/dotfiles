"""Tests for digest.py, written from the spec. Run from this directory: python3 -B -m unittest test_digest"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

import digest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "digest.py")
ROW = re.compile(r"^[\s>*-]*L(\d+)\b")


def human(text, ts="2026-11-06T19:26:47.388Z", origin="human", meta=None):
    e = {"type": "user", "promptId": "p1", "timestamp": ts, "gitBranch": "claude/x",
         "message": {"role": "user", "content": text}}
    if origin == "human":
        e["origin"] = {"kind": "human"}
    elif origin != "missing":
        e["origin"] = origin  # a dict, or None
    if meta is not None:
        e["isMeta"] = meta
    return e


def peer(title, body, ts="2026-11-06T19:30:00.000Z"):
    return {"type": "user", "timestamp": ts,
            "origin": {"kind": "peer", "name": title, "members": [{"body": body}]},
            "message": {"role": "user", "content": body}}


def notice(text, ts="2026-11-06T19:31:00.000Z"):
    return {"type": "user", "timestamp": ts, "origin": {"kind": "task-notification"},
            "message": {"role": "user", "content": text}}


def say(text, ts="2026-11-06T19:27:00.000Z"):
    return {"type": "assistant", "timestamp": ts, "message": {"content": [{"type": "text", "text": text}]}}


def tool(name, inp, tid="t1", ts="2026-11-06T19:28:00.000Z"):
    return {"type": "assistant", "timestamp": ts, "message": {"content": [
        {"type": "tool_use", "id": tid, "name": name, "input": inp}]}}


def result(tid, content, error=False):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": content, "is_error": error}]}}


def pr(n=112, repo="AppliedAgents/sellside"):
    return {"type": "pr-link", "prNumber": n, "prUrl": f"https://github.com/{repo}/pull/{n}",
            "prRepository": repo, "sessionId": "s1"}


def title(text):
    return {"type": "custom-title", "customTitle": text}


def lines(*entries):
    return [json.dumps(e) for e in entries]


def rows(md, n=None):
    """Timeline rows as (line_number, row_text); only rows for transcript line n when given."""
    out = []
    for line in md.splitlines():
        m = ROW.match(line)
        if m and (n is None or int(m.group(1)) == n):
            out.append((int(m.group(1)), line))
    return out


def row_text(md, n):
    found = rows(md, n)
    return "\n".join(r for _, r in found)


class HumanPrompts(unittest.TestCase):
    def test_human_prompt_row_has_line_time_and_text(self):
        md, m = digest.digest(lines(title("T"), human("Set up CI please")))
        row = row_text(md, 2)
        self.assertTrue(row, md)
        self.assertIn("19:26", row)
        self.assertIn("JULIAN:", row)
        self.assertIn("Set up CI please", row)
        self.assertEqual(m["human_prompts"], 1)

    def test_text_blocks_and_missing_origin_count_as_human(self):
        md, m = digest.digest(lines(
            human([{"type": "text", "text": "first ask"}], origin="missing"),
            human("second ask", origin=None)))
        self.assertIn("first ask", row_text(md, 1))
        self.assertIn("second ask", row_text(md, 2))
        self.assertEqual(m["human_prompts"], 2)

    def test_system_reminders_are_stripped_and_reminder_only_prompt_is_not_human(self):
        md, m = digest.digest(lines(
            human("<system-reminder>secret context</system-reminder>Fix the zone order"),
            human("<system-reminder>only a reminder</system-reminder>")))
        self.assertIn("Fix the zone order", row_text(md, 1))
        self.assertNotIn("secret context", md)
        self.assertNotIn("only a reminder", md)
        self.assertNotIn("JULIAN", row_text(md, 2))
        self.assertEqual(m["human_prompts"], 1)

    def test_meta_prompt_is_not_human(self):
        md, m = digest.digest(lines(human("caveat: local command", meta=True)))
        self.assertNotIn("JULIAN", md)
        self.assertEqual(m["human_prompts"], 0)

    def test_long_prompt_is_cut_at_2000_with_marker(self):
        md, _ = digest.digest(lines(human("x" * 2500)))
        row = row_text(md, 1)
        self.assertIn("[+500 chars]", row)
        self.assertNotIn("x" * 2001, row)

    def test_newlines_are_collapsed_to_one_row(self):
        md, _ = digest.digest(lines(human("line one\nline two\n\nline three")))
        found = rows(md, 1)
        self.assertEqual(len(found), 1)
        self.assertIn("line one", found[0][1])
        self.assertIn("line three", found[0][1])


class OtherVoices(unittest.TestCase):
    def test_peer_message_is_its_own_kind_with_session_title(self):
        md, m = digest.digest(lines(peer("Callie build", "PR is green")))
        row = row_text(md, 1)
        self.assertIn("PEER Callie build:", row)
        self.assertIn("PR is green", row)
        self.assertEqual(m["peer_messages"], 1)
        self.assertEqual(m["human_prompts"], 0)

    def test_task_notification_is_a_notice_not_a_prompt(self):
        md, m = digest.digest(lines(notice("Background task finished")))
        self.assertIn("NOTICE:", row_text(md, 1))
        self.assertNotIn("JULIAN", md)
        self.assertEqual(m["human_prompts"], 0)

    def test_assistant_text_is_cut_at_600_and_thinking_is_dropped(self):
        entry = {"type": "assistant", "timestamp": "2026-11-06T19:27:00.000Z", "message": {"content": [
            {"type": "thinking", "thinking": "private musing"},
            {"type": "text", "text": "y" * 1000}]}}
        md, m = digest.digest(lines(entry, say("short reply")))
        row = row_text(md, 1)
        self.assertIn("CLAUDE:", row)
        self.assertIn("y" * 550, row)
        self.assertNotIn("y" * 601, row)
        self.assertNotIn("private musing", md)
        self.assertEqual(m["assistant_messages"], 2)


class Tools(unittest.TestCase):
    def test_tool_rows_summarise_input_and_are_counted(self):
        md, m = digest.digest(lines(
            tool("Bash", {"command": "git status --short", "description": "status"}, "t1"),
            tool("Edit", {"file_path": "/repo/a.py", "old_string": "OLDBODY", "new_string": "NEWBODY"}, "t2"),
            tool("Agent", {"description": "Write the tests", "model": "sonnet", "prompt": "LONGPROMPT"}, "t3"),
            tool("Bash", {"command": "ls"}, "t4")))
        bash = row_text(md, 1)
        self.assertIn("TOOL Bash:", bash)
        self.assertIn("git status --short", bash)
        edit = row_text(md, 2)
        self.assertIn("TOOL Edit:", edit)
        self.assertIn("/repo/a.py", edit)
        self.assertNotIn("OLDBODY", md)
        agent = row_text(md, 3)
        self.assertIn("TOOL Agent:", agent)
        self.assertIn("Write the tests", agent)
        self.assertIn("sonnet", agent)
        self.assertEqual(m["tool_calls"], {"Bash": 2, "Edit": 1, "Agent": 1})

    def test_tool_summary_is_cut_at_200(self):
        md, _ = digest.digest(lines(tool("Bash", {"command": "z" * 500})))
        self.assertIn("z" * 150, row_text(md, 1))
        self.assertNotIn("z" * 201, md)

    def test_wrap_up_is_a_recap_row_not_a_tool_row(self):
        md, _ = digest.digest(lines(tool("mcp__ccd_turn__wrap_up",
                                         {"recap": "CI runs on every PR now.", "ask": "Merge it?"})))
        row = row_text(md, 1)
        self.assertIn("RECAP:", row)
        self.assertIn("CI runs on every PR now.", row)
        self.assertIn("Merge it?", row)
        self.assertNotIn("TOOL mcp__ccd_turn__wrap_up", md)

    def test_error_result_names_the_tool_and_success_result_is_silent(self):
        md, m = digest.digest(lines(
            tool("Bash", {"command": "pytest"}, "t1"),
            result("t1", "ERRBODY " + "e" * 500, error=True),
            tool("Read", {"file_path": "/repo/b.py"}, "t2"),
            result("t2", [{"type": "text", "text": "SUCCESSBODY"}], error=False),
            tool("Write", {"file_path": "/repo/c.py", "content": "x"}, "t3"),
            result("t3", [{"type": "text", "text": "LISTERR"}], error=True)))
        err = row_text(md, 2)
        self.assertIn("ERROR Bash:", err)
        self.assertIn("ERRBODY", err)
        self.assertNotIn("e" * 301, err)
        self.assertIn("ERROR Write:", row_text(md, 6))
        self.assertIn("LISTERR", row_text(md, 6))
        self.assertNotIn("SUCCESSBODY", md)
        self.assertEqual(rows(md, 4), [])
        self.assertEqual(m["tool_errors"], 2)


class Markers(unittest.TestCase):
    def test_pr_and_title_rows_are_deduped(self):
        md, m = digest.digest(lines(pr(112), pr(112), title("A"), title("A"), title("B"), pr(113)))
        self.assertIn("PR:", row_text(md, 1))
        self.assertEqual(rows(md, 2), [])
        self.assertIn("TITLE:", row_text(md, 3))
        self.assertEqual(rows(md, 4), [])
        self.assertIn("B", row_text(md, 5))
        self.assertIn("pull/113", row_text(md, 6))
        self.assertEqual(m["prs"], ["https://github.com/AppliedAgents/sellside/pull/112",
                                    "https://github.com/AppliedAgents/sellside/pull/113"])
        self.assertEqual(m["title"], "B")

    def test_compact_boundary_row_and_count(self):
        md, m = digest.digest(lines(
            {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-11-06T20:00:00.000Z"},
            {"type": "system", "subtype": "informational"}))
        self.assertIn("COMPACT", row_text(md, 1))
        self.assertEqual(rows(md, 2), [])
        self.assertEqual(m["compactions"], 1)

    def test_irrelevant_types_and_bad_lines_are_skipped_but_numbering_holds(self):
        raw = ["{not json", json.dumps({"type": "api-request"}), json.dumps({"type": "attachment"}),
               json.dumps({"type": "queue-operation"}), "", json.dumps(human("after junk")).encode()]
        md, m = digest.digest(raw)
        self.assertEqual([n for n, _ in rows(md)], [6])
        self.assertIn("after junk", row_text(md, 6))
        self.assertEqual(m["human_prompts"], 1)


class Metrics(unittest.TestCase):
    def test_time_span_and_wall_hours(self):
        _, m = digest.digest(lines(human("start", ts="2026-11-06T19:26:47.388Z"),
                                   say("end", ts="2026-11-06T21:56:47.388Z")))
        self.assertTrue(m["first_ts"].startswith("2026-11-06T19:26"))
        self.assertTrue(m["last_ts"].startswith("2026-11-06T21:56"))
        self.assertEqual(m["wall_hours"], 2.5)

    def test_empty_transcript_has_zero_metrics(self):
        md, m = digest.digest([])
        self.assertEqual(rows(md), [])
        self.assertEqual(m["human_prompts"], 0)
        self.assertEqual(m["tool_calls"], {})
        self.assertEqual(m["prs"], [])
        self.assertIsNone(m["first_ts"])
        self.assertIsNone(m["last_ts"])
        self.assertIsNone(m["wall_hours"])
        self.assertEqual(m["subagents"], 0)
        self.assertEqual(m["workflows"], 0)


def write_session_dir(root):
    sd = os.path.join(root, "s1")
    os.makedirs(os.path.join(sd, "subagents"))
    os.makedirs(os.path.join(sd, "workflows", "scripts"))
    with open(os.path.join(sd, "subagents", "agent-a1.jsonl"), "w") as f:
        f.write("\n".join(lines(human("Write tests from the spec", origin="missing"),
                                say("working"), say("All 12 tests written."))))
    with open(os.path.join(sd, "subagents", "agent-a1.meta.json"), "w") as f:
        json.dump({"description": "Test author", "model": "opus", "agentType": "general-purpose"}, f)
    with open(os.path.join(sd, "workflows", "wf_9.json"), "w") as f:
        json.dump({"id": "wf_9"}, f)
    with open(os.path.join(sd, "workflows", "scripts", "review-loop-wf_9.js"), "w") as f:
        f.write("// script")
    return sd


class SessionDir(unittest.TestCase):
    def test_subagents_and_workflows_sections(self):
        sd = write_session_dir(tempfile.mkdtemp())
        md, m = digest.digest(lines(human("go")), session_dir=sd)
        self.assertIn("## Subagents", md)
        sub = md.split("## Subagents", 1)[1]
        self.assertIn("Test author", sub)
        self.assertIn("opus", sub)
        self.assertIn("Write tests from the spec", sub)
        self.assertIn("All 12 tests written.", sub)
        self.assertIn("## Workflows", md)
        self.assertIn("review-loop", md.split("## Workflows", 1)[1])
        self.assertEqual(m["subagents"], 1)
        self.assertEqual(m["workflows"], 1)

    def test_missing_session_dir_omits_sections_without_crashing(self):
        for sd in [None, os.path.join(tempfile.mkdtemp(), "does-not-exist")]:
            md, m = digest.digest(lines(human("go")), session_dir=sd)
            self.assertNotIn("## Subagents", md)
            self.assertNotIn("## Workflows", md)
            self.assertEqual(m["subagents"], 0)


class Cli(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.transcript = os.path.join(d, "s1.jsonl")
        with open(self.transcript, "w") as f:
            f.write("\n".join(lines(human("Ship APP-289"), say("On it."))))
        self.dir = d

    def test_out_flag_writes_markdown_file_and_metrics_to_stdout(self):
        out = os.path.join(self.dir, "digest.md")
        p = subprocess.run([sys.executable, "-B", SCRIPT, self.transcript, "--out", out],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out) as f:
            self.assertIn("Ship APP-289", f.read())
        self.assertEqual(json.loads(p.stdout)["human_prompts"], 1)

    def test_without_out_markdown_goes_to_stdout(self):
        p = subprocess.run([sys.executable, "-B", SCRIPT, self.transcript],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("JULIAN:", p.stdout)
        self.assertIn("Ship APP-289", p.stdout)


if __name__ == "__main__":
    unittest.main()
