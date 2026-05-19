"""
Load and save code standards in .claude/code-standards.json (stdlib only).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

CLAUDE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STANDARDS_PATH = CLAUDE_ROOT / "code-standards.json"


def load(path: str | Path | None = None) -> dict:
    p = Path(path) if path else DEFAULT_STANDARDS_PATH
    if not p.exists():
        raise FileNotFoundError(f"Standards file not found: {p}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def save(data: dict, path: str | Path | None = None) -> Path:
    p = Path(path) if path else DEFAULT_STANDARDS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return p


def read_setup(data: dict) -> dict[str, str]:
    setup = data.get("setup") or {}
    return {k: str(v) for k, v in setup.items() if v is not None}


def write_setup(data: dict, setup: dict[str, str]) -> None:
    data["setup"] = dict(setup)


def index_questions(data: dict) -> dict[str, dict]:
    """Map question id -> question object (mutable)."""
    idx: dict[str, dict] = {}
    for section in data.get("form", []):
        for q in section.get("questions", []):
            qid = q.get("id")
            if qid:
                idx[qid] = q
    return idx


def question_value(q: dict) -> Any | None:
    override = q.get("override")
    if override not in (None, ""):
        return override
    suggested = q.get("suggested")
    if suggested in (None, ""):
        return None
    return suggested


def is_empty_value(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def iter_answered_questions(data: dict) -> Iterator[tuple[str, dict]]:
    for section in data.get("form", []):
        section_name = section.get("section", "")
        for q in section.get("questions", []):
            yield section_name, q
