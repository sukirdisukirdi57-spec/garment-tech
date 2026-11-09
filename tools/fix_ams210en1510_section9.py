import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")

MACHINE_ID = 15
COMPONENT_ID = 449
TITLE = "9. WIPER MECHANISM COMPONENTS"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-22.jpg"
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)
STAGING_OLD = "AMS-210EN catalog staging; section 10"
STAGING_NEW = "AMS-210EN catalog staging; section 9"
EXPECTED_REFS = 40


def stop(message):
    raise SystemExit("STOP: " + message)


def read_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    hits = [i for i, line in enumerate(lines) if TITLE in line]
    if not hits:
        stop("Judul Section 9 tidak ditemukan")

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
        stop("Header tabel Section 9 tidak ditemukan")

    pattern = re.compile(
        r"^\s*(\d{1,3})\s+"
        r"(?:(☆)\s*)?"
        r"(?:(#\d{2})\s*)?"
        r"([A-Z0-9_-]+)\s+"
        r"(.+?)\s+"
        r"(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    for line in lines[header_index + 1:]:
        if re.match(r"^\s*10\.\s+", line, re.IGNORECASE):
            break
        match = pattern.match(line)
        if not match:
            continue

        ref, star, marker, pn, name, qty = match.groups()
        markers = []
        if star:
            markers.append("☆")
        if marker:
            markers.append(marker)

        records.append((
            int(ref), pn, name.strip(), qty,
            " ".join(markers) if markers else "COMMON",
        ))

    refs = [r[0] for r in records]
    if len(records) != EXPECTED_REFS:
        stop(f"Jumlah REF sumber salah: {len(records)}/{EXPECTED_REFS}")
    if refs != list(range(1, EXPECTED_REFS + 1)):
        stop(f"REF sumber tidak lengkap: {refs}")

    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file() or not TXT.is_file():
        stop("Database atau teks katalog tidak ditemukan")
    if not (Path("static") / IMAGE).is_file():
        stop("File diagram Section 9 tidak ditemukan")

    records = read_source()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        component = con.execute("""
            SELECT * FROM components
            WHERE id=? AND machine_id=?
        """, (COMPONENT_ID, MACHINE_ID)).fetchone()

        if not component:
            stop("Komponen ID449 tidak ditemukan")

        if component["image_path"] != IMAGE:
            stop("Image path ID449 tidak sesuai")
        if component["source_url"] != SOURCE_URL:
            stop("Source URL ID449 tidak sesuai")
        if component["part_number"] != "400-86363":
            stop("Part number induk ID449 tidak sesuai")

        old = con.execute("""
            SELECT cp.part_id, cp.relation_type, p.catalog_ref,
                   p.part_number, p.part_name, p.quantity_raw
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(p.catalog_ref AS INTEGER)
        """, (COMPONENT_ID,)).fetchall()

        if len(old) != 35:
            stop(f"Relasi lama harus 35, ditemukan {len(old)}")

        for expected, row in zip(records[:35], old):
            ref, pn, name, qty, marker = expected
            actual = (
                int(row["catalog_ref"]), row["part_number"],
                row["part_name"], row["quantity_raw"],
            )
            if actual != (ref, pn, name, qty):
                stop(f"Data relasi lama tidak cocok REF {ref}")
            if row["relation_type"] not in (
                "matched_catalog_part", "sub-part"
            ):
                stop(f"Tipe relasi tidak dikenal REF {ref}")

        staged = {}
        expected_staging = {
            36: "SM-4040855-SP",
            37: "SM-4050855-SP",
            38: "400-25440",
            39: "WP-0450801-SD",
            40: "WP-0531001-SC",
        }

        for ref, expected_pn in expected_staging.items():
            matches = con.execute("""
                SELECT id, catalog_ref, part_number, part_name,
                       quantity_raw, notes
                FROM parts
                WHERE machine_id=?
                  AND CAST(catalog_ref AS INTEGER)=?
                  AND part_number=?
                  AND notes IN (?, ?)
                ORDER BY id
            """, (
                MACHINE_ID, ref, expected_pn,
                STAGING_OLD, STAGING_NEW
            )).fetchall()

            if len(matches) != 1:
                stop(
                    f"Staging REF {ref}: ditemukan {len(matches)} "
                    f"baris untuk part {expected_pn}"
                )
            staged[ref] = matches[0]

        for ref, pn, name, qty, marker in records[35:]:
            row = staged.get(ref)
            if not row:
                stop(f"Staging REF {ref} tidak ditemukan")
            if (
                row["part_number"], row["part_name"],
                row["quantity_raw"]
            ) != (pn, name, qty):
                stop(f"Data staging tidak cocok REF {ref}")
            linked = con.execute("""
                SELECT COUNT(*) FROM component_parts WHERE part_id=?
            """, (row["id"],)).fetchone()[0]
            if linked:
                stop(f"Staging REF {ref} sudah memiliki relasi")

        if set(staged) != {36, 37, 38, 39, 40}:
            stop(f"Staging tidak tepat: {sorted(staged)}")

        protected = con.execute(
            "SELECT * FROM components WHERE id=696"
        ).fetchone()
        protected_relations = con.execute("""
            SELECT part_id, relation_type, notes
            FROM component_parts WHERE component_id=696
            ORDER BY part_id
        """).fetchall()

        baseline = {
            "parts": con.execute(
                "SELECT COUNT(*) FROM parts WHERE machine_id=?",
                (MACHINE_ID,),
            ).fetchone()[0],
            "components": con.execute(
                "SELECT COUNT(*) FROM components WHERE machine_id=?",
                (MACHINE_ID,),
            ).fetchone()[0],
            "relations": con.execute("""
                SELECT COUNT(*) FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                WHERE c.machine_id=?
            """, (MACHINE_ID,)).fetchone()[0],
        }

        print("=== PREFLIGHT SECTION 9 ===")
        print("Judul:", TITLE)
        print("Sumber REF:", len(records))
        print("Relasi lama cocok:", len(old))
        print("Staging REF baru:", sorted(staged))
        print("Diagram:", IMAGE, "OK")
        print("Komponen target:", COMPONENT_ID)
        print("Nama lama:", component["component_name"])
        print("Catalog ref lama:", component["catalog_ref"])
        print("Tipe relasi lama akan dipertahankan")
        print("Komponen ID696 akan dipertahankan")
        print("Baseline:", baseline)
        print("Rencana: tambah 5 relasi; total menjadi 40")

        if not args.apply:
            print("\nDRY-RUN BERHASIL — database belum diubah.")
            return

        backup = DB.with_name(
            "garment-before-ams210en1510-section9-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        con.close()
        shutil.copy2(DB, backup)
        print("\nBackup:", backup)

        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("BEGIN IMMEDIATE")

        current = con.execute("""
            SELECT * FROM components WHERE id=? AND machine_id=?
        """, (COMPONENT_ID, MACHINE_ID)).fetchone()

        if not current or tuple(current) != tuple(component):
            stop("Komponen berubah setelah preflight")

        con.execute("""
            UPDATE components
            SET component_name=?, catalog_ref='9', diagram_page=17
            WHERE id=? AND machine_id=?
        """, (TITLE, COMPONENT_ID, MACHINE_ID))

        for expected, row in zip(records[:35], old):
            ref = expected[0]
            con.execute("""
                UPDATE component_parts SET notes=?
                WHERE component_id=? AND part_id=?
            """, (f"REF {ref}", COMPONENT_ID, row["part_id"]))

        for ref in range(36, 41):
            row = staged[ref]
            con.execute("""
                UPDATE parts SET notes=?
                WHERE id=? AND machine_id=?
            """, (STAGING_NEW, row["id"], MACHINE_ID))

            con.execute("""
                INSERT INTO component_parts
                    (component_id, part_id, relation_type, notes)
                VALUES (?, ?, 'catalog_component_part', ?)
            """, (COMPONENT_ID, row["id"], f"REF {ref}"))

        final = con.execute("""
            SELECT cp.notes, p.catalog_ref, p.part_number,
                   p.part_name, p.quantity_raw
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(p.catalog_ref AS INTEGER)
        """, (COMPONENT_ID,)).fetchall()

        if len(final) != EXPECTED_REFS:
            raise RuntimeError("Jumlah relasi akhir bukan 40")

        for expected, row in zip(records, final):
            ref, pn, name, qty, marker = expected
            if (
                row["notes"] != f"REF {ref}"
                or int(row["catalog_ref"]) != ref
                or row["part_number"] != pn
                or row["part_name"] != name
                or row["quantity_raw"] != qty
            ):
                raise RuntimeError(f"Validasi akhir gagal REF {ref}")

        if con.execute("""
            SELECT COUNT(*) FROM component_parts
            WHERE component_id=?
              AND relation_type='catalog_component_part'
        """, (COMPONENT_ID,)).fetchone()[0] != 5:
            raise RuntimeError("Jumlah relasi baru bukan 5")

        after = con.execute(
            "SELECT * FROM components WHERE id=696"
        ).fetchone()
        after_rel = con.execute("""
            SELECT part_id, relation_type, notes
            FROM component_parts WHERE component_id=696
            ORDER BY part_id
        """).fetchall()

        if tuple(protected) != tuple(after):
            raise RuntimeError("Komponen ID696 berubah")
        if [tuple(r) for r in protected_relations] != [
            tuple(r) for r in after_rel
        ]:
            raise RuntimeError("Relasi ID696 berubah")

        con.commit()
        print("\nAPPLY BERHASIL")
        print("Component ID:", COMPONENT_ID)
        print("Judul:", TITLE)
        print("Relasi akhir:", len(final))
        print("Tipe relasi lama dipertahankan.")
        print("ID696 tetap identik.")
        print("Backup:", backup)

    except BaseException:
        if con and con.in_transaction:
            con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
