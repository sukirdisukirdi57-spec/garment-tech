
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
MACHINE_ID = 44

# Baris thread trimmer yang salah ditempatkan di Section 12.
DELETE_IDS = {
    7574: ("400-30934", 24),
    7575: ("B2424-210-000", 25),
    7576: ("B2418-280-000", 30),
    7577: ("B2416-280-000", 31),
    7578: ("B2415-280-0A0", 32),
    7579: ("SS-7090410-SP", 33),
    7580: ("B2414-280-0A0", 34),
    7581: ("SS-1060210-TP", 35),
    7582: ("B2417-210-000", 36),
    7583: ("WP-0450846-SP", 37),
    7584: ("B2417-280-000", 38),
    7585: ("SS-7110740-TP", 39),
}

# Baris thread clamp yang salah ditempatkan di Section 13.
MOVE_IDS = {
    7604: ("400-06768", 19),
    7605: ("SM-2360110-TP", 20),
    7606: ("SM-6040650-TP", 21),
    7607: ("400-10527", 22),
    7608: ("400-10528", 23),
    7609: ("400-11152", 24),
    7610: ("SD-0800407-TP", 25),
    7611: ("400-30940", 26),
    7612: ("SD-0350156-TP", 27),
    7613: ("400-33191", 28),
    7614: ("SM-6030502-TP", 29),
    7615: ("400-85033", 30),
    7616: ("SM-6041202-TP", 31),
    7617: ("SM-6040602-TP", 32),
    7618: ("400-32508", 33),
    7619: ("400-33190", 34),
    7620: ("HD-0020400-0A", 35),
    7621: ("HD-0020400-0B", 36),
    7622: ("SM-6020450-TP", 37),
    7623: ("NM-6030003-SC", 39),
}

def section_note(section):
    return f"AMS-210EN catalog staging; section {section}"

