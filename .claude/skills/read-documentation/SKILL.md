---
name: read-documentation
description: Answer questions from the text library — ranked search over both tiers, graph hops via edges, loud fail. Use for any what/who/when question about a modeled domain.
---

# Read documentation

Recall already ran on your prompt (the hook injects up to 8 triples plus
descriptions). Use this skill when that wasn't enough or the question is
about content, not structure.

1. `python search.py "<question>"` — ranked, capped at 15.
2. Trust tiers: `library/` hits are authoritative. Hits tagged
   `[UNVERIFIED — inbox]` are recent captures — usable, cite with the
   caveat. If inbox contradicts library, answer from library and flag it.
3. Multi-hop: `related:` lines are plain links (open the file for the how);
   `edge:` lines carry direction and meaning. A `part_of` edge from a
   scoped variant (`Last 4 (Acme)`) to its general entity means
   inheritance: answer from the variant where it speaks and from the
   general entity for everything else; a scope with no variant is answered
   by the general entity. Look the target name up in registry.tsv (entity,
   type, file, aliases, ref) — don't grep the corpus, common words hit
   everywhere.
   Edges tagged `[staging]` point at a not-yet-promoted inbox entity;
   `[unresolved]` edges are broken — don't traverse, report them.
4. Answer citing `file § section`. Check `updated:` and `provenance:` — a
   fact from a fast-moving source deserves a staleness caveat.
5. No hits → say "no memory matches" and suggest write-documentation.
   NEVER answer a modeled-domain question from general knowledge without
   saying the library has no entry.
