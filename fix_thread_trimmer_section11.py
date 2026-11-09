
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("backups")
MACHINE_ID = 44

# REF, part number, description, quantity, raw quantity, catalog note
NEW_ROWS = [
    (4,  "235-17501",     "NEEDLE CAM ROLLER A",            1, "(1)", "#01"),
    (5,  "235-17600",     "NEEDLE CAM ROLLER B",            1, "(1)", "#01"),
    (6,  "235-17709",     "NEEDLE CAM ROLLER C",            1, "(1)", "#01"),
    (7,  "235-17808",     "NEEDLE CAM ROLLER D",            1, "(1)", "#01"),
    (17, "400-30933",     "NEEDLE_PLATE_H_ASM.",            1, "1",   "#02"),
    (18, "400-73085",     "NEEDLE_PLATE_H_2.4_ASM.",        1, "1",   "#04"),
    (20, "B2423-280-00D", "MOVING KNIFE WASHER D",          1, "(1)", "#01"),
    (21, "B2423-280-00C", "MOVING KNIFE WASHER C",          1, "(1)", "#01"),
    (22, "B2423-280-00A", "MOVING KNIFE WASHER A",          1, "(1)", "#01"),
    (23, "B2423-280-00B", "MOVING KNIFE WASHER B",          1, "(1)", "#01"),
    (24, "400-30934",     "NEEDLE_PLATE",                   1, "(1)", ""),
    (25, "B2424-210-000", "COUNTER KNIFE",                  1, "(1)", ""),
    (26, "B2426-210-00A", "NEEDLE HOLE GUIDE D=1.6",        1, "(1)", "☆ #03"),
    (27, "B2426-210-00B", "NEEDLE HOLE GUIDE D=2.0",        1, "(1)", "☆ #02"),
    (28, "B2426-210-00D", "NEEDLE HOLE GUIDE D=2.4",        1, "(1)", "☆ #04"),
    (29, "B2421-210-AA0", "MOVING KNIFE COMPL.",            1, "(1)", "☆"),
    (30, "B2418-280-000", "MOVING KNIFE LINK",              1, "(1)", ""),
    (31, "B2416-280-000", "THREAD CUTTING LEVER RING",      1, "(1)", ""),
    (32, "B2415-280-0A0", "THREAD CUTTER LEVER ASM. SMALL", 1, "(1)", ""),
    (33, "SS-7090410-SP", "SCREW 9/64-40 L=3.5",            1, "(1)", ""),
    (34, "B2414-280-0A0", "THREAD CUTTER LEVER ASM. LARGE", 1, "(1)", ""),
    (35, "SS-1060210-TP", "SCREW 3/32-56 L=2.2",            2, "(2)", ""),
    (36, "B2417-210-000", "MOVING KNIFE HINGE SCREW",       1, "(1)", ""),
    (37, "WP-0450846-SP", "WASHER",                         1, "(1)", ""),
    (38, "B2417-280-000", "THREAD CUTTER LEVER SHAFT",      1, "(1)", ""),
    (39, "SS-7110740-TP", "SCREW 11/64-40 L=7",             1, "(1)", ""),
    (40, "401-56892",     "STAINLESS_NEEDLE_PLATE_H_ASSY",  1, "1",   "#05"),
    (41, "402-39626",     "STAINLESS_NEEDLE_PLATE_S_ASSY",  1, "1",   "#06"),
    (42, "401-56890",     "STAINLESS_NEEDLE_PLATE",         1, "(1)", "#07"),
]

