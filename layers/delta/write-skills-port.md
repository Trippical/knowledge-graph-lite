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
   Entity types; never invent vocabulary. `provenance_rev:` (commit SHA)
   when the source is code.
2. Link related entities with `related: Name, Name` (canonical names, no
   verb). Unsure of the canonical name → put the fact in body prose
   instead; never write `relations:` from this skill.
3. `python validate.py --format inbox/<domain>/<file>.md` — fix errors.
4. PR touching ONLY `inbox/`. Never edit `library/` from this skill.

Code sources: extract policy, ownership, why-facts only — classes and
endpoints never get entities; point `provenance:` at them. A named table
or dataset people consume by name MAY get a DATA_ASSET entity: the
business of the asset (purpose, grain, cadence, ownership, gotchas),
bound via `ref: uc://catalog.schema.object` — never its columns, never
the values inside it.

## Extract — batch driver over write-documentation

Use for backfilling a domain from SQL, repos, wikis, or docs — not for a
single fact someone just told you (that's write-documentation directly).
Extract owns no capture rules: it decomposes sources into candidate
facts, gates them, and runs write-documentation once per survivor.

1. Scope the sweep with the domain owner: paths, domain, rough entity
   count. No open-ended crawling.
2. Decompose each source into candidates (definitions, why-decisions,
   ownership, grain, gotchas, derivations). Never copy code/column
   lists/enumerations — `provenance:` points at them.
3. THE GATE, in order: source defines a key term → capture; can't write
   the `answers:` question first, as a person would ask it → drop;
   borderline → keep only if ignorance causes wrong decisions, repeated
   questions, or breakage; measure value → capture the derivation,
   never the value.
4. Per survivor: a write-documentation run, plus batch extras —
   `--dupe` before any new name (near-match takes the existing
   canonical name), `provenance_rev:` for code, verbatim quotes for
   judgment-heavy facts, doc-vs-code conflicts recorded for synthesize.
5. `python validate.py --format` on every new file.
6. PR touching ONLY `inbox/`, `backfill-wave` label, one domain per PR,
   ≤ ~25 files; body lists sources swept, duplicates skipped, and the
   gate log (captured vs dropped, each drop tagged with its failing
   prong).

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
