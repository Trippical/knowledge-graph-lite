# graph-lite — the starter read layer

A zero-dependency read layer over the corpus: deterministic structure
instead of embeddings, stdlib instead of infrastructure.

- **recall.py (push):** seeds entities named in the question, BFS-walks
  edges.tsv both directions ≤3 hops, injects capped triples plus one-line
  descriptions. Wire as a UserPromptSubmit hook — zero tool calls, fixed
  ~400 tokens at any corpus size.
- **search.py (pull):** two-tier ranked search over names, aliases, and
  `answers:` lines; inbox hits flagged UNVERIFIED.
- **read-documentation/**: this layer's read skill — how an agent should
  query, traverse, cite, and fail loudly.

Loud-fail only when both paths miss.

## The layer contract

A read layer may read the corpus (`library/`, `inbox/`) and any
projection (edges.tsv, registry.tsv, INDEX.md, warehouse tables). It may
never write the corpus or bypass SCHEMA. Each layer ships its own read
skill and must pass the gold tables (`library/<domain>/GOLD.md`) through
its own retrieval — `tests/test_gold.py` is THIS layer's runner.

Swap this layer for anything — SQL over the Delta mirror
(layers/delta/), a hybrid RAG stack, an MCP server — without touching
connectors, the gate, or the corpus.
