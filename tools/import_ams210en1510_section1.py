import argparse
import re
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-6.jpg"
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)
TITLE = "1. FRAME & MISCELLANEOUS COVER COMPONENTS (1)"
STAGING_NOTE = "AMS-210EN catalog staging; section 1"
MACHINE_ID = 15
DOCUMENT_ID = 136


def stop(message):
    raise SystemExit("STOP: " + message)


def read_source():
    lines = TXT.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    title_indexes = [
        i for i, line in enumerate(lines)
        if TITLE in line and "." not in line.split(TITLE, 1)[1]
    ]
    if not title_indexes:
        stop("Judul diagram Section 1 tidak ditemukan")

    # Ambil judul diagram, bukan entri daftar isi.
    title_index = title_indexes[-1]

    # Header tabel terletak setelah diagram Section 1.
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
        stop("Header tabel PART NO / DESCRIPTION / QTY tidak ditemukan")

    records = []
    pattern = re.compile(
        r"^\s*(\d{1,3})\s+([A-Z0-9_-]+)\s+(.+?)\s+"
        r"(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    for line in lines[header_index + 1:]:
        if re.match(
            r"^\s*2\.\s+FRAME & MISCELLANEOUS COVER COMPONENTS",
            line
        ):
            break

        m = pattern.match(line)
        if not m:
            continue

        ref, pn, name, qty = m.groups()
        records.append((int(ref), pn, name.strip(), qty))

    refs = [r[0] for r in records]
    if len(records) != 63 or refs != list(range(1, 64)):
        stop(
            f"REF sumber tidak lengkap/berurutan: "
            f"{len(records)} baris, REF={refs}"
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
        stop("File gambar Section 1 tidak ditemukan: " + IMAGE)

    records = read_source()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=?",
            (MACHINE_ID,),
        ).fetchone()
        if not machine or machine["model"] != "AMS-210EN-1510":
            stop("Identitas mesin ID 15 tidak sesuai")

        document = con.execute(
            "SELECT id, source_url FROM documents WHERE id=? AND machine_id=?",
            (DOCUMENT_ID, MACHINE_ID),
        ).fetchone()
        if not document:
            stop("Dokumen Parts List ID 136 tidak ditemukan")

        components = con.execute("""
            SELECT id, component_name, diagram_page
            FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, TITLE)).fetchall()

        if components:
            stop(f"Komponen Section 1 sudah ada: "
                 f"{[dict(x) for x in components]}")

        staged = con.execute("""
            SELECT id, catalog_ref, part_number, part_name, quantity_raw
            FROM parts
            WHERE machine_id=? AND notes=?
            ORDER BY id
        """, (MACHINE_ID, STAGING_NOTE)).fetchall()

        by_ref = {}
        for row in staged:
            try:
                ref = int(row["catalog_ref"])
            except (TypeError, ValueError):
                stop(f"catalog_ref staging tidak valid: {dict(row)}")
            if ref in by_ref:
                stop(f"REF staging duplikat: {ref}")
            by_ref[ref] = row

        missing = []
        for ref, pn, name, qty in records:
            row = by_ref.get(ref)
            if row is None:
                missing.append((ref, pn, name, qty))
                continue

            actual = (
                row["part_number"],
                row["part_name"],
                row["quantity_raw"],
            )
            expected = (pn, name, qty)
            if actual != expected:
                stop(
                    f"Data staging REF {ref} berbeda. "
                    f"DB={actual}; katalog={expected}"
                )

        extra_refs = sorted(set(by_ref) - {r[0] for r in records})
        if extra_refs:
            stop(f"REF staging di luar Section 1: {extra_refs}")

        if len(staged) != 52 or len(missing) != 11:
            stop(
                f"Baseline berubah: staging={len(staged)}, "
                f"REF belum ada={len(missing)}"
            )

        print("=== PREFLIGHT SECTION 1 ===")
        print("Mesin:", machine["model"], "| ID:", MACHINE_ID)
        print("Judul:", TITLE)
        print("REF sumber:", len(records))
        print("Staging cocok:", len(staged))
        print("REF baru:", len(missing))
        for item in missing:
            print("TAMBAH:", item)
        print("Gambar:", IMAGE, "| VALID")
        print("Komponen Section 1: belum ada")
        print("Relasi lama ID 443: akan dipertahankan")

        if not args.apply:
            print("\nDRY-RUN OK: database tidak diubah.")
            return

        backup = Path(
            "database",
            "garment-before-ams210en1510-section1-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db",
        )
        shutil.copy2(DB, backup)
        print("\nBackup:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")

            # Simpan kondisi komponen lama dan seluruh relasinya.
            protected_ids = (443, 449)
            protected_components = {
                cid: tuple(con.execute(
                    "SELECT * FROM components WHERE id=?", (cid,)
                ).fetchone() or ())
                for cid in protected_ids
            }
            protected_relations = {
                cid: sorted(
                    tuple(r) for r in con.execute("""
                        SELECT component_id, part_id, relation_type, notes
                        FROM component_parts
                        WHERE component_id=?
                        ORDER BY part_id
                    """, (cid,)).fetchall()
                )
                for cid in protected_ids
            }

            new_part_ids = {}
            for ref, pn, name, qty in missing:
                cur = con.execute("""
                    INSERT INTO parts (
                        machine_id, source_document_id, part_number,
                        part_name, quantity, catalog_ref, diagram_page,
                        note, source_url, notes, quantity_raw
                    )
                    VALUES (?, NULL, ?, ?, ?, ?, NULL, 'COMMON',
                            ?, ?, ?)
                """, (
                    MACHINE_ID,
                    pn,
                    name,
                    quantity_value(qty),
                    str(ref),
                    SOURCE_URL,
                    STAGING_NOTE,
                    qty,
                ))
                new_part_ids[ref] = cur.lastrowid

            cur = con.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?, '1', 1)
            """, (
                MACHINE_ID,
                TITLE,
                "Official JUKI AMS-210EN Series Parts List, Section 1.",
                IMAGE,
                SOURCE_URL,
            ))
            component_id = cur.lastrowid

            for ref, pn, name, qty in records:
                part_id = (
                    new_part_ids[ref]
                    if ref in new_part_ids
                    else by_ref[ref]["id"]
                )
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

            if linked != 63:
                stop(f"Relasi baru tidak lengkap: {linked}/63")

            # Pastikan komponen lama dan seluruh relasinya identik.
            for cid in protected_ids:
                current_component = tuple(con.execute(
                    "SELECT * FROM components WHERE id=?", (cid,)
                ).fetchone() or ())
                current_relations = sorted(
                    tuple(r) for r in con.execute("""
                        SELECT component_id, part_id, relation_type, notes
                        FROM component_parts
                        WHERE component_id=?
                        ORDER BY part_id
                    """, (cid,)).fetchall()
                )

                if current_component != protected_components[cid]:
                    stop(f"Data komponen lama ID {cid} berubah")
                if current_relations != protected_relations[cid]:
                    stop(f"Relasi komponen lama ID {cid} berubah")

            con.commit()
            print("APPLY BERHASIL")
            print("Component ID:", component_id)
            print("Part baru:", len(new_part_ids))
            print("Relasi Section 1:", linked)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
