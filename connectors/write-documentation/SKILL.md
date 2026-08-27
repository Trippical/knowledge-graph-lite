---
name: write-documentation
description: Add new knowledge to the knowledge library inbox in correct format — lightweight, no synthesis. Use when someone shares a fact, doc, policy, or update worth recording.
---

# Write documentation

Get information INTO the corpus cheaply. No dedupe, no linking, no
comprehension — that's the synthesize skill's job, on its own cadence.

This skill is the capture PRIMITIVE — the only thing that writes inbox
files. Other connectors (extract, future thread-summarize) drive it in
batch, one run per gated fact; its rules apply unchanged there.

## Steps

1. Fill the template below — one file per entity, saved to
   `inbox/<domain>/<slug>.md`. Types come from SCHEMA.md § Entity types;
   never invent vocabulary. Add `provenance_rev:` (commit SHA) when the
   source is code. Don't know the domain? Use `inbox/_unsorted/` —
   synthesize will file it.
2. Link related entities with `related: Name, Name` — canonical names,
   comma-separated, no verb. Unsure of the canonical name? Put the fact
   in body prose instead — synthesize will connect it. Never write
   `relations:` from this skill; predicated edges are the librarian's job.
3. Run `python validate.py --format inbox/<domain>/<file>.md` — fix errors.
4. Open a PR touching ONLY `inbox/`. Never edit `library/` from this skill.

## Template

```markdown
---
title: <human title>
entity: <canonical name — check registry.tsv first>
type: <one of SCHEMA.md § Entity types>
aliases: # optional — other names people use
  - <name>
related: <Entity, Entity> # optional — canonical names, no verb
answers: # optional, 3-5 — questions this settles, as people ask them
  - <question>
provenance: <path or URL — required; verbal/chat fact: slack://<channel>/<YYYY-MM-DD>-<who>; several sources: YAML list ("- " entries under one provenance: key)>
ref: <optional — one URI for the system object this entity IS (e.g. uc://catalog.schema.object); DATA_ASSET/REPORT/DOCUMENT only. Provenance says where you learned it; ref says what it is>
updated: <YYYY-MM-DD>
---

# <title>

<the facts — why, who, gotchas; cite specifics. Never paste code or
enumerations; provenance: points at them.>
```

## Does the document itself get an entity?

Default NO — a document is a citation (`provenance:`), not an entity; its
factoids go to the entities they're about. File it (DOCUMENT, REPORT, or
DATA_ASSET for a table/dataset) only if people ask for it by name
("where's the Acme runbook?") or it has behavior worth explaining
(cadence, grain, lag, gotchas — reports, queries, dashboards, tables).
Even then the file describes the document; the factoids inside still fan
out.

## Rules

- Code sources: extract policy, ownership, and why-facts only. Classes and
  endpoints never get entities — point `provenance:` at them. A named table
  or dataset people query MAY get a DATA_ASSET entity: document the business
  of the asset (purpose, grain, cadence, how to derive), bind it with
  `ref:` (e.g. `uc://catalog.schema.object`), never copy its columns or the
  values inside it.
- Access, not answers: never record data values ("Q2 total was 5000") —
  record where and how to get them. Values go stale the moment they're
  written; the corpus holds the map, the data holds the numbers.
- A change to an existing entity is NOT a new entity — never mint
  "<X> Update" or "<X> Change". Check registry.tsv (aliases included) and
  file the fact under the existing canonical name.
- Same topic already sitting in inbox? Append to that file, don't fork it.
- This should take minutes. If it needs judgment, capture the raw fact
  verbatim and let synthesize judge.
