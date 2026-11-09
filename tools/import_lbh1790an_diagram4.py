import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = Path("static/component_images/lbh1790an_diagram4.png")
IMAGE_PATH = "component_images/lbh1790an_diagram4.png"

MACHINE = 6
DOC = 119
PAGE = 7

COMPONENT_NAME = "HOOK SLEEVE CONNEC."
MAIN_REF = 30

GROUP = [
    (30, "137-29652"),
    (31, "137-29603"),
    (32, "CQ-2520000-00"),
    (33, "HX-0025500-00"),
]


def get_part(con, ref):
    return con.execute("""
        SELECT id, catalog_ref, part_number, part_name,
               quantity, quantity_raw
        FROM parts
        WHERE machine_id=? AND source_document_id=?
          AND diagram_page=? AND catalog_ref=?
    """, (MACHINE, DOC, PAGE, ref)).fetchall()


def preflight(con):
    if not IMAGE.is_file():
        raise RuntimeError("File gambar Diagram 4 tidak ditemukan.")

    existing = con.execute("""
        SELECT id, component_name
        FROM components
        WHERE machine_id=? AND catalog_ref=? AND diagram_page=?
    """, (MACHINE, str(MAIN_REF), PAGE)).fetchall()

    if existing:
        raise RuntimeError(
            f"Komponen REF 30 sudah ada: {existing}"
        )

    print("=== PREFLIGHT DIAGRAM 4 ===")

    for ref, number in GROUP:
        rows = get_part(con, ref)

        if len(rows) != 1:
            raise RuntimeError(
                f"REF {ref}: ditemukan {len(rows)} baris, seharusnya 1."
            )

        part = rows[0]

        if part["part_number"] != number:
            raise RuntimeError(
                f"REF {ref}: nomor part tidak cocok: "
                f"{part['part_number']}"
            )

        rel = con.execute("""
            SELECT COUNT(*)
            FROM component_parts
            WHERE part_id=?
        """, (part["id"],)).fetchone()[0]

        if rel:
            raise RuntimeError(
                f"REF {ref} sudah memiliki {rel} relasi."
            )

        print(
            f"REF {ref} | {number} | "
            f"{part['part_name']} | Relasi {rel}"
        )

    print("\nKomponen: 1")
    print("Jumlah relasi: 4")
    print("PREFLIGHT LULUS.")


def apply_import(con):
    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, part_number,
            catalog_ref, diagram_page, image_path
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        MACHINE,
        COMPONENT_NAME,
        GROUP[0][1],
        str(MAIN_REF),
        PAGE,
        IMAGE_PATH
    ))

    component_id = cur.lastrowid

    for ref, number in GROUP:
        rows = get_part(con, ref)

        if len(rows) != 1 or rows[0]["part_number"] != number:
            raise RuntimeError(f"REF {ref} gagal divalidasi.")

        con.execute("""
            INSERT INTO component_parts (
                component_id, part_id, relation_type, notes
            ) VALUES (?, ?, 'catalog_component_part', ?)
        """, (
            component_id,
            rows[0]["id"],
            f"REF {ref}"
        ))

    count = con.execute("""
        SELECT COUNT(*)
        FROM component_parts
        WHERE component_id=?
    """, (component_id,)).fetchone()[0]

    if count != 4:
        raise RuntimeError(
            f"Jumlah relasi tidak sesuai: {count}"
        )

    print(f"\nKomponen ID {component_id} | {COMPONENT_NAME}")
    print(f"Relasi berhasil dibuat: {count}")

    return component_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")

    try:
        preflight(con)

        if not args.apply:
            print("\nDRY-RUN BERHASIL. Database belum diubah.")
            return

        backup = DB.with_name(
            "garment-before-lbh1790an-diagram4-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )

        backup_con = sqlite3.connect(backup)
        con.backup(backup_con)
        backup_con.close()

        print("Backup:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")
            component_id = apply_import(con)

            con.commit()
            print("\nIMPORT BERHASIL. Transaksi tersimpan.")

        except Exception:
            con.rollback()
            print("\nIMPORT GAGAL. Transaksi dibatalkan.")
            raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
