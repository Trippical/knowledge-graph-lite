---
name: write-documentation
description: Record one fact, doc, policy, or update into the text library inbox in correct format. Lightweight capture only — no dedupe, no linking; synthesize does that later. Use when someone shares something worth remembering.
---

# Write documentation

Get information INTO the corpus cheaply. This is the capture primitive —
the only thing that writes inbox files. Extract drives it in batch; these
rules apply unchanged there.

## Steps

1. Check `registry.tsv` (entities and aliases) for the canonical name. A
   change to an existing entity is NOT a new entity — never mint
   "<X> Update"; file the fact under the existing name. No registry yet
   (fresh library)? Skip it — the inbox is the only thing to scan.
   List the inbox again right before writing: same topic already there?
   Append to that file, don't fork it. Never overwrite a file you did not
   create. Appending means adding a `##` section and extending the header
   lists; never rewrite someone else's prose. Found it wrong? Add the
   correction as its own section and let synthesize reconcile.
2. Fill the template — one file per entity at `inbox/<domain>/<slug>.md`.
   Type from SCHEMA.md. Don't know the domain? Use `inbox/_unsorted/`.
3. `related:` is canonical names, comma-separated, no verb. Names that so
   far exist only in inbox are fine — synthesize resolves them. Unsure of
   a name? Put the fact in body prose; synthesize connects it. Never write
   `relations:` from this skill.
4. `python validate.py --format inbox/<domain>/<slug>.md` — fix every error.

## Template

Keys marked optional are omitted entirely when unused — the parser treats
any text after a colon as the value, so never leave a comment there.

```markdown
---
title: <human title>
entity: <canonical name>
type: <one of SCHEMA.md § Entity types>
description: <one line — definition plus the conditions (amounts, windows)>
aliases:
  - <other names people use — optional>
related: <Entity, Entity — canonical names, no verb, optional>
answers:
  - <3-5 questions this settles, phrased as people ask them>
provenance:
  - <repo:<name>/<path> for a file in another repo; a URL, or slack://<channel>/<YYYY-MM-DD>-<who> for a verbal fact; or a path inside this library. One entry per source, never an absolute path>
provenance_rev: <commit SHA — only when the source is code>
updated: <YYYY-MM-DD>
---

# <title>

<the facts — why, who, gotchas; cite specifics. Never paste code or
enumerations; provenance points at them.>
```

## Rules

- **Access, not answers.** Never record a data value ("Q2 total was 5000").
  Record where and how to get it. Rule constants a question turns on (a
  cost, a threshold, a tick count) are facts, not values — state them and
  pin the revision. Measured results, totals, and test outcomes are values.
- **Provenance is portable.** `repo:<name>/<path>` for another
  repository's file, a URL, or a library-relative path — never an
  absolute path, which validate rejects. One entry per source, nothing
  appended: line numbers and function names go in the body.
- **Code is evidence.** Capture policy, ownership, and why-facts; point
  `provenance:` at the code. A class's API surface never gets an entity;
  a mechanism with rules of its own (a spatial index's work cap, a
  scheduler's stagger, a resolution chokepoint) is a CONCEPT like any
  other — document the rule, not the fields. A
  named table or dataset people query MAY get a DATA_ASSET entity — its
  purpose, grain, cadence, gotchas — never its columns or values.
- **A document gets its own entity** (DOCUMENT / REPORT / DATA_ASSET) only
  if people ask for it by name or it has behaviour worth explaining.
  Otherwise it's a citation, and its facts fan out to the entities they're
  about.
- **Intersections are their own entity.** One scope's version of a general
  thing (a client's variant of a report, a hero's spell) IS its own entity
  when it carries its own facts. Name it `<Thing> (<Scope>)` where the
  general name would otherwise collide, give it the general thing's type,
  and link `related:` to BOTH parents. Never fold it into the general file.
  A one-paragraph difference stays a `## <Scope>` section in the general
  file instead.
- **Minutes, not judgment.** If it needs judgment, capture the raw fact
  verbatim with the source quote and let synthesize judge.