def main():
    if not DB.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"garment-before-fix-thread-clamp-{stamp}.db"

    # Pastikan database bisa dibuka sebelum membuat backup.
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        con.execute("PRAGMA foreign_keys=ON")
        columns = [
            row["name"]
            for row in con.execute("PRAGMA table_info(parts)")
        ]
        if not columns:
            raise RuntimeError("Tabel parts tidak ditemukan.")

        # Pastikan semua baris target cocok dengan kondisi yang diharapkan.
        for part_id, (part_number, ref) in DELETE_IDS.items():
            row = con.execute("""
                SELECT id, part_number, catalog_ref, notes
                FROM parts
                WHERE id=? AND machine_id=?
            """, (part_id, MACHINE_ID)).fetchone()

            if not row:
                raise RuntimeError(
                    f"Baris target penghapusan tidak ditemukan: ID {part_id}"
                )
            if row["part_number"] != part_number:
                raise RuntimeError(
                    f"Part number tidak cocok untuk ID {part_id}: "
                    f"{row['part_number']}"
                )
            if row["catalog_ref"] != ref or "section 12" not in row["notes"]:
                raise RuntimeError(
                    f"REF/section tidak sesuai untuk ID {part_id}"
                )

            # Pastikan pasangan katalog yang sama sudah ada di Section 11.
            matches = con.execute("""
                SELECT id, part_name, quantity_raw
                FROM parts
                WHERE machine_id=?
                  AND part_number=?
                  AND catalog_ref=?
                  AND notes LIKE '%section 11%'
            """, (MACHINE_ID, part_number, ref)).fetchall()

            if len(matches) != 1:
                raise RuntimeError(
                    f"Pasangan Section 11 untuk ID {part_id} "
                    f"tidak unik: ditemukan {len(matches)}"
                )

            if row["part_number"] != part_number:
                raise RuntimeError("Validasi part number gagal.")

        for part_id, (part_number, ref) in MOVE_IDS.items():
            row = con.execute("""
                SELECT id, part_number, catalog_ref, notes
                FROM parts
                WHERE id=? AND machine_id=?
            """, (part_id, MACHINE_ID)).fetchone()

            if not row:
                raise RuntimeError(
                    f"Baris target pemindahan tidak ditemukan: ID {part_id}"
                )
            if (
                row["part_number"] != part_number
                or row["catalog_ref"] != ref
                or "section 13" not in row["notes"]
            ):
                raise RuntimeError(
                    f"Part/REF/section tidak sesuai untuk ID {part_id}"
                )

        # REF 38 belum boleh ada di Section 12.
        existing_38 = con.execute("""
            SELECT id, part_number
            FROM parts
            WHERE machine_id=?
              AND catalog_ref=38
              AND notes LIKE '%section 12%'
              AND id NOT IN (?)
        """, (MACHINE_ID, 7584)).fetchall()

        if existing_38:
            raise RuntimeError(
                f"REF 38 sudah ditempati baris lain di Section 12: "
                f"{[dict(r) for r in existing_38]}"
            )

        # Backup saat koneksi tidak sedang memiliki transaksi tulis.
        con.close()
        shutil.copy2(DB, backup)
        print("BACKUP:", backup)

        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("BEGIN IMMEDIATE")

        # Pindahkan thread clamp dari Section 13 ke Section 12.
        for part_id in MOVE_IDS:
            con.execute("""
                UPDATE parts
                SET notes=?
                WHERE id=? AND machine_id=44
            """, (section_note(12), part_id))

        if con.execute("SELECT changes()").fetchone()[0] < 0:
            raise RuntimeError("Gagal memindahkan baris.")

        # Hapus salinan thread trimmer dari Section 12.
        for part_id in DELETE_IDS:
            con.execute("""
                DELETE FROM parts
                WHERE id=? AND machine_id=44
            """, (part_id,))
            if con.execute("SELECT changes()").fetchone()[0] != 1:
                raise RuntimeError(
                    f"Gagal menghapus tepat satu baris: ID {part_id}"
                )

        # Tambahkan REF 38 dengan menyalin nilai REF 27 yang identik.
        # Semua kolom lain dipertahankan, kecuali ID, catalog_ref, notes.
        source = con.execute("""
            SELECT *
            FROM parts
            WHERE id=7612 AND machine_id=44
        """).fetchone()

        if not source or source["part_number"] != "SD-0350156-TP":
            raise RuntimeError("Baris sumber REF 27 tidak cocok.")

        insert_columns = [c for c in columns if c != "id"]
        values = []
        for col in insert_columns:
            if col == "catalog_ref":
                values.append(38)
            elif col == "notes":
                values.append(section_note(12))
            else:
                values.append(source[col])

        placeholders = ", ".join("?" for _ in insert_columns)
        names = ", ".join(f'"{c}"' for c in insert_columns)

        con.execute(
            f"INSERT INTO parts ({names}) VALUES ({placeholders})",
            values
        )

        # Audit Section 12: REF 1–39 harus lengkap dan unik.
        s12 = con.execute("""
            SELECT id, part_number, catalog_ref
            FROM parts
            WHERE machine_id=44
              AND notes LIKE '%section 12%'
            ORDER BY catalog_ref
        """).fetchall()

        refs12 = [r["catalog_ref"] for r in s12]
        if len(s12) != 39 or refs12 != list(range(1, 40)):
            raise RuntimeError(
                f"Audit Section 12 gagal: jumlah={len(s12)}, REF={refs12}"
            )

        # Pastikan semua komponen X-Y yang sudah ada tetap ada.
        x_y_ids = set(range(7624, 7633))
        still_present = {
            r["id"]
            for r in con.execute("""
                SELECT id FROM parts WHERE machine_id=44
            """)
        }
        if not x_y_ids.issubset(still_present):
            raise RuntimeError("Ada baris X-Y yang hilang.")

        # Section 13 tidak boleh lagi berisi 20 baris thread clamp tersebut.
        remaining = con.execute("""
            SELECT id, part_number
            FROM parts
            WHERE machine_id=44
              AND id BETWEEN 7604 AND 7623
              AND notes LIKE '%section 13%'
        """).fetchall()
        if remaining:
            raise RuntimeError(
                f"Masih ada baris thread clamp di Section 13: "
                f"{[dict(r) for r in remaining]}"
            )

        con.commit()

        print("\nBERHASIL")
        print("Baris thread clamp dipindahkan:", len(MOVE_IDS))
        print("Duplikat thread trimmer dihapus:", len(DELETE_IDS))
        print("REF 38 ditambahkan: SD-0350156-TP")
        print("Section 12: 39 baris, REF 1–39 lengkap dan unik.")
        print("Baris X-Y ID 7624–7632 tetap ada.")
        print("Backup:", backup)

    except Exception:
        if con:
            con.rollback()
        raise
    finally:
        if con:
            con.close()

if __name__ == "__main__":
    main()
