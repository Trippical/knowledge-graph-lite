---
name: scope
description: Survey a source repo or doc set and produce the wave plan an extract backfill will follow. Read-only. Use before any extract sweep bigger than one area; the plan decides what every extract agent gets to read, so its coverage is the corpus's coverage.
---

# Scope (wave plan for a backfill)

Extract only reads what the plan hands it. A thin plan produces thin
waves and repeats stale docs. Run this on a strong model (Opus or
better); it is one pass, and it is cheaper than a wrong wave.

## Steps

1. **Inventory the curated sources.** Docs, READMEs, specs, session
   summaries, source code, content data, and the test projects. Never
   build output, generated artifacts, or session logs. Note which docs
   are untracked or newer than the last summary — those are usually the
   freshest and the least trusted.
2. **Read the repo's own gap notes first** (a doc-vs-code gaps file, a
   "known gaps" section, a milestone log). Reuse them; don't re-derive.
   Then check them against code — they go stale too.
3. **Cut the material into waves.** One coherent area per wave, 6-10
   entities, roughly ≤25 source files. Foundational concepts first
   (architecture, tick loop, units and stats) so later waves can link
   to them. Split where the mechanism differs (terrain vs navigation,
   skill framework vs a hero's kit, layouts vs structures); merge where
   one wave would be a paragraph.
4. **For every wave, list:** a name; the topics in one line; the
   starting files (code, content, AND the tests that pin the rules —
   tests are where the real numbers live); an estimated entity count;
   and a one-line stale-doc note when a doc disagrees with code.
5. **Verify anything you state as a count or a rule** ("the five
   authoring rules", "four effect kinds") against the code before
   writing it — extract agents will take the plan's word for it.
6. **List what you deliberately left out and why**: pure rendering,
   retired systems (one line of history in the successor wave is
   enough), scratch fixtures, implementation plans that duplicate specs.
7. Report the plan under ~120 lines. The user confirms scope per the
   extract skill; then each wave runs as its own extract, one at a time.

## Rules

- Read-only. This skill writes nothing into the corpus.
- Prefer the newest doc set as primary and the milestone log as history.
- A wave's starting files are a floor, not a ceiling — say so in the
  plan, so extract follows live threads without treating it as scope
  creep.
- Model split that has held up: scope on Opus, extract on Sonnet,
  synthesize on Opus.
