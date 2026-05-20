---
name: gitlab-mr-review
description: >-
  Use when reviewing GitLab merge requests (MRs) with glab or the GitLab REST API — draft notes for batched inline feedback, then publish after explicit user approval. Use for MR review, merge request review, GitLab code review, or glab mr workflows.
allowed-tools: AskUserQuestion
disable-model-invocation: true
---

# GitLab MR review

## Overview

Workflow for reviewing **GitLab merge requests** using **draft notes** so feedback stays batched until you publish. **Always create draft notes first, then publish in one step** — same idea as GitHub’s pending reviews.

**CRITICAL: Get explicit user approval before creating or publishing any review content on GitLab.** Show exactly what will be posted (files, lines, bodies, approve vs comment) and ask yes/no using **AskUserQuestion** (or the product’s equivalent confirmation step).

## When to use

- Reviewing a GitLab merge request (MR)
- Posting inline comments or suggestions on an MR
- Using `glab` or `curl` against the GitLab API

## Terminology

| GitHub | GitLab |
|--------|--------|
| Pull request (PR) | **Merge request (MR)** |
| PR number | **MR IID** (per-project merge request index) |

## Prerequisites

**CRITICAL: Confirm tooling before starting.**

### Option A — GitLab CLI (`glab`) (recommended)

```bash
glab version
```

If missing, tell the user to install from [GitLab CLI](https://gitlab.com/gitlab-org/cli) (e.g. `brew install glab`), then:

```bash
glab auth login
```

Use a token with at least **`api`** scope (and MR read/write as required by your instance).

### Option B — `curl` + token

Require `GITLAB_TOKEN` (or `PRIVATE_TOKEN`) and `GITLAB_HOST` (default `https://gitlab.com` for SaaS).

**If neither `glab` nor a usable token is available:** stop and give install/auth steps. Do not guess MR or project IDs.

### Resolve project and MR

- **Remote URL:** infer `namespace/project` from `git remote -v` when possible.
- **Project ID:** numeric ID or URL-encoded path, e.g. `mygroup%2Fmyproject`.
- **MR IID:** the small integer in the MR URL (`.../-/merge_requests/42` → IID `42`).

```bash
# From repo with glab configured
glab mr view <IID> --web   # optional: open in browser
glab mr diff <IID>
glab mr view <IID> --json author,title,state,source_branch,target_branch,head_pipeline
```

## Core workflow

**Required steps (do not skip):**

1. **Verify `glab` or `GITLAB_TOKEN`** — do not assume.
2. **Draft the review** — analyze the MR diff; list every draft note (path, line or position summary, body).
3. **Show the user exactly what will be posted** — AskUserQuestion (yes / no / revise).
4. **Wait for explicit approval** — no API calls that create or publish notes until approved.
5. **Create draft notes, then publish** — only after approval.

### Approval pattern

Before any `draft_notes` POST or bulk publish, show:

- MR IID and project
- Each note: file path, line (or position description), full body (including suggestion blocks)
- Intended outcome: **approve**, **comment only**, or **request changes** (map to GitLab actions below)
- Overall summary comment (if any)

**Example AskUserQuestion:**

- Question: “Post this GitLab MR review as drafted below?”
- Options: “Yes, create draft notes then publish” / “No, let me edit first”

### Why draft notes

- One batch of feedback instead of many separate notifications
- You can re-read bodies before publish
- Matches the discipline of the GitHub pending-review pattern

## GitLab API — draft notes (REST)

Base URL: `$GITLAB_HOST/api/v4` (SaaS: `https://gitlab.com/api/v4`).

**Create a draft note** (general comment on the MR — no position):

```bash
glab api --method POST "projects/<PROJECT_ID>/merge_requests/<MR_IID>/draft_notes" \
  -f "note=Your comment body (markdown supported)"
```

**Create an inline draft note** (simplified; real diff comments need a `position` object — see GitLab docs *Draft notes*):

```bash
# Prefer building position from the MR diff metadata (base_sha, start_sha, head_sha, paths, line).
glab api --method POST "projects/<PROJECT_ID>/merge_requests/<MR_IID>/draft_notes" \
  -F "note=Comment on the change" \
  --input - <<'JSON'
{ "position": { "base_sha": "...", "start_sha": "...", "head_sha": "...", "old_path": "README.md", "new_path": "README.md", "position_type": "text", "new_line": 12 } }
JSON
```

Use **`glab api` help** and [Draft notes API](https://docs.gitlab.com/ee/api/draft_notes.html) for exact `position` fields your GitLab version expects.

**Publish all draft notes** for the MR:

```bash
glab api --method POST "projects/<PROJECT_ID>/merge_requests/<MR_IID>/draft_notes/bulk_publish"
```

**List draft notes** (verify before publish):

```bash
glab api "projects/<PROJECT_ID>/merge_requests/<MR_IID>/draft_notes"
```

### Shas for inline comments

From the MR:

```bash
glab api "projects/<PROJECT_ID>/merge_requests/<MR_IID>" --jq '.diff_refs'
```

Use `diff_refs.base_sha`, `start_sha`, `head_sha` in `position`.

## Suggested code blocks (GitLab)

GitLab comments use Markdown; fenced code blocks work for examples. For **suggested change** style text, use a clear prefix so authors can copy/paste, e.g.:

````markdown
**Suggestion**

```ts
const fixed = true;
```

Replace the block above line 20 …
````

(Unlike GitHub’s ```suggestion blocks, GitLab’s apply-in-UI behavior depends on version and product; keep suggestions explicit and copyable.)

### Nested fences in suggestions

If the note itself contains triple backticks, wrap the outer block with four backticks or tildes (same pattern as the GitHub skill example).

## Outcome mapping (conceptual)

| Intent | After draft notes exist |
|--------|-------------------------|
| Approve MR | Use **Approve merge request** API / `glab mr approve <IID>` **after** user approves posting — only if policy allows automated approval |
| Request changes | Publish drafts + add a summary comment that states blocking issues; or use **unapprove** / reviewer state if your org uses it |
| Comment only | `bulk_publish` draft notes (or publish individually) with neutral summary |

**Do not** click Approve on behalf of the user without the same explicit confirmation you use for comments.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Posting notes before showing full text | Always approval step first |
| Using GitHub `gh` URLs or paths | Use GitLab project ID + MR IID + `/api/v4/` |
| Guessing `position` | Read `diff_refs` and diff hunks from `glab mr diff` |
| One-off comments under time pressure | Still use draft notes, then publish once |
| Missing `api` scope | Regenerate token and re-auth `glab` |

## Red flags — stop

- Skipping **AskUserQuestion** because the user said “LGTM” in chat
- Publishing without listing every note body
- Assuming `glab` is logged in without checking
- Mixing up **project ID** vs **MR IID** vs **note ID**

## Quick reference

```bash
# MR metadata
glab mr view <IID> --json title,state,author,source_branch,target_branch

# Diff
glab mr diff <IID>

# Pipelines (if relevant)
glab ci view <IID>
```

## Combining with local standards

If the repo has `.claude/skills/code-review/SKILL.md` (or `code-standards.json`), read it and align findings with those rules **before** drafting GitLab notes.
