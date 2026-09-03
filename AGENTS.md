# Working in this repo (any agent: Claude Code, GitHub Copilot, OpenCode, Codex)

This is a text library: markdown files whose frontmatter carries graph
structure (entity, type, aliases, related, relations, answers, provenance).
`library/` is canonical; `inbox/` is staging. `SCHEMA.md` is the vocabulary;
`README.md` explains the lifecycle; `DECISIONS.md` is the log.

## Skills

Five skills live in `.claude/skills/<name>/SKILL.md`. Copilot CLI and
OpenCode discover that folder natively; if your tool doesn't, read the
file for the task at hand before starting.

| Task | Skill |
| --- | --- |
| Someone tells you one fact worth keeping | write-documentation |
| Plan a backfill of a repo or doc set (read-only) | scope |
| Backfill one area from docs or code | extract |
| Promote inbox captures into the library | synthesize |
| Answer a question about a modeled domain | read-documentation |

## Before answering a domain question

Claude Code injects graph context automatically through a hook. Copilot
CLI has a prompt hook too, but config-file hooks have their output
dropped, so it can't feed the model; OpenCode's plugin hook for this is
experimental. In those tools, run it yourself first:

    python recall.py "<the question>"      # graph walk, ~8 triples
    python search.py "<the question>"      # ranked search, both tiers

If both miss, say the library has no entry. Never answer a modeled-domain
question from general knowledge without saying so.

## Scripts

Run from the repo root (or set `KG_ROOT` to the corpus root):

    python validate.py                     # full lint; 0 errors is the bar
    python validate.py --format <file>     # one inbox file
    python validate.py --dupe "<name>"     # near-duplicate lookup before minting a name
    python build_index.py                  # regenerate INDEX.md, registry.tsv, edges.tsv — never hand-edit those

## Rules that matter most

- Never record a data value; record where and how to get it.
- One entity per file; a change to an existing entity is not a new entity.
- Provenance on every inbox capture: `repo:<name>/<path>`, a URL, or a
  library-relative path. Never paste secrets.
- Only synthesize writes to `library/`.
