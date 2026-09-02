# Decisions

One page. Add a dated line when something durable is decided; delete lines
that stop being true.

## 2026-09-01 — simplification (this project created)

Rebuilt from `../knowledge_graph/text_library/` with the governance and
speculative machinery removed. The old project is untouched; anything below
can be pulled back from there.

**Kept:** the file format, the four skills, validate / build_index / search
/ recall, the recall hook, all library and inbox content.

**Cut, and why:**

- PR policy, CODEOWNERS, backfill-wave labels, human-ack rules — there is
  no git repo and no team; the skills now say "validate, then save".
- Variants (hub/spoke, `variant_of`, scope tests in three skills) — zero
  instances in the corpus. Model a variant as its own entity with a
  `related:` link to the hub when one actually appears.
- `ref:`, `valid_from`, `valid_to`, `proposed_predicate`, `proposed_type`
  header keys — zero or near-zero use. The four inbox files that carried
  `valid_from` now state the date in the body.
- Closed-vocabulary governance — two thirds of the rts domain needed the
  `proposed_type` escape hatch. Types are still listed in SCHEMA.md and
  linted, but adding one is a one-line edit, not a proposal queue.
  Applied: GAME_MECHANIC, HERO, GAME_MODE, DECISION, INVARIANT added and
  the 17 proposals resolved (PROGRESSION stayed RULE_SET, SAVE_SLOT stayed
  CONCEPT).
- Gold suites and the test runner — opt-in was already the ruling; opt-in
  files nobody runs are clutter.
- Databricks projection (`publish_delta.py`), staleness checker, CI and
  CODEOWNERS samples, the databricks-port skill copy — none wired, one
  admitted to drifting.
- The 607-line modification queue, proposals, specs, and session logs —
  collapsed into this page.

## 2026-09-01 — dry run of the stripped skills on the game (rts)

Fresh project `../knowledge_graph_dryrun/` (this framework, empty
library). Four cold extract agents + one cold synthesize agent, same four
areas as wave 1, source repo at f521070. Result: 35 entities, validate
0/0, 41 predicated edges. Score 29/29 — the intersection example (Raise
Dead is a SKILL, part_of Necromancer, requires Mana; Necrobolt and Mana
captured on their own) passed at both the inbox and library stage; all 26
wave-1 entities recaptured (14 under different names); all 15 primer
questions answered by recall or search.

Fixes applied from the agents' "where the skill was unclear" lists:

- Template had inline `# optional` comments that the parser reads as
  values — template now shows bare keys and includes `description:`.
- Empty library: registry and `--dupe` are no-ops until something is
  promoted. write-documentation, extract, synthesize now say so.
- Parallel extract agents on one domain overwrote each other's file.
  Extract: one run per domain at a time; write-documentation: re-list the
  inbox right before writing, never overwrite a file you didn't create.
- Gate gained prong 0 `scope`; "capture" defined (own file vs section).
- Rule constants (a cost, a DC) are facts; measured results are values.
- Synthesize: `part_of` is the default verb for a scoped instance;
  upgrading a link replaces it; every promoted entity gets a description;
  fix warnings before promotion.
- recall.py: within a hop, verb edges come before plain links — a
  generic seed word ("cost") was crowding the spell edges out of the cap.

## 2026-09-01 — the same dry run on Sonnet and Opus

Two more fresh projects (`../knowledge_graph_dryrun_sonnet/`,
`../knowledge_graph_dryrun_opus/`), same four areas, run sequentially per
the updated extract skill, one cold synthesize each. Same scorer.

| | Fable (parallel) | Sonnet | Opus |
|---|---|---|---|
| score | 29/29 | 29/29 | 29/29 |
| entities | 35 | 30 | 33 |
| verb edges after synthesize | 41 | 15 | 33 |
| validate warnings left | 0 | 50 | 0 |
| doc-vs-code conflicts found | 17 | 3 | 20 |
| Necromancer handled on append | overwritten | appended | appended + reconciled |

