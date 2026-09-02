# Schema

Names are join keys, so the vocabulary below is what `validate.py` checks
against. Adding a type or predicate is a one-line edit to this file — do it
when a real capture needs it, and say so in the session. Skills never invent
vocabulary silently.

## Header keys

| Key            | Required   | Notes                                                                 |
| -------------- | ---------- | --------------------------------------------------------------------- |
| title          | yes        | human title                                                           |
| entity         | yes        | canonical name, unique across library/                                |
| type           | yes        | one of the entity types below                                         |
| description    | no         | ONE line: definition + conditions (amounts, dates, windows). Never used for matching; it is what recall injects once the node is found |
| aliases        | no         | one per line: variants, former names, head nouns people actually say  |
| related        | no         | comma-separated canonical names — a plain link, no verb; anyone writes these |
| relations      | synthesize | "Subject predicate Object" — added when the VERB matters              |
| answers        | no         | 3-5 questions this file settles, phrased as people ask them           |
| provenance     | inbox: yes | where the facts came from, one entry per source: `repo:<name>/<path>` for a file in another repository (forward slashes, relative to that repo's root); a URL (`https://…`, `slack://<channel>/<date>-<who>` for verbal facts, `uc://catalog.schema.table`); or a path relative to this library. A local absolute path is accepted but flagged NEEDS WORK, since it won't resolve on anyone else's machine |
| provenance_rev | code: yes  | commit SHA when the source is code                                    |
| updated        | yes        | ISO date                                                              |

## Entity types

Core (any domain):

- CONCEPT — a domain thing (Redemption, Offer, Mana)
- PROCESS — an activity, workflow, or recurring step
- ROLE — a job function, never a person's name
- POLICY — a rule-bearing authority or mandate
- RULE_SET — a named collection of rules with IDs (RR-01)
- ENUM — a closed value list
- DECISION — a locked design or business decision and its why
- INVARIANT — a boundary or constraint the system must always hold
- DOCUMENT — a reference artifact people ask for by name
- REPORT — a recurring deliverable, dashboard, or query; documents access, never values
- DATA_ASSET — a named table or dataset people consume by name; the business of the asset, never its columns or values

Domain-specific (add freely, one line each):

- ADVERTISER — a client/brand that funds offers
- PUBLISHER — an FI or channel partner that hosts offers
- SKILL — a named ability a hero or unit can use
- HERO — a playable hero character
- GAME_MECHANIC — a rule of play (rolls, phases, bonuses, respawn)
- GAME_MODE — a top-level way to play
- TOOL — a checked-in dev harness or utility that is not part of the shipped product

## Predicates

Coworkers link with `related:`; synthesize upgrades a link to a predicated
relation when the verb matters (who approves, what blocks, what replaced
what). Direction matters; the definition here is normative.

- is_a — "X is_a Y": X is a kind of Y
- part_of — "X part_of Y": X is a component or attribute of Y. Also the membership verb: a hero's skill, a mode's mechanic, a phase of a loop
- requires — "X requires Y": X cannot exist or complete without Y
- receives — "X receives Y": Y is delivered or paid out to X — a client receives a report, a redemption receives a reward
- references — "X references Y": X cites or depends on information in Y
- owned_by — "X owned_by Y": role Y is accountable for X
- produces — "X produces Y": running X creates or refreshes Y (a pipeline and its table)
- consumes — "X consumes Y": X reads Y as an input
- applies_to — "X applies_to Y": rules or policy X govern Y
- constrained_by — "X constrained_by Y": Y limits or caps X
- approved_by — "X approved_by Y": role Y grants approval for X
- delegates_to — "X delegates_to Y": when X is unavailable, authority passes to Y (one per subject)
- escalates_to — "X escalates_to Y": unresolved X moves up to Y
- superseded_by — "X superseded_by Y": X is retired; Y replaces it (one per subject)

## Namespacing

Directory under library/ = domain. Entity names are unique across the whole
library. When two domains need the same word, qualify the name ("Bank
Offer") and keep the bare word as an alias in ONE file only.

A scoped variant — `<Thing> (<Client>)` — lives in the scope's folder (a
client's variant in that client's directory) and links `part_of` to the
general entity in its home domain. A scope with no material difference gets
no variant; the general entity is its answer.

## Bindings

An entity that denotes a system object (a table, a dashboard, a document)
lists that object's URI as its FIRST provenance entry:
`uc://catalog.schema.table`, `https://…`. A REPORT binds to the table or
dashboard it writes, not to the email or file it is delivered as; a
variant with no object of its own has no binding and inherits the
general report's. Inputs are not provenance; they are `requires` or
`consumes` edges to their own entities.
`build_index.py` exports that first URI as the `ref` column of
registry.tsv, so SQL can join the graph to the catalog.
