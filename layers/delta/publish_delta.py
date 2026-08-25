"""Flatten library/ headers into <catalog>.<schema>.kg_entities /
kg_edges (same parse as build_index.py) so a SQL/BI layer can sit on top.

Dry-run by default (prints SQL). Pass --execute to publish via the
Databricks CLI Statement Execution API — each statement is submitted
separately (DDL and DML cannot combine), submitted async (wait_timeout=0s)
and then polled until it reaches a terminal state.

Configuration (no defaults ship with this repo — bring your own workspace):
  --target    catalog.schema table prefix   (or env KG_DELTA_TARGET)
  --profile   Databricks CLI profile name   (or env KG_DELTA_PROFILE)
  --warehouse SQL warehouse id              (or env KG_DELTA_WAREHOUSE)
--target is enough for a dry run; --execute needs all three.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kglib import load_docs, load_schema, split_relation


def ddl(prefix: str) -> dict:
    return {
        "kg_entities": f"""CREATE OR REPLACE TABLE {prefix}.kg_entities (
  entity STRING, type STRING, description STRING, file STRING,
  aliases STRING, updated STRING
) USING DELTA""",
        "kg_edges": f"""CREATE OR REPLACE TABLE {prefix}.kg_edges (
  subject STRING, predicate STRING, object STRING, source_file STRING
) USING DELTA""",
    }


def esc(s: str) -> str:
    return s.replace("'", "''")


def build_rows(docs: list, preds: set) -> tuple:
    entities, edges = [], []
    for d in docs:
        if not d["entity"]:
            continue
        entities.append(
            "('{}','{}','{}','{}','{}','{}')".format(
                esc(d["entity"]),
                esc(d["type"]),
                esc(d["description"]),
                esc(d["file"]),
                esc("|".join(d["aliases"])),
                esc(d["updated"]),
            )
        )
        for rel in d["relations"]:
            s, p, o = split_relation(rel, preds)
            if p:
                edges.append(f"('{esc(s)}','{esc(p)}','{esc(o)}','{esc(d['file'])}')")
        for r in d["related"]:
            edges.append(
                f"('{esc(d['entity'])}','related','{esc(r)}','{esc(d['file'])}')"
            )
    return entities, edges


def api(method: str, path: str, profile: str, payload: dict = None) -> dict:
    cmd = ["databricks", "api", method, path, "-p", profile]
    body = None
    if payload is not None:
        body = ROOT / "_stmt.json"
        body.write_text(json.dumps(payload), encoding="utf-8")
        cmd += ["--json", f"@{body}"]
    try:
        out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    finally:
        if body:
            body.unlink()
    return json.loads(out.stdout)


def run_statement(sql: str, profile: str, warehouse: str) -> None:
    resp = api(
        "post",
        "/api/2.0/sql/statements",
        profile,
        {"warehouse_id": warehouse, "statement": sql, "wait_timeout": "0s"},
    )
    stmt_id = resp["statement_id"]
    state = resp["status"]["state"]
    while state in ("PENDING", "RUNNING"):
        time.sleep(1)
        resp = api("get", f"/api/2.0/sql/statements/{stmt_id}", profile)
        state = resp["status"]["state"]
    if state != "SUCCEEDED":
        raise RuntimeError(f"statement {stmt_id} ended {state}: {resp['status']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--execute",
        action="store_true",
        help="publish to Databricks; default prints SQL only",
    )
    ap.add_argument(
        "--target",
        default=os.environ.get("KG_DELTA_TARGET", "catalog.schema"),
        help="catalog.schema prefix for kg_entities/kg_edges "
        "(env KG_DELTA_TARGET)",
    )
    ap.add_argument(
        "--profile",
        default=os.environ.get("KG_DELTA_PROFILE"),
        help="Databricks CLI profile (env KG_DELTA_PROFILE)",
    )
    ap.add_argument(
        "--warehouse",
        default=os.environ.get("KG_DELTA_WAREHOUSE"),
        help="SQL warehouse id (env KG_DELTA_WAREHOUSE)",
    )
    args = ap.parse_args()

    docs = load_docs(ROOT, tiers=("library",))
    _, preds = load_schema(ROOT)
    entities, edges = build_rows(docs, preds)

    tables = ddl(args.target)
    statements = [tables["kg_entities"], tables["kg_edges"]]
    if entities:
        statements.append(
            f"INSERT OVERWRITE {args.target}.kg_entities VALUES {', '.join(entities)}"
        )
    if edges:
        statements.append(
            f"INSERT OVERWRITE {args.target}.kg_edges VALUES {', '.join(edges)}"
        )

    if not args.execute:
        print("-- dry run: pass --execute to publish --\n")
        print(";\n\n".join(statements) + ";")
        return

    if not args.profile or not args.warehouse:
        raise SystemExit(
            "--execute needs --profile and --warehouse "
            "(or KG_DELTA_PROFILE / KG_DELTA_WAREHOUSE)"
        )
    for stmt in statements:
        run_statement(stmt, args.profile, args.warehouse)
    print(f"submitted: {len(entities)} entities, {len(edges)} edges -> {args.target}")


if __name__ == "__main__":
    main()
