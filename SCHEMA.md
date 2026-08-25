# Schema — closed vocabulary

The join keys of this system are strings, so everything here is CLOSED.
Adding a type or predicate requires a PR to this file, acked by the schema
owner. Skills never invent vocabulary — a fact that fits no predicate goes
in body prose plus a `proposed_predicate:` header line (the governance queue).

## Header keys

| Key                | Required   | Notes                                                                               |
| ------------------ | ---------- | ----------------------------------------------------------------------------------- |
| title              | yes        | human title                                                                         |
| entity             | yes        | canonical name, unique across library/                                              |
| type               | yes        | from Entity types below                                                             |
| description        | no         | ONE tight line: definition + conditions (amounts, dates, windows, "together with X"). NEVER used for matching — aliases find the node; description is what it says once found. Must not repeat what name/aliases/answers already carry. Injected by recall.py; exported as the warehouse description column |
| aliases            | no         | one per line; variants and former names                                             |
| related            | no         | comma-separated canonical entity names — a plain link, no verb; anyone writes these |
| relations          | librarian  | "Subject predicate Object" — synthesize adds these where the verb matters           |
| answers            | no         | 3-5 max, canonical names only                                                       |
| source             | inbox: yes | provenance path or URL, one per line. When synthesize merges facts from several captures, keep one source line per capture so "says who?" stays answerable |
| valid_from         | no         | ISO date — when a time-bounded fact starts holding (delegation window, decision)    |
| valid_to           | no         | ISO date — when it stops. Supersede, never delete; expired facts stay for history   |
| source_rev         | extracted  | commit SHA or doc revision at extraction                                            |
| proposed_predicate | no         | vocabulary proposal for the schema owner                                            |
| updated            | yes        | ISO date                                                                            |

## Entity types

Each type is grounded in a published standard, or declared home-grown with
the reason stated. The grounding travels with every extraction call — it is
what stops note-by-note schema drift once backfill waves start.

- CLIENT — a specific client/customer organization (Acme Ltd). Grounded: schema.org/Organization (customer role)
- SUPPLIER — a specific supplier/vendor organization. Grounded: schema.org/Organization (supplier role)
- REPORT — a recurring deliverable, dashboard, query, or data asset. Grounded: schema.org/Dataset (loosely; home-grown because it also covers queries and dashboards). A REPORT documents access — grain, cadence, how to derive the numbers people ask for — never the measure values it contains
- CONCEPT — a domain thing (Refund, Invoice). Grounded: SKOS skos:Concept
- ROLE — a job function, never a person's name. Grounded: schema.org/Role
- PROCESS — an activity or workflow step. Grounded: schema.org/Action (loosely; home-grown because our processes are recurring, not single acts)
- POLICY — a rule-bearing authority or mandate. Home-grown: no schema.org equivalent carries the "grants authority" sense we need
- RULE_SET — a named collection of business rules. Home-grown: closest is skos:Collection, but members are rules with IDs (RR-xx), not concepts
- ENUM — a closed value list. Grounded: schema.org/Enumeration
- DOCUMENT — a reference artifact. Grounded: schema.org/DigitalDocument

## Predicates

Librarian tier only: coworkers link with `related:`; the synthesize skill
upgrades a related-link to a predicated relation when the VERB matters
(who approves, who backs up whom, what blocks launch).
Direction matters; the definition here is normative. High-risk predicates
(⚠) require a named human ack in the PR body when added or redirected.

- is_a — "X is_a Y": X is a kind of Y
- part_of — "X part_of Y": X is a component or attribute of Y
- requires — "X requires Y": X cannot exist or complete without Y
- receives — "X receives Y": Y is produced or paid out as part of X
- references — "X references Y": X cites or depends on information in Y
- applies_to — "X applies_to Y": rules or policy X govern Y
- constrained_by — "X constrained_by Y": Y limits or caps X
- approved_by — ⚠ "X approved_by Y": role Y grants approval for X
- delegates_to — ⚠ "X delegates_to Y": when X is unavailable, X's authority passes to Y
- escalates_to — "X escalates_to Y": unresolved X moves up to Y
- superseded_by — ⚠ "X superseded_by Y": X is retired; Y replaces it

## Namespacing

Directory under library/ = domain (library/ops/, library/clients/,
library/code/). Entity names are unique across the WHOLE library. When two
domains need the same word (Invoice for clients vs suppliers), qualify the
entity name ("Supplier Invoice") and keep the bare word as an alias in ONE
file only.
