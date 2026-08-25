# Knowledge Graph Lite — governed file memory

Connectors turn unstructured information into governed markdown; a
human-gated synthesis step compacts it into a canonical corpus; pluggable
read layers sit on top. No database in the core — flat files and small
stdlib scripts. The corpus is the interface.

    CONNECTORS            GATE                CORPUS              READ LAYERS
    (in: any source)      (judgment)          (the product)       (out: pluggable)

    human ──────────┐
    docs/code ──────┼─► inbox/<domain>/ ─► synthesize ─► library/<domain>/
    threads* ───────┘    formatted .md,     dedupe,        canonical, graph-
                         UNVERIFIED but     canonicalize,  complete, tested
                         queryable          connect            │
                                                               │ projections
                              SCHEMA.md + validate.py          ├─ edges.tsv / registry / INDEX
                              govern every arrow               ├─ kg_entities / kg_edges (Delta)
                                                               └─ embeddings table*
                                                               │
                                            ┌──────────────────┼────────────────┐
                                            ▼                  ▼                ▼
                                      layers/graph-lite   layers/delta     RAG / MCP*
                                      recall + search     SQL / BI         (bring your own)
                                                                     * = planned

Three rules make the decoupling real:

1. **The corpus is the interface.** Layers read `library/`, `inbox/`, and
   projections; nothing downstream ever writes the corpus or bypasses
   SCHEMA.
2. **Connectors are cheap plugins.** New source system → new connector
   emitting valid inbox markdown (see CONNECTORS.md). The core never
   changes.
3. **Each read layer ships its own read skill and gold runner.** The gold
   tables (`library/<domain>/GOLD.md`) are layer-independent; proving
   they pass is each layer's job.

## Layout

    SCHEMA.md            closed vocabulary: types, predicates, header keys — the law
    CONNECTORS.md        the connector contract (in-flow)
    connectors/          write-documentation (human), extract (docs/code) — SKILL.md each
    inbox/<domain>/      staging tier — captures awaiting synthesis
                         (inbox/ops/ holds one worked sample capture)
    gate/synthesize/     the ONLY path inbox → library (strong model + human)
    library/<domain>/    canonical tier — validated, graph-complete
    library/<domain>/GOLD.md  machine-parsed acceptance table, written once per domain
    kglib.py             shared parser (core)
    validate.py          deterministic lint — the CI gate (core)
    build_index.py       projection: INDEX.md + registry.tsv + edges.tsv (generated, never hand-edited)
    staleness_check.py   projection freshness: source_rev vs HEAD
    tests/test_gold.py   gold runner for the graph-lite layer + governance invariants
    layers/graph-lite/   starter read layer: recall.py (push), search.py (pull), read skill
    layers/delta/        optional warehouse mirror: publish_delta.py (parameterized), ported write skills
    ci/kg.yml.sample     GitHub Action: validate + gold on every PR
    CODEOWNERS.sample    domain ownership for the governed dirs

The demo corpus in `library/ops/` models a small company's operations —
refund approvals, delegation cover, onboarding, supplier payments,
incident response.

## Hook wiring (push recall)

