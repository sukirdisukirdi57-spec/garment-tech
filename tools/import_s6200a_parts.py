#!/usr/bin/env python3
import argparse
import csv
import sqlite3
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database/garment.db"
CSV = ROOT / "tmp/catalog-audit/s6200a_parts_candidates.csv"
BACKUP = ROOT / "database/garment.db.backup-before-s6200a-import"
MACHINE_ID = 52
DOCUMENT_ID = 219
EXPECTED_ROWS = 623
EXPECTED_MECHANISMS = 21


def fail(message):
    raise RuntimeError(message)


def load_rows():
    if not CSV.is_file():
        fail(f"CSV tidak ditemukan: {CSV}")

    with CSV.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {
            "mechanism_id", "mechanism", "catalog_ref",
            "quantity_raw", "rm", "part_number", "part_name",
            "source_url", "diagram_url"
        }
        if not required.issubset(reader.fieldnames or []):
            fail("Kolom CSV tidak sesuai.")
        rows = list(reader)

    if len(rows) != EXPECTED_ROWS:
        fail(f"Jumlah baris {len(rows)}, seharusnya {EXPECTED_ROWS}")

    mechanisms = {}
    for n, r in enumerate(rows, start=2):
        for k in required:
            r[k] = (r.get(k) or "").strip()

        mid = r["mechanism_id"]
        if not mid.isdigit() or not r["mechanism"]:
            fail(f"ID/nama mekanisme invalid pada baris {n}")
        if not r["part_number"] or not r["part_name"]:
            fail(f"Kode/nama part kosong pada baris {n}")
        if not r["source_url"].startswith(
            "https://partsbook.brother.co.jp/"
        ):
            fail(f"URL sumber invalid pada baris {n}")
        if r["quantity_raw"] and not r["quantity_raw"].isdigit():
            fail(f"Quantity invalid pada baris {n}")

        if mid in mechanisms and mechanisms[mid] != r["mechanism"]:
            fail(f"Nama mekanisme tidak konsisten untuk ID {mid}")
        mechanisms[mid] = r["mechanism"]

    plus = sum(r["catalog_ref"].endswith("+") for r in rows)
    blank = sum(not r["catalog_ref"] for r in rows)

    if len(mechanisms) != EXPECTED_MECHANISMS:
        fail(f"Mekanisme unik tidak sesuai: {len(mechanisms)}")
    if plus != 41:
        fail(f"Referensi plus tidak sesuai: {plus}")
    if blank != 17:
        fail(f"Referensi kosong tidak sesuai: {blank}")

    return rows, mechanisms


def scalar(con, sql, args=()):
    return con.execute(sql, args).fetchone()[0]


def check_db(con):
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    if not machine or "S-6200A" not in machine["model"].upper():
        fail("Mesin ID 52 tidak terverifikasi sebagai S-6200A.")

    doc = con.execute(
        "SELECT id, machine_id FROM documents WHERE id=?",
        (DOCUMENT_ID,)
    ).fetchone()
    if not doc or doc["machine_id"] != MACHINE_ID:
        fail("Dokumen ID 219 bukan dokumen milik mesin 52.")

    return {
        "components": scalar(
            con, "SELECT COUNT(*) FROM components WHERE machine_id=?",
            (MACHINE_ID,)
        ),
        "parts": scalar(
            con, "SELECT COUNT(*) FROM parts WHERE machine_id=?",
            (MACHINE_ID,)
        ),
        "relations": scalar(con, """
            SELECT COUNT(*) FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,))
    }


def backup_database(con):
    if BACKUP.exists():
        fail(f"Backup sudah ada; tidak ditimpa: {BACKUP}")
    bcon = sqlite3.connect(str(BACKUP))
    try:
        con.backup(bcon)
    finally:
        bcon.close()
    print(f"Backup dibuat: {BACKUP} ({BACKUP.stat().st_size:,} bytes)")


def import_data(con, rows, mechanisms):
    counts = check_db(con)
    if any(counts.values()):
        fail(f"Database mesin 52 tidak kosong: {counts}")

    backup_database(con)

    try:
        con.execute("BEGIN IMMEDIATE")
        component_ids = {}

        for mid, name in sorted(mechanisms.items(), key=lambda x: int(x[0])):
            url = (
                "https://partsbook.brother.co.jp/pub/"
                f"machine/detail/en/3/{mid}"
            )
            cur = con.execute("""
                INSERT INTO components
                    (machine_id, component_name, location, function,
                     notes, source_url, catalog_ref, diagram_page)
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
            """, (
                MACHINE_ID, name, f"Brother PartsBook mechanism {mid}",
                "Seksi katalog resmi Brother S-6200A",
                f"Brother S-6200A Official PartsBook; mechanism ID {mid}.",
                url
            ))
            component_ids[mid] = cur.lastrowid

        for r in rows:
            qraw = r["quantity_raw"]
            ref = r["catalog_ref"] or None

            cur = con.execute("""
                INSERT INTO parts
                    (machine_id, source_document_id, part_number,
                     part_name, quantity, catalog_ref, note,
                     source_url, notes, quantity_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, DOCUMENT_ID, r["part_number"],
                r["part_name"], int(qraw) if qraw else None,
                ref, r["rm"] or None, r["source_url"],
                f"Brother S-6200A PartsBook; mechanism "
                f"{r['mechanism_id']} ({r['mechanism']}).",
                qraw or None
            ))

            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'catalog_section', ?)
            """, (
                component_ids[r["mechanism_id"]], cur.lastrowid,
                f"Listed in Brother S-6200A mechanism "
                f"{r['mechanism_id']}."
            ))

        result = {
            "components": scalar(
                con, "SELECT COUNT(*) FROM components WHERE machine_id=?",
                (MACHINE_ID,)
            ),
            "parts": scalar(
                con, """SELECT COUNT(*) FROM parts
                        WHERE machine_id=? AND source_document_id=?""",
                (MACHINE_ID, DOCUMENT_ID)
            ),
            "relations": scalar(con, """
                SELECT COUNT(*) FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                JOIN parts p ON p.id=cp.part_id
                WHERE c.machine_id=? AND p.source_document_id=?
            """, (MACHINE_ID, DOCUMENT_ID))
        }

        expected = {
            "components": 21, "parts": 623, "relations": 623
        }
        if result != expected:
            fail(f"Verifikasi gagal: {result}; seharusnya {expected}")

        con.commit()
        print("IMPORT BERHASIL:", result)

    except Exception:
        con.rollback()
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Buat backup dan impor ke database lokal"
    )
    args = parser.parse_args()

    try:
        rows, mechanisms = load_rows()
        con = sqlite3.connect(str(DB))
        con.row_factory = sqlite3.Row
        try:
            counts = check_db(con)
            print("===== S-6200A IMPORT CHECK =====")
            print("Mode:", "APPLY" if args.apply else "PREVIEW")
            print("Baris CSV:", len(rows))
            print("Mekanisme:", len(mechanisms))
            print("Ref plus:", sum(
                r["catalog_ref"].endswith("+") for r in rows
            ))
            print("Ref kosong:", sum(
                not r["catalog_ref"] for r in rows
            ))
            print("Database saat ini:", counts)
            print("Jumlah per mekanisme:")
            for name, n in sorted(
                Counter(r["mechanism"] for r in rows).items()
            ):
                print(f"  {name}: {n}")

            if args.apply:
                import_data(con, rows, mechanisms)
            else:
                print("PREVIEW LULUS. Database tidak diubah.")
                print("Mode impor belum dijalankan.")
        finally:
            con.close()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
