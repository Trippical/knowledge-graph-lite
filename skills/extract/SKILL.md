---
name: kg-extract
description: Distill existing code and documentation into inbox captures — batch, source-driven, provenance-pinned. Use for backfilling a domain from SQL, repos, wikis, or docs; NOT for single facts someone just told you (that's write-documentation).
---

# Extract (distill sources into the corpus)

Capture at scale, driven by sources instead of a human's head. Output goes
to `inbox/` ONLY — synthesize remains the sole path to `library/`.

## Steps

1. Read SCHEMA.md (types, predicates, header keys). Never invent vocabulary.
2. Scope the sweep with the domain owner FIRST: which paths/docs, which
   domain, roughly how many entities. No open-ended crawling.
3. For each source file, extract only what the source cannot say by being
   read: intent, why-decisions, ownership, grain, gotchas, and the
   questions it answers. Never copy code, column lists, or enumerations —
   `source:` points at them; agents follow the link for detail.
   Fan out: one inbox file per entity the source touches. The source
   itself gets an entity (DOCUMENT/REPORT) only if it's asked for by
   name or has behavior worth explaining — default: citation only.
4. Before creating any entity, run `python validate.py --dupe "<name>"`.
   Near-match in the registry → write the new facts into an inbox file
   named for the EXISTING entity (synthesize merges); don't fork a name.
5. Write one file per entity to `inbox/<domain>/<slug>.md`:
   - `source:` mandatory; `source_rev:` mandatory when the source is code
     (commit SHA at extraction time).
   - `answers:` lines for the questions the asset settles (3-5 max).
   - Every claim in the body must trace to a source line or section —
     no general-knowledge fill. Can't cite it? Leave it out.
   - Link entities with `related:` (comma-separated names). Predicated
     `relations:` only when the verb is stated verbatim in the source —
     verbatim means the verb appears in the source sentence; matching the
     phrasing pattern of existing library edges does not count.
6. `python validate.py --format` on every new file — fix all errors.
7. Open the PR touching ONLY `inbox/`: `backfill-wave` label, one domain
   per PR, ≤ ~25 files. Bigger sweep → multiple waves. PR body lists the
   sources swept and the entities skipped as duplicates (auditable scope).

## Rules

- Code sources: policy, ownership, and why-facts only. Classes and
  endpoints never get entities. A table or dataset people consume by name
  MAY get a REPORT entity: document access (grain, cadence, source-of-truth
  status, how to derive the numbers people ask for), NEVER the values
  themselves — "how to derive Q2 refund totals" belongs in the corpus,
  "Q2 refunds totalled £46k" never does.
- Docs that contradict code: code wins for what-it-does; record the doc's
  why-claim with both sources cited and note the conflict for synthesize.
- Ambiguous or judgment-heavy fact → capture verbatim with the source
  quote; synthesize judges, extract doesn't.
- This skill is for maintainers and backfill waves, not everyday use —
  a coworker with one fact wants write-documentation, not this.
