#!/usr/bin/env python3
"""
Build component_parts ('sub-part' edges) for machine 159 (YAMATO DT-30)
by parsing part_name pattern "... for <part_number>".

Usage:
    python3 scripts/build_dt30_bom.py            # dry-run (default, SAFE)
    python3 scripts/build_dt30_bom.py --commit   # actually insert
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "garment.db"
MACHINE_ID = 159
RELATION_TYPE = "sub-part"
NOTE = "parsed from part_name pattern 'for <num>'"

# Match trailing " for 12345" (case-insensitive, allow trailing whitespace)
PARENT_RE = re.compile(r"\bfor\s+(\d+)\s*$", re.IGNORECASE)


def parse_parent(part_name: str):
    m = PARENT_RE.search(part_name or "")
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", action="store_true", help="Actually insert into DB (default: dry-run)")
    ap.add_argument("--db", default=str(DB_PATH), help=f"Path to SQLite DB (default: {DB_PATH})")
    args = ap.parse_args()

    if not Path(args.db).exists():
        sys.exit(f"DB not found: {args.db}")

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    parts = con.execute(
        "SELECT id, part_number, part_name FROM parts WHERE machine_id = ?",
        (MACHINE_ID,),
    ).fetchall()

    if not parts:
        sys.exit(f"No parts found for machine_id={MACHINE_ID}")

    by_num = {}
    for p in parts:
        by_num.setdefault(p["part_number"], p)

    edges, skipped = [], []
    for p in parts:
        parent_num = parse_parent(p["part_name"])
        if not parent_num:
            continue
        par = by_num.get(parent_num)
        if not par:
            skipped.append((p["part_number"], parent_num, "parent not found"))
            continue
        if par["id"] == p["id"]:
            skipped.append((p["part_number"], parent_num, "self-reference"))
            continue
        edges.append({
            "component_id": par["id"],
            "part_id": p["id"],
            "relation_type": RELATION_TYPE,
            "notes": NOTE,
            "parent_num": parent_num,
            "child_num": p["part_number"],
        })

    existing = {
        (r["component_id"], r["part_id"])
        for r in con.execute(
            "SELECT component_id, part_id FROM component_parts WHERE relation_type = ?",
            (RELATION_TYPE,),
        )
    }

    new_edges = [e for e in edges if (e["component_id"], e["part_id"]) not in existing]
    dup_edges = [e for e in edges if (e["component_id"], e["part_id"]) in existing]

    print(f"Machine {MACHINE_ID}: {len(parts)} parts")
    print(f"Parsed edges       : {len(edges)}")
    print(f"Already in DB      : {len(dup_edges)}  (will skip)")
    print(f"To insert          : {len(new_edges)}")
    if skipped:
        print(f"Skipped            : {len(skipped)}")
        for c, p, why in skipped:
            print(f"   - {c}: parent '{p}' -> {why}")

    print("\n--- Preview of edges to insert ---")
    print(f"{'parent_num':<12} {'child_num':<12} {'parent_id':<10} {'child_id'}")
    for e in new_edges:
        print(f"{e['parent_num']:<12} {e['child_num']:<12} {e['component_id']:<10} {e['part_id']}")

    if not new_edges:
        print("\nNothing to insert.")
        return

    if not args.commit:
        print("\n[DRY-RUN] No changes written. Re-run with --commit to insert.")
        return

    with con:
        con.executemany(
            "INSERT INTO component_parts (component_id, part_id, relation_type, notes) "
            "VALUES (?, ?, ?, ?)",
            [(e["component_id"], e["part_id"], e["relation_type"], e["notes"]) for e in new_edges],
        )
    print(f"\n[COMMITTED] Inserted {len(new_edges)} rows into component_parts.")


if __name__ == "__main__":
    main()
