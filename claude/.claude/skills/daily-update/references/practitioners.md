# Agentic engineering: what the best practitioners say

Reference for the evening coach: compare Julian's day of Claude Code threads against current practice, then suggest changes. Researched 2026-11-05; refresh by searching for newer posts from these people.

How to use: each theme gives the idea, practices with sources, and signals. "Doing it" = Julian already works this way; "missing it" = candidate suggestion. Signals come from transcripts, prompts and the turn log; "(git/GitHub)" marks ones needing that data. "bg" = background: predates skills/plugins (before ~2025-10); principle may hold, mechanics may be dated. Where sources disagree, the theme says so; never present one view as settled. Settings and hook signals describe what to observe, not cues to edit config.

---

## Themes

### 1. Verification: a check the agent can run, and evidence it ran

"Done" is a claim. Results improve most when the agent has a pass/fail check it runs itself and shows command plus output.

- Falsifiable done condition per task (tests, typecheck, screenshot); ask for the command and its output. Escalate: prompt, /goal, Stop hook, fresh-context reviewer. [Claude Code docs, accessed 2026-11-05](https://code.claude.com/docs/en/best-practices)
- State declarative success criteria, not step lists: tests first, browser loop, naive-correct before optimized. [Karpathy, 2026-01](https://x.com/karpathy/status/2015883857489522876) A feedback loop (e.g. browser check) is his top tip; he claims 2-3x quality. [Cherny, 2026-01](https://x.com/bcherny/status/2007179832300581177)
- User-facing flows: agents declared done early until made to test through browser automation. [Anthropic Engineering, 2025-11](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Verifier must be near-perfect or agents solve the wrong problem; add a fast sampled test mode, since Claude is time-blind. [Carlini, 2026-02](https://www.anthropic.com/research/building-c-compiler)
- Demand irrefutable proof (end-to-end demo, video, before/after numbers); write in AGENTS.md that unsupported claims are not evidence. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082)
- Big builds: trust came from an outside oracle (conformance suite, differential fuzzing), not agent-written tests. [Willison, 2026-10](https://simonwillison.net/2026/Oct/16/sqlite-sparql-rust/)
- Red/green TDD; run the suite first for a baseline. [Willison, 2026-02](https://simonwillison.net/guides/agentic-engineering-patterns/) Experts gate on passing CI; occasional contributors merge unchecked. [Cynthia, Das, Roy, 2026-01](https://arxiv.org/abs/2601.20106)

**Signals in a day's threads.** Doing it: kickoff prompts state a measurable target and stop condition; completion messages carry command output, screenshots or numbers; failing test shown before the fix; browser or live checks on user-facing flows. Missing it: bare "done"/"tests pass" accepted; prompts script steps instead of naming a check; unit tests only on email or scheduling flows; no fast test subset named for agents.

### 2. Harness engineering: turn repeated corrections into mechanical checks

Most agent failures are harness problems, not model problems. Prose rules drift; zero-exception rules belong in hooks, lint or CI. Add config only after a real failure; remove what doesn't help.

- Zero-exception rules go in hooks or deny rules, not louder CLAUDE.md wording; keep the enforced set small. [Claude Code docs, accessed 2026-11-05](https://code.claude.com/docs/en/best-practices)
- Pre-commit hook rejects a forbidden pattern and tells the agent the right one; he reports ten-of-ten compliance vs. drifting AGENTS.md lines. Single anecdote. [Huntley, 2026-10](https://ghuntley.com/agency/)
- Hand-write a short CLAUDE.md (his: under 60 lines) of universal rules; disable unused MCP servers, whose tool descriptions eat context; hooks silent on success, loud on error. [Kyle (HumanLayer), 2026-03](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)
- Every agent mistake gets a permanent fix (AGENTS.md line or tool); build tools so the agent can check itself. [Hashimoto, 2026-02](https://mitchellh.com/writing/my-ai-adoption-journey) Team CLAUDE.md in git, extended whenever Claude errs; PostToolUse formatter hook. [Cherny, 2026-01](https://x.com/bcherny/status/2007179832300581177)
- Test whether AGENTS.md or skills change behavior: fresh agents with vs. without. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082)
- Write architecture rules where agents read them; agents break core constraints to fit a pattern. [Anthropic source control team, 2026-10](https://www.anthropic.com/engineering/redesigning-source-control)
- bg: 45% of merged Claude Code PRs still needed human edits, mostly for unstated conventions. [Watanabe et al., 2025-09](https://arxiv.org/abs/2509.14745)

**Signals in a day's threads.** Doing it: hook, lint or CI check added after a repeated miss; hook failure messages name the correct pattern; CLAUDE.md edited right after an observed mistake; settings show Stop or PostToolUse hooks (observe only). Missing it: same correction typed in 2+ threads; ALWAYS/NEVER/IMPORTANT rules agents still miss; CLAUDE.md or memory growing with situational rules; many MCP servers connected but unused; full test/build output pasted on success.

### 3. Context: small, fresh, written down

Quality drops as context grows. Keep each agent's context short, save state in files, compact on purpose.

- Research, plan, implement: map the code, write exact steps with a test per phase, implement one phase at a time. Distill progress to a file or commits and restart fresh; keep utilization ~40-60%. Wrong context is worst, then missing, then noise. [Horthy, 2025-08](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md)
- 1M context hurt: design docs ignored, instructions disobeyed. Instruction budget scales with model, not window; prefer isolation (subagents) to expansion; warn near ~100k tokens. [Kyle (HumanLayer), 2026-03](https://www.humanlayer.dev/blog/long-context-isnt-the-answer)
- Smallest set of high-signal tokens; notes re-read after reset; subagents return ~1-2k-token summaries; add instructions only for seen failures. [Anthropic Engineering, 2025-09](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- CLAUDE.md under ~200 lines; /clear between unrelated tasks; after two failed corrections, /clear and write one better prompt. [Claude Code docs, accessed 2026-11-05](https://code.claude.com/docs/en/best-practices)
- Sessions start from a progress file and git log, then a basic end-to-end test. [Anthropic Engineering, 2025-11](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) Harness prints a few lines; details to logs. [Carlini, 2026-02](https://www.anthropic.com/research/building-c-compiler)
- Disagreement. Ball: one thread per task, let compaction manage context. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082) Horthy and Kyle favor deliberate handoffs. bg: a focused 300-token prompt beat 113k of history. [Chroma, 2025-07](https://www.trychroma.com/research/context-rot)

**Signals in a day's threads.** Doing it: fresh threads seeded from a plan or handoff file; progress file updated between phases; short subagent returns with file:line citations; memory or CLAUDE.md pruned. Missing it: repeated auto-compactions in one thread; agent ignoring CLAUDE.md or plan late in a long thread; 3+ corrections in a row on one point; test output flooding the transcript; cold starts rediscovering state; overlapping memory entries.

### 4. Specs and plans, sized to the task

A written done-definition sharpens build and review. Heavy spec process on small changes is overhead.

- Unclear work: Claude interviews you into SPEC.md; build fresh against it; point the reviewer at the same spec. [Claude Code docs, accessed 2026-11-05](https://code.claude.com/docs/en/best-practices)
- Review research and plans first: one bad plan line yields far more bad code than one bad code line. [Horthy, 2025-08](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md)
- Agree each task's done definition and check before coding; keep the planner, since builders under-scope. [Rajasekaran, 2026-03](https://www.anthropic.com/research/harness-design-long-running-apps)
- Start in plan mode, iterate the plan, then auto-accept edits. [Cherny, 2026-01](https://x.com/bcherny/status/2007179832300581177) Vague work: plan in one session, execute in another. [Hashimoto, 2026-02](https://mitchellh.com/writing/my-ai-adoption-journey)
- bg: hone the idea one question at a time into spec.md; small test-driven steps in a plan plus todo.md carrying state; tests after each step. [Reed, 2025-02](https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/)
- Kick off by assessing state and proposing; Opus 5.5 ran far from one broad prompt. [Willison, 2026-10](https://simonwillison.net/2026/Oct/1/pwasm/)
- Disagreement. Spec tooling is overkill for small fixes (one bug became 4 stories, 16 criteria); specs can be more tedious to review than code. [Böckeler, 2025-10](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) bg: Steinberger rejects rigid spec-driven work but has a second model critique tricky specs. [Steinberger, 2025-10](https://steipete.me/posts/just-talk-to-it)

**Signals in a day's threads.** Doing it: plan or spec edited or challenged by Julian before builders start; sessions open in plan mode; build starts fresh from the spec; spec weight matches change size. Missing it: speckit or plan-doc ceremony on a one-line fix; long plan approved unedited within seconds (turn-log timestamps); one session plans and builds a fuzzy feature; several plan steps run with no tests between; goals clarified over many turns.

### 5. Review: by risk, capped, correctness-first, willing to say no

A reviewer asked for problems always finds some. Tier by risk, cap rounds, filter noise, keep a human on intent.

- Tier by the change: docs and flagged additive changes need no human once checks pass; core and sensitive paths get more. Cap ~3 rounds, then rethink; later rounds re-review only the diff and never repeat a finding; tag Important/Nit/Pre-existing; REVIEW.md requires file:line evidence. [Osmani, Lunt, Wang, 2026-10](https://claude.dev/blog/solving-code-review-at-anthropic)
- Same team's data: ~59% of later-round findings were already in pass one; one PR ran 50+ rounds overnight. Name the bug class so every instance gets fixed; after three rounds escalate. Reviews-to-pass fell 2.08 to 1.32. [RAZ Team, 2026-10](https://www.realaization.com/blog/four-rules-that-make-an-ai-review-loop-converge)
- Counter on caps: a shorter loop may just shift cost to missed bugs (unmeasured); high-risk changes may merit more rounds. [RAZ Team, 2026-10](https://www.realaization.com/blog/four-rules-that-make-an-ai-review-loop-converge)
- Reviewer reports correctness gaps against the spec and skips style; fixing every finding adds needless abstraction. [Claude Code docs, accessed 2026-11-05](https://code.claude.com/docs/en/best-practices) Adversarial review goes myopic; engineers rejected over-engineering for hypothetical threats. [Anthropic source control team, 2026-10](https://www.anthropic.com/engineering/redesigning-source-control)
- Untuned Claude QA finds real issues then talks itself into approving; tune it by reading its logs. [Rajasekaran, 2026-03](https://www.anthropic.com/research/harness-design-long-running-apps) AI review is a sensor, not a verdict; watch for weakened tests. [Osmani, 2026-06](https://addyosmani.com/blog/agentic-code-review/)
- Self-review first, small PRs, read the agent's PR description before posting. [Willison, 2026-02](https://simonwillison.net/guides/agentic-engineering-patterns/anti-patterns/) Review only high-blast-radius code. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082)
- Counter-voice: line-by-line review can't keep up with AI volume; put humans on specs and acceptance criteria, plus deterministic checks, adversarial agents, narrow permissions, fast rollback. Author sells verification tooling. [Jain, 2026-03](https://www.latent.space/p/reviews-dead)

**Signals in a day's threads.** Doing it: review depth differs by risk; rounds stop near 3 or the approach changes; findings triaged, some declined with a reason; fixes target the bug class; reviewer prompt says correctness only. Missing it: same multi-round review on docs and core logic; 4+ rounds with growing diffs; findings re-raised after being fixed; every finding becomes a fixer task; review never touches the running app; PRs lack Risk/Revert sections (git/GitHub).

### 6. Independent review: what a second model buys

Julian's setup: Fable reviews, Opus builds. Evidence: fresh context matters most; model diversity helps somewhat; no LLM reviewer is fully independent.

- 900 sessions, 150 planted errors: a strong cross-model reviewer matched the same model in a fresh session. Findings overlapped only 41%; one same-model plus one cross-model pass caught 56.7% vs. 42.7% for two same-model passes, but confounded with reviewer strength; a lightweight cross-model reviewer was no better. Single-author preprint; suggestive. [Song, 2026-10](https://arxiv.org/abs/2610.01471)
- When two models are both wrong they pick the same wrong answer ~60% of the time; larger, more accurate models correlate even across vendors, so correlated judges confirm each other's mistakes. [Kim et al., 2025-06](https://arxiv.org/abs/2506.07962)
- AI review of AI code shares the builder's blind spots; tests the builder writes after reading its code just move the problem, so derive checks from the spec. [Jain, 2026-03](https://www.latent.space/p/reviews-dead)
- Model choice. Ball: strongest model everywhere; a sometimes-wrong cheap one costs more in rechecks. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082) Kyle: cheaper model for research, expensive for planning and orchestration. [Kyle (HumanLayer), 2026-03](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)

**Signals in a day's threads.** Doing it: reviewer starts in fresh context with spec plus diff, not the builder's transcript; review passes vary in configuration; a deterministic check (tests, live run) backs each "clean" verdict; test author kept from the implementation. Missing it: reviewer handed the builder's full context; two identical review passes; "clean" review with no test or live run; builder and reviewer agree on behavior the spec contradicts; top model on every pass regardless of diff size.

### 7. Agent security and permissions

Julian's agents read customer email while holding CRM and calendar data. Prompt injection is unsolved; design around it.

- bg: lethal trifecta: private data + untrusted content + an outbound channel lets hidden text steal data. No reliable fix; 95% detection is a failing grade; remove one leg. [Willison, 2025-06](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)
- Meta's Rule of Two: per session at most two of untrusted input, sensitive data, state change/outbound; all three needs human supervision. Gap: untrusted input plus state change alone can harm. Adaptive attacks beat 12 published defenses, mostly above 90%. [Willison, 2025-11](https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/)
- Whoever puts text in context steers the next tool call; sandboxing is the only credible defense; network egress limits matter most. [Willison, 2025-10](https://simonwillison.net/2025/Oct/22/living-dangerously-with-claude/)
- Frequent prompts breed unread approvals; OS sandbox cut prompts 84%; filesystem and network isolation are both required. [Dworken, Weller-Davies, 2025-10](https://www.anthropic.com/engineering/claude-code-sandboxing)
- Pre-allow safe commands via /permissions in shared settings, not skip-permissions (except in sandboxes). [Cherny, 2026-01](https://x.com/bcherny/status/2007179832300581177) Skip-permissions only where untrusted input can't reach context. [Willison, 2025-10](https://simonwillison.net/2025/Oct/5/parallel-coding-agents/)

**Signals in a day's threads.** Doing it: human approval gate on irreversible outbound actions (send, book, CRM write); sandbox or narrow allowlist; secrets outside the working tree. Missing it: skip-permissions or bypass mode outside a sandbox, worst on threads reading customer email; broad allow rules (Bash(*), WebFetch(*)) in settings.local.json; many connectors (Gmail, Notion, Linear, Drive) plus web browsing in one session; an injection classifier cited as the safety argument; long runs of routine permission prompts.

### 8. Parallelism and attention: the human is the bottleneck

Starting agents is cheap; review isn't. Throughput equals the rate Julian can review and understand.

- Throughput = review throughput; batch review. [Osmani, 2026-05](https://addyosmani.com/blog/orchestration-tax/) Ceiling ~3-4 threads, each reviewable in ~30 min. [Osmani, 2026-04](https://addyosmani.com/blog/cognitive-parallel-agents/) Worktrees remove collisions, not the review ceiling. [Osmani, 2026-06](https://addyosmani.com/blog/loop-engineering/)
- Can properly review one significant change at a time; fill extra slots with research, explanation, fully specified low-stakes work. [Willison, 2025-10](https://simonwillison.net/2025/Oct/5/parallel-coding-agents/)
- Review stays human because humans are accountable; throttle inflow to review capacity; unreviewed work piles up as stale PRs. [Ronacher, 2026-02](https://lucumr.pocoo.org/2026/2/13/the-final-bottleneck/)
- Notifications off, check in at natural breaks; one background agent by day; research and triage agents in the last 30 minutes. [Hashimoto, 2026-02](https://mitchellh.com/writing/my-ai-adoption-journey)
- Let agents wait on you, not the reverse: bigger tasks, batched input, scheduled check-ins. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082)
- Heavy adoption: review time up, larger PRs, more merged unreviewed; vendor data. [Faros AI, 2025-10](https://www.faros.ai/blog/bain-technology-report-2025-why-ai-gains-are-stalling) Many sessions at odd hours: step away. [Ronacher, 2026-01](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/)
- Disagreement. Cherny runs ~5 local plus 5-10 web sessions with notifications on. [Cherny, 2026-01](https://x.com/bcherny/status/2007179832300581177) bg: Steinberger runs 3-8 agents in one checkout. [Steinberger, 2025-10](https://steipete.me/posts/just-talk-to-it) Hashimoto, Osmani, Willison argue for fewer.

**Signals in a day's threads.** Doing it: few threads waiting on input at once; turns carrying several batched instructions; research and build threads kept separate; late-day report-only runs. Missing it: many threads opened, few merged (git/GitHub); new threads started while earlier PRs await review; "where are we" or tldr requests; long idle waits on Julian; threads abandoned mid-plan; late-night bursts (turn-log timestamps); several concurrent threads each producing large diffs.

### 9. Delegation and cost: what subagents and roles are worth

Subagents buy parallelism or fresh eyes, not smarter answers, and multiply tokens. Each role encodes an assumption about model weakness; test whether it still earns its place.

- bg: multi-agent used ~15x chat tokens; coding parallelizes less than research; briefs need objective, format, tools, boundaries. [Anthropic Engineering, 2025-06](https://www.anthropic.com/engineering/multi-agent-research-system)
- Full harness cost >20x solo (~$200 vs. $9), winning only beyond solo reach; remove components as models improve. [Rajasekaran, 2026-03](https://www.anthropic.com/research/harness-design-long-running-apps)
- Cost grows quadratically: cache reads dominate long threads (87% of a ~$13 session). Fresh session per task; iterate in subagents; return big outputs whole, not via many re-reads. [Zeyliger, 2026-02](https://blog.exe.dev/expensively-quadratic)
- Subagents mainly protect the parent's context: search in a fresh window, return a compressed result. [Horthy, 2025-08](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md) Haiku for simple jobs. [Claude Code docs, accessed 2026-11-05](https://code.claude.com/docs/en/best-practices)
- bg: one task per subagent, reviewed before the next. [Vincent, 2025-10](https://blog.fsck.com/2025/10/09/superpowers/) bg: read-only parallel work is fine; mixed writers cause chaos. [Ronacher, 2025-07](https://lucumr.pocoo.org/2025/7/30/things-that-didnt-work/) Own ports and database per parallel agent. [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082)
- Disagreement. bg: Steinberger doubts persona subagents. [Steinberger, 2025-10](https://steipete.me/posts/just-talk-to-it) Anthropic found planner and evaluator roles earn their cost on hard tasks. Julian's full roster is a hypothesis to test per task size.

**Signals in a day's threads.** Doing it: roster scaled to task; model varies by role; briefs state format and boundaries; a role dropped as an experiment; fresh thread per task. Missing it: full team on small changes; duplicate findings from reviewer and failure analyst; parallel writers on shared files; one long thread reused across unrelated tasks; many small reads where one would do; iteration loops in the main thread; a model downgrade followed by retries.

### 10. Stay the engineer: comprehension, judgment, trust

Pure delegation erodes the skills needed to supervise agents. The human owns tradeoffs and must be able to explain what merged.

- Anthropic RCT (52 engineers): AI group 50% vs. 67% on comprehension, worst on debugging; asking for explanations scored 65%+. [Shen, Tamkin, 2026-01](https://www.anthropic.com/research/AI-assistance-coding-skills)
- Top agent failure: silent wrong assumptions, rarely flagging uncertainty or tradeoffs; also overcomplication, dead code, unrelated edits. Review skill can hold while writing skill fades. [Karpathy, 2026-01](https://x.com/karpathy/status/2015883857489522876)
- Jagged ability: strong where verifiable, weak elsewhere; set autonomy per task, not from one success. [Karpathy, 2025-12](https://karpathy.bearblog.dev/year-in-review-2025/)
- Code piles up faster than trust; XP practices manufacture it; slow down to confirm it works, and talk to people more. [Beck, 2026-06](https://newsletter.kentbeck.com/p/trust-factory) bg: stop loops, unrequested features, deleted tests; separate structural from behavior commits. [Beck, 2025-06](https://newsletter.kentbeck.com/p/augmented-coding-beyond-the-vibes)
- Own the outer loop: ship, block, redirect, reject, explain why safe. [Osmani, 2026-07](https://addyosmani.com/blog/own-the-outer-loop/) Make tradeoffs yourself; ask if you'll maintain it. [Ronacher, 2026-01](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/)
- Walkthroughs before merge. [Willison, 2026-02](https://simonwillison.net/guides/agentic-engineering-patterns/) Keep some tasks by hand. [Hashimoto, 2026-02](https://mitchellh.com/writing/my-ai-adoption-journey) Agent prose for people mostly no [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082); tension with agent-drafted PRs; middle path: read and edit before posting.

**Signals in a day's threads.** Doing it: "why this approach?" or "explain" prompts; walkthrough requested before merge; Julian rejects or narrows proposals; agent stops to ask at an ambiguity. Missing it: "fix it"/"keep going" relaying a failure with no added diagnosis; agent proceeds past an ambiguity unasked; diffs with unrequested abstractions, unrelated edits, weakened or deleted tests; structural and behavior changes in one commit (git); PR Decisions text identical to the agent's draft (git/GitHub).

### 11. Evals and regressions for product agents

Julian ships LLM agents to customers. One good demo run isn't evidence; real failures should grow a regression set.

- Error analysis decides which evals to write: read representative traces, note each in free text, cluster into a counted failure taxonomy, repeat to saturation. Read ~30 yourself before letting AI propose categories. [Husain, Shankar, 2026-09](https://hamel.dev/blog/posts/evals-faq/)
- Binary pass/fail over 1-5 scales; one judge per failure mode, validated against human labels (TPR/TNR, held-out set); a viewer showing real outcomes (the email sent, the booking made). [Husain, Shankar, 2026-09](https://hamel.dev/blog/posts/evals-faq/)
- Start with 20-50 tasks from real failures; unambiguous pass/fail; balance should and should-not cases; pass^k for customer-facing agents; read transcripts, not just scores. [Grace et al., 2026-01](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
- Past bug-causing PRs as an eval set run daily. [Osmani, Lunt, Wang, 2026-10](https://claude.dev/blog/solving-code-review-at-anthropic) New features break old ones; keep regression checks. [Carlini, 2026-02](https://www.anthropic.com/research/building-c-compiler)
- Disagreement on order. Grace et al.: write evals before the capability exists. Husain and Shankar: real traces first; spec-only evals miss production failures.

**Signals in a day's threads.** Doing it: demo or live failures turned into eval cases; Julian reads real sent emails or traces and notes failures; repeated trials on customer-facing behavior; binary graders. Missing it: eval scenarios only from the spec, never from real traces; "N of M live runs passed" as a one-off; LLM judge with no measured agreement with Julian; Likert grading prompts; agent asked for failure categories before Julian read traces; same bug class found twice.

### 12. Measure yourself honestly, record shortfalls

Felt speed misleads. Judge the process by measured outcomes; report agent failures as findings.

- bg: experienced devs were 19% slower with AI yet felt ~20% faster. [METR, 2025-07](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) Follow-up leaned to speedup on weak evidence; parallel agents blur time per task. [METR, 2026-02](https://metr.org/blog/2026-02-24-uplift-update/)
- Self-reported speed ~3x, value 1.4-2x; cheap AI work may pull toward lower-value tasks. [METR, 2026-05](https://metr.org/blog/2026-05-11-ai-usage-survey/)
- AI amplifies the existing system: throughput up, stability down; small batches and fast feedback decide who gains. [DORA, 2025-09](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)
- Track guardrails: least human time without more reverts. [Osmani, Lunt, Wang, 2026-10](https://claude.dev/blog/solving-code-review-at-anthropic) Where AI doesn't help, write down why and raise it with your manager (one secondhand source). [Terkowitz via Willison, 2026-10](https://simonwillison.net/2026/Oct/28/terk-terkowitz/)

**Signals in a day's threads.** Doing it: daily update has numbers (threads, review rounds; PRs merged, reverts, branch-to-merge time from git/GitHub); agent failures noted with causes. Missing it: "productive day" with no numbers; only wins reported; tooling or polish threads outnumber customer-goal threads (by thread prompts); follow-up fix PRs after merges never counted (git/GitHub).

### 13. Reuse and automate the inner loop, but prune

Solve a technique once, keep a working example, point agents at it. Automate only what recurs; delete what nobody uses.

- Hoard solved problems with working code; prompt "do it like X". [Willison, 2026](https://simonwillison.net/guides/agentic-engineering-patterns/hoard-things-you-know-how-to-do/)
- Routine loops as slash commands (/commit-push-pr many times a day); subagents for simplification and end-to-end checks. [Cherny, 2026-01](https://x.com/bcherny/status/2007179832300581177)
- Routines and scheduled agents; overnight "dreaming" review of past sessions writes memories. [Willison live blog, 2026-05](https://simonwillison.net/2026/May/6/code-w-claude-2026/) Heartbeats: "check logs in 2 hours". [Ball, 2026-10](https://x.com/thorstenball/status/2114386050638336082)
- bg: pressure-test skills on realistic scenarios first; mine memory files to consolidate. [Vincent, 2025-10](https://blog.fsck.com/2025/10/09/superpowers/) bg: ~20% of time on agent refactoring. [Steinberger, 2025-10](https://steipete.me/posts/just-talk-to-it)
- Disagreement. Huntley deletes skill packs and revisits what used to be hard. [Huntley, 2026-10](https://ghuntley.com/agency/) bg: Ronacher dropped most slash commands; rigid steps belong in plain scripts. [Ronacher, 2025-07](https://lucumr.pocoo.org/2025/7/30/things-that-didnt-work/)

**Signals in a day's threads.** Doing it: prompts citing a prior working example; skills invoked often; scheduled checks after deploys. Missing it: same multi-step request typed repeatedly; same solution reworked in several threads; skills never invoked; CI or merge conflicts driven turn by turn in a thread.

---

## Sources

| Person | Why credible | Title | Date |
|---|---|---|---|
| Anthropic | Official docs for Julian's tool | [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) | accessed 2026-11-05 |
| Prithvi Rajasekaran, Anthropic Labs | Multi-agent harness with cost data | [Harness design for long-running application development](https://www.anthropic.com/research/harness-design-long-running-apps) | 2026-03-24 |
| Nicholas Carlini, Anthropic | Many parallel Claudes, big codebase | [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/research/building-c-compiler) | 2026-02-05 |
| Grace, Hadfield, Olivares, De Jonghe, Anthropic | Practical agent-eval guide | [Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 2026-01-09 |
| Anthropic Engineering | Canonical multi-session pattern | [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 2025-11-26 |
| Anthropic Applied AI | Foundational context framing | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 2025-09-29 |
| Anthropic Engineering | When multi-agent pays off (bg) | [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | 2025-06-13 |
| Dworken, Weller-Davies, Anthropic | Claude Code sandbox design | [Beyond permission prompts](https://www.anthropic.com/engineering/claude-code-sandboxing) | 2025-10-20 |
| Nick G. and source control team, Anthropic | Review at 30k+ merges/day | [Redesigning source control at Anthropic](https://www.anthropic.com/engineering/redesigning-source-control) | 2026-10-13 |
| Osmani, Lunt, Wang, Claude Code team | Measured review results; claude.dev domain unverified | [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic) | 2026-10-15 |
| RAZ Team, RealAIzation | Reports same team's data; adds caveats | [Four rules that make an AI review loop converge](https://www.realaization.com/blog/four-rules-that-make-an-ai-review-loop-converge) | 2026-10-23 |
| Shen, Tamkin, Anthropic | RCT on skill formation | [How AI assistance impacts the formation of coding skills](https://www.anthropic.com/research/AI-assistance-coding-skills) | 2026-01-29 |
| Boris Cherny | Creator of Claude Code | [Setup thread (X)](https://x.com/bcherny/status/2007179832300581177) | 2026-01-02 |
| Simon Willison (Cherny, Wu, Na Penn) | Conference notes; secondhand | [Code w/ Claude 2026 live blog](https://simonwillison.net/2026/May/6/code-w-claude-2026/) | 2026-05-06 |
| Dex Horthy, HumanLayer | 12-factor agents author; research-plan-implement | [Advanced Context Engineering for Coding Agents](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md) | 2025-08-29 |
| Kyle, HumanLayer | Harness practice; 1M-context trial | [Skill Issue: Harness Engineering](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) (2026-03-12); [Long-Context Isn't the Answer](https://www.humanlayer.dev/blog/long-context-isnt-the-answer) (2026-03-23) | 2026-03 |
| Mitchell Hashimoto | HashiCorp co-founder; Ghostty | [My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey) | 2026-02-05 |
| Thorsten Ball | Amp co-creator (X blocked fetch; read via mirror) | [How I work with Agents (X)](https://x.com/thorstenball/status/2114386050638336082) | 2026-10-25 |
| Geoffrey Huntley | "Ralph" agent loop author; hook detail via Willison | [nobody should type code by hand anymore](https://ghuntley.com/agency/) | 2026-10-13 |
| Andrej Karpathy | Coined "vibe coding" | [LLM coding notes (X)](https://x.com/karpathy/status/2015883857489522876) (2026-01-26); [2025 LLM Year in Review](https://karpathy.bearblog.dev/year-in-review-2025/) (2025-12-19) | 2025-12, 2026-01 |
| Kent Beck | Creator of XP and TDD | [Trust Factory](https://newsletter.kentbeck.com/p/trust-factory) (2026-06-02); [Augmented Coding: Beyond the Vibes](https://newsletter.kentbeck.com/p/augmented-coding-beyond-the-vibes) (2025-06-25, bg) | 2025-06, 2026-06 |
| Harper Reed | Widely copied spec-plan-codegen workflow (bg) | [My LLM codegen workflow atm](https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/) | 2025-02-16 |
| Hamel Husain, Shreya Shankar | Leading evals teachers; non-Anthropic | [AI Evals FAQ](https://hamel.dev/blog/posts/evals-faq/) | 2026-09-18 |
| Addy Osmani | Google engineering lead | [Loop Engineering](https://addyosmani.com/blog/loop-engineering/) (2026-06-07); [The Orchestration Tax](https://addyosmani.com/blog/orchestration-tax/) (2026-05-24); [Your parallel Agent limit](https://addyosmani.com/blog/cognitive-parallel-agents/) (2026-04-07); [Agentic Code Review](https://addyosmani.com/blog/agentic-code-review/) (2026-06-15); [Own the Outer Loop](https://addyosmani.com/blog/own-the-outer-loop/) (2026-07-15) | 2026-04 to 07 |
| Simon Willison | Django co-creator; top agent-practice writer | [Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/), incl. [Anti-patterns](https://simonwillison.net/guides/agentic-engineering-patterns/anti-patterns/) and [Hoard things you know how to do](https://simonwillison.net/guides/agentic-engineering-patterns/hoard-things-you-know-how-to-do/) | 2026-02-23 |
| Simon Willison | Same; 12-hour agent build | [sparqlite](https://simonwillison.net/2026/Oct/16/sqlite-sparql-rust/) | 2026-10-16 |
| Simon Willison | Same; one Opus 5.5 session | [pwasm 0.2a0](https://simonwillison.net/2026/Oct/1/pwasm/) | 2026-10-01 |
| Simon Willison | Coined "prompt injection" (bg) | [The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) | 2025-06-16 |
| Simon Willison | Same | [Living dangerously with Claude](https://simonwillison.net/2025/Oct/22/living-dangerously-with-claude/) | 2025-10-22 |
| Simon Willison | Same; summarizes Meta and 14-author papers | [Agents Rule of Two and The Attacker Moves Second](https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/) | 2025-11-02 |
| Simon Willison | Same | [Embracing the parallel coding agent lifestyle](https://simonwillison.net/2025/Oct/5/parallel-coding-agents/) | 2025-10-05 |
| Terk Terkowitz via Willison | Amazon guidance; secondhand | [Role of the developer in the age of AI](https://simonwillison.net/2026/Oct/28/terk-terkowitz/) | 2026-10-28 |
| Armin Ronacher | Flask creator; critical heavy user | [The Final Bottleneck](https://lucumr.pocoo.org/2026/2/13/the-final-bottleneck/) (2026-02-13); [Agent Psychosis](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/) (2026-01-18); [Agentic Coding Things That Didn't Work](https://lucumr.pocoo.org/2025/7/30/things-that-didnt-work/) (2025-07-30, bg) | 2025-07 to 2026-02 |
| Peter Steinberger | PSPDFKit founder; 3-8 parallel agents (bg) | [Just Talk To It](https://steipete.me/posts/just-talk-to-it) | 2025-10 |
| Jesse Vincent | Superpowers skills author (bg) | [Superpowers](https://blog.fsck.com/2025/10/09/superpowers/) | 2025-10-09 |
| Philip Zeyliger, exe.dev | Agent cost analysis with session data | [Expensively Quadratic](https://blog.exe.dev/expensively-quadratic) | 2026-02-03 |
| Ankit Jain, Aviator (Latent Space guest) | Counter-voice; sells verification tooling | [How to Kill the Code Review](https://www.latent.space/p/reviews-dead) | 2026-03-02 |
| Tae-Eun Song | Only study of cross-model review; preprint | [When Does a Second Model Help?](https://arxiv.org/abs/2610.01471) | 2026-10-01 |
| Kim, Garg, Peng, Garg | ICML 2025; 350+ models | [Correlated Errors in Large Language Models](https://arxiv.org/abs/2506.07962) | 2025-06-09 |
| METR | Only rigorous RCTs on experienced devs | [Early-2025 AI on OS dev productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) (2025-07-10, bg); [Changing our experiment design](https://metr.org/blog/2026-02-24-uplift-update/) (2026-02-24); [Self-reported impact of early-2026 AI](https://metr.org/blog/2026-05-11-ai-usage-survey/) (2026-05-11) | 2025-07 to 2026-05 |
| Google Cloud DORA | ~5,000-person delivery research | [Announcing the 2025 DORA Report](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report) | 2025-09-23 |
| Faros AI | Telemetry from ~22k devs; vendor | [Bain Technology Report 2025](https://www.faros.ai/blog/bain-technology-report-2025-why-ai-gains-are-stalling) | 2025-10-03 |
| Cynthia, Das, Roy (Saskatchewan) | 9,427 agent PRs | [Are We All Using Agents the Same Way?](https://arxiv.org/abs/2601.20106) | 2026-01-27 |
| Watanabe, Hassan et al. | 567 Claude Code PRs (bg) | [On the Use of Agentic Coding](https://arxiv.org/abs/2509.14745) | 2025-09-18 |
| Chroma | 18-model context benchmark (bg) | [Context Rot](https://www.trychroma.com/research/context-rot) | 2025-07-14 |
| Birgitta Böckeler, Thoughtworks | Hands-on look at spec-driven tools | [Understanding Spec-Driven-Development](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) | 2025-10-15 |
| Rachel Laycock, Thoughtworks CTO | Week-long agents-write-everything trial | [Why are good developers so wary of agentic development?](https://martinfowler.com/rachels-ramblings/good-devs-wary.html) | 2026-10-29 |