Add to `.claude/settings.json` (or your agent's prompt-hook equivalent):

    {
      "hooks": {
        "UserPromptSubmit": [
          { "hooks": [ { "type": "command",
              "command": "python <libdir>/layers/graph-lite/recall.py --hook" } ] }
        ]
      }
    }

## Lifecycle (journal + compaction)

1. **Capture** (any connector, cheap): facts land in `inbox/` in correct
   format with `source:` provenance. Format-linted, PR'd, merged fast.
   No dedupe, no linking — comprehension is deferred.
2. **Synthesize** (the gate — strong model + human, on cadence): promotes
   inbox → `library/` — dedupes against registry.tsv, canonicalizes
   names, connects relations, files vocabulary proposals, and ALWAYS ends
   by reindexing. Inbox depth is the health metric: if it grows faster
   than the cadence drains it, raise the cadence.
3. **Read** (any layer): the starter layer searches both tiers; library
   hits are authoritative, inbox hits are flagged UNVERIFIED.

## Validation gates

`validate.py` runs in CI on every PR:

- inbox files: parseable header, required keys, `source:` present, type and
  predicates from SCHEMA.md (format mode — cheap, never blocks captures long).
- library files: all of the above plus referential integrity (every relation
  endpoint resolves to a library `entity:`), global entity uniqueness,
  near-duplicate detection, alias-collision warnings.

INDEX.md and registry.tsv are generated from library/ only (so capture
PRs never touch them); `validate.py` full mode fails if the committed
copies differ from regenerated ones. `tests/test_gold.py` then runs every
gold-table row through the active read layer. Copy `ci/kg.yml.sample`
into `.github/workflows/` and `CODEOWNERS.sample` into CODEOWNERS to make
every gate mechanical — without them this section is prose.

## Gold tables

Each domain owner writes `library/<domain>/GOLD.md` ONCE, before the
domain is modeled: a machine-parsed table of questions, expected
substrings, and source files — the domain's acceptance test, written by
someone who didn't build the corpus. CI executes every row from then on
(adding a test = adding a row); post-launch, the read layer's loud-fail
misses become the real regression queue.

## PR policy

- Capture PRs (any connector): touch only `inbox/`. Fast merge.
- Synthesize PRs (steady-state): one merge decision each, ≤ ~10 entities,
  domain-owner review via directory CODEOWNERS. High-risk predicate (⚠)
  changes need a named human ack in the PR body.
- Backfill waves (initialization): exempt from the entity cap via the
  `backfill-wave` PR label. One PR per domain wave, gated on the domain's
  gold table, runner output pasted in the PR body. Each wave is a single
  squashable PR so `git revert` is surgical.

## The alias rule

`relations` and `answers` use canonical entity names only; variants and
former names live once, in `aliases`. A grep hit on any header line lands
in the right file, so one alias covers every question and edge in it.

## Renames and removals

Names are join keys, so name changes follow protocol:

**Rename:** grep the old name (the hit list IS the migration plan); rewrite
every header line and body mention — never mix old and new in headers; add
the old name to `aliases:` in the entity's home file; note the change in a
dated `## Name changes` section. `validate.py` catches any edge left behind.

**Removal:** never silent-delete. Drop the entity's edges, add a succession
edge (`Old superseded_by New`), keep the name as an alias, state removal +
date + successor in the body. Hard-delete only when the loud-fail log shows
nobody asks anymore.

## Scope rule for code sources

Code is EVIDENCE for policy, ownership, and why-facts — never transcribe
code structure. Classes and endpoints never get entities (LSP and the
compiler already know those, and they never go stale). A table or dataset
people consume by name may get a REPORT entity documenting access — grain,
cadence, how to derive the numbers people ask for — never the values
themselves. Point `source:` + `source_rev:` at the code. (Planned, not yet
built: a CI job diffing `source_rev` against HEAD to flag stale entities —
required before any code-derived backfill wave.)

## File format rules

- One entity per file; `##` headings written as the questions they answer.
- Enumerations as tables; rule conditions inline with stable IDs (RR-01).
- Facts stated once; cross-reference by rule ID or file link.
- Stub entities are legal and encouraged — a minimal file that gives an
  edge endpoint a home beats a dangling edge.

## Credits

The graph-headers-in-markdown approach, the push-recall hook pattern, and
the demo corpus scenario derive from
[Glitch-Cat-Club/graph-memory-starter](https://github.com/Glitch-Cat-Club/graph-memory-starter)
(MIT) and its companion articles. The connector/layer separation is
inspired by the plugin-connector architecture described in Cerebras's
"How we built our knowledge base." This repo generalizes both into a
governed two-tier library: closed schema, connector contract, human-gated
synthesis, deterministic validation, gold-table testing, and pluggable
read layers.
