---
name: extract
description: Batch-distill sources (docs, code, wikis, SQL) into inbox captures by driving write-documentation once per gated fact. Use for backfilling a domain; NOT for a single fact someone just told you (that's write-documentation).
---

# Extract (batch driver over write-documentation)

Extract owns NO capture rules. It decomposes sources into candidate facts,
gates them for usefulness, and runs write-documentation once per survivor.
Output goes to `inbox/` only; synthesize is the only path to `library/`.

Scripts run as `python <script>.py` from the corpus root. Installed as the
plugin, they live at `${CLAUDE_PLUGIN_ROOT}/` and the corpus is `$KG_ROOT`.

## Steps

1. **Scope first.** Agree the sweep with the user: which paths or docs,
   which domain, roughly how many entities. For anything bigger than one
   area, the scope skill produces that plan and each wave is one extract
   run. The plan's starting files are a floor: follow live threads into
   files they cite. No open-ended crawling. Running
   unattended? Self-scope conservatively — curated docs only, never
   generated artifacts or logs — and mark the scope UNCONFIRMED in the
   report. One extract run per domain at a time: parallel agents writing
   into the same inbox folder overwrite each other. If a sweep must be
   split, split it by domain folder.
2. Read SCHEMA.md and the write-documentation skill. A fact whose natural
   type is missing from SCHEMA.md gets the closest existing type; note the
   missing type in the report so the user can add it.
3. **Decompose** each source into candidate facts: term definitions,
   why-decisions, ownership, grain, gotchas, access and derivation info.
   Never copy code, column lists, or enumerations — provenance points at
   them.
4. **Run the gate** on every candidate, in order:
   0. *Scope* — outside the agreed sweep → drop, tagged `scope`, before
      the gate runs. Note it as a candidate for a later wave.
   1. *Key term* — the source DEFINES a domain term → capture. "Capture"
      means its own file when the term carries facts of its own; a
      one-paragraph term becomes a `##` section of its parent. A scope's
      version of a general thing that the source says does not differ is
      not a candidate at all — log it as "no variant", mint nothing.
   2. *Question-first (hard gate)* — write the `answers:` line BEFORE
      capturing, phrased as a person would ask it. Can't write one → drop.
   3. *Cost of ignorance (tiebreaker)* — borderline? Keep only if not
      knowing it would cause a wrong decision, a repeated question, or a
      broken process.
   4. *Metric guideline* — the fact is a measure value → capture the
      derivation (grain, source of truth, how to compute), never the value.
5. **Per survivor, run write-documentation**, with these batch additions:
   - Before minting any NEW name, `python validate.py --dupe "<name>"`. A
     near-match in the registry means the capture takes the existing
     canonical name. An empty result on a fresh library is a pass — the
     inbox listing is then the only dedupe surface.
   - `provenance_rev:` (commit SHA) is mandatory when the source is code.
     Every body claim traces to a source line — no general-knowledge fill.
   - Ambiguous or judgment-heavy fact → capture verbatim with the source
     quote; synthesize judges, extract doesn't.
   - Docs that contradict code: code wins for what-it-does; record the
     doc's why-claim with both sources cited and flag the conflict.
   - Never write `relations:`, even in batch. Link with `related:`; the
     verbs are synthesize's step.
6. `python validate.py --format` on every new file — fix all errors.
7. **Report the gate log** to the user: sources swept, entities skipped as
   duplicates, candidates captured vs dropped with the prong that failed
   each drop. Filtering is reviewable, never silent. Keep a wave to one
   domain and ≤ ~25 files; bigger sweeps run as multiple waves.
