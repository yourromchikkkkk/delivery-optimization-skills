# Code standards → agent skills

Turn **code-standards.json** into Claude Code skills for PR feedback, commit messages, and README generation.

No third-party dependencies — Python 3.9+ standard library only.

## Layout

```text
.claude/
├── README.md
├── code-standards.json           # questions + setup + answers (edit overrides here)
├── settings.json                 # Claude Code permissions
├── scripts/
│   ├── apply-preset.py           # interactive preset picker; preset data lives in this file
│   ├── generate-code-review-skill.py
│   └── standards_store.py        # JSON load/save helpers
├── commands/
│   └── code-reviewer-generator.md
└── skills/
    ├── code-review/
    │   └── SKILL.md              # generated from code-standards.json
    ├── commit-message/
    │   └── SKILL.md              # diffs, summarises, suggests, commits on approval
    ├── update-readme/
    │   └── SKILL.md              # explores codebase and writes/updates README files
    ├── github-pr-review/
    │   └── SKILL.md              # GitHub PR review via gh pending reviews + explicit approval
    └── gitlab-mr-review/
        └── SKILL.md              # GitLab MR review via draft notes + explicit approval
```

## Skills

| Slash command | What it does |
|---|---|
| `/code-reviewer-generator` | Apply presets and regenerate the `/code-review` skill |
| `/code-review` | Review a diff or PR against team standards |
| `/github-pr-review` | Review a GitHub PR with `gh`: pending reviews, suggestions, COMMENT/APPROVE/REQUEST_CHANGES — approval before post |
| `/gitlab-mr-review` | Review a GitLab merge request: draft notes, batch publish, explicit approval before posting |
| `/commit-message` | Summarise staged changes, suggest a commit message, update READMEs, then commit on approval |
| `/update-readme` | Explore the codebase and create or update README.md files |

## Quick start

From the **repository root**:

```bash
# Interactive: choose language, framework, methodologies, department, contact
python .claude/scripts/apply-preset.py

# Generate the code-review skill
python .claude/scripts/generate-code-review-skill.py
```

Or run `/code-reviewer-generator` in Claude Code to do both steps in one command.

## Config file

`.claude/code-standards.json` contains:

- **`setup`** — `setup.lang`, `setup.framework`, `method.*` (Y/N)
- **`form`** — sections with questions (`id`, `question`, `type`, `suggested`, `override`, `other`)

The generator prefers freshly computed preset values for fields covered by a preset, and falls back to `override` → `suggested` for everything else. To permanently override a preset value, set `override` in the JSON and it will be used for fields the preset does not cover.

### Flags

```bash
python .claude/scripts/apply-preset.py --from-config      # no prompts; use saved setup
python .claude/scripts/apply-preset.py --fill-empty-only  # only fill blank suggested fields
```

## Workflow

1. Run `apply-preset.py` and select your stack, department, and contact.
2. Optionally edit `override` fields in `code-standards.json`.
3. Run `generate-code-review-skill.py` or `/code-reviewer-generator`.
4. Use `/code-review` when reviewing PRs.
5. Use `/commit-message` to stage, commit, and keep READMEs up to date.
