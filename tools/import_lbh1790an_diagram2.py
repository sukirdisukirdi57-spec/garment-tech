import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")

MACHINE_ID = 6
DOCUMENT_ID = 119
DIAGRAM_PAGE = 3

# Kelompok pertama: REF 27–49
MAIN_REF_1 = "27"
COMPONENT_NAME_1 = "ASSY_BTW"
REFS_1 = list(range(27, 50))

# Kelompok kedua: REF 59–64
MAIN_REF_2 = "59"
COMPONENT_ID_2 = 228
REFS_2 = list(range(59, 65))


def get_parts(con, refs):
    placeholders = ",".join("?" for _ in refs)
    return con.execute(f"""
        SELECT id, catalog_ref, part_number, part_name, note
        FROM parts
        WHERE machine_id=?
          AND source_document_id=?
          AND diagram_page=?
          AND CAST(catalog_ref AS INTEGER) IN ({placeholders})
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, DOCUMENT_ID, DIAGRAM_PAGE, *refs)).fetchall()


def main():
    apply = "--apply" in sys.argv

    if not DB.exists():
        raise SystemExit("Database tidak ditemukan.")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        # Pastikan komponen REF 27 belum ada.
        existing_27 = con.execute("""
            SELECT id FROM components
            WHERE machine_id=?
              AND diagram_page=?
              AND catalog_ref=?
        """, (MACHINE_ID, DIAGRAM_PAGE, MAIN_REF_1)).fetchone()

        if existing_27:
            raise ValueError(
                f"Komponen REF 27 sudah ada (ID {existing_27['id']})."
            )

        # Pastikan komponen REF 59 adalah ID 228.
        component_59 = con.execute("""
            SELECT id, component_name, catalog_ref
            FROM components
            WHERE id=? AND machine_id=?
        """, (COMPONENT_ID_2, MACHINE_ID)).fetchone()

        if not component_59:
            raise ValueError("Komponen ID 228 tidak ditemukan.")

        if str(component_59["catalog_ref"]) != MAIN_REF_2:
            raise ValueError(
                "ID 228 bukan komponen dengan catalog REF 59."
            )

        parts_1 = get_parts(con, REFS_1)
        parts_2 = get_parts(con, REFS_2)

        for label, parts, expected in (
            ("REF 27–49", parts_1, REFS_1),
            ("REF 59–64", parts_2, REFS_2),
        ):
            found = [int(p["catalog_ref"]) for p in parts]
            if found != expected:
                raise ValueError(
                    f"{label} tidak lengkap/duplikat: {found}"
                )

            for p in parts:
                duplicate = con.execute("""
                    SELECT cp.component_id, c.component_name
                    FROM component_parts cp
                    JOIN components c ON c.id=cp.component_id
                    WHERE cp.part_id=?
                """, (p["id"],)).fetchall()

                if duplicate:
                    raise ValueError(
                        f"REF {p['catalog_ref']} sudah memiliki relasi: "
                        f"{[tuple(x) for x in duplicate]}"
                    )

        print("=== PREFLIGHT DIAGRAM 2 ===")
        print("\nKELOMPOK 1: ASSY_BTW")
        for p in parts_1:
            print(
                f"REF {p['catalog_ref']} | ID {p['id']} | "
                f"{p['part_number']} | {p['part_name']}"
            )

        print("\nKELOMPOK 2: BOBBIN THREAD TENSION ASM.")
        for p in parts_2:
            print(
                f"REF {p['catalog_ref']} | ID {p['id']} | "
                f"{p['part_number']} | {p['part_name']}"
            )

        print("\nKomponen baru:", COMPONENT_NAME_1)
        print("Komponen yang digunakan:", component_59["component_name"])
        print("Relasi kelompok 1:", len(parts_1))
        print("Relasi kelompok 2:", len(parts_2))
        print("Total relasi:", len(parts_1) + len(parts_2))

        if not apply:
            print("\nDRY-RUN: belum ada perubahan database.")
            return

        # Backup sebelum transaksi perubahan.
        con.commit()
        backup = BACKUP_DIR / (
            "garment-before-lbh1790an-diagram2-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )
        shutil.copy2(DB, backup)
        print("\nBackup:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")

            main_part_1 = next(
                p for p in parts_1
                if str(p["catalog_ref"]) == MAIN_REF_1
            )

            cur = con.execute("""
                INSERT INTO components (
                    machine_id, component_name, part_number,
                    location, function, notes, image_path,
                    source_url, catalog_ref, diagram_page
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                COMPONENT_NAME_1,
                main_part_1["part_number"],
                "Diagram 2",
                "BTW assembly",
                "Catalog REF 27–49; main REF 27",
                "component_images/lbh1790an_diagram2.png",
                None,
                MAIN_REF_1,
                DIAGRAM_PAGE
            ))

            component_id_1 = cur.lastrowid

            for component_id, parts in (
                (component_id_1, parts_1),
                (COMPONENT_ID_2, parts_2),
            ):
                for p in parts:
                    con.execute("""
                        INSERT INTO component_parts (
                            component_id, part_id,
                            relation_type, notes
                        )
                        VALUES (?, ?, ?, ?)
                    """, (
                        component_id,
                        p["id"],
                        "catalog_component_part",
                        f"REF {p['catalog_ref']}"
                    ))

            for component_id, expected_count in (
                (component_id_1, 23),
                (COMPONENT_ID_2, 6),
            ):
                count = con.execute("""
                    SELECT COUNT(*)
                    FROM component_parts
                    WHERE component_id=?
                """, (component_id,)).fetchone()[0]

                if count != expected_count:
                    raise ValueError(
                        f"Validasi ID {component_id} gagal: "
                        f"{count}, seharusnya {expected_count}."
                    )

            con.commit()

            print("\nIMPORT BERHASIL")
            print("Komponen baru ID:", component_id_1)
            print("Relasi ASSY_BTW:", 23)
            print("Relasi Bobbin Thread Tension:", 6)
            print("Total relasi ditambahkan:", 29)

        except Exception:
            con.rollback()
            raise

    finally:
        con.close()


if __name__ == "__main__":
    main()
