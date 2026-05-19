# Code standards → code-review skill

Turn **code-standards.json** into a Cursor/Claude **code-review skill** for PR feedback.

No third-party dependencies — Python 3.9+ standard library only.

## Layout

```text
.claude/
├── README.md
├── code-standards.json           # questions + setup + answers (edit overrides here)
├── scripts/
│   ├── apply-preset.py           # interactive preset picker; preset data in this file
│   ├── generate-code-review-skill.py
│   └── standards_store.py        # JSON load/save helpers
├── commands/
│   └── code-reviewer-generator.md
└── skills/
    └── code-review/
        └── SKILL.md              # generated
```

## Quick start

From the **repository root**:

```bash
# Interactive: language, framework, methodologies, department, contact; fill form from presets
python .claude/scripts/apply-preset.py

python .claude/scripts/generate-code-review-skill.py
```

Or: `/code-reviewer-generator`

## Config file

`.claude/code-standards.json` contains:

- **`setup`** — `setup.lang`, `setup.framework`, `method.*` (Y/N)
- **`form`** — sections with questions (`id`, `question`, `type`, `suggested`, `override`, `other`)

Effective answer = `override` if set, else `suggested`. Run `apply-preset.py` to populate `suggested` from presets in `apply-preset.py`.

### Flags

```bash
python .claude/scripts/apply-preset.py --from-config      # no prompts; use saved setup
python .claude/scripts/apply-preset.py --fill-empty-only    # only fill blank suggested fields
```

## Workflow

1. Run `apply-preset.py` and select your stack, department, and contact.
2. Optionally edit `override` fields in `code-standards.json`.
3. Run `generate-code-review-skill.py` or `/code-reviewer-generator`.
4. Use `/code-review` when reviewing PRs.
