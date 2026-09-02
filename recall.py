"""Push-retrieval: walk the graph as code, before the model answers.

Seeds = entities whose name/alias appears in the question (full phrase, or
any distinctive token of a multi-word name). BFS over edges.tsv, both
directions, <= MAX_HOPS. Emits capped triples nearest-first plus one
description line per touched entity, so conditions (amounts, windows) ride
along with the verbs. No LLM, no ranking model — the graph walks the hops.

Library tier only. search.py is the document/content path. Loud-fail only
when BOTH miss.

Usage:
    python recall.py "your question"     # CLI: exit 1 if nothing seeded
    python recall.py --hook              # UserPromptSubmit hook: reads
                                         # {"prompt": ...} JSON on stdin,
                                         # silent exit 0 when unseeded
Stdlib only.
"""

import json
import re
import sys
from pathlib import Path

from kglib import STOP, corpus_root, load_docs, words

ROOT = corpus_root(__file__)
MAX_HOPS = 3
MAX_TRIPLES = 8
MAX_ENTITIES = 8
MIN_TOKEN_LEN = 4


def load_edges():
    p = ROOT / "edges.tsv"
    if not p.exists():
        return None
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            rows.append(tuple(parts))
    return rows


def phrase_in(phrase: str, q: str) -> bool:
    return bool(re.search(rf"\b{re.escape(phrase.lower())}\b", q.lower()))


def seed_entities(docs: list, question: str) -> list:
    q_words = words(question) - STOP
    seeds = []
    for d in docs:
        if not d["entity"]:
            continue
        for ph in [d["entity"], *d["aliases"]]:
            if not ph or not (words(ph) - STOP):
                continue
            tokens = {w for w in words(ph) - STOP if len(w) >= MIN_TOKEN_LEN}
            if phrase_in(ph, question) or tokens & q_words:
                seeds.append(d["entity"])
                break
    return seeds


def walk(edges: list, seeds: list, max_hops: int) -> list:
    """Breadth-first over edges, both directions. Returns [(hop, edge_row)]
    nearest-first; within a hop, predicated edges (the verbs) come before
    plain `related` links so a chatty neighbour can't crowd them out of
    the cap."""
    frontier = {s.lower() for s in seeds}
    visited, out = set(), []
    for hop in range(1, max_hops + 1):
        nxt, found = set(), []
        for i, (s, p, o, f) in enumerate(edges):
            if i in visited:
                continue
            sl, ol = s.lower(), o.lower()
            if sl in frontier or ol in frontier:
                visited.add(i)
                found.append((s, p, o, f))
                nxt.update((sl, ol))
        found.sort(key=lambda e: e[1] == "related")  # stable: verbs first
        out.extend((hop, e) for e in found)
        frontier |= nxt
        if not nxt:
            break
    return out


def describe(d: dict) -> str:
    if d["description"]:
        return d["description"]
    try:
        body = d["path"].read_text(encoding="utf-8")
    except OSError:
        body = ""
    return f"stub — see {d['file']}" if "Stub entity" in body else ""


def recall(question: str) -> str:
    docs = load_docs(ROOT, tiers=("library",))
    edges = load_edges()
    if edges is None:
        print("recall: edges.tsv missing — run build_index.py", file=sys.stderr)
        return ""
    seeds = seed_entities(docs, question)
    if not seeds:
        return ""
    hits = walk(edges, seeds, MAX_HOPS)[:MAX_TRIPLES]

    by_name = {d["entity"].lower(): d for d in docs if d["entity"]}
    by_file = {d["file"]: d for d in docs if d["entity"]}
    touched = list(seeds)
    for _, (s, _, o, f) in hits:
        names = [s, o]
        if f in by_file:
            names.append(by_file[f]["entity"])
        for e in names:
            if e.lower() in by_name and e not in touched:
                touched.append(e)
    touched = touched[:MAX_ENTITIES]

    lines = [
        f"## Library recall ({len(hits)} triples, {len(touched)} entities) "
        f"— seeds: {', '.join(seeds)}"
    ]
    for _, (s, p, o, f) in hits:
        lines.append(f"{s} --[{p}]--> {o}  ({f})")
    desc_lines = [
        f"{name}: {describe(by_name[name.lower()])}"
        for name in touched
        if describe(by_name[name.lower()])
    ]
    if desc_lines:
        lines.append("")
        lines.extend(desc_lines)
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--hook" in sys.argv:
        try:
            question = json.load(sys.stdin).get("prompt", "")
        except (json.JSONDecodeError, OSError):
            sys.exit(0)
        out = recall(question)
        if out:
            print(out)
        sys.exit(0)  # a hook must never block the prompt
    question = " ".join(sys.argv[1:])
    if not question:
        print('usage: python recall.py "your question"  (or --hook)')
        sys.exit(2)
    out = recall(question)
    if not out:
        print("recall: no entity seeded from the question — try search.py.")
        sys.exit(1)
    print(out)


if __name__ == "__main__":
    main()
