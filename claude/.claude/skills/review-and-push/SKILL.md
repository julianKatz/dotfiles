---
name: review-and-push
description: Before pushing a branch, get an independent code review from a Fable reviewer, fix what it finds with Opus-or-below fixers in rounds until it's clean, ask the user about anything ambiguous, then push and open or update the PR. Use when the user types /review-and-push, says "review and push", "review the PR then push", or asks for a Fable review pass before pushing.
argument-hint: "[branch or PR number; default: the current branch]"
---

# Review and push

The user wants a branch reviewed by a strong, independent reviewer, the clear problems fixed without
babysitting, the judgement calls brought to them, and then the branch pushed with a PR that says what
happened. Invoking this skill is their go-ahead to push **this branch** and open or update **its PR** at the
end. It is not permission for anything else: no merging, no other branches, no Linear, Slack or email.

## Hard rules

- **The reviewer is always Fable** (`model: "fable"` on the Agent call). Fable only reviews: it never edits,
  commits or pushes.
- **Fixers are always Opus or below** (`model: "opus"`, or `"sonnet"` for mechanical nits). Never Fable.
- **Work in the branch's git worktree**, never the repository's main checkout. If the branch is checked out in
  the main checkout, move it to a worktree under `.claude/worktrees/` first.
- **No paid or outward actions inside the loop:** fixers run free tests only. No live model calls, no posting
  review comments to GitHub, no Linear changes.
- **Never edit a test or scenario just to make it pass.** If a fix needs a test changed, the fixer must say why
  the old expectation was wrong according to the spec.

## Steps

### 1. Set up

- Find the branch (argument, or the current one) and its base (the PR's base if a PR exists, else `main`).
- Check that the working tree is clean and committed. If not, stop and ask.
- Run the project's free test commands once to get a baseline. If they fail before review, report that and ask.
- Find the spec or plan doc for the work (e.g. a dated doc under `spec/`) and any "Decisions" list in it.

### 2. Review (Fable)

Spawn one Agent with `model: "fable"`, `subagent_type: "general-purpose"`, read-only. Give it the code, not
your conclusions: the worktree path, `git diff <base>...HEAD`, the spec/plan doc, and what the work is for.
Ask for a ranked list of findings, each with:

- severity: **must-fix**, **should-fix** or **nit**;
- file:line, and a concrete input with the wrong outcome;
- whether it confirmed the finding by running something;
- a suggested fix;
- **ambiguous: yes/no.** Yes when the right behaviour is a product or design choice, when the spec or a
  recorded decision says otherwise, or when the reviewer isn't sure it's a bug.

It runs only free tests. The report should stay under about 600 words.

### 3. Triage (you)

Sort every must-fix and should-fix finding into:

- **Clear:** a real defect with one obvious right fix that matches the spec and the recorded decisions.
  Check it against the code yourself before treating it as real; drop findings that don't hold up, and say so.
- **Ambiguous:** anything the reviewer marked ambiguous, anything that changes behaviour the spec or a recorded
  decision sets, or anything you can't confirm. **Ask the user** in one batched question round
  (AskUserQuestion), each with your recommendation first. Don't fix these until they answer.

Nits: fix the cheap, clearly-right ones in the same round; list the rest in the PR.

### 4. Fix (Opus or below)

- One fixer Agent per group of findings that touch the same files (`model: "opus"`; `"sonnet"` is fine for
  nits). Groups with no shared files can run in parallel; overlapping ones run one after another.
- Each fixer: reproduce with a failing test first, fix in the module that owns the job, run the free tests, and
  report what changed and the real test counts. No commits from fixers.
- After the fixers, run the free tests yourself, then commit each fix (or each group) in the worktree with a
  message naming the finding.
- A user answer to an ambiguous finding is a decision: add it to the spec's decisions list (see below).

### 5. Re-review, up to 3 rounds

Send Fable the new diff since its last review (plus the full diff for context) and ask it to check the fixes
and look for anything the fixes broke. Repeat steps 3–4. Stop when a round finds no clear must-fix or
should-fix, or after 3 rounds; if must-fix items remain after 3 rounds, stop and ask the user instead of
pushing.

### 6. Push and PR

- Push the branch (`git push -u origin <branch>`).
- Open a PR against the base if none exists (draft unless the user said otherwise), or update the existing
  PR's description. The description has:
  - what the change does, in a few bullets;
  - **Decisions not in the PRD or ticket:** the full list from the spec, including answers given during this
    review (the user wants these surfaced to product for async review);
  - **Review:** reviewer Fable, the number of rounds, what was fixed, what was dropped as not real, and any
    nits or should-fix items left, with why;
  - the real test counts from the last run.
- End with the repository's PR attribution line if one is configured.

### 7. Report

Tell the user, in short bullets: the PR link, rounds run, what was fixed, what they decided, and anything left
open. Say plainly what wasn't verified (for example, live or paid evals not run).
