"""CI gate for code-derived entities: flags any library file whose `provenance:`
path changed after `provenance_rev` (the SHA recorded at extraction) in --repo.
Required before the first code-derived backfill wave (see README.md, Scope
rule for code sources). No-ops cleanly while no file carries provenance_rev yet.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from kglib import load_docs

ROOT = Path(__file__).resolve().parent


def changed_since(repo: Path, path: str, rev: str) -> bool:
    out = subprocess.run(
        ["git", "-C", str(repo), "log", f"{rev}..HEAD", "--oneline", "--", path],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return bool(out.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--repo", required=True, help="git root the provenance: paths resolve against"
    )
    args = ap.parse_args()
    repo = Path(args.repo)

    stale = []
    for d in load_docs(ROOT, tiers=("library",)):
        if not d["provenance_rev"]:
            continue
        for src in d["provenance"]:
            try:
                if changed_since(repo, src, d["provenance_rev"]):
                    stale.append(
                        f"{d['file']}: {src} changed since {d['provenance_rev'][:8]}"
                    )
            except subprocess.CalledProcessError as e:
                stale.append(f"{d['file']}: {src} -- git error: {e.stderr.strip()}")

    if stale:
        print(f"{len(stale)} stale code-derived entities:")
        print("\n".join(stale))
        sys.exit(1)
    print("no stale code-derived entities")


if __name__ == "__main__":
    main()
