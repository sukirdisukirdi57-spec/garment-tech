import re
import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("database/garment.db")
TXT_PATH = Path("assets/documents/juki/ams210en-parts.txt")
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

WRONG_IDS = (6564, 6565, 6566)
SECTION2_NOTE = "AMS-210EN catalog staging; section 2"
SECTION3_NOTE = "AMS-210EN catalog staging; section 3"
LEGACY_NOTE = "AMS-210EN legacy staging duplicate; section 2"

def stop(message):
    raise RuntimeError(message)

def parse_source():
    lines = TXT_PATH.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    start = next(
        i for i, line in enumerate(lines)
        if "3. FRAME & MISCELLANEOUS COVER COMPONENTS (3)" in line
        and i > 100
    )
    header = next(
        i for i in range(start, len(lines))
        if "REF.NO" in lines[i] and "PART NO" in lines[i]
    )

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+(?:(#\d{2})\s+)?"
        r"([A-Z0-9_-]+)\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    for line in lines[header + 1:]:
        if re.match(
            r"^\s*4\.\s+MAIN SHAFT & NEEDLE BAR COMPONENTS",
            line
        ):
            break
        match = pattern.match(line)
        if not match:
            continue

        ref, marker, pn, name, qty_raw = match.groups()
        qty_clean = qty_raw.strip("()")
        qty = float(qty_clean) if "." in qty_clean else int(qty_clean)
        records.append({
            "ref": int(ref),
            "pn": pn,
            "name": name.strip(),
            "qty_raw": qty_raw,
            "qty": qty,
            "note": marker or "COMMON",
        })

    if [r["ref"] for r in records] != list(range(1, 83)):
        stop("Sumber Section 3 bukan REF 1–82 lengkap.")
    return records

def row_matches(row, expected):
    return (
        row["part_number"] == expected["pn"]
        and row["part_name"] == expected["name"]
        and row["quantity_raw"] == expected["qty_raw"]
        and row["note"] == expected["note"]
    )

def main():
    apply = "--apply" in sys.argv
    source = parse_source()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        wrong = conn.execute("""
            SELECT id, machine_id, part_number, part_name, quantity_raw,
                   catalog_ref, note, notes
            FROM parts
            WHERE id IN (6564,6565,6566)
            ORDER BY id
        """).fetchall()

        if len(wrong) != 3:
            stop("Tiga ID staging yang perlu dikoreksi tidak lengkap.")

        expected_wrong = {
            6564: ("400-05712", "EARTH CODE ASM", "1", 48),
            6565: ("SL-4041891-SC", "SCREW M4 L=18", "1", 49),
            6566: ("SL-4041091-SC", "SCREW M4 L=10", "5", 50),
        }

        for row in wrong:
            exp = expected_wrong[row["id"]]
            actual = (
                row["part_number"], row["part_name"],
                row["quantity_raw"], row["catalog_ref"]
            )
            if (
                row["machine_id"] != 15
                or actual != exp
                or row["notes"] != SECTION3_NOTE
            ):
                stop(f"ID {row['id']} berubah dari kondisi yang diharapkan.")

            counterpart = conn.execute("""
                SELECT id
                FROM parts
                WHERE machine_id=15
                  AND notes=?
                  AND catalog_ref=?
                  AND part_number=?
                  AND part_name=?
                  AND quantity_raw=?
                  AND note='COMMON'
            """, (
                SECTION2_NOTE, exp[3], exp[0], exp[1], exp[2]
            )).fetchone()

            if not counterpart:
                stop(f"Pasangan staging Section 2 untuk ID {row['id']} tidak ditemukan.")

        staged = conn.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note
            FROM parts
            WHERE machine_id=15 AND notes=?
            ORDER BY id
        """, (SECTION3_NOTE,)).fetchall()

        by_ref = {}
        for row in staged:
            by_ref.setdefault(int(row["catalog_ref"]), []).append(row)

        # Keluarkan tiga baris yang salah klasifikasi dari pemeriksaan Section 3.
        for wrong_id in WRONG_IDS:
            ref = expected_wrong[wrong_id][3]
            by_ref[ref] = [
                row for row in by_ref.get(ref, [])
                if row["id"] != wrong_id
            ]
            if not by_ref[ref]:
                del by_ref[ref]

        for ref, rows in by_ref.items():
            if len(rows) != 1:
                stop(f"REF {ref} memiliki duplikasi staging yang tidak diharapkan.")
            expected = source[ref - 1]
            if not row_matches(rows[0], expected):
                stop(f"Data staging existing REF {ref} tidak cocok dengan katalog.")

        unexpected = sorted(set(by_ref) - set(range(1, 83)))
        if unexpected:
            stop(f"REF staging di luar rentang: {unexpected}")

        missing = [
            record for record in source
            if record["ref"] not in by_ref
        ]

        section2 = conn.execute("""
            SELECT COUNT(*) AS total,
                   COUNT(DISTINCT catalog_ref) AS unik,
                   MIN(CAST(catalog_ref AS INTEGER)) AS min_ref,
                   MAX(CAST(catalog_ref AS INTEGER)) AS max_ref
            FROM parts
            WHERE machine_id=15 AND notes=?
        """, (SECTION2_NOTE,)).fetchone()

        if tuple(section2) != (50, 50, 1, 50):
            stop(f"Staging Section 2 tidak lagi lengkap: {tuple(section2)}")

        print("=== PREFLIGHT PERBAIKAN SECTION 3 ===")
        print("REF sumber:", len(source))
        print("Staging Section 3 valid:", len(by_ref))
        print("REF yang akan ditambahkan:", len(missing))
        print("Daftar REF baru:", [r["ref"] for r in missing])
        print("ID yang dikembalikan ke Section 2:", list(WRONG_IDS))
        print("Staging Section 2:", tuple(section2))

        if not apply:
            print("\nDRY-RUN OK. Database belum diubah.")
            print("Jika hasil ini sesuai, jalankan ulang dengan --apply.")
            return

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = DB_PATH.with_name(
            f"garment-before-ams210en1510-section3-staging-{stamp}.db"
        )
        shutil.copy2(DB_PATH, backup)
        print("\nBackup:", backup)

        conn.execute("BEGIN IMMEDIATE")

        conn.execute("""
            UPDATE parts
            SET notes=?
            WHERE id IN (6564,6565,6566)
        """, (LEGACY_NOTE,))

        for record in missing:
            conn.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number, part_name,
                    quantity, catalog_ref, diagram_page, note, source_url,
                    notes, quantity_raw
                )
                VALUES (15,136,?,?,?,?,5,?,?,?,?)
            """, (
                record["pn"], record["name"], record["qty"],
                record["ref"], record["note"], SOURCE_URL,
                SECTION3_NOTE, record["qty_raw"]
            ))

        final_rows = conn.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note
            FROM parts
            WHERE machine_id=15 AND notes=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (SECTION3_NOTE,)).fetchall()

        if len(final_rows) != 82:
            stop(f"Jumlah akhir staging bukan 82: {len(final_rows)}")

        if [int(r["catalog_ref"]) for r in final_rows] != list(range(1, 83)):
            stop("REF akhir Section 3 tidak unik dan berurutan 1–82.")

        for row, expected in zip(final_rows, source):
            if not row_matches(row, expected):
                stop(f"Validasi akhir gagal pada REF {expected['ref']}.")

        section2_after = conn.execute("""
            SELECT COUNT(*), COUNT(DISTINCT catalog_ref),
                   MIN(CAST(catalog_ref AS INTEGER)),
                   MAX(CAST(catalog_ref AS INTEGER))
            FROM parts
            WHERE machine_id=15 AND notes=?
        """, (SECTION2_NOTE,)).fetchone()

        if tuple(section2_after) != (50, 50, 1, 50):
            stop("Staging Section 2 berubah atau tidak lengkap setelah perbaikan.")

        conn.commit()
        print("\nAPPLY BERHASIL")
        print("Section 3: 82 baris, REF 1–82 valid.")
        print("Section 2: 50 baris, REF 1–50 tetap valid.")
        print("Backup:", backup)

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STOP:", exc)
        sys.exit(1)
