"""Two-tier ranked search over the library's frontmatter (the pull path).

Tokens on both sides are lowercased, hyphen-split, and lightly stemmed
(kglib.words), and a query token that is a closed compound of two known
words is split ("tiebreak" -> tie + break), so word-form differences
between a question and the stored phrasing don't zero the score.

Scoring (per file, best-of not sum-of, so alias stuffing has no payoff):
  answers line   Dice overlap >= 0.4 -> up to ~190 (verbatim beats everything)
                 else 10 per shared distinctive token (partial)
  entity match   40 + 30 per token (multi-word names beat bare stubs)
  alias match    30 + 25 per token
  inbox tier     total halved, hits tagged UNVERIFIED

Pass 2 on miss: swap stem-matched question words for canonical entity names
(deterministic order, library first, max 2 swaps).
Pass 3 on miss: body text, clearly labelled low confidence. Then loud fail.

Edges: [staging] = endpoint only exists in inbox; [unresolved] = endpoint
exists nowhere (broken — do not traverse).

Stdlib only. Usage: python search.py "your question"
"""

import re
import sys
from pathlib import Path

from kglib import STOP, corpus_root, load_docs, load_schema, split_compound, split_relation, words

ROOT = corpus_root(__file__)
CAP = 15
STOPS = {w for s in STOP for w in words(s)}


def phrase_in(phrase: str, q: str) -> bool:
    return bool(re.search(rf"\b{re.escape(phrase.lower())}\b", q.lower()))


def query_tokens(question: str, vocab: set) -> set:
    """Question tokens, minus stopwords, plus the halves of any compound."""
    toks = words(question) - STOPS
    for t in list(toks):
        toks.update(split_compound(t, vocab))
    return toks


def best_name(d: dict, q_words: set, question: str) -> tuple:
    best, why = 0, None
    for kind, base, per, phrases in (
        ("entity", 40, 30, [d["entity"]]),
        ("alias", 30, 25, d["aliases"]),
    ):
        for ph in phrases:
            if not ph or not (words(ph) - STOPS):
                continue
            if phrase_in(ph, question):
                pts = base + per * len(ph.split())
                if pts > best:
                    best, why = pts, f"{kind} match: '{ph}'"
                continue
            hit = sorted(w for w in words(ph) - STOPS if len(w) >= 4 and w in q_words)
            if hit:
                pts = 15 * len(hit)
                if pts > best:
                    best, why = pts, f"partial {kind} match: '{ph}' via {', '.join(hit)}"
    return best, why


def best_answer(d: dict, q_words: set) -> tuple:
    best, why = 0, None
    for ans in d["answers"]:
        a_words = words(ans) - STOPS
        if not a_words or not q_words:
            continue
        shared = a_words & q_words
        if not shared:
            continue
        dice = 2 * len(shared) / (len(a_words) + len(q_words))
        if dice >= 0.4:
            pts = int(150 * dice) + (40 if dice >= 0.8 else 0)
            label = f"answers: '{ans}' (overlap {dice:.2f}: {', '.join(sorted(shared))})"
        else:
            distinctive = sorted(w for w in shared if len(w) >= 3)
            if not distinctive:
                continue
            pts = 10 * len(distinctive)
            label = f"partial answers: '{ans}' via {', '.join(distinctive)}"
        if pts > best:
            best, why = pts, label
    return best, why


def score(d: dict, q_words: set, question: str) -> tuple:
    n_pts, n_why = best_name(d, q_words, question)
    a_pts, a_why = best_answer(d, q_words)
    pts = n_pts + a_pts
    if d["tier"] == "inbox":
        pts //= 2
    return pts, [w for w in (n_why, a_why) if w]


def run(docs: list, q_words: set, question: str) -> list:
    hits = []
    for d in docs:
        pts, why = score(d, q_words, question)
        if pts:
            hits.append((pts, d["file"], d, why))
    return [(p, d, w) for p, _, d, w in sorted(hits, key=lambda h: (-h[0], h[1]))]


def expand(docs: list, q_words: set, question: str) -> tuple:
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
    extra = set()
    for e in swaps.values():
        extra |= words(e)
    return run(docs, q_words | extra, question + " " + " ".join(sorted(set(swaps.values())))), swaps


def body_pass(docs: list, q_words: set) -> list:
    """Low-confidence fallback: distinctive query tokens found in body text."""
    hits = []
    distinctive = {w for w in q_words if len(w) >= 4}
    for d in docs:
        if "path" not in d:
            continue
        try:
            text = d["path"].read_text(encoding="utf-8")
        except OSError:
            continue
        body = text.partition("\n---\n")[2]
        shared = sorted(distinctive & words(body))
        if len(shared) >= 2:
            pts = 5 * len(shared)
            hits.append((pts, d["file"], d, [f"body match (low confidence) via {', '.join(shared)}"]))
    return [(p, d, w) for p, _, d, w in sorted(hits, key=lambda h: (-h[0], h[1]))]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    question = " ".join(sys.argv[1:])
    docs = load_docs(ROOT)
    _, preds = load_schema(ROOT)
    lib_entities = {d["entity"].lower() for d in docs if d["tier"] == "library"}
    all_entities = {d["entity"].lower() for d in docs if d["entity"]}
    vocab = set()
    for d in docs:
        for p in [d["entity"], *d["aliases"], *d["answers"]]:
            vocab |= words(p)
    q_words = query_tokens(question, vocab)

    hits, via = run(docs, q_words, question), "pass 1 (normalized tokens)"
    if not hits:
        hits, swaps = expand(docs, q_words, question)
        if hits:
            via = "pass 2 (alias expansion: " + ", ".join(
                f"{k} -> {v}" for k, v in sorted(swaps.items())
            ) + ")"
    if not hits:
        hits = body_pass(docs, q_words)
        if hits:
            via = "pass 3 (body text — LOW CONFIDENCE, open the file before relying on it)"

    if not hits:
        print(f"no memory matches — tried normalized terms, alias expansion, and body text on: {', '.join(sorted(q_words))}")
        print("if this should be answerable, record it with the write-documentation skill.")
        sys.exit(1)

    print(f"{len(hits)} hit(s), showing top {min(len(hits), CAP)} — matched via {via}\n")
    for pts, d, why in hits[:CAP]:
        tag = "  [UNVERIFIED — inbox, not yet synthesized]" if d["tier"] == "inbox" else ""
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
