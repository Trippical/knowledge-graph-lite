# Text Library — governed markdown with a graph in the headers

Markdown files whose frontmatter carries graph structure (`entity`, `type`,
`aliases`, `related`, `relations`, `answers`, `provenance`). Two tiers,
four skills, five small stdlib scripts. No database.

The product is the CAPTURE CONTRACT: skills write files in this shape,
`validate.py` keeps them honest, `build_index.py` turns them into a flat
edge table. Anything can be built on top — the included recall and search
scripts are the starter read layer, and an embedding index or a real graph
DB can read the same files later.

## Layout

    SCHEMA.md          types, predicates, header keys — the vocabulary
    README.md          this file
    DECISIONS.md       one-page log of durable decisions and what was cut
    library/<domain>/  canonical tier — validated, graph-complete
    inbox/<domain>/    staging tier — captures awaiting synthesis
    .claude/skills/    write-documentation, scope, extract, synthesize, read-documentation
    .claude/settings.json  recall.py wired as a UserPromptSubmit hook
    kglib.py           shared parser
    validate.py        lint (--format one file, --dupe a name, or full)
    build_index.py     regenerates INDEX.md, registry.tsv (entity/type/file/aliases/ref), edges.tsv — never hand-edit
    search.py          ranked search over names, aliases, answers (pull path)
    recall.py          seed entities + walk edges.tsv (push path, hook)

## Lifecycle

1. **write-documentation** — one fact lands in `inbox/` in the right shape
   with `provenance:`. No dedupe, no linking. Minutes.
2. **scope** — read-only survey of a repo or doc set that produces the
   wave plan for a backfill. Only for sweeps bigger than one area.
3. **extract** — batch driver over write-documentation, one wave at a
   time: decompose, gate, capture.
4. **synthesize** — promotes `inbox/` to `library/`: dedupe against
   registry.tsv, canonicalize names, connect relations, reindex. Run per
   domain when its inbox exceeds ~8 files or its oldest capture is >14
   days; on a backfill, after every one or two waves.
5. **read-documentation** — `search.py` over both tiers; library hits are
   authoritative, inbox hits are flagged UNVERIFIED. `recall.py` runs
   automatically on every prompt via the hook.

Model split that has held up in testing: scope and synthesize on Opus,
extract and write-documentation on Sonnet.

## Quality floor

`validate.py` at 0 errors is the bar for `library/`. It checks: parseable
header, required keys, type and predicates from SCHEMA.md, every relation
and related endpoint resolves to a library entity, no duplicate or
near-duplicate names, no alias collisions, inbox files carry provenance.

## Principles

- **Access, not answers.** Never record a data value ("Q2 total was 5000").
  Record where and how to get it. Values go stale the moment they're written.
- **Code is evidence, not content.** Capture policy, ownership, and why.
  Point `provenance:` at the code with `provenance_rev:`. Classes and
  endpoints never get entities; the compiler already knows those.
- **Verb on the edge, conditions in the description.** `Refund approved_by
  Ops Manager` is the edge; "over £500" lives in the description line.
- **The alias rule.** `relations` and `answers` use canonical names only.
  Variants and former names live once, in `aliases`.
- **One entity per file.** `##` headings written as the questions they
  answer. Enumerations as tables. Stubs are legal — a minimal file that
  gives an edge endpoint a home beats a dangling edge.
- **Rename:** grep the old name, rewrite every mention, add the old name to
  `aliases:`, note it in a dated `## Name changes` section.
- **Remove:** never silently. Drop the edges, add `Old superseded_by New`,
  keep the name as an alias, state the removal and date in the body.
- **Correct:** a fact that turned out wrong is rewritten in place, and
  the change is logged under `## Supersessions` with the date, what was
  removed, and what replaced it. History stays readable; the entry stays
  true.
