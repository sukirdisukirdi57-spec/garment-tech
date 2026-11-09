import argparse
import re
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

IMAGE = "images/mechanisms/juki/ams210en/pdf-page-10.jpg"
TITLE = "3. FRAME & MISCELLANEOUS COVER COMPONENTS (3)"
STAGING_NOTE = "AMS-210EN catalog staging; section 3"
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 5
EXPECTED_REFS = 82


def stop(message):
    raise SystemExit("STOP: " + message)


def read_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    hits = [i for i, line in enumerate(lines) if TITLE in line]
    if not hits:
        stop("Judul diagram Section 3 tidak ditemukan")

    title_index = hits[-1]

    header_index = next(
        (
            i for i in range(title_index + 1, min(title_index + 120, len(lines)))
            if "PART NO" in lines[i].upper()
            and "DESCRIPTION" in lines[i].upper()
            and "QTY" in lines[i].upper()
        ),
        None,
    )
    if header_index is None:
        stop("Header tabel Section 3 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+(?:(#\d{2})\s+)?"
        r"([A-Z0-9_-]+)\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    for line in lines[header_index + 1:]:
        if re.match(
            r"^\s*4\.\s+MAIN SHAFT & NEEDLE BAR COMPONENTS",
            line
        ):
            break

        match = pattern.match(line)
        if match:
            ref, marker, pn, name, qty = match.groups()
            records.append((
                int(ref), pn, name.strip(), qty, marker or "COMMON"
            ))

    refs = [record[0] for record in records]
    if len(records) != EXPECTED_REFS or refs != list(range(1, EXPECTED_REFS + 1)):
        stop(
            f"REF sumber tidak lengkap: jumlah={len(records)}, REF={refs}"
        )

    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file() or not TXT.is_file():
        stop("Database atau teks katalog tidak ditemukan")

    if not Path("static", IMAGE).is_file():
        stop("Gambar Section 3 tidak ditemukan")

    records = read_source()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine or machine["model"] != "AMS-210EN-1510":
            stop("Identitas mesin tidak sesuai")

        document = con.execute("""
            SELECT id, source_url
            FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not document:
            stop("Dokumen Parts List ID 136 tidak ditemukan")

        existing = con.execute("""
            SELECT id, component_name
            FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, TITLE)).fetchall()

        if existing:
            stop(f"Komponen Section 3 sudah ada: {[dict(x) for x in existing]}")

        staged = con.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY CAST(catalog_ref AS INTEGER)
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        by_ref = {}
        for row in staged:
            ref = row["catalog_ref"]
            if not isinstance(ref, int):
                stop(f"catalog_ref tidak valid: {dict(row)}")
            if ref in by_ref:
                stop(f"REF staging duplikat: {ref}")
            by_ref[ref] = row

        if len(staged) != EXPECTED_REFS:
            stop(
                f"Jumlah staging harus {EXPECTED_REFS}, "
                f"ditemukan {len(staged)}"
            )

        if set(by_ref) != set(range(1, EXPECTED_REFS + 1)):
            stop(f"REF staging tidak lengkap: {sorted(by_ref)}")

        for ref, pn, name, qty, marker in records:
            row = by_ref[ref]
            actual = (
                row["part_number"],
                row["part_name"],
                row["quantity_raw"],
                row["note"],
            )
            expected = (pn, name, qty, marker)

            if actual != expected:
                stop(
                    f"Data staging REF {ref} berbeda. "
                    f"DB={actual}; katalog={expected}"
                )

        print("=== PREFLIGHT SECTION 3 ===")
        print("Mesin:", machine["model"], "| ID:", MACHINE_ID)
        print("Judul:", TITLE)
        print("Halaman katalog:", PAGE)
        print("REF sumber:", len(records))
        print("Staging cocok:", len(staged))
        print("REF belum ada: 0")
        print("REF tambahan: 0")
        print(
            "Marker:",
            [(r[0], r[4]) for r in records if r[4] != "COMMON"]
        )
        print("Gambar:", IMAGE, "| VALID")
        print("Komponen Section 3: belum ada")

        baseline = {
            table: con.execute(
                f"SELECT COUNT(*) FROM {table} WHERE machine_id=?",
                (MACHINE_ID,)
            ).fetchone()[0]
            for table in ("parts", "components")
        }
        baseline["relations"] = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        print("Baseline:", baseline)

        if not args.apply:
            print("\nDRY-RUN OK: database tidak diubah.")
            return

        backup = DB.with_name(
            "garment-before-ams210en1510-section3-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con.execute("BEGIN IMMEDIATE")

        old_components = {
            row["id"]: tuple(row)
            for row in con.execute("""
                SELECT * FROM components
                WHERE machine_id=?
                ORDER BY id
            """, (MACHINE_ID,)).fetchall()
        }
        old_ids = tuple(old_components)

        old_relations = [
            tuple(row)
            for row in con.execute("""
                SELECT component_id, part_id, relation_type, notes
                FROM component_parts
                WHERE component_id IN (
                    SELECT id FROM components WHERE machine_id=?
                )
                ORDER BY component_id, part_id
            """, (MACHINE_ID,)).fetchall()
        ]

        cursor = con.execute("""
            INSERT INTO components (
                machine_id, component_name, part_number,
                location, function, notes, image_path,
                source_url, catalog_ref, diagram_page
            )
            VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?, '3', ?)
        """, (
            MACHINE_ID,
            TITLE,
            "Official JUKI AMS-210EN Series Parts List, Section 3.",
            IMAGE,
            SOURCE_URL,
            PAGE,
        ))

        component_id = cursor.lastrowid

        for ref, pn, name, qty, marker in records:
            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, 'catalog_component_part', ?)
            """, (component_id, by_ref[ref]["id"], f"REF {ref}"))

        linked = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE component_id=?
        """, (component_id,)).fetchone()[0]

        if linked != EXPECTED_REFS:
            stop(f"Relasi baru tidak lengkap: {linked}/{EXPECTED_REFS}")

        current_components = {
            row["id"]: tuple(row)
            for row in con.execute("""
                SELECT * FROM components
                WHERE machine_id=?
                ORDER BY id
            """, (MACHINE_ID,)).fetchall()
            if row["id"] in old_ids
        }

        if current_components != old_components:
            stop("Data komponen lama berubah")

        current_relations = [
            tuple(row)
            for row in con.execute("""
                SELECT component_id, part_id, relation_type, notes
                FROM component_parts
                WHERE component_id IN (
                    SELECT id FROM components WHERE machine_id=?
                )
                AND component_id != ?
                ORDER BY component_id, part_id
            """, (MACHINE_ID, component_id)).fetchall()
        ]

        if current_relations != old_relations:
            stop("Relasi komponen lama berubah")

        final_count = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE component_id=?
              AND relation_type='catalog_component_part'
        """, (component_id,)).fetchone()[0]

        if final_count != EXPECTED_REFS:
            stop("Validasi akhir relasi gagal")

        con.commit()

        print("\nAPPLY BERHASIL")
        print("Component ID:", component_id)
        print("Relasi REF:", final_count)
        print("Komponen lama: tetap identik")
        print("Relasi lama: tetap identik")
        print("Backup:", backup)

    except Exception:
        if con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