Hybrid run (`../knowledge_graph_dryrun_hybrid/`, Sonnet extract on the
fully fixed skills, Opus synthesize): 29/29, 29 entities, 37 verb edges +
19 plain (the leanest graph of the four), 0 warnings at every stage, 4
doc-vs-code conflicts. Sonnet's extract quality gap closed once the
validator showed it warnings and the skill said provenance is a bare
path — the earlier 79 warnings were a tooling gap, not a model gap.

Reading: all three tiers pass the floor. Sonnet captures correctly but
connects less and left provenance paths annotated with line numbers (its
validate copy predated the warnings fix, so it never saw them). Opus
matched Fable on structure and found the most doc-vs-code drift. For
pricing: Sonnet for write-documentation and extract, Opus for synthesize.

Fixes applied from these two runs: `--format` mode now shows warnings;
`--dupe` says "no candidates" on an empty library; provenance must be a
bare path (line notes go in the body); extract never writes `relations:`;
appending to another agent's file means new sections only; synthesize
removes the mirror link on upgrade, files supersessions under
`## Supersessions`; `part_of` blessed as the membership verb in SCHEMA.md.

## 2026-09-02 — full-game run (Sonnet extract, Opus synthesize)

Fifth project `../knowledge_graph_dryrun_full/`: a Sonnet scoping survey
proposed 17 waves covering the whole repo; each wave was one Sonnet extract,
with an Opus synthesize after every two waves (8 passes), so every pass
after the first promoted into a non-empty library.

Result: 133 entities, 421 edges (239 verb, 182 plain), 12 types, validate
0/0 at every one of the 25 stages, inbox empty. Standard scorer 27/29 —
both misses are scorer artifacts (a regex hit on "Change" in "Where A
Change Belongs"; "melee hit resolved" shares no token with "Opposed Attack
Roll"). Synthesize handled 4 name collisions by rename+alias, moved 2
misplaced aliases, filed 2 open questions instead of guessing, and cleaned
up 6 double-linked pairs left by the first pass. ~20 doc-vs-code drifts
recorded across waves. One Opus rate-limit retry, no data loss.

Framework fixes that came out of it (all applied here):

- validate.py now warns on near-duplicate captures WITHIN the inbox —
  two same-wave names at 0.875 were invisible until promotion.
- write-documentation: a class's API never gets an entity, but a mechanism
  with rules (spatial hash work cap, scheduler stagger) is a CONCEPT.
- synthesize: two real entities whose names merely collide → rename the
  newcomer, alias the old name; plain links are one per pair too.
- SCHEMA.md: TOOL type (a checked-in dev harness, not shipped game).

Scoping comparison (same prompt, read-only): Sonnet 17 waves / 2
stale-doc notes; Opus 22 / 11; Fable 23 / 17. Sonnet's plan misstated a
rule count (a–g vs the real a–e) and never pointed wave 14 at
BattlePlanner, so the corpus's Army Shop entry repeats a stale doc claim
that Fable's plan had flagged (squad Level DOES fold into stats via
ApplyTraining). Decision: scoping is now its own skill (`scope`), run on
Opus; extract stays on Sonnet. Loose end: fix army-shop.md's Level
paragraph in the full corpus.

2026-09-02, provenance made portable: entries are `repo:<name>/<path>`
(another repository, forward slashes, relative to its root), a URL, or a
library-relative path. Absolute paths are accepted but flagged NEEDS WORK
(a warning, not an error — softened the same day; the forms are a
recommendation, not a gate). 137 entries
across v2 migrated; the full corpus migrated too (491 entries). Existence
is checked only for library-relative paths.

Still open, deliberately (add when a real capture needs it): a `triggers`
predicate, a sequencing predicate (Draft → Shop → Muster can only be
prose), and which rule wins when the edge's subject file isn't the file
whose body explains the edge.

## Durable principles that survived (see README § Principles)

Access not answers; code is evidence; verb on the edge, conditions in the
description; the alias rule; question-first gate in extract; park-then-
decide before minting a stub; `slack://` for verbal provenance; never mint
"<X> Update" entities.
