"""Shared frontmatter parsing for the text library. Stdlib only."""

import re
from pathlib import Path

LIST_KEYS = ("aliases", "related", "relations", "answers", "provenance")
SCALAR_KEYS = ("title", "entity", "type", "description", "provenance_rev", "updated")
KNOWN_KEYS = set(LIST_KEYS) | set(SCALAR_KEYS)
STOP = {
    "what", "when", "who", "how", "does", "is", "are", "a", "an", "the",
    "to", "of", "for", "in", "on", "and", "or", "can", "do", "did", "it",
}


def words(text: str) -> set:
    return set(re.findall(r"[a-z0-9£-]+", text.lower()))


def parse_header(path: Path, root: Path) -> dict:
    doc = {k: "" for k in SCALAR_KEYS}
    doc.update({k: [] for k in LIST_KEYS})
    try:
        doc["file"] = str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        doc["file"] = str(path)
        doc["problems"] = [f"file is outside the library root ({root})"]
        return doc
    doc["path"] = path
    doc["problems"] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("﻿"):
        doc["problems"].append("file has a UTF-8 BOM")
        lines[0] = lines[0].lstrip("﻿")
    if not lines or lines[0].strip() != "---":
        doc["problems"].append("missing frontmatter")
        return doc
    key, closed, seen = None, False, set()
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key in seen:
                doc["problems"].append(f"duplicate header key '{key}'")
            seen.add(key)
            if key not in KNOWN_KEYS:
                doc["problems"].append(f"unknown header key '{key}'")
            elif key in SCALAR_KEYS:
                if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                    val = val[1:-1]
                doc[key] = val
            elif val:
                if val.startswith("[") and val.endswith("]"):
                    doc[key] = [v.strip() for v in val[1:-1].split(",") if v.strip()]
                elif key == "related":  # comma-separated entity names inline
                    doc[key] = [v.strip() for v in val.split(",") if v.strip()]
                else:
                    doc[key] = [val]
        elif re.match(r"^\s+-\s+", line):
            if key in LIST_KEYS:
                doc[key].append(re.sub(r"^\s+-\s+", "", line).strip())
            else:
                doc["problems"].append(
                    f"list item under non-list key '{key}': {line.strip()!r}"
                )
        elif line.strip():
            doc["problems"].append(f"unparseable line under '{key}': {line.strip()!r}")
    if not closed:
        doc["problems"].append("frontmatter never closed")
    return doc


def load_docs(root: Path, tiers=("library", "inbox")) -> list:
    docs = []
    for tier in tiers:
        base = root / tier
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.md")):
            d = parse_header(p, root)
            d["tier"] = tier
            d["domain"] = p.parent.name if p.parent != base else ""
            docs.append(d)
    return docs


def load_schema(root: Path) -> tuple:
    """Returns (types, predicates) parsed from SCHEMA.md list items."""
    types, preds = set(), set()
    section = None
    for line in (root / "SCHEMA.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
        m = re.match(r"^- `?([A-Za-z_]+)`?", line)
        if m and section and section.startswith("entity types"):
            types.add(m.group(1))
        elif m and section and section.startswith("predicates"):
            preds.add(m.group(1))
    return types, preds


def relation_predicates(rel: str, predicates: set) -> list:
    """All schema predicates appearing in the relation string."""
    return [p for p in predicates if re.search(rf"\s{re.escape(p)}\s", rel)]


def split_relation(rel: str, predicates: set) -> tuple:
    """'Subject predicate Object' -> (subject, predicate, object) or Nones."""
    found = relation_predicates(rel, predicates)
    if not found:
        return None, None, None
    p = min(found, key=lambda x: rel.find(f" {x} "))
    m = re.search(rf"\s{re.escape(p)}\s", rel)
    return rel[: m.start()].strip(), p, rel[m.end() :].strip()
