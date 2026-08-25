# Knowledge-graph write skills (ported)

Canonical source: `skills/{write-documentation,extract,synthesize}/SKILL.md`
in this repo. This is a read-only port for when you're already in a
Databricks context and need to record a fact — if the two copies ever
disagree, the repo copy wins; update this file to match.

The corpus lives as governed markdown (`library/`, `inbox/`) with an
optional `kg_entities` / `kg_edges` mirror in your `<catalog>.<schema>`
(see `layers/delta/publish_delta.py` — target is parameterized via
`--target` or `KG_DELTA_TARGET`) so SQL and BI tools can sit on top. Markdown is the
source of truth; the Delta tables are a generated projection.

## Write documentation — add one fact, cheaply

Use when someone shares a fact, doc, policy, or update worth recording.
No dedupe, no linking, no comprehension — that's synthesize's job.

1. One file per entity → `inbox/<domain>/<slug>.md`. Type from SCHEMA.md §
   Entity types; never invent vocabulary. `source_rev:` (commit SHA) when
   the source is code.
2. Link related entities with `related: Name, Name` (canonical names, no
   verb). Unsure of the canonical name → put the fact in body prose
   instead; never write `relations:` from this skill.
3. `python validate.py --format inbox/<domain>/<file>.md` — fix errors.
4. PR touching ONLY `inbox/`. Never edit `library/` from this skill.

Code sources: extract policy, ownership, why-facts only — classes and
endpoints never get entities; a table or dataset people consume by name
may get a REPORT entity documenting access, never values.

## Extract — batch-distill sources into the corpus

Use for backfilling a domain from SQL, repos, wikis, or docs — not for a
single fact someone just told you (that's write-documentation).

1. Read SCHEMA.md first. Scope the sweep with the domain owner: paths,
   domain, rough entity count. No open-ended crawling.
2. Per source file, extract only what the source can't say by being read
   (intent, why, ownership, grain, gotchas, questions answered). Never
   copy code/column lists/enumerations — `source:` points at them.
3. `python validate.py --dupe "<name>"` before creating any entity —
   near-match → write into the existing entity's inbox file instead of
   forking a name.
4. One file per entity, `source:` mandatory, `source_rev:` mandatory for
   code sources, `answers:` 3-5 lines. Every body claim traces to a
   source line — no general-knowledge fill.
5. `python validate.py --format` on every new file.
6. PR touching ONLY `inbox/`, `backfill-wave` label, one domain per PR,
   ≤ ~25 files; body lists sources swept and duplicates skipped.

## Synthesize — promote inbox → library (the only path)

Cadenced compaction, strong model + human PR partner. Run per-domain when
its inbox exceeds ~8 files or the oldest capture is >14 days old.

1. `python build_index.py`; read INDEX.md + registry.tsv.
2. Per inbox file: `python validate.py --dupe "<entity>"` → promote new
   entities, merge into canonical file for existing ones (newer source
   wins on conflicts, record supersession with date), merge near-dupes to
   one canonical (losers become aliases).
3. Upgrade `related:` to predicated `relations:` only where the verb
   matters; every endpoint must resolve (stub entity if real-but-unmodeled).
4. `proposed_predicate:` lines → separate SCHEMA.md PR for the schema
   owner; never merge content using unapproved predicates.
5. `python validate.py` — zero errors, triage every warning.
6. Reindex last: `python build_index.py`, commit INDEX.md + registry.tsv.
7. Then mirror to your warehouse (optional): `python
   layers/delta/publish_delta.py --execute --target <catalog.schema>` so
   the Delta mirror stays in sync with what just landed in `library/`.
8. PR: steady-state ≤ ~10 entities per merge decision; backfill waves
   exempt via the `backfill-wave` label, one PR per domain wave.

High-risk predicates (⚠ in SCHEMA.md) added/redirected need a named human
ack in the PR body.
