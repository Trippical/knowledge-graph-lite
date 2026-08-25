---
name: kg-synthesize
description: Cadenced compaction — promote inbox captures into library/, dedupe, canonicalize, connect, then reindex. Run per-domain when its inbox exceeds ~8 files OR its oldest capture is >14 days old. Strong model, human PR partner.
---

# Synthesize (compaction)

The ONLY path from `inbox/` to `library/`. Partner with a human reviewer.

## Steps

1. `python build_index.py`; read INDEX.md and registry.tsv (entity, type, file).
2. For each inbox file, run `python validate.py --dupe "<entity name>"` —
   a deterministic top-10 similarity lookup against the registry (never
   eyeball the full registry for dedupe). Then decide:
   - New entity → promote to `library/<domain>/`.
   - Existing entity → merge facts into the canonical file. Conflicting
     values: newer source wins; record the supersession in the body with date.
   - Near-duplicate names → merge to one canonical; losers become aliases.
3. Connect: upgrade `related:` names to predicated relations where the
   VERB matters (approval, delegation, requirement, supersession); keep
   plain related-links otherwise. Every relation/related endpoint must
   resolve — but stub creation is a CHECKED decision, never automatic
   (park, then decide): an unknown name has four resolutions and only one
   of them is a new entity. Before minting any stub, run
   `python validate.py --dupe "<name>"` and triage with your human partner:
   - alias of an existing entity → add the alias, no new file;
   - typo/variant → fix the name at the capture site;
   - noise (not a real durable thing) → drop it;
   - genuinely new → create the stub, noting the human confirmation
     in the PR body.
4. Vocabulary: collect `proposed_predicate:` lines into a separate SCHEMA.md
   PR for the schema owner. Never merge content using unapproved predicates.
5. Renames and removals: follow README § Renames and removals
   (grep-migration, old name becomes alias, tombstone + superseded_by).
6. `python validate.py` — zero errors required; triage every warning.
7. **Reindex — always the last step:** `python build_index.py`, commit the
   regenerated INDEX.md and registry.tsv.
8. Open the PR:
   - Steady-state: one merge DECISION per PR, ≤ ~10 entities.
   - Backfill waves are exempt from the cap (add the `backfill-wave` PR
     label): one PR per domain wave, gated on the domain's committed
     gold-question suite (`library/<domain>/GOLD.md`, 10-20 owner-written
     questions; write them BEFORE modeling the domain) — paste each
     question's recall.py/search.py output in the PR body so pass/fail is
     visible, not asserted. Every answer must cite its source line or it
     doesn't count. Questions written before real users exist are marked
     `primer` — a failing primer question is a modeling to-do, a failing
     real-user question is a fire.

## Rules

- High-risk predicates (⚠ in SCHEMA.md) added or redirected → named human
  ack in the PR body.
- Delete inbox files only in the same PR that promotes their content.
- Cross-domain merges → separate PRs so both CODEOWNERS see them.
