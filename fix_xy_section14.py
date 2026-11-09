import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import re
import sys

DB = Path("database/garment.db")
if not DB.exists():
    sys.exit(f"Database tidak ditemukan: {DB}")

# Data REF 21-45 berdasarkan katalog AMS-210EN, halaman 31.
# Format: REF, part number, part name, quantity_raw, note
DATA = [
    (21, "SM-6041200-SP", "SCREW M4 L=12", "4", "COMMON"),
    (22, "SB-3100013-00", "BEARING", "1", "COMMON"),
    (23, "SM-8060812-TP", "SCREW M6 L=8", "2", "COMMON"),
    (24, "SM-8060602-TP", "SCREW M6X6", "2", "COMMON"),
    (25, "SM-8060612-TP", "SCREW M6 L=6", "2", "COMMON"),
    (26, "SM-8050612-TP", "SCREW M5X6", "2", "COMMON"),
    (27, "SB-3100012-00", "BEARING", "1", "COMMON"),
    (28, "EA-9500B01-00", "CABLE BAND", "1", "COMMON"),
    (29, "WP-0450846-SP", "WASHER", "8", "COMMON"),
    (30, "169-92604", "THRUST WASHER", "4", "COMMON"),
    (31, "400-25439", "Y_FEED_MOTOR_BASE", "1", "COMMON"),
    (32, "SM-6041200-SP", "SCREW M4 L=12", "4", "COMMON"),
    (33, "SM-6042000-SP", "SCREW", "2", "COMMON"),
    (34, "WP-0450846-SP", "WASHER", "2", "COMMON"),
    (35, "B2526-210-D00", "X DRIVE GEAR", "1", "COMMON"),
    (36, "SM-8060602-TP", "SCREW M6X6", "2", "COMMON"),
    (37, "400-77994", "DRIVE SPROCKET", "1", "COMMON"),
    (38, "HD-0005700-0A", "PHOTO SENSOR", "1", "COMMON"),
    (39, "SL-4031081-SC", "SCREW M3X10", "1", "COMMON"),
    (40, "B4004-210-D00", "X SENSOR INSTALLING PLATE", "1", "COMMON"),
    (41, "SM-6040802-TP", "SCREW M4X0.7 L=8", "2", "COMMON"),
    (42, "SM-6040602-TP", "SCREW M4 L=6", "2", "COMMON"),
    (43, "400-32505", "Y_SENSOR_ASM.", "1", "COMMON"),
    (44, "SL-4031081-SC", "SCREW M3X10", "1", "COMMON"),
    (45, "400-78058", "Y_SENSOR_INSTALLING_PLATE_A", "1", "COMMON"),
]

SECTION14 = "AMS-210EN catalog staging; section 14"
SECTION13 = "AMS-210EN catalog staging; section 13"

def quantity_value(raw):
    # quantity INTEGER menyimpan angka; quantity_raw mempertahankan
    # format katalog, termasuk tanda kurung bila ada.
    m = re.fullmatch(r"\s*\(?\s*(\d+)\s*\)?\s*", raw)
    return int(m.group(1)) if m else None

