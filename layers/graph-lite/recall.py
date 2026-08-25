"""Push-retrieval: walk the graph as code, before the model answers.

Seeds = entities whose name/alias appears in the question (full phrase, or
any distinctive token of a multi-word name — so "onboarding" seeds
Onboarding Process). BFS over edges.tsv, both directions, ≤ MAX_HOPS. Emits capped
triples nearest-first plus one description line per touched entity, so the
conditions (amounts, windows, "together with X") ride along with the verbs.
No LLM, no ranking model — deterministic structure; multi-hop is code.

Library tier only: recall answers from canonical structure. search.py stays
the document/content path (answers: lines, prose, inbox). Loud-fail only
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kglib import STOP, load_docs, words
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
    """Canonical names of entities the question mentions, full-phrase or
    per-token (distinctive tokens only)."""
    q_words = words(question) - STOP
    seeds = []
    for d in docs:
        if not d["entity"]:
            continue
        hit = False
        for ph in [d["entity"], *d["aliases"]]:
            if not ph or not (words(ph) - STOP):
                continue
            if phrase_in(ph, question):
                hit = True
                break
            tokens = {
                w for w in words(ph) - STOP if len(w) >= MIN_TOKEN_LEN
            }
            if tokens & q_words:
                hit = True
                break
        if hit:
            seeds.append(d["entity"])
    return seeds


def walk(edges: list, seeds: list, max_hops: int) -> list:
    """Breadth-first over edges, both directions. Returns [(hop, edge_row)]
    nearest-first, in stable edge order within a hop."""
    seed_norms = {s.lower() for s in seeds}
    frontier = set(seed_norms)
    visited_edges, out = set(), []
    for hop in range(1, max_hops + 1):
        nxt = set()
        for i, (s, p, o, f) in enumerate(edges):
            if i in visited_edges:
                continue
            sl, ol = s.lower(), o.lower()
            if sl in frontier or ol in frontier:
                visited_edges.add(i)
                out.append((hop, (s, p, o, f)))
                nxt.update((sl, ol))
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
    if "Stub entity" in body:
        return f"stub — see {d['file']}"
    return ""


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
        # endpoints, plus the entity whose file documents the edge — that
        # file's description is where the conditions live
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
    desc_lines = []
    for name in touched:
        text = describe(by_name[name.lower()])
        if text:
            desc_lines.append(f"{name}: {text}")
    if desc_lines:
        lines.append("")
        lines.extend(desc_lines)
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if "--hook" in sys.argv:
        try:
            payload = json.load(sys.stdin)
            question = payload.get("prompt", "")
        except (json.JSONDecodeError, OSError):
            sys.exit(0)
        out = recall(question)
        if out:
            print(out)
        sys.exit(0)  # hook must never block the prompt
    question = " ".join(sys.argv[1:])
    if not question:
        print('usage: python recall.py "your question"  (or --hook)')
        sys.exit(2)
    out = recall(question)
    if not out:
        print(
            "recall: no entity seeded from the question — structural path "
            "has nothing; try search.py for document content."
        )
        sys.exit(1)
    print(out)


if __name__ == "__main__":
    main()
