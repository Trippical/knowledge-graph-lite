"""Deterministic lint. Full mode checks library/ + inbox/; format mode checks
single files.

Usage:
    python validate.py                       # full: format + graph checks
    python validate.py --format <file>...    # format-check specific files
    python validate.py --dupe "<name>"       # top near-duplicate candidates

Exit 1 on any error. Warnings print but do not fail.
"""

import datetime
import difflib
import re
import sys
from pathlib import Path

from kglib import (
    STOP,
    corpus_root,
    load_docs,
    load_schema,
    parse_header,
    relation_predicates,
    split_relation,
)

ROOT = corpus_root(__file__)
NAME_CHARS = re.compile(r"[^A-Za-z0-9 £/&()'._-]")
FUNCTIONAL = {"delegates_to", "superseded_by"}  # one object per subject


def norm(name: str) -> str:
    return name.lower().strip()


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def scoped_family(a: str, b: str) -> bool:
    """'Last 4 (Acme)' vs 'Last 4' or 'Last 4 (Beta)': one general thing and
    its scoped versions share a base name by design — not near-duplicates."""
    base = lambda n: re.sub(r"\s*\(.*?\)", "", norm(n)).strip()
    return ("(" in a or "(" in b) and base(a) == base(b) and norm(a) != norm(b)


def check_name(label, value, fname, preds, errors, warnings):
    if NAME_CHARS.search(value):
        errors.append(f"{fname}: {label} '{value}' contains a disallowed character")
    if set(norm(value).split()) & preds:
        warnings.append(f"{fname}: {label} '{value}' contains a schema predicate word")


def check_format(d, types, preds, errors, warnings, require_provenance=False):
    f = d["file"]
    for p in d["problems"]:
        errors.append(f"{f}: {p}")
    for key in ("title", "entity", "type", "updated"):
        if not d[key]:
            errors.append(f"{f}: missing required key '{key}'")
    if d["type"] and d["type"] not in types:
        errors.append(
            f"{f}: type '{d['type']}' not in SCHEMA.md (typo? or add it there)"
        )
    if d["updated"]:
        try:
            if datetime.date.fromisoformat(d["updated"]) > datetime.date.today():
                errors.append(f"{f}: updated '{d['updated']}' is in the future")
        except ValueError:
            errors.append(f"{f}: updated '{d['updated']}' is not an ISO date")
    if d["entity"]:
        check_name("entity", d["entity"], f, preds, errors, warnings)
    if len(d["description"]) > 200:
        warnings.append(
            f"{f}: description is {len(d['description'])} chars — keep it one line"
        )
    for a in d["aliases"]:
        check_name("alias", a, f, preds, errors, warnings)
        if norm(a) in STOP or len(a.strip()) < 2 or not re.search(r"[A-Za-z]", a):
            errors.append(f"{f}: alias '{a}' is a stopword or too short")
    for rel in d["relations"]:
        found = relation_predicates(rel, preds)
        if not found:
            errors.append(f"{f}: relation uses no SCHEMA.md predicate: '{rel}'")
        elif len(found) > 1:
            errors.append(f"{f}: ambiguous relation ({sorted(found)}): '{rel}'")
    for src in d["provenance"]:
        if "://" in src:
            continue  # URL / URI — never checked
        if src.startswith("repo:"):
            if not re.match(r"^repo:[\w.-]+/\S+$", src):
                warnings.append(f"{f}: provenance '{src}' — repo form is repo:<name>/<path>")
            continue  # another repository — not checked from here
        if re.match(r"^[A-Za-z]:[\\/]|^[\\/]", src):
            warnings.append(
                f"{f}: provenance '{src}' is a local absolute path — NEEDS WORK: "
                f"it won't resolve on another machine; prefer repo:<name>/<path> or a URL"
            )
        elif not (ROOT / src).exists():
            warnings.append(f"{f}: provenance path '{src}' does not exist in this library")
    if d["provenance_rev"] and not re.match(
        r"^[0-9a-f]{7,40}$|^r\d+$", d["provenance_rev"]
    ):
        errors.append(f"{f}: provenance_rev '{d['provenance_rev']}' is not a SHA")
    if require_provenance and not d["provenance"]:
        errors.append(f"{f}: inbox files require 'provenance:'")


