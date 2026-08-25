---
name: kg-extract
description: Batch-distill sources into the corpus by driving write-documentation once per gated fact — decompose, gate, capture, provenance-pinned. Use for backfilling a domain from SQL, repos, wikis, or docs; NOT for a single fact someone just told you (that's write-documentation directly).
---

# Extract (batch driver over write-documentation)

Extract owns NO capture rules. It decomposes sources into candidate
facts, gates them for usefulness, and executes one write-documentation
run per survivor — the primitive's template, merge rule, and format lint
apply unchanged. Output goes to `inbox/` ONLY; synthesize remains the
sole path to `library/`.

## Steps

1. Scope the sweep with the domain owner FIRST: which paths/docs, which
   domain, roughly how many entities. No open-ended crawling.
2. Read SCHEMA.md and the write-documentation skill — they define the
   capture format. Never invent vocabulary.
3. DECOMPOSE each source into candidate facts: term definitions,
   why-decisions, ownership, grain, gotchas, access/derivation info.
   Never copy code, column lists, or enumerations — `source:` points at
   them; agents follow the link for detail.
4. Run THE GATE on every candidate, in order:
   1. **Key term** — the source DEFINES a domain term → capture; its
      question is inherently "what is X?".
   2. **Question-first (hard gate)** — write the `answers:` line BEFORE
      capturing, phrased as a person would actually ask it. Can't write
      one → drop the fact.
   3. **Cost-of-ignorance (tiebreaker)** — borderline survivor? Keep
      only if not knowing it would cause a wrong decision, a repeated
      question, or a broken process.
   4. **Metric guideline** — the fact is a measure value → capture the
      derivation (grain, source of truth, how to compute), NEVER the
      value: "how to derive Q2 refund totals" belongs in the corpus,
      "Q2 refunds totalled £46k" never does.
5. Per survivor, run write-documentation. Batch additions on top of the
   primitive:
   - Before minting any NEW entity name, `python validate.py --dupe
     "<name>"` — near-match in the registry → the capture takes the
     EXISTING canonical name (the primitive's merge rule); don't fork.
   - `source_rev:` mandatory when the source is code (commit SHA at
     extraction time). Every body claim must trace to a source line —
     no general-knowledge fill; can't cite it, leave it out.
   - Ambiguous or judgment-heavy fact → capture verbatim with the
     source quote; synthesize judges, extract doesn't.
   - Docs that contradict code: code wins for what-it-does; record the
     doc's why-claim with both sources cited and note the conflict for
     synthesize.
   - Predicated `relations:` only when the verb is stated verbatim in
     the source sentence — matching the phrasing of existing library
     edges does not count. (The primitive alone never writes relations;
     this is extract's one extension.)
6. `python validate.py --format` on every new file — fix all errors.
7. Open the PR touching ONLY `inbox/`: `backfill-wave` label, one domain
   per PR, ≤ ~25 files. Bigger sweep → multiple waves. The PR body
   carries:
   - the sources swept and the entities skipped as duplicates
     (auditable scope);
   - the GATE LOG — candidates captured vs dropped, each drop tagged
     with the prong that failed it. Filtering is reviewable, never
     silent.

## Rules

- A source document itself gets an entity (DOCUMENT/REPORT) only if
  it's asked for by name or has behavior worth explaining — default:
  citation only. A table or dataset people consume by name MAY get a
  REPORT entity documenting access, never values.
- This skill is for maintainers and backfill waves, not everyday use —
  a coworker with one fact wants write-documentation directly.
