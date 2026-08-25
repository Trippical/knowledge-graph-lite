# The connector contract

A connector is anything that turns information from a source system into
capture files the corpus can govern. Human, agent, or script — the
contract is the same:

**Read your source. Emit valid inbox markdown. Nothing else.**

    connectors  ─►  inbox/<domain>/*.md  ─►  gate (synthesize)  ─►  library/
    (any source)    formatted captures,      human-approved         canonical
                    instantly queryable      compaction             corpus
                    as UNVERIFIED

## What a connector emits

One file per entity, `inbox/<domain>/<slug>.md`, that passes
`python validate.py --format`:

- `entity:` — canonical name (check registry.tsv; an existing name means
  the facts MERGE there, never fork)
- `type:` — from SCHEMA.md's closed list, never invented
- `source:` — provenance path or URL, always; `source_rev:` when the
  source is code
- `answers:` — the questions this capture settles, as people ask them
- body — why-facts, ownership, gotchas; every claim traceable to the
  source; never copied enumerations, column lists, or measure values

## What a connector never does

- Write to `library/` — the gate is the only door
- Invent vocabulary — unknown verb? body prose + `proposed_predicate:`
- Dedupe, canonicalize, or link with predicated `relations:` — judgment
  is the gate's job; connectors capture

## Shipped connectors

| Connector | Source | Skill |
| --------- | ------ | ----- |
| write-documentation | a human with one fact — THE PRIMITIVE all others drive | connectors/write-documentation/ |
| extract | docs, code, SQL, wikis — batch driver: decompose, gate, one write-documentation run per surviving fact | connectors/extract/ |
| thread-summarize | chat threads (planned) | — |

Adding a source system = adding a connector. The core never changes.
