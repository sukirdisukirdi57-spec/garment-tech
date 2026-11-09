import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
BACKUP_DIR = Path("database")

MACHINE_ID = 15
PAGE = 11
STAGING_NOTE = "AMS-210EN catalog staging; section 6"
ARCHIVE_NOTE = "AMS-210EN legacy staging duplicate; section 6"

TITLE = "6. PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (2)"
NEXT_TITLE = "7. PRESSER PLATE & MANUAL PRESSER MECHANISM COMPONENTS"

SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()


def read_source():
    lines = TXT.read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(lines) if TITLE in line]

    if not starts:
        raise RuntimeError("Judul Section 6 tidak ditemukan.")

    start = starts[-1]
    end = next(
        (i for i in range(start + 1, len(lines))
         if NEXT_TITLE in lines[i]),
        None
    )

    if end is None:
        raise RuntimeError("Batas Section 7 tidak ditemukan.")

    section = lines[start:end]
    header = next(
        (i for i, line in enumerate(section)
         if "REF.NO" in line and "PART NO" in line
         and "DESCRIPTION" in line and "Qty" in line),
        None
    )

    if header is None:
        raise RuntimeError("Header tabel Section 6 tidak ditemukan.")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+(?:(☆)\s*)?(?:(#\d{2})\s*)?"
        r"([A-Z0-9_-]+)\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = {}
    for line in section[header + 1:]:
        m = pattern.match(line)
        if not m:
            continue

        ref, star, marker, pn, name, qty = m.groups()
        ref = int(ref)
        note = " ".join(x for x in (star, marker) if x) or "COMMON"

        if ref in records:
            raise RuntimeError(f"REF sumber duplikat: {ref}")

        records[ref] = {
            "part_number": pn,
            "part_name": name,
            "quantity_raw": qty,
            "note": note,
        }

    if sorted(records) != list(range(1, 53)):
        raise RuntimeError(
            f"REF sumber tidak lengkap: {sorted(records)}"
        )

    return records


def main():
    if not DB.is_file() or not TXT.is_file():
        raise RuntimeError("Database atau teks katalog tidak ditemukan.")

    source = read_source()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute(
            "SELECT model FROM machines WHERE id=?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine or machine["model"] != "AMS-210EN-1510":
            raise RuntimeError("Identitas mesin tidak cocok.")

        rows = con.execute("""
            SELECT *
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        wrong = [
            r for r in rows
            if r["catalog_ref"] is not None
            and int(r["catalog_ref"]) not in source
        ]
        wrong_ids = {r["id"] for r in wrong}
        valid = [r for r in rows if r["id"] not in wrong_ids]

        refs = [int(r["catalog_ref"]) for r in valid]

        if len(refs) != len(set(refs)):
            raise RuntimeError("Ada REF staging duplikat.")

        for r in valid:
            ref = int(r["catalog_ref"])
            s = source[ref]
            actual = (
                r["part_number"], r["part_name"],
                r["quantity_raw"], r["note"]
            )
            expected = (
                s["part_number"], s["part_name"],
                s["quantity_raw"], s["note"]
            )
            if actual != expected:
                raise RuntimeError(
                    f"Data staging REF {ref} berbeda.\n"
                    f"Staging: {actual}\nKatalog: {expected}"
                )

        missing = sorted(set(source) - set(refs))
        wrong_refs = sorted(int(r["catalog_ref"]) for r in wrong)

        print("=== PREFLIGHT PERBAIKAN SECTION 6 ===")
        print("Mesin:", machine["model"], "| ID:", MACHINE_ID)
        print("REF sumber:", len(source))
        print("Baris staging:", len(rows))
        print("Baris valid:", len(valid))
        print("Baris salah:", len(wrong))
        print("REF salah:", wrong_refs)
        print("REF hilang:", missing)

        if len(rows) != 43 or len(valid) != 37:
            raise RuntimeError("Jumlah staging tidak sesuai audit.")

        if len(wrong) != 6 or wrong_refs != [58, 59, 60, 61, 62, 66]:
            raise RuntimeError("Daftar baris arsip tidak sesuai.")

        if missing != [29, 30, 32, 34, 42, 43, 44, 45,
                       46, 47, 48, 49, 50, 51, 52]:
            raise RuntimeError("Daftar REF yang hilang tidak sesuai.")

        document = con.execute("""
            SELECT id, machine_id, document_type, source_url
            FROM documents
            WHERE id=136 AND machine_id=?
        """, (MACHINE_ID,)).fetchone()

        if (
            not document
            or document["document_type"] != "Parts List"
            or document["source_url"] != SOURCE_URL
        ):
            raise RuntimeError("Metadata dokumen Parts List tidak cocok.")

        metadata = (
            document["id"],
            PAGE,
            document["source_url"]
        )

        print("Metadata staging:", metadata)
        print("Marker khusus:", [
            (ref, source[ref]["note"])
            for ref in source if source[ref]["note"] != "COMMON"
        ])
        print("DRY-RUN OK: belum ada perubahan database.")

        if not args.apply:
            return

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / (
            f"garment-before-ams210en1510-section6-staging-{stamp}.db"
        )
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con.execute("BEGIN IMMEDIATE")

        for r in wrong:
            cur = con.execute("""
                UPDATE parts
                SET notes=?
                WHERE id=? AND machine_id=? AND notes=?
            """, (ARCHIVE_NOTE, r["id"], MACHINE_ID, STAGING_NOTE))

            if cur.rowcount != 1:
                raise RuntimeError(f"Gagal mengarsipkan ID {r['id']}.")

        source_doc, diagram_page, source_url = metadata

        for ref in missing:
            s = source[ref]
            quantity = int(float(s["quantity_raw"].strip("()")))

            con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id,
                    part_number, part_name, quantity,
                    catalog_ref, diagram_page, note,
                    source_url, notes, quantity_raw
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, source_doc,
                s["part_number"], s["part_name"], quantity,
                ref, diagram_page or PAGE, s["note"],
                source_url or SOURCE_URL, STAGING_NOTE,
                s["quantity_raw"]
            ))

        final_rows = con.execute("""
            SELECT catalog_ref, part_number, part_name,
                   quantity_raw, note
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        if len(final_rows) != 52:
            raise RuntimeError("Jumlah staging akhir bukan 52.")

        for r in final_rows:
            ref = int(r["catalog_ref"])
            s = source[ref]
            actual = (
                r["part_number"], r["part_name"],
                r["quantity_raw"], r["note"]
            )
            expected = (
                s["part_number"], s["part_name"],
                s["quantity_raw"], s["note"]
            )
            if actual != expected:
                raise RuntimeError(f"Validasi akhir gagal REF {ref}.")

        final_refs = [int(r["catalog_ref"]) for r in final_rows]
        if final_refs != list(range(1, 53)):
            raise RuntimeError("REF akhir tidak berurutan 1–52.")

        archived_ids = [r["id"] for r in wrong]
        placeholders = ",".join("?" for _ in archived_ids)
        archived = con.execute(
            f"SELECT COUNT(*) FROM parts WHERE id IN ({placeholders}) "
            "AND notes=?",
            (*archived_ids, ARCHIVE_NOTE)
        ).fetchone()[0]

        if archived != 6:
            raise RuntimeError("Validasi enam baris arsip gagal.")

        con.commit()

        print("\nPERBAIKAN BERHASIL")
        print("Staging Section 6:", len(final_rows), "REF")
        print("REF lengkap: 1–52")
        print("Baris baru:", len(missing))
        print("Baris diarsipkan:", len(wrong))
        print("Marker dan data katalog: cocok")
        print("Backup:", backup)

    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
