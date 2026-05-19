---
name: update-readme
description: >-
  Reviews the codebase and creates or updates README.md files. Use when the user asks to write, generate, or refresh README documentation for the project or a specific directory.
---

# README Updater

Explore the codebase and write or update README.md files with accurate, useful documentation.

## Step 1 — Determine scope

Check whether the user specified a target directory. If not, default to the repository root.

```bash
ls
```

For each target directory, check if a README.md already exists:

```bash
find . -name "README.md" -not -path "*/node_modules/*" -not -path "*/.git/*"
```

## Step 2 — Understand the codebase

Read enough of the project to write accurate documentation. Collect:

- **Purpose** — what this project/directory does and why it exists
- **Structure** — key files, directories, and their roles
- **Setup** — how to install dependencies and configure the environment
- **Usage** — how to run, build, or invoke the main entry points
- **Testing** — how to run tests
- **Configuration** — notable env vars, config files, or flags

Useful commands to gather this context (run what's relevant):

```bash
# Detect package manager and scripts
cat package.json 2>/dev/null || cat pyproject.toml 2>/dev/null || cat Cargo.toml 2>/dev/null || cat go.mod 2>/dev/null

# Understand directory layout
find . -maxdepth 2 -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/__pycache__/*" | sort

# Check for existing CI or Makefile targets
cat Makefile 2>/dev/null || cat .github/workflows/*.yml 2>/dev/null | head -80
```

Read key source files to understand the actual behaviour — don't rely solely on file names.

## Step 3 — Write or update the README

### If no README exists — create one

Use this structure (omit sections that don't apply):

```markdown
# <Project Name>

<One-paragraph description of what this is and why it exists.>

## Requirements

- <runtime / language version>
- <other system dependency>

## Installation

```bash
<install command>
```

## Usage

```bash
<run command>
```

<Brief description of key options or arguments.>

## Project structure

```
<directory tree, 1–2 levels deep, with short annotations>
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ENV_VAR` | `value` | What it controls |

## Testing

```bash
<test command>
```

## Contributing

<Short note on how to contribute, if applicable.>
```

### If a README already exists — update it

1. Read the existing file in full.
2. Preserve any sections that are still accurate.
3. Update outdated information (commands, structure, versions).
4. Add sections that are missing and relevant.
5. Remove sections that no longer apply.
6. Keep the author's tone and style where possible.

### Writing rules

- Be concise — one clear sentence beats a vague paragraph.
- Use fenced code blocks for all commands.
- Don't document implementation details — document how to use and run.
- Avoid phrases like "This project is a..." — start with a direct description.
- Don't add emojis unless the existing README already uses them.

## Step 4 — Write the file

Write the README to the appropriate path (e.g., `README.md` or `<subdir>/README.md`).

After writing, briefly tell the user what was created or changed and which sections were added, updated, or removed.
