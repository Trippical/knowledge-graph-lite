---
name: synthesize
description: Promote inbox captures into library/ — dedupe, canonicalize, connect relations, then reindex. Run per domain when its inbox exceeds ~8 files or its oldest capture is >14 days old. Work with the user on judgment calls.
---

# Synthesize (compaction)

The ONLY path from `inbox/` to `library/`. Scripts run as
`python <script>.py` from the corpus root; installed as the plugin, they
live at `${CLAUDE_PLUGIN_ROOT}/` and the corpus is `$KG_ROOT`.

## Steps

1. `python build_index.py`, then read INDEX.md and registry.tsv. On a
   fresh library these are empty and `--dupe` finds nothing until
   something is promoted: promote the first batch, rebuild the index, and
   run the dedupe sweep against that. Interim rebuilds are fine; only the
   LAST step must be a rebuild.
2. For each inbox file, `python validate.py --dupe "<entity name>"` — a
   deterministic top-10 similarity lookup. Then decide:
   - New entity → promote to `library/<domain>/`.
   - Existing entity → merge facts into the canonical file. Conflicting
     values: newer source wins. Rewrite the stale sentences so the entry
     states the current rule; record what was removed, what replaced it,
     and what still holds under `## Supersessions` as
     `**YYYY-MM-DD — one-line headline.**` plus prose. Add the new
     sources to `provenance:`; keep a superseded source only if it still
     backs other content in the entry. A merge may justify a brand-new
     verb edge, and may touch a second library file to add it — that is
     still one merge decision.
   - Near-duplicate names → merge to one canonical; losers become aliases.
     If both are real, distinct things whose names merely collide
     ("Shipped Unit Roster" vs "Shipped Item Roster"), rename the
     newcomer to something the lint won't flag, keep the old name as its
     alias, and note it under `## Name changes`.
   - EXCEPTION: a capture scoped to one client, hero, or region's version
     of a general entity is its OWN entity, not a merge — and two such
     siblings are not duplicates of each other. Promote it with
     `part_of` → the general entity (the default verb for a scoped
     instance) and `related:` → the scope it belongs to, and put what
     differs in its body.
   - Keep one provenance entry per source so "says who?" stays answerable.
3. **Connect.** Upgrade `related:` names to predicated `relations:` where
   the VERB matters (approval, delegation, requirement, supersession);
   keep plain links otherwise. An upgrade REPLACES the name in `related:`
   — one link, one edge — and removes the mirror link from the other
   entity's file too; recall walks edges both ways, so nothing is lost.
   The relation line lives in the subject's file. Plain links are one per
   pair too: keep the one in the file whose body explains the connection
   and drop the mirror, so recall's triple cap isn't spent on echoes. Put
   the verb on the
   edge and the condition
   (amount, window) in the `description:` line, and give every promoted
   entity a `description:` — recall injects it, and it is where the
   conditions live. Fix warnings (long descriptions, >5 answers) before
   promoting; don't carry them into the library.
4. **Unknown names: park, then decide.** Every endpoint must resolve, but
   a stub is a checked decision, never automatic. An unknown name has four
   resolutions, and only one is a new entity. Run `--dupe` on it and ask
   the user when unsure:
   - alias of an existing entity → add the alias, no new file;
   - typo or variant → fix the name at the capture site;
   - noise (not a real durable thing) → drop it;
   - genuinely new → create a stub file.
5. A capture that needs a type SCHEMA.md lacks → add the type to SCHEMA.md
   (one line) and tell the user. Never leave a file on a wrong type to pass
   lint.
6. Renames and removals follow README § Principles: grep the old name,
   old name becomes an alias, removal gets a `superseded_by` edge.
7. `python validate.py` — zero errors required; read every warning.
8. **Reindex, always last:** `python build_index.py`.

## Rules

- Delete an inbox file only in the same pass that promotes its content.
- Keep a pass to one domain and ≤ ~10 entities per merge decision so the
  user can review it. Backfill waves are the exception: one pass per wave.
- Summarize what was promoted, merged, aliased, and stubbed at the end.
