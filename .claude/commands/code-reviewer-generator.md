---
description: Apply code-standards presets, generate a code-review skill from code-standards.json, and verify the output.
argument-hint: [path-to-json]
---

Generate a project code-review skill from the team's **code standards config**.

## Step 1 — Apply presets

If the user has not run `apply-preset.py` interactively yet, ask them to run it in a terminal and choose language, framework, methodologies, department, and contact. Preset definitions live in `.claude/scripts/apply-preset.py`; questions and answers persist in `.claude/code-standards.json`.

Then apply saved setup to the form (non-interactive):

!`python3 .claude/scripts/apply-preset.py "${ARGUMENTS:-.claude/code-standards.json}" --from-config`

## Step 2 — Generate the skill

!`python3 .claude/scripts/generate-code-review-skill.py "${ARGUMENTS:-.claude/code-standards.json}"`

## Step 3 — Verify

1. Read `.claude/skills/code-review/SKILL.md`.
2. Confirm sections match the config (style, required/forbidden patterns, warnings, testing, security, tooling, skip list).
3. If sections are empty, tell the user to run `apply-preset.py` or fill overrides in `.claude/code-standards.json`.

## After generation

- Use `/code-review` for PR reviews.
- Re-run `/code-reviewer-generator` after editing `.claude/code-standards.json` or re-running `apply-preset.py`.
