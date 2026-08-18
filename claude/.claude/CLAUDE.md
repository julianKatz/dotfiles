# Working guidelines

Applies across projects. A project's own CLAUDE.md wins on conflict.

**Define success before starting.** Turn the task into something falsifiable,
and say what the check is, before writing code.

- "Fix the bug" -> write a test that reproduces it, then make it pass
- "Add validation" -> write tests for the invalid inputs, then make them pass
- Not testable -> name the observable behavior you'll check, and how

"Make it work" is a weak criterion and costs a clarification round trip. A
strong one means you can iterate without me.

**Build what was asked.** No speculative abstractions, no configurability that
wasn't requested, no error handling for impossible states. Over-building early
is what makes a young repo unworkable.

**Report faithfully.** Say what you ran and what you didn't; unverified means
unverified. This matters most when I'm working at the behavior level and not
reading the diff -- a plausible-looking wrong implementation has nothing
catching it except the success criteria above.
