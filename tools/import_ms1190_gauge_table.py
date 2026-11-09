import re
import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
TEXT = Path("assets/documents/juki/ms1190-parts.txt")
MACHINE_ID = 14
DOCUMENT_ID = 134
PDF_PAGE = 21
SOURCE_URL = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ms1190_1261/menu/ms_1190/pdf/partslist.pdf"

ROW_RE = re.compile(
    r"^\s*(\d+)\s+([A-Z0-9-]+)\s+(.+?)\s+(\(?\d+\)?)\s*$"
)

def parse_rows():
    pages = TEXT.read_text(errors="replace").split("\f")
    rows = []
    for line in pages[PDF_PAGE - 1].splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        ref, pn, name, qty = m.groups()
        rows.append({
            "ref": int(ref),
            "part_number": pn,
            "part_name": name.strip(),
            "quantity_raw": qty,
            "original": line.rstrip()
        })
    return rows

def main():
    rows = parse_rows()
    refs = [r["ref"] for r in rows]

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    machine = con.execute(
        "SELECT id,model FROM machines WHERE id=?", (MACHINE_ID,)
    ).fetchone()
    doc = con.execute(
        "SELECT id,machine_id,title,source_url FROM documents WHERE id=?",
        (DOCUMENT_ID,)
    ).fetchone()

    print("MESIN:", dict(machine) if machine else None)
    print("DOKUMEN:", dict(doc) if doc else None)
    print("JUMLAH BARIS:", len(rows))
    print("REF BERURUT:", refs == list(range(1,70)))
    print("BARIS GAGAL: 0")
    print("KONFLIK:", con.execute("""
        SELECT COUNT(*) FROM catalog_occurrences
        WHERE machine_id=? AND pdf_page=?
    """, (MACHINE_ID, PDF_PAGE)).fetchone()[0])

    if not machine or not doc or doc["machine_id"] != MACHINE_ID:
        raise SystemExit("GAGAL: mesin/dokumen tidak cocok")
    if len(rows) != 69 or refs != list(range(1,70)):
        raise SystemExit("GAGAL: jumlah atau urutan REF tidak valid")

    conflicts = con.execute("""
        SELECT catalog_ref FROM catalog_occurrences
        WHERE machine_id=? AND pdf_page=?
    """, (MACHINE_ID, PDF_PAGE)).fetchall()
    if conflicts:
        raise SystemExit("GAGAL: REF halaman sudah ada")

    print("\nPREVIEW:")
    for r in rows:
        print(
            f'{r["ref"]:02} | {r["part_number"]} | '
            f'{r["part_name"]} | {r["quantity_raw"]}'
        )

    if "--apply" not in sys.argv:
        print("\\nDRY-RUN: 69 occurrence siap diimpor.")
        print("Belum ada perubahan database.")
        con.close()
        return

    backup = DB.with_name(
        "garment-before-ms1190-gauge-" +
        datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
    )
    con.close()
    shutil.copy2(DB, backup)
    print("\\nBACKUP:", backup)

    con = sqlite3.connect(DB)
    try:
        con.execute("BEGIN IMMEDIATE")
        for r in rows:
            con.execute("""
                INSERT INTO catalog_occurrences (
                    machine_id, source_document_id, pdf_page,
                    catalog_ref, marker, part_number, part_name,
                    quantity_raw, catalog_line_original, source_url
                ) VALUES (?, ?, ?, ?, '', ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, DOCUMENT_ID, PDF_PAGE,
                str(r["ref"]), r["part_number"], r["part_name"],
                r["quantity_raw"], r["original"], SOURCE_URL
            ))

        count = con.execute("""
            SELECT COUNT(*) FROM catalog_occurrences
            WHERE machine_id=? AND source_document_id=? AND pdf_page=?
        """, (MACHINE_ID, DOCUMENT_ID, PDF_PAGE)).fetchone()[0]

        refs_after = [
            int(x[0]) for x in con.execute("""
                SELECT catalog_ref FROM catalog_occurrences
                WHERE machine_id=? AND source_document_id=? AND pdf_page=?
                ORDER BY CAST(catalog_ref AS INTEGER)
            """, (MACHINE_ID, DOCUMENT_ID, PDF_PAGE))
        ]

        if count != 69 or refs_after != list(range(1,70)):
            raise RuntimeError(
                f"Audit gagal: count={count}, refs={refs_after}"
            )

        con.commit()
        print("APPLY BERHASIL")
        print("HASIL:", count, "catalog occurrences")
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