# REF 1–3, 8–15, dan 19 sudah terdaftar di Section 11.
EXPECTED_EXISTING = {
    1:  ("400-30936", "THREAD_TRIMMER_CAM", "1"),
    2:  ("SM-8050592-TP", "SCREW", "2"),
    3:  ("SM-1040650-TP", "SCREW", "4"),
    8:  ("400-40256", "ROLLER_SHAFT", "1"),
    9:  ("NM-6040001-SP", "NUT M4X0.7", "2"),
    10: ("400-72228", "THREAD_TRIMMER_LINK_ASM", "1"),
    11: ("SD-0800327-TP", "SHOULDER SCREW", "1"),
    12: ("NM-6050001-SP", "NUT M5", "1"),
    13: ("400-23624", "THREAD_TRIMMER_SHAFT", "1"),
    14: ("SM-8060812-TP", "SCREW M6 L=8", "2"),
    15: ("400-30935", "CONNECTING_BAR", "1"),
    16: ("400-30932", "NEEDLE_PLATE_ASM.", "1"),
    19: ("SS-6110430-TP", "SCREW 11/64-40 L=4.0", "(1)"),
}

DUPLICATE_IDS = list(range(7548, 7561))


def section_rows(con, section):
    return con.execute("""
        SELECT id, catalog_ref, part_number, part_name,
               quantity_raw, notes
        FROM parts
        WHERE machine_id = ?
          AND notes LIKE ?
        ORDER BY CAST(catalog_ref AS INTEGER), id
    """, (MACHINE_ID, f"%section {section}%")).fetchall()


