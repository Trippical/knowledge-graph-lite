---
name: read-documentation
description: Answer questions from the knowledge library — two-tier ranked search, graph hops via relations, loud fail. Use for any what/who/when question about modeled domains.
---

# Read documentation

1. `python search.py "<question>"` — ranked, capped at 15, total shown.
2. Trust tiers: `library/` hits are authoritative. Hits tagged
   `[UNVERIFIED — inbox]` are recent captures — usable, but cite with that
   caveat. If inbox contradicts library, answer from library and flag the
   conflict for the synthesize skill.
3. Multi-hop: `related:` lines are plain links (no verb — open the file
   for the how); `edge:` lines carry direction and meaning. Look the
   target name up in registry.tsv
   (entity / type / file / aliases — exact one-line answer; don't grep the
   corpus, common words hit everywhere). Edges tagged `[staging]` point at
   a not-yet-promoted inbox entity; edges tagged `[unresolved]` are broken —
   do not traverse; report them.
4. Answer citing `file § section`. Check `updated:` and `source:` — a fact
   derived from a fast-moving source deserves a staleness caveat.
5. No hits → say "no memory matches" and suggest the write-documentation skill. NEVER
   answer a modeled-domain question from general knowledge without stating
   the library has no entry.
