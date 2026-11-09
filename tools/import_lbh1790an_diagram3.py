import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram3.png")
IMAGE_PATH = "component_images/lbh1790an_diagram3.png"

MACHINE = 6
DOC = 119
PAGE = 5

GROUPS = [
    (2, "IDLER_ASSY", [
        (2, "401-42152"), (3, "RC-3781518-KP"),
        (4, "RC-0100001-KP"), (5, "401-43150"),
        (6, "401-41721"), (7, "SB-1100007-00"),
        (8, "NM-6100001-SD"), (9, "401-41720")
    ]),
    (10, "SQUARE_BLOCK_GUIDE_ASM", [
        (10, "401-44351"), (11, "401-41725"),
        (12, "401-41726"), (13, "401-42878"),
        (14, "SM-80404A2-TP")
    ]),
    (15, "COUPLING ASM.", [
        (15, "400-51473"), (16, "400-51474"),
        (17, "SM-80608A2-TP")
    ]),
    (29, "THRUST COLLAR", [
        (29, "400-32269"), (30, "SM-80506A2-TP"),
        (31, "CS-1000881-TP")
    ])
]

MISSING = {
    10: ("401-44351", "SQUARE_BLOCK_GUIDE_ASM", 1, "1"),
    14: ("SM-80404A2-TP", "SCREW M4 L=4", None, "(1)")
}


def part_rows(con, ref):
    return con.execute("""
        SELECT id, part_number, part_name, quantity,
               quantity_raw, catalog_ref, diagram_page
        FROM parts
        WHERE machine_id=? AND source_document_id=?
          AND diagram_page=? AND catalog_ref=?
    """, (MACHINE, DOC, PAGE, ref)).fetchall()


def preflight(con):
    if not IMAGE.is_file():
        raise RuntimeError("Gambar Diagram 3 tidak ditemukan.")

    print("=== PREFLIGHT DIAGRAM 3 ===")
    missing = []

    for main_ref, name, refs in GROUPS:
        existing_component = con.execute("""
            SELECT id, component_name
            FROM components
            WHERE machine_id=? AND catalog_ref=? AND diagram_page=?
        """, (MACHINE, str(main_ref), PAGE)).fetchall()

        if existing_component:
            raise RuntimeError(
                f"Komponen REF {main_ref} sudah ada: {existing_component}"
            )

        for ref, number in refs:
            rows = part_rows(con, ref)

            if len(rows) == 0 and ref in MISSING:
                missing.append(ref)
                print(f"REF {ref} | {number} | BELUM ADA, akan ditambahkan")
                continue

            if len(rows) != 1:
                raise RuntimeError(
                    f"REF {ref}: jumlah baris database {len(rows)}"
                )

            row = rows[0]
            if row["part_number"] != number:
                raise RuntimeError(
                    f"REF {ref}: nomor part tidak cocok: {row['part_number']}"
                )

            rel = con.execute("""
                SELECT COUNT(*) FROM component_parts WHERE part_id=?
            """, (row["id"],)).fetchone()[0]

            if rel:
                raise RuntimeError(
                    f"REF {ref} sudah memiliki {rel} relasi"
                )

            print(f"REF {ref} | {number} | Relasi 0")

    for ref, data in MISSING.items():
        if ref not in missing:
            continue
        duplicate = con.execute("""
            SELECT id, part_number, catalog_ref, diagram_page
            FROM parts
            WHERE machine_id=? AND source_document_id=?
              AND part_number=?
        """, (MACHINE, DOC, data[0])).fetchall()

        if duplicate:
            raise RuntimeError(
                f"Nomor part {data[0]} sudah ada: {duplicate}"
            )

    # REF 30 wajib berjumlah dua baut.
    bolt = part_rows(con, 30)
    if len(bolt) != 1 or bolt[0]["part_number"] != "SM-80506A2-TP":
        raise RuntimeError("Data REF 30 tidak valid.")

    if bolt[0]["quantity"] not in (None, 2):
        raise RuntimeError("Quantity REF 30 bukan 2.")

    if bolt[0]["quantity_raw"] not in ("(2)", "2"):
        raise RuntimeError(
            f"quantity_raw REF 30 tidak sesuai: {bolt[0]['quantity_raw']}"
        )

    print("\nREF yang akan ditambahkan:", missing)
    print("Jumlah kelompok:", len(GROUPS))
    print("Jumlah relasi:", sum(len(g[2]) for g in GROUPS))
    print("PREFLIGHT LULUS.")
    return missing