def main():
    if not DB.is_file():
        raise FileNotFoundError(f"Database tidak ditemukan: {DB}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Periksa semua prasyarat sebelum membuat perubahan.
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        duplicate_rows = con.execute("""
            SELECT id, catalog_ref, part_number, part_name, quantity_raw, notes
            FROM parts
            WHERE machine_id = ?
              AND id BETWEEN 7548 AND 7560
            ORDER BY id
        """, (MACHINE_ID,)).fetchall()

        if [r["id"] for r in duplicate_rows] != DUPLICATE_IDS:
            raise RuntimeError(
                "ID 7548–7560 tidak sesuai kondisi yang diharapkan. "
                "Tidak ada perubahan dilakukan."
            )

        # Setiap baris salah label harus mempunyai pasangan Section 10
        # dengan REF, part number, nama, dan quantity_raw yang sama.
        for r in duplicate_rows:
            matches = con.execute("""
                SELECT id
                FROM parts
                WHERE machine_id = ?
                  AND catalog_ref = ?
                  AND part_number = ?
                  AND part_name = ?
                  AND quantity_raw = ?
                  AND notes LIKE '%section 10%'
            """, (
                MACHINE_ID, r["catalog_ref"], r["part_number"],
                r["part_name"], r["quantity_raw"]
            )).fetchall()

            if not matches:
                raise RuntimeError(
                    f"Duplikat ID {r['id']} tidak terverifikasi "
                    "terhadap Section 10. Tidak ada perubahan dilakukan."
                )

        # Verifikasi daftar Section 11 saat ini setelah mengabaikan
        # ID duplikat yang akan dihapus.
        actual_existing = {}
        for r in con.execute("""
            SELECT catalog_ref, part_number, part_name, quantity_raw
            FROM parts
            WHERE machine_id = ?
              AND notes LIKE '%section 11%'
              AND id NOT IN (
                  7548,7549,7550,7551,7552,7553,7554,
                  7555,7556,7557,7558,7559,7560
              )
        """, (MACHINE_ID,)):
            ref = r["catalog_ref"]
            if ref in actual_existing:
                raise RuntimeError(f"REF {ref} ganda di Section 11.")
            actual_existing[ref] = (
                r["part_number"], r["part_name"], r["quantity_raw"]
            )

        if actual_existing != EXPECTED_EXISTING:
            raise RuntimeError(
                "Data Section 11 tidak cocok dengan prasyarat. "
                "Tidak ada perubahan dilakukan."
            )

        # Backup SQLite yang konsisten.
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / f"garment-before-fix-thread-trimmer-{stamp}.db"

        backup_con = sqlite3.connect(backup)
        con.backup(backup_con)
        backup_con.close()
        print(f"BACKUP: {backup}")

        # Transaksi dimulai setelah semua prasyarat terverifikasi.
        con.execute("BEGIN IMMEDIATE")

        deleted = con.execute("""
            DELETE FROM parts
            WHERE machine_id = ?
              AND id BETWEEN 7548 AND 7560
        """, (MACHINE_ID,)).rowcount

        if deleted != 13:
            raise RuntimeError(f"Jumlah duplikat terhapus {deleted}, bukan 13.")

        # Pastikan REF yang akan ditambahkan benar-benar belum ada.
        remaining_refs = {
            r["catalog_ref"] for r in con.execute("""
                SELECT catalog_ref FROM parts
                WHERE machine_id = ?
                  AND notes LIKE '%section 11%'
            """, (MACHINE_ID,))
        }

        to_insert = [row for row in NEW_ROWS if row[0] not in remaining_refs]

        # Jika REF sudah ada, pastikan datanya identik.
        for ref, part_no, name, qty, raw, note in NEW_ROWS:
            if ref in remaining_refs:
                existing = con.execute("""
                    SELECT part_number, part_name, quantity_raw
                    FROM parts
                    WHERE machine_id = ?
                      AND catalog_ref = ?
                      AND notes LIKE '%section 11%'
                """, (MACHINE_ID, ref)).fetchall()

                if len(existing) != 1 or (
                    existing[0]["part_number"],
                    existing[0]["part_name"],
                    existing[0]["quantity_raw"]
                ) != (part_no, name, raw):
                    raise RuntimeError(
                        f"REF {ref} sudah ada tetapi datanya berbeda."
                    )

        for ref, part_no, name, qty, raw, catalog_note in to_insert:
            notes = "AMS-210EN catalog staging; section 11"

            if catalog_note:
                if catalog_note.startswith("☆"):
                    rest = catalog_note.replace("☆", "", 1).strip()
                    notes += "; catalog NOTE ☆"
                    if rest:
                        notes += f" {rest}"
                else:
                    notes += f"; catalog NOTE {catalog_note}"

            con.execute("""
                INSERT INTO parts (
                    machine_id, part_number, part_name, quantity,
                    catalog_ref, notes, quantity_raw
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID, part_no, name, qty,
                ref, notes, raw
            ))

        # Audit final: REF 1–42 harus muncul tepat sekali.
        final_rows = con.execute("""
            SELECT catalog_ref, part_number, part_name, quantity_raw
            FROM parts
            WHERE machine_id = ?
              AND notes LIKE '%section 11%'
        """, (MACHINE_ID,)).fetchall()

        final_map = {}
        for r in final_rows:
            if r["catalog_ref"] in final_map:
                raise RuntimeError(f"REF {r['catalog_ref']} ganda.")
            final_map[r["catalog_ref"]] = (
                r["part_number"], r["part_name"], r["quantity_raw"]
            )

        expected = dict(EXPECTED_EXISTING)
        for ref, part_no, name, qty, raw, note in NEW_ROWS:
            expected[ref] = (part_no, name, raw)

        if len(final_rows) != 42 or final_map != expected:
            missing = sorted(set(range(1, 43)) - set(final_map))
            extra = sorted(set(final_map) - set(range(1, 43)))
            raise RuntimeError(
                f"Audit gagal: jumlah={len(final_rows)}, "
                f"REF hilang={missing}, REF ekstra={extra}."
            )

        # Pastikan Section 10 tetap 48 REF unik.
        section10 = section_rows(con, 10)
        refs10 = [r["catalog_ref"] for r in section10]

        if len(section10) != 48 or len(set(refs10)) != 48:
            raise RuntimeError(
                "Audit Section 10 gagal; transaksi dibatalkan."
            )

        con.commit()

        print("\nBERHASIL")
        print(f"Duplikat Section 10 yang dihapus: {deleted}")
        print(f"REF baru Section 11 yang ditambahkan: {len(to_insert)}")
        print("Section 11: 42 baris, REF 1–42 lengkap dan unik.")
        print("Section 10: 48 baris, REF unik.")
        print(f"Backup tersimpan: {backup}")

    except Exception as exc:
        if con.in_transaction:
            con.rollback()
        print(f"\nGAGAL — transaksi dibatalkan: {exc}")
        print("Periksa pesan di atas; database tidak di-commit.")
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
