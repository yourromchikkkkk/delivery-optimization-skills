---
name: github-pr-review
description: >-
  Use when reviewing GitHub pull requests with the gh CLI: pending reviews, batched inline comments,
  code suggestions, and event types COMMENT / APPROVE / REQUEST_CHANGES. Trigger on GitHub PR review,
  gh pr review, or pull request feedback.
allowed-tools: AskUserQuestion
disable-model-invocation: true
---

# GitHub PR review

## Overview

Workflow for reviewing GitHub pull requests using `gh api` to create **pending** reviews with optional **```suggestion`** blocks. **Always use pending reviews to batch comments, even under time pressure.**

**CRITICAL: Always get explicit user approval before posting any review comments.** Show exactly what will be posted and ask for yes/no confirmation using **AskUserQuestion**.

## When to use

- Reviewing pull requests on GitHub
- Adding code suggestions to PRs
- Posting review comments with the `gh` CLI

## Path placeholder

In API URLs, **`repos/:owner/:repo`** means your repository slug **`OWNER/REPO`** (e.g. `acme/widget`). Resolve it with:

```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

Example: `repos/acme/widget/pulls/42/reviews`.

## Prerequisites

**CRITICAL: Check if `gh` is installed before starting.**

```bash
gh --version
```

**If `gh` is not installed:**

1. **Stop** — do not run `gh api` commands.
2. Tell the user to install from [https://cli.github.com/](https://cli.github.com/) (e.g. `brew install gh`, `winget install GitHub.cli`).
3. They must run `gh auth login` after install.
4. **Do not proceed** until `gh` works.

### After installation

```bash
gh auth login
```

## Core workflow

**Required steps (do not skip):**

1. **Check `gh`** — `gh --version`
2. **Draft the review** — analyze the PR; list every comment (path, line, body, suggestions).
3. **Show exactly what will be posted** — AskUserQuestion (yes / no / revise).
4. **Get explicit approval** — wait for confirmation.
5. **Post the review** — only after approval.

### Approval pattern

Before posting, show:

- File and line for each comment
- Exact body (including ```suggestion blocks)
- Event type: `APPROVE` / `REQUEST_CHANGES` / `COMMENT`
- Overall review message

## Technical workflow

**ALWAYS use the pending review pattern, even for a single comment:**

```bash
# Step 1: Create PENDING review (omit event on create)
gh api repos/OWNER/REPO/pulls/<PR_NUMBER>/reviews \
  -X POST \
  -f commit_id="<COMMIT_SHA>" \
  -f 'comments[][path]=path/to/file.ts' \
  -F 'comments[][line]=<LINE_NUMBER>' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=Comment text

```suggestion
// suggested code here
```

Additional explanation...' \
  --jq '{id, state}'

# Returns: {"id": <REVIEW_ID>, "state": "PENDING"}

# Step 2: Submit the pending review
gh api repos/OWNER/REPO/pulls/<PR_NUMBER>/reviews/<REVIEW_ID>/events \
  -X POST \
  -f event="COMMENT" \
  -f body="Optional overall review message"
```

## Event types

| Event | When to use |
|-------|-------------|
| `APPROVE` | PR ready; only minor / non-blocking notes |
| `REQUEST_CHANGES` | Blocking issues (security, bugs, missing tests) |
| `COMMENT` | Neutral feedback or questions |

## Quick reference

```bash
# Latest commit on the PR
gh pr view <PR_NUMBER> --json commits --jq '.commits[-1].oid'

# Repo slug
gh repo view --json nameWithOwner -q .nameWithOwner
```

### Required parameters

- **`commit_id`**: latest head SHA of the PR
- **`comments[][path]`**: path relative to repo root
- **`comments[][line]`**: end line (use **`-F`** for numbers)
- **`comments[][side]`**: usually **`RIGHT`** for new/changed lines, **`LEFT`** for deletions
- **`comments[][body]`**: markdown; optional ```suggestion fenced block

### Syntax rules

- **DO:** single quotes around keys with `[]`, e.g. `'comments[][path]'`; **`-f`** strings, **`-F`** numbers.
- **DON'T:** double-quote `comments[][]` keys; don’t mix `-f`/`-F` incorrectly; don’t skip fetching `commit_id`.

## Code suggestions format

```bash
-f 'comments[][body]=Your comment

```suggestion
const fixed = "like this";
```

More context.'
```

Suggestions replace the targeted line(s); keep suggested code complete and correct.

### Nested code fences in suggestions

For markdown/docs that contain triple backticks, wrap the suggestion in four backticks or tildes (see nested-block examples in GitHub’s review docs).

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Posting without pending review | Always create pending review first |
| Skipping approval “because user said LGTM in chat” | Still show bodies + AskUserQuestion |
| Wrong quotes on `comments[]` | Use `'comments[][path]=...'` |
| No commit SHA | `gh pr view <N> --json commits --jq '.commits[-1].oid'` |

## Red flags — stop

- “ASAP → skip pending review”
- “One comment → post directly”
- “User approved the idea → skip showing exact posted text”
- “`gh` is probably installed”

**Stop: verify `gh`, draft, approve, then pending review + submit.**

## Full multi-comment example

After approval:

```bash
gh api repos/OWNER/REPO/pulls/123/reviews \
  -X POST \
  -f commit_id="abc123" \
  -f 'comments[][path]=src/auth.ts' \
  -F 'comments[][line]=20' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=First issue...' \
  -f 'comments[][path]=src/auth.ts' \
  -F 'comments[][line]=35' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=Second issue...' \
  --jq '{id, state}'

gh api repos/OWNER/REPO/pulls/123/reviews/<REVIEW_ID>/events \
  -X POST \
  -f event="REQUEST_CHANGES" \
  -f body="Found issues that should be fixed before merge."
```

## Combining with team standards

If this repo has **`/code-review`** (from `code-standards.json`), use that skill to **draft** findings first, then map them into the `gh api` bodies above — still follow pending review + AskUserQuestion before posting.

## Why this pattern

- **Pending:** batch notifications, add comments before submit, consistent process.
- **Approval:** review comments are public; suggestions can be wrong; tone may need edits.
