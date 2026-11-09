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
PAGE = 9
STAGING_NOTE = "AMS-210EN catalog staging; section 5"
ARCHIVE_NOTE = "AMS-210EN legacy staging duplicate; section 4"

TITLE = "5. PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (1)"
NEXT_TITLE = "6. PRESSER MECHANISM & PRESSER VARIABLE COMPONENTS (2)"

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
        raise RuntimeError("Judul Section 5 tidak ditemukan.")

    start = starts[-1]
    end = next(
        (i for i in range(start + 1, len(lines))
         if NEXT_TITLE in lines[i]),
        None
    )
    if end is None:
        raise RuntimeError("Batas Section 6 tidak ditemukan.")

    section = lines[start:end]
    header = next(
        (i for i, line in enumerate(section)
         if "REF.NO" in line and "PART NO" in line
         and "DESCRIPTION" in line and "Qty" in line),
        None
    )
    if header is None:
        raise RuntimeError("Header tabel Section 5 tidak ditemukan.")

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

    if sorted(records) != list(range(1, 67)):
        raise RuntimeError(
            f"REF sumber tidak lengkap: {sorted(records)}"
        )

    return records


def main():
    if not DB.is_file():
        raise RuntimeError("Database tidak ditemukan.")

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
            ORDER BY catalog_ref
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

        # Pastikan semua baris yang dipertahankan cocok dengan katalog.
        for r in valid:
            ref = int(r["catalog_ref"])
            s = source[ref]

            actual = (
                r["part_number"],
                r["part_name"],
                r["quantity_raw"],
                r["note"],
            )
            expected = (
                s["part_number"],
                s["part_name"],
                s["quantity_raw"],
                s["note"],
            )
            if actual != expected:
                raise RuntimeError(
                    f"Data staging REF {ref} berbeda dari katalog.\n"
                    f"Staging: {actual}\nSumber: {expected}"
                )

        missing = sorted(set(source) - set(refs))

        print("=== PREFLIGHT PERBAIKAN SECTION 5 ===")
        print("Mesin:", machine["model"], "| ID:", MACHINE_ID)
        print("REF sumber:", len(source))
        print("Baris staging:", len(rows))
        print("Baris valid dipertahankan:", len(valid))
        print("Baris salah untuk diarsipkan:", len(wrong))
        print("ID arsip:", [r["id"] for r in wrong])
        print("REF hilang:", missing)

        if len(rows) != 59 or len(valid) != 52:
            raise RuntimeError("Jumlah staging tidak sesuai audit.")

        if len(wrong) != 7 or len(missing) != 14:
            raise RuntimeError("Jumlah baris perbaikan tidak sesuai.")

        # Metadata sumber untuk baris staging baru.
        if valid:
            template = valid[0]
            metadata = (
                template["source_document_id"],
                template["diagram_page"],
                template["source_url"],
            )
        else:
            metadata = (None, PAGE, SOURCE_URL)

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
            f"garment-before-ams210en1510-section5-staging-{stamp}.db"
        )
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con.execute("BEGIN IMMEDIATE")

        for r in wrong:
            con.execute("""
                UPDATE parts
                SET notes=?
                WHERE id=? AND machine_id=? AND notes=?
            """, (ARCHIVE_NOTE, r["id"], MACHINE_ID, STAGING_NOTE))

        source_doc, diagram_page, source_url = metadata

        for ref in missing:
            s = source[ref]
            raw = s["quantity_raw"].strip("()")
            quantity = int(float(raw))

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

        if len(final_rows) != 66:
            raise RuntimeError("Jumlah staging akhir bukan 66.")

        for r in final_rows:
            ref = int(r["catalog_ref"])
            s = source[ref]
            if (
                r["part_number"], r["part_name"],
                r["quantity_raw"], r["note"]
            ) != (
                s["part_number"], s["part_name"],
                s["quantity_raw"], s["note"]
            ):
                raise RuntimeError(f"Validasi akhir gagal REF {ref}.")

        final_refs = [int(r["catalog_ref"]) for r in final_rows]
        if final_refs != list(range(1, 67)):
            raise RuntimeError("REF akhir tidak berurutan 1–66.")

        archived = con.execute("""
            SELECT COUNT(*) FROM parts
            WHERE machine_id=? AND notes=?
        """, (MACHINE_ID, ARCHIVE_NOTE)).fetchone()[0]

        if archived < 7:
            raise RuntimeError("Validasi arsip gagal.")

        con.commit()

        print("\nPERBAIKAN BERHASIL")
        print("Staging Section 5:", len(final_rows), "REF")
        print("REF lengkap: 1–66")
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
