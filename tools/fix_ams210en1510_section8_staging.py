import re
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 15
EXPECTED_REFS = 49
STAGING_NOTE = "AMS-210EN catalog staging; section 8"
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

def stop(message):
    raise SystemExit("STOP: " + message)

def read_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    title_hits = [
        i for i, line in enumerate(lines)
        if re.search(r"8\.\s+SHUTTLE DRIVER SHAFT COMPONENTS", line, re.I)
    ]
    if not title_hits:
        stop("Judul Section 8 tidak ditemukan")

    title_index = next((i for i in title_hits if i >= 1194), None)
    if title_index is None:
        stop(f"Judul Section 8 tidak ditemukan di area tabel: {title_hits}")

    start = next(
        (i for i in range(title_index + 1, min(title_index + 120, len(lines)))
         if "PART NO" in lines[i].upper()
         and "DESCRIPTION" in lines[i].upper()
         and "QTY" in lines[i].upper()),
        None,
    )
    if start is None:
        stop("Header tabel setelah judul Section 8 tidak ditemukan")
    end = next(
        (i for i in range(start + 1, len(lines))
         if re.match(r"^\s*9\.\s+WIPER MECHANISM COMPONENTS", lines[i])),
        None,
    )
    if end is None:
        stop("Batas akhir Section 8 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+"
        r"(?:(☆)\s*)?"
        r"(?:(#\d{2})\s*)?"
        r"([A-Z0-9_-]+)\s+"
        r"(.+?)\s+"
        r"(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    for line in lines[start + 1:end]:
        m = pattern.match(line)
        if not m:
            continue
        ref, star, marker, pn, name, qty = m.groups()
        note = " ".join(x for x in (star, marker) if x) or "COMMON"
        records.append((int(ref), pn, name.strip(), qty, note))

    refs = [r[0] for r in records]
    if len(records) != EXPECTED_REFS:
        stop(f"Jumlah REF sumber salah: {len(records)}/{EXPECTED_REFS}")
    if refs != list(range(1, EXPECTED_REFS + 1)):
        stop(f"REF sumber tidak lengkap/berurutan: {refs}")
    return records

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file() or not TXT.is_file():
        stop("Database atau teks katalog tidak ditemukan")

    records = read_source()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (MACHINE_ID,),
        ).fetchone()
        if not machine or machine["model"] != "AMS-210EN-1510":
            stop("Identitas mesin tidak sesuai")

        document = con.execute("""
            SELECT id, source_url FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()
        if not document or document["source_url"] != SOURCE_URL:
            stop("Dokumen Parts List tidak sesuai")

        staged = con.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note, source_document_id,
                   diagram_page, source_url, notes
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY catalog_ref
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        by_ref = {}
        for row in staged:
            ref = row["catalog_ref"]
            if not isinstance(ref, int) or ref in by_ref:
                stop(f"catalog_ref staging tidak valid/duplikat: {ref}")
            by_ref[ref] = row

        if set(by_ref) != set(range(1, 33)):
            stop(f"Staging awal bukan REF 1-32: {sorted(by_ref)}")

        for ref, pn, name, qty, marker in records[:32]:
            row = by_ref[ref]
            actual = (
                row["part_number"], row["part_name"],
                row["quantity_raw"]
            )
            expected = (pn, name, qty)
            if actual != expected:
                stop(f"Data REF {ref} berbeda: DB={actual}; katalog={expected}")

        existing_component = con.execute("""
            SELECT id, component_name FROM components
            WHERE machine_id=?
              AND component_name='8. SHUTTLE DRIVER SHAFT COMPONENTS'
        """, (MACHINE_ID,)).fetchall()
        if existing_component:
            stop(f"Komponen Section 8 sudah ada: {[dict(x) for x in existing_component]}")

        print("=== PREFLIGHT PERBAIKAN SECTION 8 ===")
        print("Mesin:", machine["model"], "| ID:", MACHINE_ID)
        print("REF katalog:", len(records), "| lengkap 1-49")
        print("Staging cocok:", len(staged), "| REF 1-32")
        print("REF baru:", 17, "| REF 33-49")
        print("Marker:", [(r[0], r[4]) for r in records if r[4] != "COMMON"])
        print("Metadata yang akan dilengkapi: 49 baris")
        print("Komponen Section 8: belum ada")

        if not args.apply:
            print("\nDRY-RUN OK: database tidak diubah.")
            return

        backup = DB.with_name(
            "garment-before-ams210en1510-section8-staging-"
            + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
        )
        con.close()
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("BEGIN IMMEDIATE")

        for ref, pn, name, qty, marker in records[:32]:
            con.execute("""
                UPDATE parts
                SET note=?, source_document_id=?, diagram_page=?,
                    source_url=?
                WHERE id=?
            """, (marker, DOCUMENT_ID, PAGE, SOURCE_URL, by_ref[ref]["id"]))

        inserted = []
        for ref, pn, name, qty, marker in records[32:]:
            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number,
                    part_name, quantity, catalog_ref, diagram_page,
                    note, source_url, notes, quantity_raw
                )
                VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, DOCUMENT_ID, pn, name, ref, PAGE,
                marker, SOURCE_URL, STAGING_NOTE, qty
            ))
            inserted.append(cur.lastrowid)

        final = con.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note, source_document_id,
                   diagram_page, source_url
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY catalog_ref
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        if len(final) != EXPECTED_REFS:
            raise RuntimeError(f"Jumlah akhir salah: {len(final)}")

        for i, (row, expected) in enumerate(zip(final, records), 1):
            ref, pn, name, qty, marker = expected
            actual = (
                row["catalog_ref"], row["part_number"],
                row["part_name"], row["quantity_raw"], row["note"],
                row["source_document_id"], row["diagram_page"],
                row["source_url"]
            )
            target = (
                ref, pn, name, qty, marker,
                DOCUMENT_ID, PAGE, SOURCE_URL
            )
            if actual != target:
                raise RuntimeError(f"Audit REF {i} gagal: {actual} != {target}")

        con.commit()
        print("\nPERBAIKAN STAGING BERHASIL")
        print("Total staging:", len(final))
        print("Baris baru:", len(inserted))
        print("Metadata valid:", len(final), "/", EXPECTED_REFS)
        print("REF:", final[0]["catalog_ref"], "-", final[-1]["catalog_ref"])
        print("Backup:", backup)

    except BaseException:
        if con and con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
