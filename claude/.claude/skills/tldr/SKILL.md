---
name: tldr
description: Boil the recent work down to a one-screen recap in three labeled parts (Goal, Found, Next) so the user can take it in at a glance instead of reading a wall of text. Use when the user types /tldr, asks for a TL;DR, "where are we", "catch me up", "what did you find", "bottom line", or says a reply was too long to follow, and whenever a Stop hook asks for a tldr after a long turn.
argument-hint: "[scope, e.g. 'whole session']"
---

# TL;DR

The user often comes back to a thread after Claude has worked for a while and
finds a long wall of text. The recap is what they read instead: one quick
top-to-bottom pass on a laptop screen, with room to spare. They'll ask
follow-up questions for detail, so leave detail out.

## Scope

Recap the work since the user's last real request (a Stop hook's request
doesn't count as one). If the user passed an argument such as "whole session",
use that scope instead.

## Format

Use these three bold labels, in this order, each followed by 1–3 bullets:

**Goal**
- What you understood you needed to do, and what you dug into to do it.

**Found**
- What turned up. Put the one thing the user most needs to know first, the
  bullet you'd keep if you could keep only one.

**Next**
- What should happen now, who does it (the user or you), and why, in a short
  "so…" or "because…" clause. If the user needs to decide or do something,
  make that the first bullet. If it isn't settled who does a step, say it's
  open rather than assigning it; don't promise work nobody agreed to.

Each bullet is one sentence of about 20 words or fewer, with no sub-bullets.
The whole recap stays under 150 words and 9 bullets. These limits are the point:
the user is scanning, and a bullet that runs to three sentences turns the recap
back into the wall of text it replaces. When something doesn't fit, cut it; the
user can ask. Nothing before the first label and nothing after the last bullet:
no title, no preamble, no "let me know if…".

## Writing it

- Plain words. Keep the number or name that carries a finding ("4 s → 0.3 s",
  "12 of 84 tests fail"); drop incidental ones like commit hashes, how many
  tests passed, file names and commands unless the user needs them to act.
  Link a file as `path:line` when they do.
- Say what you actually verified. Mark claims you didn't check as unverified,
  and say plainly if something failed or was skipped. A confident-sounding
  guess in a recap is worse than none, because the user may act on it without
  reading further.
- Lead each bullet with the point, not the backstory.
- Don't start new work or call tools to write this; everything you need is
  already in the conversation.
- If there's nothing substantive to recap, say so in one line.

## Example

**Goal**
- Find why the 30-day heat map loads slowly, since you asked about caching.
- I timed each stage of the request.

**Found**
- Caching would fix it: rebuilding hourly buckets on every request takes ~90% of load time.
- The database query itself is fast, about 40 ms.
- Unverified: whether the mobile view has the same bottleneck.

**Next**
- You: pick in-memory or a small SQLite table for the cache; SQLite survives restarts.
- Me: then cache per day and clear it on relabel, so 30-day loads drop from ~4 s to well under 1 s.

## The automatic trigger

`scripts/stop_hook.py` is a Stop hook (wired up in `~/.claude/settings.json`)
that asks for this recap at the end of long turns: a closing message of 200+
words after 8+ tool calls, or when 10+ minutes have passed since the user's
last message. It fires at most once per turn and skips headless `claude -p`
runs. Tune the thresholds at the top of the script; tests are alongside it.
