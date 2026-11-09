export const meta = {
  name: 'pr-retro',
  description: 'Grade how one PR was built: five lenses read the session digests, a skeptic per lens refutes weak findings, one synthesizer ranks the rest',
  whenToUse: 'Run by the pr-retro skill after find_work.py and digest.py have filled the work folder',
  phases: [
    { title: 'Read', detail: 'one reader per lens over the digests' },
    { title: 'Refute', detail: 'a skeptic per lens checks each finding against the transcript' },
    { title: 'Synthesize', detail: 'dedupe across lenses, rank, score' },
  ],
}

// args: { work: folder with pr.json, digests/*.md, manifest.json; stage: 'open'|'merge';
//         since: ISO time the earlier retro covered up to (merge stage only); previous: path to earlier .json }
const A = args || {}
const WORK = A.work
const STAGE = A.stage === 'merge' ? 'merge' : 'open'
if (!WORK) throw new Error('args.work is required')

const ROOT_CAUSES = ['missing-instruction', 'instruction-ignored', 'instruction-wrong', 'tool-gap', 'judgment', 'spec-gap', 'external']
const TARGETS = ['global-claude-md', 'aa-claude-md', 'repo-claude-md', 'memory', 'skill', 'hook', 'tooling', 'spec-process', 'none']

const FINDING = {
  type: 'object',
  properties: {
    title: { type: 'string', description: 'the lesson in under 12 words' },
    what_happened: { type: 'string', description: 'facts only, with counts; 1-3 sentences' },
    refs: { type: 'array', items: { type: 'string' }, description: 'evidence: "<session_id 8 chars>:L<line>" rows from the digests, or "pr:<thing>"' },
    cost: { type: 'string', description: 'what it cost: Julian attention, wall time, tokens, or quality risk; with a number when the evidence gives one' },
    severity: { enum: ['high', 'medium', 'low'] },
    better_way: { type: 'string', description: 'what should have happened, knowable at the time (no hindsight)' },
    root_cause: { enum: ROOT_CAUSES },
    proposed_change: {
      type: 'object',
      properties: { target: { enum: TARGETS }, text: { type: 'string', description: 'the exact rule, check or tool change; empty when target is none' } },
      required: ['target', 'text'],
    },
    actor: { enum: ['claude', 'julian', 'both'] },
  },
  required: ['title', 'what_happened', 'refs', 'cost', 'severity', 'better_way', 'root_cause', 'proposed_change', 'actor'],
}
const LENS_OUT = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: FINDING },
    went_well: { type: 'array', items: { type: 'string' }, description: 'habits worth keeping, each with a ref' },
  },
  required: ['findings', 'went_well'],
}
const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer' },
          keep: { type: 'boolean' },
          reason: { type: 'string', description: 'what the transcript showed when you checked' },
          amended: { ...FINDING, description: 'the finding corrected (cost, severity, wording); omit when unchanged' },
        },
        required: ['index', 'keep', 'reason'],
      },
    },
  },
  required: ['verdicts'],
}
const RETRO = {
  type: 'object',
  properties: {
    headline: { type: 'string', description: 'one sentence: the biggest lesson from this PR' },
    scores: {
      type: 'object',
      description: '1-5 each, 5 best; judged from the evidence, not from effort',
      properties: Object.fromEntries(['verification', 'rework', 'communication', 'orchestration', 'instructions'].map(k => [k, { type: 'integer', minimum: 1, maximum: 5 }])),
      required: ['verification', 'rework', 'communication', 'orchestration', 'instructions'],
    },
    findings: { type: 'array', items: { ...FINDING, properties: { ...FINDING.properties, category: { enum: ['verification', 'rework', 'communication', 'orchestration', 'instructions'] } }, required: [...FINDING.required, 'category'] } },
    went_well: { type: 'array', items: { type: 'string' } },
    dropped: { type: 'array', items: { type: 'string' }, description: 'findings the skeptics or you dropped, one line each with why' },
  },
  required: ['headline', 'scores', 'findings', 'went_well', 'dropped'],
}

const LENSES = [
  {
    key: 'verification',
    ask: `Verification. Was success defined before code (a failing test, an eval, a named check)? Were tests and evals run, and were results shown before anything was called done? Did a claim of "done", "passes" or "fixed" go out without evidence? What did the reviewer, CI, or a later round find that the builder should have caught? Were live or paid evals skipped, and was that said plainly?`,
  },
  {
    key: 'rework',
    ask: `Rework and waste. Dead ends, reverted or re-done edits, the same failing command run repeatedly, tool friction (sandbox refusals, permission blocks, wrong folder), fix rounds that re-opened earlier work, merge conflicts, waiting. For each, what it cost (count rows or minutes from the timestamps) and what would have avoided it.`,
  },
  {
    key: 'communication',
    ask: `Communication with Julian. Every JULIAN row that corrects, redirects, repeats an earlier instruction, or answers a question the spec or an earlier message already answered is a strong signal: find each one and the Claude turn that caused it. Also: questions Claude should have asked but guessed; decisions Claude took that were Julian's to make; reports that overstated or buried what was unverified; messages too long or unclear for his writing standard. Messages relayed by a parent session (PEER rows) count when they carry Julian's words.`,
  },
  {
    key: 'orchestration',
    ask: `Planning and orchestration. Was the work broken down well? Were subagents, workflows and sessions used where they paid off, and avoided where they did not? Model choice per role (Fable once per PR for review, Opus or lower elsewhere). Parallel work that collided (two PRs touching one file, merge order). Handoffs between sessions that lost context. Worktree and branch hygiene. Scope: work outside the ticket, or ticket work left out.`,
  },
  {
    key: 'instructions',
    ask: `Standing instructions. Read Julian's rules: ~/.claude/CLAUDE.md, ~/dev-applied-agents/CLAUDE.md, ~/dev-applied-agents/PR-WRITING.md, the repo's CLAUDE.md, and the memory files in ~/.claude/projects/-Users-juliankatz-dev-applied-agents-sellside/memory/. Find where the work broke a rule (root_cause instruction-ignored), where a rule was missing and Julian had to say it (missing-instruction), and where following a rule cost more than it saved or two rules conflicted (instruction-wrong). Quote the rule.`,
  },
]