def apply_import(con, missing):
    for ref in missing:
        number, name, qty, raw = MISSING[ref]
        con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number,
                part_name, quantity, catalog_ref, diagram_page,
                note, source_url, notes, quantity_raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
        """, (MACHINE, DOC, number, name, qty, ref, PAGE, "＊", raw))
        print(f"Tambah REF {ref}: {number}")

    for main_ref, name, refs in GROUPS:
        main_number = refs[0][1]

        cur = con.execute("""
            INSERT INTO components (
                machine_id, component_name, part_number,
                catalog_ref, diagram_page, image_path
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (MACHINE, name, main_number, str(main_ref), PAGE, IMAGE_PATH))

        component_id = cur.lastrowid

        for ref, number in refs:
            rows = part_rows(con, ref)
            if len(rows) != 1 or rows[0]["part_number"] != number:
                raise RuntimeError(f"REF {ref} gagal ditemukan setelah insert.")

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                ) VALUES (?, ?, 'catalog_component_part', ?)
            """, (component_id, rows[0]["id"], f"REF {ref}"))

        count = con.execute("""
            SELECT COUNT(*) FROM component_parts WHERE component_id=?
        """, (component_id,)).fetchone()[0]

        if count != len(refs):
            raise RuntimeError(f"Relasi {name} tidak lengkap.")

        print(
            f"Komponen ID {component_id} | {name} | "
            f"{count} relasi"
        )

    con.execute("""
        UPDATE parts SET quantity=2
        WHERE machine_id=? AND source_document_id=?
          AND diagram_page=? AND catalog_ref=30
          AND part_number='SM-80506A2-TP'
          AND quantity IS NULL
    """, (MACHINE, DOC, PAGE))

    bolt = part_rows(con, 30)[0]
    if bolt["quantity"] != 2:
        raise RuntimeError("Validasi kuantitas baut REF 30 gagal.")

    # Validasi akhir: empat komponen dan 19 relasi.
    component_count = con.execute("""
        SELECT COUNT(*) FROM components
        WHERE machine_id=? AND diagram_page=?
          AND catalog_ref IN ('2','10','15','29')
    """, (MACHINE, PAGE)).fetchone()[0]

    relation_count = con.execute("""
        SELECT COUNT(*)
        FROM component_parts cp
        JOIN components c ON c.id=cp.component_id
        WHERE c.machine_id=? AND c.diagram_page=?
          AND c.catalog_ref IN ('2','10','15','29')
    """, (MACHINE, PAGE)).fetchone()[0]

    if component_count != 4 or relation_count != 19:
        raise RuntimeError(
            f"Validasi akhir gagal: komponen={component_count}, "
            f"relasi={relation_count}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")

    try:
        missing = preflight(con)

        if not args.apply:
            print("\nDRY-RUN BERHASIL. Database belum diubah.")
            return

        backup = DB.with_name(
            "garment-before-lbh1790an-diagram3-"
            + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
        )

        backup_con = sqlite3.connect(backup)
        con.backup(backup_con)
        backup_con.close()
        print("Backup:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")
            apply_import(con, missing)
            con.commit()
            print("\nIMPORT BERHASIL. Transaksi tersimpan.")
        except Exception:
            con.rollback()
            print("\nIMPORT GAGAL. Seluruh transaksi dibatalkan.")
            raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
