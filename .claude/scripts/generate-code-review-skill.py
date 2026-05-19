#!/usr/bin/env python3
"""
Read .claude/code-standards.json and generate a Cursor/Claude code-review skill.

Uses override when set, otherwise suggested, then apply-preset defaults for gaps.

Usage:
    python .claude/scripts/generate-code-review-skill.py
    python .claude/scripts/generate-code-review-skill.py --apply-preset
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from standards_store import (
    DEFAULT_STANDARDS_PATH,
    load,
    question_value,
    read_setup,
)

CLAUDE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL_DIR = CLAUDE_ROOT / "skills" / "code-review"

YN_YES = frozenset({"Y", "YES", "TRUE", "X", "1"})


@dataclass
class FormEntry:
    qid: str
    question: str
    qtype: str
    value: Any
    other: str | None = None


@dataclass
class FormData:
    setup: dict[str, str] = field(default_factory=dict)
    sections: dict[str, list[FormEntry]] = field(default_factory=dict)
    meta: dict[str, str] = field(default_factory=dict)


def is_yes(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().upper() in YN_YES


def load_apply_preset_module():
    path = Path(__file__).resolve().parent / "apply-preset.py"
    spec = importlib.util.spec_from_file_location("apply_preset", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load apply-preset module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_preset_values(setup: dict[str, str]) -> dict[str, Any]:
    mod = load_apply_preset_module()
    presets = mod.collect_presets(setup)
    values: dict[str, Any] = {}
    for _source, preset in presets:
        for qid, val in preset.items():
            if qid in ("_additions", "_includes", "_other_text"):
                continue
            values.setdefault(qid, val)
        for target, lines in preset.get("_additions", {}).items():
            existing = values.get(target, "")
            current_lines = [ln for ln in str(existing).splitlines() if ln.strip()]
            merged = current_lines[:]
            for ln in lines:
                if ln not in merged:
                    merged.append(ln)
            if merged:
                values[target] = "\n".join(merged)
    return values


def collect_form(data: dict) -> FormData:
    result = FormData()
    result.setup = read_setup(data)
    preset_values = build_preset_values(result.setup) if result.setup else {}

    for section in data.get("form", []):
        section_name = section.get("section", "")
        if not section_name:
            continue
        result.sections.setdefault(section_name, [])

        for q in section.get("questions", []):
            qid = (q.get("id") or "").strip()
            if not qid or "." not in qid:
                continue

            val = question_value(q)
            if val is None:
                val = preset_values.get(qid)
            if val is None:
                continue

            entry = FormEntry(
                qid=qid,
                question=(q.get("question") or qid).strip(),
                qtype=(q.get("type") or "text").strip().lower(),
                value=val,
                other=(str(q["other"]).strip() if q.get("other") else None),
            )
            result.sections[section_name].append(entry)
            if qid.startswith("meta."):
                result.meta[qid] = str(val).strip()

    return result


def bullets_from_text(text: str) -> list[str]:
    lines: list[str] = []
    for ln in str(text).splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if re.search(r"<openpyxl\.", ln) or re.search(r" object at 0x[0-9a-f]+>$", ln):
            continue
        lines.append(ln)
    return lines


def format_choice(entry: FormEntry) -> str:
    text = str(entry.value).strip()
    if entry.other:
        text = f"{text} ({entry.other})"
    return f"- **{entry.question}**: {text}"


def format_yn_list(entries: list[FormEntry], *, only_yes: bool = True) -> list[str]:
    lines: list[str] = []
    for e in entries:
        if e.qtype != "yn":
            continue
        if only_yes and not is_yes(e.value):
            continue
        if not only_yes and is_yes(e.value):
            continue
        lines.append(f"- {e.question}")
    return lines


def format_text_bullets(entries: list[FormEntry], qids: set[str]) -> list[str]:
    lines: list[str] = []
    for e in entries:
        if e.qid not in qids:
            continue
        for line in bullets_from_text(str(e.value)):
            lines.append(f"- {line}")
    return lines


def active_methodologies(setup: dict[str, str]) -> list[str]:
    labels = {
        "method.clean_code": "Clean Code",
        "method.solid": "SOLID",
        "method.ddd": "Domain-Driven Design (DDD)",
        "method.hex": "Hexagonal / Ports & Adapters",
        "method.twelve": "12-Factor App",
        "method.tdd": "Test-Driven Development",
        "method.functional": "Functional core / immutable data",
    }
    return [label for key, label in labels.items() if is_yes(setup.get(key))]


def build_description(data: FormData, skill_name: str) -> str:
    lang = data.setup.get("setup.lang", data.meta.get("meta.lang", "the team's stack"))
    fw = data.setup.get("setup.framework", "")
    team = data.meta.get("meta.team", "")
    parts = [
        f"Reviews code for quality, security, and maintainability using {team or 'team'} standards"
        f" ({lang}" + (f", {fw}" if fw else "") + ").",
        "Use when reviewing pull requests, diffs, or when the user asks for code review or feedback.",
    ]
    return " ".join(parts)[:1020]


def section_entries(data: FormData, *prefixes: str) -> list[FormEntry]:
    out: list[FormEntry] = []
    for _sec, entries in data.sections.items():
        for e in entries:
            if any(e.qid.startswith(p) for p in prefixes):
                out.append(e)
    return out


def render_skill(data: FormData, skill_name: str) -> str:
    lang = data.setup.get("setup.lang") or data.meta.get("meta.lang", "Not specified")
    fw = data.setup.get("setup.framework", "Not specified")
    team = data.meta.get("meta.team", "Team")
    scope = data.meta.get("meta.scope", "")
    contact = data.meta.get("meta.contact", "")
    date = data.meta.get("meta.date", "")
    methods = active_methodologies(data.setup)

    description = build_description(data, skill_name)

    lines: list[str] = [
        "---",
        f"name: {skill_name}",
        "description: >-",
        f"  {description}",
        "---",
        "",
        f"# {team} Code Review",
        "",
        "Review changes against the standards below. Be specific: cite file/line, explain the rule, and suggest a fix.",
        "",
        "## Context",
        "",
        f"- **Language**: {lang}",
        f"- **Framework**: {fw}",
    ]
    if scope:
        lines.append(f"- **Scope**: {scope}")
    if methods:
        lines.append(f"- **Methodologies**: {', '.join(methods)}")
    if contact:
        lines.append(f"- **Contact**: {contact}")
    if date:
        lines.append(f"- **Standards dated**: {date}")

    style = section_entries(data, "style.", "name.")
    if style:
        lines.extend(["", "## Style and naming", ""])
        for e in style:
            if e.qtype == "choice":
                lines.append(format_choice(e))

    req_yn = format_yn_list(section_entries(data, "req."), only_yes=True)
    req_other = format_text_bullets(section_entries(data, "req."), {"req.other"})
    if req_yn or req_other:
        lines.extend(["", "## Required patterns (must have)", ""])
        lines.extend(req_yn)
        lines.extend(req_other)

    fb_yn = format_yn_list(section_entries(data, "fb."), only_yes=True)
    fb_other = format_text_bullets(section_entries(data, "fb."), {"fb.other"})
    if fb_yn or fb_other:
        lines.extend(["", "## Forbidden patterns (blockers)", ""])
        lines.extend(fb_yn)
        lines.extend(fb_other)

    warn_yn = format_yn_list(section_entries(data, "warn."), only_yes=True)
    warn_other = format_text_bullets(section_entries(data, "warn."), {"warn.other"})
    if warn_yn or warn_other:
        lines.extend(["", "## Warnings (non-blocking)", ""])
        lines.extend(warn_yn)
        lines.extend(warn_other)

    test = section_entries(data, "test.")
    if test:
        lines.extend(["", "## Testing", ""])
        for e in test:
            if e.qtype == "choice":
                lines.append(format_choice(e))
            elif e.qtype == "yn" and is_yes(e.value):
                lines.append(f"- {e.question}")

    sec_yn = format_yn_list(section_entries(data, "sec."), only_yes=True)
    sec_other = format_text_bullets(section_entries(data, "sec."), {"sec.other"})
    if sec_yn or sec_other:
        lines.extend(["", "## Security", ""])
        lines.extend(sec_yn)
        lines.extend(sec_other)

    tool = section_entries(data, "tool.")
    if tool:
        lines.extend(["", "## Tooling (CI enforces these)", ""])
        for e in tool:
            if e.qtype == "choice":
                lines.append(format_choice(e))

    skip_yn = format_yn_list(section_entries(data, "skip."), only_yes=True)
    skip_other = format_text_bullets(section_entries(data, "skip."), {"skip.other"})
    if skip_yn or skip_other:
        lines.extend(["", "## Do not flag in review (already automated or out of scope)", ""])
        lines.extend(skip_yn)
        lines.extend(skip_other)

    refs = section_entries(data, "ref.")
    ref_lines = [f"- **{e.question}**: {str(e.value).strip()}" for e in refs if str(e.value).strip()]
    if ref_lines:
        lines.extend(["", "## References", ""])
        lines.extend(ref_lines)

    lines.extend(
        [
            "",
            "## Review workflow",
            "",
            "1. Understand the change goal and affected areas.",
            "2. Check **forbidden** and **security** items first — these are merge blockers.",
            "3. Verify **required patterns** and **testing** expectations.",
            "4. Note **warnings** and style/naming issues as non-blocking suggestions.",
            "5. Skip anything listed under **Do not flag**.",
            "",
            "## Feedback format",
            "",
            "Group findings by severity:",
            "",
            "- **Critical** — forbidden pattern, security issue, or missing required pattern; must fix before merge.",
            "- **Suggestion** — warning thresholds, style, or maintainability; should fix or justify.",
            "- **Nice to have** — optional polish.",
            "",
            "For each finding: location → rule violated → recommended fix.",
        ]
    )

    return "\n".join(lines) + "\n"


def run_apply_preset(config_path: Path) -> None:
    script = Path(__file__).resolve().parent / "apply-preset.py"
    subprocess.run(
        [sys.executable, str(script), str(config_path), "--from-config"],
        check=True,
    )


def write_skill(content: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    skill_path = output_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")
    return skill_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_STANDARDS_PATH),
        help=f"Standards JSON path (default: {DEFAULT_STANDARDS_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_SKILL_DIR),
        help=f"Directory for generated skill (default: {DEFAULT_SKILL_DIR})",
    )
    parser.add_argument(
        "--skill-name",
        help="Skill name slug (default: code-review)",
    )
    parser.add_argument(
        "--apply-preset",
        action="store_true",
        help="Run apply-preset.py --from-config before generating",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"File not found: {config_path}", file=sys.stderr)
        sys.exit(2)

    if args.apply_preset:
        run_apply_preset(config_path)

    data = load(config_path)
    form_data = collect_form(data)

    if not form_data.sections:
        print("No answers in config. Run apply-preset.py first.", file=sys.stderr)
        sys.exit(1)

    skill_name = args.skill_name or "code-review"
    skill_path = write_skill(render_skill(form_data, skill_name), Path(args.output_dir))

    filled = sum(len(v) for v in form_data.sections.values())
    print(f"Collected {filled} answers from config.")
    print(f"Wrote {skill_path} (name: {skill_name})")
    print(f"Invoke in Claude Code/Cursor with /{skill_name} or ask for a code review.")


if __name__ == "__main__":
    main()
