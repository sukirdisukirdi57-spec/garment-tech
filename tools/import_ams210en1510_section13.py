import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path("database/garment.db")
TXT = Path("assets/documents/juki/ams210en-parts.txt")
TITLE = "13. X-Y COMPONENTS (1)"
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-28.jpg"
URL = "https://www.juki.co.id/"  # Akan diganti dari dokumen database
MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 23
EXPECTED_REFS = 48
OLD_COMPONENT_ID = 454
STAGING_NOTE = "AMS-210EN catalog staging; section 13"


def load_source():
    lines = TXT.read_text(errors="replace").splitlines()
    starts = [
        i for i, line in enumerate(lines)
        if i > 100 and TITLE in line
    ]
    if len(starts) != 1:
        raise RuntimeError(f"Judul body tidak unik: {starts}")

    start = starts[0]
    header = next(
        (i for i in range(start, len(lines))
         if "REF.NO" in lines[i] and "PART NO" in lines[i]),
        None
    )
    if header is None:
        raise RuntimeError("Header tabel tidak ditemukan")

    data = []
    pattern = re.compile(
        r"^\s*(\d+)\s+(?:(#\d{2}|☆)\s+)?"
        r"([A-Z0-9][A-Z0-9-]+)\s+(.+?)\s+(\(?\d+\)?)\s*$"
    )

    for line in lines[header + 1:]:
        if re.match(r"^\s*14\.\s+", line):
            break
        m = pattern.match(line)
        if m:
            ref, marker, pn, name, qty = m.groups()
            data.append((
                int(ref), marker or "COMMON",
                pn, name.strip(), qty
            ))

    refs = [r[0] for r in data]
    if len(data) != EXPECTED_REFS or refs != list(range(1, 49)):
        raise RuntimeError(
            f"Parsing sumber tidak lengkap: jumlah={len(data)}, REF={refs}"
        )
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file():
        raise SystemExit("Database tidak ditemukan")
    if not TXT.is_file():
        raise SystemExit("File teks katalog tidak ditemukan")
    if not Path("static", IMAGE).is_file():
        raise SystemExit(f"Gambar tidak ditemukan: static/{IMAGE}")

    data = load_source()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")

    try:
        doc = con.execute(
            "SELECT source_url FROM documents WHERE id=? AND machine_id=?",
            (DOCUMENT_ID, MACHINE_ID)
        ).fetchone()
        if not doc or not doc["source_url"]:
            raise RuntimeError("Dokumen Parts List 136 tidak valid")
        source_url = doc["source_url"]

        existing_component = con.execute("""
            SELECT id FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, TITLE)).fetchall()
        if existing_component:
            raise RuntimeError(
                f"Komponen utama sudah ada: {[r['id'] for r in existing_component]}"
            )

        catalog_ref_component = con.execute("""
            SELECT id,component_name FROM components
            WHERE machine_id=? AND CAST(catalog_ref AS INTEGER)=13
        """, (MACHINE_ID,)).fetchall()
        if catalog_ref_component:
            raise RuntimeError(
                f"catalog_ref 13 sudah dipakai: "
                f"{[dict(r) for r in catalog_ref_component]}"
            )

        old = con.execute(
            "SELECT * FROM components WHERE id=? AND machine_id=?",
            (OLD_COMPONENT_ID, MACHINE_ID)
        ).fetchone()
        if not old:
            raise RuntimeError("Komponen lama ID454 tidak ditemukan")

        old_relations = [
            tuple(r) for r in con.execute("""
                SELECT component_id,part_id,relation_type,notes
                FROM component_parts
                WHERE component_id=?
                ORDER BY part_id,relation_type,notes
            """, (OLD_COMPONENT_ID,))
        ]
        if len(old_relations) != 12:
            raise RuntimeError(
                f"Relasi lama ID454 berubah: {len(old_relations)}, "
                "seharusnya 12"
            )

        mapped = {}
        missing = []
        duplicates = []

        for ref, marker, pn, name, qty in data:
            rows = con.execute("""
                SELECT * FROM parts
                WHERE machine_id=? AND part_number=?
                  AND CAST(catalog_ref AS INTEGER)=?
                ORDER BY id
            """, (MACHINE_ID, pn, ref)).fetchall()

            if len(rows) > 1:
                exact = [
                    r for r in rows
                    if str(r["quantity_raw"]) == qty
                    and (r["note"] or "COMMON") == marker
                ]
                if len(exact) == 1:
                    mapped[ref] = exact[0]
                else:
                    duplicates.append((
                        ref, pn,
                        [(r["id"], r["quantity_raw"], r["note"])
                         for r in rows]
                    ))
            elif len(rows) == 1:
                r = rows[0]
                if (str(r["quantity_raw"]) != qty
                        or (r["note"] or "COMMON") != marker):
                    duplicates.append((
                        ref, pn,
                        [(r["id"], r["quantity_raw"], r["note"])]
                    ))
                else:
                    mapped[ref] = r
            else:
                missing.append(ref)

        if duplicates:
            raise RuntimeError(f"Kandidat ganda: {duplicates}")

        print("=== PREFLIGHT SECTION 13 ===")
        print("Judul:", TITLE)
        print("Total REF katalog:", len(data))
        print("Part terpetakan:", len(mapped))
        print("Part baru:", len(missing), missing)
        print("Relasi lama ID454:", len(old_relations))
        print("Komponen utama sudah ada:", len(existing_component))
        print("Komponen catalog_ref 13 lain:", len(catalog_ref_component))
        print("Gambar tersedia:", Path("static", IMAGE).is_file())

        print("\n=== PEMETAAN PART ===")
        for ref, marker, pn, name, qty in data:
            row = mapped.get(ref)
            print(
                f"REF {ref:02} | {pn} | {marker} | "
                f"{'ID '+str(row['id']) if row else 'BARU'} | {name} | {qty}"
            )

        if len(mapped) != 31 or missing != [
            1,3,4,6,7,8,9,10,11,12,14,15,17,19,21,22,28
        ]:
            # Perbedaan mapping harus diperiksa manual sebelum apply.
            print("\nPERINGATAN: pola mapping berbeda dari rencana awal.")
            if not args.apply:
                print("DRY-RUN SAJA. Database belum diubah.")
                return
            raise RuntimeError("Mapping tidak sesuai rencana awal")

        if not args.apply:
            print("\nDRY-RUN SAJA. Database belum diubah.")
            return

        backup = Path(
            "database",
            "garment-before-ams210en1510-section13-"
            + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
        )
        shutil.copy2(DB, backup)
        print("\nBackup dibuat:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")
            part_ids = {}

            for ref, marker, pn, name, qty in data:
                quantity = int(qty.strip("()"))
                row = mapped.get(ref)

                if row:
                    # Pertahankan metadata dan relasi part lama.
                    part_id = row["id"]
                else:
                    cur = con.execute("""
                        INSERT INTO parts (
                            machine_id,source_document_id,part_number,
                            part_name,quantity,catalog_ref,diagram_page,
                            note,source_url,notes,quantity_raw
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        MACHINE_ID, DOCUMENT_ID, pn, name,
                        quantity, ref, PAGE, marker,
                        source_url, STAGING_NOTE, qty
                    ))
                    part_id = cur.lastrowid

                part_ids[ref] = part_id

            cur = con.execute("""
                INSERT INTO components (
                    machine_id,component_name,part_number,location,
                    function,notes,image_path,source_url,
                    catalog_ref,diagram_page
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                MACHINE_ID, TITLE, None,
                "Mekanisme penggerak meja X-Y",
                "Menggerakkan dan memandu meja pada sumbu X dan Y",
                "Section utama katalog Parts List AMS-210EN-1510",
                IMAGE, source_url, "13", PAGE
            ))
            component_id = cur.lastrowid

            for ref in range(1, 49):
                con.execute("""
                    INSERT INTO component_parts (
                        component_id,part_id,relation_type,notes
                    ) VALUES (?,?,?,?)
                """, (
                    component_id, part_ids[ref],
                    "catalog_component_part", f"REF {ref}"
                ))

            current_old_relations = [
                tuple(r) for r in con.execute("""
                    SELECT component_id,part_id,relation_type,notes
                    FROM component_parts
                    WHERE component_id=?
                    ORDER BY part_id,relation_type,notes
                """, (OLD_COMPONENT_ID,))
            ]
            if current_old_relations != old_relations:
                raise RuntimeError("Relasi lama ID454 berubah")

            count = con.execute("""
                SELECT COUNT(*) FROM component_parts
                WHERE component_id=?
            """, (component_id,)).fetchone()[0]
            if count != EXPECTED_REFS:
                raise RuntimeError(f"Relasi baru tidak lengkap: {count}")

            con.commit()
            print(
                f"\nAPPLY BERHASIL | Component ID: {component_id} "
                f"| Relasi: {count}"
            )
            print("Relasi lama ID454 dipertahankan:", len(old_relations))
            print("Backup:", backup)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
