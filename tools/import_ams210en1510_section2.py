import argparse
import re
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

IMAGE = "images/mechanisms/juki/ams210en/pdf-page-8.jpg"
TITLE = "2. FRAME & MISCELLANEOUS COVER COMPONENTS (2)"
STAGING_NOTE = "AMS-210EN catalog staging; section 2"
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 3


def stop(message):
    raise SystemExit("STOP: " + message)


def read_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    hits = [i for i, line in enumerate(lines) if TITLE in line]
    if not hits:
        stop("Judul diagram Section 2 tidak ditemukan")

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
        stop("Header tabel Section 2 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+(?:(☆|#\d{2})\s+)?"
        r"([A-Z0-9_-]+)\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    for line in lines[header_index + 1:]:
        if re.match(
            r"^\s*3\.\s+FRAME & MISCELLANEOUS COVER COMPONENTS",
            line
        ):
            break

        m = pattern.match(line)
        if m:
            ref, marker, pn, name, qty = m.groups()
            records.append((
                int(ref), pn, name.strip(), qty, marker or "COMMON"
            ))

    refs = [r[0] for r in records]
    if len(records) != 50 or refs != list(range(1, 51)):
        stop(
            f"REF sumber tidak lengkap: jumlah={len(records)}, "
            f"REF={refs}"
        )

    return records


def quantity_value(raw):
    value = raw.strip("()")
    return float(value) if "." in value else int(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file() or not TXT.is_file():
        stop("Database atau teks katalog tidak ditemukan")

    if not Path("static", IMAGE).is_file():
        stop("Gambar Section 2 tidak ditemukan")

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
            stop(f"Komponen Section 2 sudah ada: {[dict(x) for x in existing]}")

        staged = con.execute("""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY catalog_ref
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        by_ref = {}
        for row in staged:
            ref = row["catalog_ref"]
            if not isinstance(ref, int):
                stop(f"catalog_ref tidak valid: {dict(row)}")
            if ref in by_ref:
                stop(f"REF staging duplikat: {ref}")
            by_ref[ref] = row

        if len(staged) != 50:
            stop(f"Jumlah staging harus 50, ditemukan {len(staged)}")

        if set(by_ref) != set(range(1, 51)):
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

        print("=== PREFLIGHT SECTION 2 ===")
        print("Mesin:", machine["model"], "| ID:", MACHINE_ID)
        print("Judul:", TITLE)
        print("Halaman katalog:", PAGE)
        print("REF sumber:", len(records))
        print("Staging cocok:", len(staged))
        print("REF belum ada: 0")
        print("REF tambahan: 0")
        print("Marker:", [(r[0], r[4]) for r in records if r[4] != "COMMON"])
        print("Gambar:", IMAGE, "| VALID")
        print("Komponen Section 2: belum ada")

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
            "garment-before-ams210en1510-section2-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        shutil.copy2(DB, backup)
        print("Backup:", backup)

        con.execute("BEGIN IMMEDIATE")

        old_components = {
            r["id"]: tuple(r)
            for r in con.execute("""
                SELECT * FROM components
                WHERE machine_id=?
                ORDER BY id
            """, (MACHINE_ID,)).fetchall()
        }

        old_ids = tuple(old_components)

        old_relations = [
            tuple(r) for r in con.execute("""
                SELECT component_id, part_id, relation_type, notes
                FROM component_parts
                WHERE component_id IN (
                    SELECT id FROM components WHERE machine_id=?
                )
                ORDER BY component_id, part_id
            """, (MACHINE_ID,)).fetchall()
        ]

        cur = con.execute("""
            INSERT INTO components (
                machine_id, component_name, part_number,
                location, function, notes, image_path,
                source_url, catalog_ref, diagram_page
            )
            VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?, '2', ?)
        """, (
            MACHINE_ID,
            TITLE,
            "Official JUKI AMS-210EN Series Parts List, Section 2.",
            IMAGE,
            SOURCE_URL,
            PAGE,
        ))

        component_id = cur.lastrowid

        for ref, pn, name, qty, marker in records:
            part_id = by_ref[ref]["id"]

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, 'catalog_component_part', ?)
            """, (component_id, part_id, f"REF {ref}"))

        linked = con.execute("""
            SELECT COUNT(*) FROM component_parts
            WHERE component_id=?
        """, (component_id,)).fetchone()[0]

        if linked != 50:
            stop(f"Relasi baru tidak lengkap: {linked}/50")

        # Pastikan seluruh komponen lama tetap identik.
        current_components = {
            r["id"]: tuple(r)
            for r in con.execute("""
                SELECT * FROM components
                WHERE machine_id=?
                ORDER BY id
            """, (MACHINE_ID,)).fetchall()
            if r["id"] in old_ids
        }

        if current_components != old_components:
            stop("Ada komponen lama yang berubah")

        current_relations = [
            tuple(r) for r in con.execute("""
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
            stop("Ada relasi komponen lama yang berubah")

        con.commit()

        print("\n=== IMPORT BERHASIL ===")
        print("Component ID:", component_id)
        print("Judul:", TITLE)
        print("Relasi:", linked)
        print("Komponen lama: tetap identik")
        print("Relasi lama: tetap identik")

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
