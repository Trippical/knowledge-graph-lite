"""Two-tier ranked search over the library's graph headers.

Scoring (per file, best-of not sum-of, so alias stuffing has no payoff):
  answers line   Dice overlap >= 0.4 -> up to ~190 (verbatim beats everything)
  entity match   40 + 30 per token (multi-word names beat bare stubs)
  alias match    30 + 25 per token
  inbox tier     total halved, hits tagged UNVERIFIED

Pass 2 on miss: swap stem-matched question words for canonical entity names
(deterministic order, library first, max 2 swaps). Then loud fail.

Edges: [staging] = endpoint only exists in inbox; [unresolved] = endpoint
exists nowhere (broken — do not traverse).

Stdlib only. Usage: python search.py "your question"
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kglib import STOP, load_docs, load_schema, split_relation, words
CAP = 15


def phrase_in(phrase: str, q: str) -> bool:
    return bool(re.search(rf"\b{re.escape(phrase.lower())}\b", q.lower()))


def best_name(d: dict, question: str) -> tuple:
    """Full-phrase match scores as before; a multi-word name whose
    distinctive tokens (len>=4, non-stop) appear in the question scores a
    reduced partial match, so "onboarding" finds Onboarding Process."""
    q_words = words(question) - STOP
    best, why = 0, None
    for kind, base, per, phrases in (
        ("entity", 40, 30, [d["entity"]]),
        ("alias", 30, 25, d["aliases"]),
    ):
        for ph in phrases:
            if not ph or not (words(ph) - STOP):
                continue
            if phrase_in(ph, question):
                pts = base + per * len(ph.split())
                if pts > best:
                    best, why = pts, f"{kind} match: '{ph}'"
                continue
            hit = sorted(
                w for w in words(ph) - STOP if len(w) >= 4 and w in q_words
            )
            if hit:
                pts = 15 * len(hit)
                if pts > best:
                    best, why = (
                        pts,
                        f"partial {kind} match: '{ph}' via {', '.join(hit)}",
                    )
    return best, why


def best_answer(d: dict, question: str) -> tuple:
    q_words = words(question) - STOP
    best, why = 0, None
    for ans in d["answers"]:
        a_words = words(ans) - STOP
        if not a_words or not q_words:
            continue
        shared = a_words & q_words
        dice = 2 * len(shared) / (len(a_words) + len(q_words))
        if dice >= 0.4:
            pts = int(150 * dice) + (40 if dice >= 0.8 else 0)
            if pts > best:
                best, why = (
                    pts,
                    (
                        f"answers: '{ans}' (overlap {dice:.2f}: "
                        f"{', '.join(sorted(shared))})"
                    ),
                )
    return best, why


def score(d: dict, question: str) -> tuple:
    n_pts, n_why = best_name(d, question)
    a_pts, a_why = best_answer(d, question)
    pts = n_pts + a_pts
    if d["tier"] == "inbox":
        pts //= 2
    return pts, [w for w in (n_why, a_why) if w]


def run(docs: list, question: str) -> list:
    hits = []
    for d in docs:
        pts, why = score(d, question)
        if pts:
            hits.append((pts, d["file"], d, why))
    return [(p, d, w) for p, _, d, w in sorted(hits, key=lambda h: (-h[0], h[1]))]


def expand(docs: list, question: str) -> tuple:
    q_words = words(question)
    cands = []
    for d in docs:
        vocab = {w for p in [d["entity"], *d["aliases"]] for w in words(p)}
        for qw in q_words:
            if qw in vocab:
                continue
            for vw in vocab:
                if len(qw) >= 5 and len(vw) >= 5 and qw[:5] == vw[:5]:
                    cands.append((d["tier"] != "library", d["entity"], qw))
    swaps = {}
    for _, entity, qw in sorted(set(cands)):
        if qw not in swaps and len(swaps) < 2:
            swaps[qw] = entity
    if not swaps:
        return [], {}
    expanded = question + " " + " ".join(sorted(set(swaps.values())))
    return run(docs, expanded), swaps


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    question = " ".join(sys.argv[1:])
    docs = load_docs(ROOT)
    _, preds = load_schema(ROOT)
    lib_entities = {d["entity"].lower() for d in docs if d["tier"] == "library"}
    all_entities = {d["entity"].lower() for d in docs if d["entity"]}

    hits, via = run(docs, question), "pass 1 (exact)"
    if not hits:
        hits, swaps = expand(docs, question)
        if hits:
            via = (
                "pass 2 (alias expansion: "
                + ", ".join(f"{k} -> {v}" for k, v in sorted(swaps.items()))
                + ")"
            )

    if not hits:
        tried = sorted(words(question) - STOP)
        print(
            f"no memory matches — tried exact terms and alias expansion on: "
            f"{', '.join(tried)}"
        )
        print(
            "if this should be answerable, record it with the write-documentation skill "
            "(or add the wording as an alias / answers: line)."
        )
        sys.exit(1)

    print(
        f"{len(hits)} hit(s), showing top {min(len(hits), CAP)} — matched via {via}\n"
    )
    for pts, d, why in hits[:CAP]:
        tag = (
            "  [UNVERIFIED — inbox, not yet synthesized]"
            if d["tier"] == "inbox"
            else ""
        )
        print(f"{d['file']}  (entity: {d['entity']}, score {pts}){tag}")
        for w in why:
            print(f"  {w}")
        for rel in d["relations"]:
            s, p, o = split_relation(rel, preds)
            mark = ""
            if p:
                ends = (s.lower(), o.lower())
                if any(e not in all_entities for e in ends):
                    mark = "  [unresolved]"
                elif any(e not in lib_entities for e in ends):
                    mark = "  [staging]"
            print(f"  edge: {rel}{mark}")
        for r in d["related"]:
            rl = r.lower()
            mark = ""
            if rl not in all_entities:
                mark = "  [unresolved]"
            elif rl not in lib_entities:
                mark = "  [staging]"
            print(f"  related: {r}{mark}")
        print()


if __name__ == "__main__":
    main()