# Backup dibuat sebelum membuka transaksi perubahan.
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path("backups") / f"garment-before-fix-xy-section14-{stamp}.db"
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(DB, backup)
print("Backup:", backup)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    con.execute("BEGIN IMMEDIATE")

    # Pastikan setiap REF 1-20 masih tepat seperti katalog yang diketahui.
    expected_existing = {
        1: ("401-03969", "ENCODER MOTOR ASM.(IP)"),
        2: ("401-03969", "ENCODER MOTOR ASM.(IP)"),
        5: ("SM-6061202-TP", "SCREW M6 L=12"),
        6: ("400-77985", "X_DRIVEN_GEAR"),
        7: ("B2526-210-D00", "X DRIVE GEAR"),
        8: ("WP-0430801-SC", "WASHER 4.3X9X0.8"),
        9: ("400-77984", "Y_REMOVAL_BUSHING_A"),
        10: ("400-78064", "Y_FEED_SHAFT"),
        11: ("CS-1000881-TP", "THRUST COLLAR"),
        14: ("400-78057", "Y_REMOVAL_BUSHING_A"),
        15: ("SM-8050512-TP", "SCREW"),
        16: ("400-78062", "Y_REMOVAL_SHAFT_HOLDER"),
        17: ("SM-6051802-TP", "SCREW M5 L=18"),
        18: ("WP-0550800-SP", "WASHER 5.5X10X0.8"),
        19: ("112-72408", "THRUST COLLAR"),
        20: ("SB-4080001-00", "BEARING"),
    }

    current = con.execute("""
        SELECT catalog_ref, part_number, part_name
        FROM parts
        WHERE machine_id = 44 AND notes LIKE '%section 14%'
          AND catalog_ref BETWEEN 1 AND 20
    """).fetchall()

    by_ref = {}
    for row in current:
        by_ref.setdefault(row["catalog_ref"], []).append(
            (row["part_number"], row["part_name"])
        )

    for ref, expected in expected_existing.items():
        if by_ref.get(ref) != [expected]:
            raise RuntimeError(
                f"REF {ref} berubah/tidak sesuai: {by_ref.get(ref)}; "
                f"ekspektasi {expected}. Tidak ada perubahan disimpan."
            )

    # REF 3, 4, 12, 13 dan 21-48 diganti/ditambahkan sesuai katalog.
    # Baris Section 13 tidak disentuh.
    con.execute("""
        DELETE FROM parts
        WHERE machine_id = 44
          AND notes LIKE '%section 14%'
          AND catalog_ref >= 21
    """)
    deleted = con.execute("SELECT changes()").fetchone()[0]
    print("Baris Section 14 REF >=21 dihapus untuk koreksi:", deleted)

    # REF 3 dan 4 serta 12 dan 13 yang sebelumnya hilang.
    missing_early = [
        (3, "400-78061", "X_GUIDE_SHAFT_SUPPORT_B", "1", "#01"),
        (4, "400-78060", "X_GUIDE_SHAFT_SUPPORT_A", "1", "#02"),
        (12, "400-36475", "X_GUIDE_SHAFT", "1", "#01"),
        (13, "400-38564", "X GUIDE SHAFT", "1", "#02"),
    ]

    insert_sql = """
        INSERT INTO parts (
            machine_id, source_document_id, part_number, part_name,
            quantity, catalog_ref, diagram_page, note, source_url,
            notes, quantity_raw
        ) VALUES (44, NULL, ?, ?, ?, ?, 30, ?, NULL, ?, ?)
    """

    for ref, pn, name, raw, note in missing_early + [
        (r, pn, name, raw, note)
        for r, pn, name, raw, note in DATA
    ]:
        con.execute(
            insert_sql,
            (pn, name, quantity_value(raw), ref, note, SECTION14, raw)
        )

    # Validasi REF dan data sebelum commit.
    rows = con.execute("""
        SELECT catalog_ref, part_number, part_name, quantity_raw, note
        FROM parts
        WHERE machine_id = 44 AND notes LIKE '%section 14%'
        ORDER BY catalog_ref, id
    """).fetchall()

    refs = [r["catalog_ref"] for r in rows]
    if len(rows) != 45 or sorted(refs) != list(range(1, 46)):
        raise RuntimeError(
            f"Validasi gagal: jumlah={len(rows)}, REF={refs}"
        )

    # Pastikan Section 13 tidak berubah dari salinan backup.
    # Tidak ada query UPDATE/DELETE/INSERT yang menargetkan Section 13.
    con.commit()

    print("\n=== BERHASIL: AUDIT SECTION 14 ===")
    print("Jumlah baris:", len(rows))
    print("REF hilang:", sorted(set(range(1, 46)) - set(refs)))
    print("REF duplikat:", sorted(
        r for r in set(refs) if refs.count(r) > 1
    ))
    print("REF di luar rentang:", sorted(
        r for r in set(refs) if r is None or not 1 <= r <= 45
    ))

    for r in rows:
        print(
            f"REF {r['catalog_ref']:>2} | {r['part_number']} | "
            f"{r['part_name']} | QTY {r['quantity_raw']} | "
            f"NOTE {r['note']}"
        )

except Exception as e:
    con.rollback()
    print("\nGAGAL — transaksi dibatalkan:", e)
    print("Backup tetap tersedia:", backup)
    sys.exit(1)
finally:
    con.close()
