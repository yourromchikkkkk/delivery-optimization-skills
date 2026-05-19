---
name: commit-message
description: >-
  Runs git diff HEAD, summarizes the staged/unstaged changes, and suggests a conventional commit message. Use when the user asks for a commit message, wants to summarize their changes, or says "what should I commit?".
---

# Commit Message Suggester

Run the following and use the output to suggest a commit message.

## Step 1 — Gather the diff

```bash
git diff HEAD
```

If the output is empty, also try:

```bash
git diff --cached
```

If both are empty, tell the user there are no changes to commit and stop.

## Step 2 — Summarize the changes

Read the diff and produce a short summary (2–4 sentences):
- What files changed and why
- What was added, removed, or modified
- Any notable side-effects or deletions

## Step 3 — Suggest a commit message

Use the **Conventional Commits** format:

```
<type>(<optional scope>): <short imperative description>

<optional body: what changed and why, wrap at 72 chars>
```

**Type rules:**
- `feat` — new feature or behaviour
- `fix` — bug fix
- `refactor` — restructuring without behaviour change
- `test` — adding or updating tests
- `chore` — tooling, config, deps, scripts
- `docs` — documentation only
- `style` — formatting, whitespace (no logic change)
- `perf` — performance improvement
- `ci` — CI/CD pipeline changes

**Message rules:**
- Subject line ≤ 72 characters, imperative mood ("add X", not "added X")
- No period at end of subject line
- Body only if changes need explanation beyond the subject
- If multiple unrelated concerns exist, flag them and suggest splitting commits

## Output format

Present output in this order:

1. **Summary** — 2–4 sentence prose description of what changed
2. **Suggested commit message** — inside a fenced code block
3. **Alternative** — one shorter or differently-scoped variant if relevant

## Step 4 — Ask for approval and commit

After presenting the output, ask the user: **"Approve this commit message?"**

- If approved (yes / looks good / etc.): first invoke the `update-readme` skill to review the codebase and create or update README.md files. Then stage all modified tracked files (including any README changes) with `git add` and run `git commit` with the approved message. Append `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` to the commit body.
- If the user requests changes: apply them, show the revised message, and ask again.
- If declined: stop without committing.
