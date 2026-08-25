"""Deterministic lint. Full mode gates library/; format mode gates inbox files.

Usage:
    python validate.py                       # full: graph checks + drift + inbox format
    python validate.py --format <file>...    # format-check specific inbox files
    python validate.py --dupe "<name>"       # top near-duplicate candidates for a name

Exit 1 on any error. Warnings print but do not fail.
"""

import datetime
import difflib
import re
import sys
from pathlib import Path

from kglib import (
    STOP,
    load_docs,
    load_schema,
    parse_header,
    relation_predicates,
    split_relation,
)

ROOT = Path(__file__).resolve().parent
NAME_CHARS = re.compile(r"[^A-Za-z0-9 £/&()'._-]")
FUNCTIONAL = {"delegates_to", "superseded_by"}  # one object per subject


def norm(name: str) -> str:
    return name.lower().strip()


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def check_name(label, value, fname, preds, errors, warnings):
    if NAME_CHARS.search(value):
        errors.append(
            f"{fname}: {label} '{value}' contains a disallowed character "
            f"(non-ASCII/homoglyph/control)"
        )
    # WARN not ERROR: the decoy-entity exploit this guards against needs a
    # contrived setup; synthesize triages warnings before promotion.
    if set(norm(value).split()) & preds:
        warnings.append(f"{fname}: {label} '{value}' contains a schema predicate word")


def check_format(d, types, preds, errors, warnings, require_source=False):
    f = d["file"]
    for p in d["problems"]:
        errors.append(f"{f}: {p}")
    for key in ("title", "entity", "type", "updated"):
        if not d[key]:
            errors.append(f"{f}: missing required key '{key}'")
    if d["type"] and d["type"] not in types:
        errors.append(f"{f}: type '{d['type']}' not in SCHEMA.md")
    if d["updated"]:
        try:
            when = datetime.date.fromisoformat(d["updated"])
            if when > datetime.date.today():
                errors.append(f"{f}: updated '{d['updated']}' is in the future")
        except ValueError:
            errors.append(f"{f}: updated '{d['updated']}' is not an ISO date")
    if d["entity"]:
        check_name("entity", d["entity"], f, preds, errors, warnings)
    if len(d["description"]) > 200:
        warnings.append(
            f"{f}: description is {len(d['description'])} chars — keep it one "
            f"tight line (conditions + definition only)"
        )
    dates = {}
    for key in ("valid_from", "valid_to"):
        if d[key]:
            try:
                dates[key] = datetime.date.fromisoformat(d[key])
            except ValueError:
                errors.append(f"{f}: {key} '{d[key]}' is not an ISO date")
    if len(dates) == 2 and dates["valid_from"] > dates["valid_to"]:
        errors.append(f"{f}: valid_from is after valid_to")
    for a in d["aliases"]:
        check_name("alias", a, f, preds, errors, warnings)
        if norm(a) in STOP or len(a.strip()) < 2 or not re.search(r"[A-Za-z]", a):
            errors.append(
                f"{f}: alias '{a}' is a stopword or too short to be a safe join key"
            )
    for rel in d["relations"]:
        found = relation_predicates(rel, preds)
        if not found:
            errors.append(
                f"{f}: relation uses no SCHEMA.md predicate: '{rel}' "
                f"(propose new vocabulary via proposed_predicate:)"
            )
        elif len(found) > 1:
            errors.append(
                f"{f}: ambiguous relation (multiple predicates "
                f"{sorted(found)}): '{rel}'"
            )
    for src in d["source"]:
        if "://" not in src:
            if not any((base / src).exists() for base in (ROOT, ROOT.parent)):
                errors.append(f"{f}: source path '{src}' does not exist")
    if d["source_rev"] and not re.match(r"^[0-9a-f]{7,40}$|^r\d+$", d["source_rev"]):
        errors.append(
            f"{f}: source_rev '{d['source_rev']}' is not a commit SHA or revision"
        )
    if require_source and not d["source"]:
        errors.append(f"{f}: inbox files require 'source:' provenance")


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
            if norm(a) != norm(b) and ratio(a, b) >= 0.85:
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
                        f"{d['file']}: relation endpoint '{end}' "
                        f"resolves to no library entity ('{rel}')"
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
            errors.append(
                f"conflicting {p} edges for '{s}': "
                f"{ {o: fs for o, fs in objs.items()} }"
            )

    owners = {}
    for d in lib:
        for a in d["aliases"]:
            owners.setdefault(norm(a), set()).add(norm(d["entity"]))
    for a, es in owners.items():
        if len(es) > 1:
            warnings.append(
                f"alias '{a}' claimed by entities: {sorted(es)} "
                f"(allowed only with disambiguation notes)"
            )

    for d in inbox:
        if len(d["answers"]) > 5:
            warnings.append(f"{d['file']}: more than 5 answers lines")
        for a in d["aliases"]:
            owner = owners.get(norm(a))
            claimed = norm(a) in names
            if (owner and norm(d["entity"]) not in owner) or (
                claimed and norm(a) != norm(d["entity"])
            ):
                errors.append(
                    f"{d['file']}: alias '{a}' collides with an existing "
                    f"library entity/alias it does not belong to"
                )
        if d["entity"] and norm(d["entity"]) not in names:
            ent = norm(d["entity"])
            owner = owners.get(ent)
            if owner:
                errors.append(
                    f"{d['file']}: entity '{d['entity']}' is an alias of "
                    f"library entity {sorted(owner)} — merge into the "
                    f"canonical file, do not promote"
                )
            for label in set(names) | set(owners):
                if ent != label and ratio(d["entity"], label) >= 0.85:
                    warnings.append(
                        f"{d['file']}: entity '{d['entity']}' is a "
                        f"near-duplicate of library name/alias '{label}' — "
                        f"synthesize should merge, not promote"
                    )
    for d in lib:
        if len(d["answers"]) > 5:
            warnings.append(f"{d['file']}: more than 5 answers lines")


def drift_check(errors):
    from build_index import render

    index_txt, registry_txt, edges_txt = render()
    for fname, want in (
        ("INDEX.md", index_txt),
        ("registry.tsv", registry_txt),
        ("edges.tsv", edges_txt),
    ):
        p = ROOT / fname
        if not p.exists() or p.read_text(encoding="utf-8") != want:
            errors.append(f"{fname} is stale or hand-edited — run build_index.py")


def dupe_lookup(name):
    lib = load_docs(ROOT, tiers=("library",))
    cands = []
    for d in lib:
        for label in [d["entity"], *d["aliases"]]:
            if label:
                cands.append((ratio(name, label), label, d["file"]))
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
                # Warnings are maintainer signals — suppress in the
                # coworker-facing format gate; full mode re-surfaces them.
                check_format(d, types, preds, errors, [], require_source=True)
    else:
        lib = load_docs(ROOT, tiers=("library",))
        inbox = load_docs(ROOT, tiers=("inbox",))
        for d in lib:
            check_format(d, types, preds, errors, warnings)
        unsourced = sum(1 for d in lib if not d["source"])
        if unsourced:
            warnings.append(
                f"{unsourced} library file(s) lack source: provenance "
                f"(fine for curated files; required for extracted ones)"
            )
        for d in inbox:
            check_format(d, types, preds, errors, warnings, require_source=True)
        graph_checks(lib, inbox, preds, errors, warnings)
        drift_check(errors)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"validate: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
