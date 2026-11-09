import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 13
IMAGE_PAGE = 18
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)
STAGING_NOTE = "AMS-210EN catalog staging; section 7"
ARCHIVE_NOTE = "AMS-210EN legacy staging duplicate; section 7"

REMAP = {
    6799: 41,
    6801: 71,
}
ARCHIVE_IDS = (6794, 6795, 6796, 6797, 6798, 6800, 6802, 6803)

def stop(message):
    raise SystemExit("STOP: " + message)

def parse_source():
    lines = TXT.read_text(encoding="utf-8", errors="replace").splitlines()

    section_hits = [
        i for i, line in enumerate(lines)
        if "PRESSER PLATE & MANUAL PRESSER MECHANISM COMPONENTS" in line
    ]
    if len(section_hits) < 2:
        stop(f"Judul isi Section 7 tidak ditemukan: {section_hits}")

    # Kemunculan pertama berada di daftar isi; gunakan judul isi katalog.
    section_start = section_hits[1]
    headers = [
        i for i, line in enumerate(lines)
        if section_start < i < section_start + 120
        and "REF.NO" in line and "PART NO" in line and "DESCRIPTION" in line
    ]
    if len(headers) != 1:
        stop(f"Header tabel Section 7 tidak unik dalam rentang section: {headers}")

    pattern = re.compile(
        r"^\s*(\d{1,2})\s+(?:(#\d{2})\s+)?"
        r"([A-Z0-9][A-Z0-9-]+)\s+(.+?)\s+(\d+)\s*$"
    )

    records = []
    started = False
    for line in lines[headers[0] + 1:]:
        m = pattern.match(line)
        if not m:
            if started:
                break
            continue

        started = True
        ref, marker, pn, name, qty = m.groups()
        records.append({
            "ref": int(ref),
            "marker": marker or "",
            "part_number": pn,
            "part_name": name.strip(),
            "quantity": int(qty),
            "quantity_raw": qty,
        })

    refs = [r["ref"] for r in records]
    if len(records) != 73 or refs != list(range(1, 74)):
        stop(f"Sumber bukan 73 REF berurutan: jumlah={len(records)}, refs={refs}")

    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file() or not TXT.is_file():
        stop("Database atau teks katalog tidak ditemukan")

    image = Path("static/images/mechanisms/juki/ams210en/pdf-page-18.jpg")
    if not image.is_file():
        stop(f"Gambar Section 7 tidak ditemukan: {image}")

    records = parse_source()
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    try:
        columns = {
            r["name"] for r in db.execute("PRAGMA table_info(parts)")
        }
        required = {
            "machine_id", "source_document_id", "part_number", "part_name",
            "quantity", "quantity_raw", "catalog_ref", "diagram_page",
            "note", "source_url", "notes",
        }
        if not required.issubset(columns):
            stop(f"Kolom parts tidak lengkap: {sorted(required - columns)}")

        staging_rows = db.execute("""
            SELECT id, catalog_ref, part_number, note, notes
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY id
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        if len(staging_rows) != 26:
            stop(f"Jumlah staging berubah: diharapkan 26, ditemukan {len(staging_rows)}")

        by_id = {r["id"]: r for r in staging_rows}
        expected_ids = set(range(6794, 6804)) | set(range(6804, 6820))
        if set(by_id) != expected_ids:
            stop("ID staging berubah dari hasil audit sebelumnya")

        # Verifikasi 16 baris yang sudah cocok.
        correct = {
            (9, "400-36471"), (13, "400-36472"), (18, "400-36470"),
            (22, "401-03968"), (23, "400-72211"), (24, "SM-6061802-TP"),
            (25, "B1816-215-P00"), (42, "SL-4031291-SC"),
            (43, "400-10443"), (44, "SM-6040802-TP"),
            (45, "400-06666"), (46, "SM-8050592-TP"),
            (47, "SB-1100024-00"), (48, "SM-6040650-TP"),
            (49, "SM-4051655-SP"), (50, "WP-0651001-SC"),
        }
        for ref, pn in correct:
            if not any(
                r["catalog_ref"] == ref and r["part_number"] == pn
                for r in staging_rows
            ):
                stop(f"Staging cocok hilang/berubah: REF {ref}, {pn}")

        # Pastikan dua pemetaan ulang memang sesuai part number sumber.
        source_by_ref = {r["ref"]: r for r in records}
        for part_id, new_ref in REMAP.items():
            old = by_id.get(part_id)
            src = source_by_ref[new_ref]
            if old is None or old["part_number"] != src["part_number"]:
                stop(f"Remap ID {part_id} tidak cocok dengan REF {new_ref}")

        for part_id in ARCHIVE_IDS:
            if part_id not in by_id:
                stop(f"ID arsip tidak ditemukan: {part_id}")

        retained_ids = set(by_id) - set(ARCHIVE_IDS)
        remapped_ids = set(REMAP)
        retained_keys = set()
        for r in staging_rows:
            if r["id"] in retained_ids and r["id"] not in remapped_ids:
                retained_keys.add((int(r["catalog_ref"]), r["part_number"]))
        for part_id, new_ref in REMAP.items():
            retained_keys.add((new_ref, by_id[part_id]["part_number"]))

        missing = [
            r for r in records
            if (r["ref"], r["part_number"]) not in retained_keys
        ]
        if len(retained_keys) != 18 or len(missing) != 55:
            stop(
                f"Rencana tidak sesuai: dipertahankan={len(retained_keys)}, "
                f"perlu dibuat={len(missing)}"
            )

        print("=== DRY-RUN SECTION 7 STAGING ===")
        print("Sumber resmi:", len(records), "REF (1–73)")
        print("Staging awal:", len(staging_rows))
        print("Dipertahankan:", len(retained_ids), "baris")
        print("Remap REF:", REMAP)
        print("Diarsipkan:", list(ARCHIVE_IDS))
        print("Baris baru:", len(missing))
        print("Target akhir: 73 staging rows")
        print("Gambar:", image, "| ada:", image.is_file())
        print("\n=== BARIS YANG AKAN DIBUAT ===")
        for r in missing:
            print(
                f"REF {r['ref']:02} | {r['part_number']:18} | "
                f"{r['part_name']} | qty={r['quantity']} | "
                f"{r['marker'] or 'COMMON'}"
            )

        if not args.apply:
            print("\nDRY-RUN: database tidak diubah.")
            return

        backup = Path("database") / (
            "garment-before-ams210en1510-section7-staging-"
            + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
        )
        shutil.copy2(DB, backup)
        print("\nBackup:", backup)

        try:
            db.execute("BEGIN IMMEDIATE")

            for part_id, new_ref in REMAP.items():
                db.execute(
                    "UPDATE parts SET catalog_ref=? WHERE id=?",
                    (new_ref, part_id),
                )

            for part_id in ARCHIVE_IDS:
                db.execute(
                    "UPDATE parts SET notes=? WHERE id=?",
                    (ARCHIVE_NOTE, part_id),
                )

            for r in missing:
                db.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id, part_number,
                        part_name, quantity, quantity_raw, catalog_ref,
                        diagram_page, note, source_url, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    MACHINE_ID, DOCUMENT_ID, r["part_number"],
                    r["part_name"], r["quantity"], r["quantity_raw"],
                    r["ref"], PAGE, r["marker"] or "COMMON",
                    SOURCE_URL, STAGING_NOTE,
                ))

            final_count = db.execute("""
                SELECT COUNT(*) FROM parts
                WHERE machine_id=? AND notes=?
            """, (MACHINE_ID, STAGING_NOTE)).fetchone()[0]

            final_refs = [
                r[0] for r in db.execute("""
                    SELECT catalog_ref FROM parts
                    WHERE machine_id=? AND notes=?
                    ORDER BY catalog_ref
                """, (MACHINE_ID, STAGING_NOTE))
            ]

            if final_count != 73 or final_refs != list(range(1, 74)):
                stop(f"Verifikasi transaksi gagal: count={final_count}, refs={final_refs}")

            db.commit()
            print("APPLY BERHASIL: 73 staging REF lengkap.")
        except Exception:
            db.rollback()
            raise

    finally:
        db.close()

if __name__ == "__main__":
    main()