// A merge-stage run with no earlier retro (the open one was missed) reviews everything.
const scope = STAGE === 'merge' && A.previous
  ? `This is the MERGE-stage retro. An earlier retro (${A.previous}) covered everything up to ${A.since}. Look only at rows after that time and at the PR's post-open history in pr.json (commits, review comments, checks, merge). Do not repeat the earlier retro's findings; read it first. Key question: what did review, CI and the time after opening reveal that the build should have caught?`
  : `This is the OPEN-stage retro: the work from the start up to the PR being opened, plus anything after it in the digests.`

const brief = `You are grading how a pull request was built: mostly Claude grading Claude, with Julian's part in it too. The goal is data for improving Claude's ways of working, so be specific, honest and fair.

Work folder: ${WORK}
- pr.json: the PR from GitHub (body, commits, reviews, comments, checks).
- manifest.json: the sessions; "why" is pr-link/branch for sessions that did the work, parent for a session that directed them (an orchestrator covering many PRs: read only its parts about this PR; grep the digest for the PR number, branch, ticket id and the worker's title).
- digests/<session_id>.md: one timeline per session. Each row starts "L<n> HH:MM KIND:"; L<n> is the line in the raw transcript (path in manifest.json). JULIAN rows are Julian; PEER rows are another session; SUBAGENT rows are a helper's hand-back. Read the whole digest for worker sessions.
- When a row is cut short, read the raw line: sed -n '<n>p' <transcript> | head -c 4000.

${scope}

Rules:
- Every finding cites refs as "<first 8 chars of session_id>:L<n>". No ref, no finding.
- No hindsight: "better_way" must have been knowable at the time.
- Cost in real terms with numbers when the evidence has them (rows, minutes, rounds, Julian messages). A finding that cost nothing and risked nothing is not a finding.
- Prefer a few strong findings (0-6) to many weak ones. A clean lens returns zero findings; that is a fine answer.
- proposed_change.text is the exact rule, check or tool change you would add, phrased to drop into its target.
- went_well: 0-3 habits worth keeping, each with a ref.`

phase('Read')
const reviewed = await pipeline(
  LENSES,
  lens => agent(`${brief}\n\nYour lens: ${lens.ask}`, { label: `read:${lens.key}`, phase: 'Read', schema: LENS_OUT }),
  (out, lens) => {
    if (!out || !out.findings.length) return { lens: lens.key, findings: [], went_well: out ? out.went_well : [], dropped: [] }
    const listed = out.findings.map((f, i) => `[${i}] ${JSON.stringify(f)}`).join('\n')
    return agent(`${brief}\n\nYou are the skeptic for the "${lens.key}" lens. Try to refute each finding below. For each: open the cited rows in the digest AND the raw transcript lines, and check (1) the rows show what it claims, (2) the cost is real and not overstated, (3) better_way was knowable then and is actually better, (4) the root cause fits, (5) it is not already handled by a rule Claude simply followed. Keep only what survives; amend what is right but overstated. Default to keep=false when the evidence is thin.\n\nFindings:\n${listed}`,
      { label: `refute:${lens.key}`, phase: 'Refute', schema: VERDICTS })
      .then(v => {
        const verdicts = (v && v.verdicts) || []
        const byIndex = new Map(verdicts.map(x => [x.index, x]))
        const kept = [], dropped = []
        out.findings.forEach((f, i) => {
          const verdict = byIndex.get(i)
          if (verdict && verdict.keep) kept.push({ ...(verdict.amended || f), category: lens.key })
          else dropped.push(`${lens.key}: ${f.title} (${verdict ? verdict.reason : 'skeptic gave no verdict'})`)
        })
        return { lens: lens.key, findings: kept, went_well: out.went_well, dropped }
      })
  },
)

const lensResults = reviewed.filter(Boolean)
const missing = LENSES.map(l => l.key).filter(k => !lensResults.some(r => r.lens === k))
if (missing.length) log(`No result from lens(es): ${missing.join(', ')}; the retro says so`)

phase('Synthesize')
const retro = await agent(`${brief}

You are the synthesizer. Below are the verified findings from five lenses. Merge duplicates (same event seen by two lenses: keep one, best category), rank by severity then cost, score each category 1-5 from the evidence, and write a one-sentence headline: the single most useful lesson. Do not add findings of your own and do not drop verified ones except as duplicates; list merges and the skeptics' drops under "dropped".${missing.length ? ` Lenses with no result: ${missing.join(', ')}; score them from what you can see and say so in dropped.` : ''}

${JSON.stringify(lensResults, null, 1)}`, { label: 'synthesize', phase: 'Synthesize', schema: RETRO })

return { stage: STAGE, missing_lenses: missing, retro, lenses: lensResults }