def graph_checks(lib, inbox, preds, errors, warnings):
    names = {}
    for d in lib:
        if not d["entity"]:
            continue
        key = norm(d["entity"])
        if key in names:
            errors.append(
                f"{d['file']}: duplicate entity '{d['entity']}' (also in {names[key]})"
            )
        else:
            names[key] = d["file"]

    ents = [(d["entity"], d["file"]) for d in lib if d["entity"]]
    for i, (a, fa) in enumerate(ents):
        for b, fb in ents[i + 1 :]:
            if norm(a) != norm(b) and ratio(a, b) >= 0.85 and not scoped_family(a, b):
                errors.append(
                    f"near-duplicate entities: '{a}' ({fa}) vs '{b}' ({fb}) "
                    f"— merge or rename"
                )

    for d in lib:
        for rel in d["relations"]:
            s, p, o = split_relation(rel, preds)
            if not p:
                continue
            for end in (s, o):
                if norm(end) not in names:
                    errors.append(
                        f"{d['file']}: relation endpoint '{end}' resolves to no "
                        f"library entity ('{rel}')"
                    )
        for r in d["related"]:
            if norm(r) not in names:
                errors.append(
                    f"{d['file']}: related name '{r}' resolves to no library entity"
                )

    sp = {}
    for d in lib:
        for rel in d["relations"]:
            s, p, o = split_relation(rel, preds)
            if p:
                sp.setdefault((norm(s), p), {}).setdefault(norm(o), []).append(
                    d["file"]
                )
    for (s, p), objs in sp.items():
        if p in FUNCTIONAL and len(objs) > 1:
            errors.append(f"conflicting {p} edges for '{s}': {objs}")

    owners = {}
    for d in lib:
        for a in d["aliases"]:
            owners.setdefault(norm(a), set()).add(norm(d["entity"]))
    for a, es in owners.items():
        if len(es) > 1:
            warnings.append(f"alias '{a}' claimed by entities: {sorted(es)}")

    for d in inbox:
        for a in d["aliases"]:
            owner = owners.get(norm(a))
            claimed = norm(a) in names
            if (owner and norm(d["entity"]) not in owner) or (
                claimed and norm(a) != norm(d["entity"])
            ):
                errors.append(
                    f"{d['file']}: alias '{a}' collides with an existing library "
                    f"entity/alias it does not belong to"
                )
        if d["entity"] and norm(d["entity"]) not in names:
            ent = norm(d["entity"])
            owner = owners.get(ent)
            if owner:
                errors.append(
                    f"{d['file']}: entity '{d['entity']}' is an alias of library "
                    f"entity {sorted(owner)} — merge into the canonical file"
                )
            for label in set(names) | set(owners):
                if (
                    ent != label
                    and ratio(d["entity"], label) >= 0.85
                    and not scoped_family(d["entity"], label)
                ):
                    warnings.append(
                        f"{d['file']}: entity '{d['entity']}' is a near-duplicate "
                        f"of library name/alias '{label}' — merge, don't promote"
                    )
    # inbox-vs-inbox: two captures in one wave can collide with each other,
    # which only becomes an error once both are promoted — warn early.
    ib = [(d["entity"], d["file"]) for d in inbox if d["entity"]]
    for i, (a, fa) in enumerate(ib):
        for b, fb in ib[i + 1 :]:
            if norm(a) != norm(b) and ratio(a, b) >= 0.85 and not scoped_family(a, b):
                warnings.append(
                    f"near-duplicate inbox captures: '{a}' ({fa}) vs '{b}' ({fb}) "
                    f"— rename one before synthesize promotes both"
                )
    for d in lib + inbox:
        if len(d["answers"]) > 5:
            warnings.append(f"{d['file']}: more than 5 answers lines")


def index_check(warnings):
    from build_index import render

    for fname, want in zip(("INDEX.md", "registry.tsv", "edges.tsv"), render()):
        p = ROOT / fname
        if not p.exists() or p.read_text(encoding="utf-8") != want:
            warnings.append(f"{fname} is stale — run build_index.py")


def dupe_lookup(name):
    lib = load_docs(ROOT, tiers=("library",))
    cands = []
    for d in lib:
        for label in [d["entity"], *d["aliases"]]:
            if label:
                cands.append((ratio(name, label), label, d["file"]))
    if not cands:
        print("no candidates — library is empty; the inbox listing is the dedupe surface")
    for r, label, f in sorted(cands, reverse=True)[:10]:
        print(f"{r:.2f}  {label}  ({f})")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    types, preds = load_schema(ROOT)
    errors, warnings = [], []

    if "--dupe" in sys.argv:
        dupe_lookup(" ".join(a for a in sys.argv[1:] if a != "--dupe"))
        return
    if "--format" in sys.argv:
        for a in sys.argv[1:]:
            if a != "--format":
                d = parse_header(Path(a).resolve(), ROOT)
                check_format(d, types, preds, errors, warnings, require_provenance=True)
    else:
        lib = load_docs(ROOT, tiers=("library",))
        inbox = load_docs(ROOT, tiers=("inbox",))
        for d in lib:
            check_format(d, types, preds, errors, warnings)
        for d in inbox:
            check_format(d, types, preds, errors, warnings, require_provenance=True)
        graph_checks(lib, inbox, preds, errors, warnings)
        index_check(warnings)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"validate: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
