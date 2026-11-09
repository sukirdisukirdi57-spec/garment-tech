import sqlite3
import sys

DB_PATH = "database/garment.db"
MACHINE_ID = 44
SOURCE_DOCUMENT_ID = 156
PDF_PAGE = 52

# (REF, marker, part_number, part_name, quantity_raw)
rows = [
    (1,  "#01", "400-42352", "MECHANICAL VALVE UNIT", "1"),
    (2,  "",    "D8001-D15-A0Y", "PEDAL BASE", "(1)"),
    (3,  "",    "D8002-D15-A0Y", "PEDAL CUSHION", "(2)"),
    (4,  "",    "SS-6111210-SP", "SCREW 11/64-40 L=12", "(2)"),
    (5,  "",    "WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)"),
    (6,  "",    "WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "(2)"),
    (7,  "",    "WP-0553216-SD", "WASHER", "(2)"),
    (8,  "",    "PX-0200020-00", "ACTUATOR", "(1)"),
    (9,  "",    "PV-0105020-00", "AIR VALVE", "(1)"),
    (10, "",    "PJ-3010405-01", "HALF UNION M5 D=4", "(6)"),
    (11, "",    "PX-5000140-00", "PLUG", "(2)"),
    (12, "",    "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.9)"),
    (13, "",    "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.8)"),
    (14, "",    "BT-0400251-EB", "URETHANE HOSE BLACK", "(1.9)"),
    (15, "",    "HX-0031400-0A", "SPIRAL TUBE", "(0.6)"),
    (16, "",    "EA-9500B01-00", "CABLE BAND", "(3)"),
    (17, "",    "GEP-01013000", "VALVE", "(1)"),
    (18, "",    "BT-0400251-EB", "URETHANE HOSE BLACK", "(0.1)"),
    (19, "",    "BT-0400251-EB", "URETHANE HOSE BLACK", "(0.1)"),
    (20, "",    "180-35204", "WIRE MARK (3)", "(2)"),
    (21, "",    "180-35303", "WIRE MARK (4)", "(1)"),
    (22, "",    "180-35600", "WIRE MARK (7)", "(2)"),
    (23, "",    "180-35709", "WIRE MARK (8)", "(1)"),
    (24, "",    "PJ-3080400-02", "QUICK COUPLING", "(2)"),
    (25, "",    "WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)"),
    (26, "",    "WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "(2)"),
    (27, "",    "SS-7111120-TP", "SCREW", "(2)"),
    (28, "#01", "400-89848", "AIR UNIT ASM.", "1"),
    (29, "",    "PV-9150050-00", "SOLENOID VALVE INSTALLING BASE", "(1)"),
    (30, "",    "SK-3412001-SE", "WOOD SCREW D=4.1 L=20", "(2)"),
    (31, "",    "PJ-3040600-01", "ELBOW", "(1)"),
    (32, "",    "PX-0500030-00", "SILENCER", "(1)"),
    (33, "",    "BT-0600401-EB", "TUBE", "(1.3)"),
    (34, "",    "400-30951", "FILTER_REGULATOR_ASM.", "(1)"),
    (35, "",    "SL-4051091-SC", "SCREW M5X0.8 L=10", "(2)"),
    (36, "",    "400-23662", "FILTER INSTALLING PLATE", "(1)"),
    (37, "",    "SL-9082093-SE", "SCREW", "(1)"),
    (38, "",    "WP-0871602-SE", "WASHER 8.7X18X1.6", "(1)"),
    (39, "",    "NM-6080721-SE", "NUT M8", "(1)"),
    (40, "",    "400-48529", "VALVE RELAY CORD ASM", "(1)"),
    (41, "",    "400-81601", "AIR RELAY CABLE ASM", "(1)"),
    (42, "",    "PJ-3095200-01", "SOCKET", "(1)"),
    (43, "",    "PB-0000100-00", "HOSE BAND", "(1)"),
    (44, "",    "EA-9500B01-00", "CABLE BAND", "(1)"),
    (45, "",    "400-93109", "AIR SW CABLE ASM", "(1)"),
]

db = sqlite3.connect(DB_PATH)
db.execute("PRAGMA foreign_keys = ON")

try:
    # Validasi daftar sebelum menyentuh database.
    assert len(rows) == 45, f"Jumlah baris salah: {len(rows)}"
    assert [r[0] for r in rows] == list(range(1, 46)), \
        "REF harus lengkap dari 1 sampai 45"
    assert all(r[2] and r[3] and r[4] for r in rows), \
        "Ada kolom wajib yang kosong"

    doc = db.execute("""
        SELECT id FROM documents
        WHERE id = ? AND machine_id = ?
          AND document_type = 'Parts List'
    """, (SOURCE_DOCUMENT_ID, MACHINE_ID)).fetchone()

    if not doc:
        raise ValueError("Dokumen sumber tidak valid.")

    conflicts = db.execute("""
        SELECT catalog_ref
        FROM catalog_occurrences
        WHERE machine_id = ? AND pdf_page = ?
    """, (MACHINE_ID, PDF_PAGE)).fetchall()

    if conflicts:
        raise ValueError(
            "Halaman PDF 52 sudah berisi occurrence: "
            + ", ".join(str(r[0]) for r in conflicts)
        )

    db.execute("BEGIN IMMEDIATE")

    for ref, marker, part_number, part_name, quantity_raw in rows:
        original = (
            f"{ref} {marker + ' ' if marker else ''}"
            f"{part_number} {part_name} {quantity_raw}"
        )

        db.execute("""
            INSERT INTO catalog_occurrences (
                machine_id, source_document_id, pdf_page,
                catalog_ref, marker, part_number, part_name,
                quantity_raw, catalog_line_original, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (
            MACHINE_ID,
            SOURCE_DOCUMENT_ID,
            PDF_PAGE,
            str(ref),
            marker,
            part_number,
            part_name,
            quantity_raw,
            original
        ))

    # Pastikan seluruh REF tersimpan sesuai daftar.
    saved = db.execute("""
        SELECT catalog_ref, marker, part_number, part_name, quantity_raw
        FROM catalog_occurrences
        WHERE machine_id = ? AND source_document_id = ?
          AND pdf_page = ?
        ORDER BY CAST(catalog_ref AS INTEGER)
    """, (MACHINE_ID, SOURCE_DOCUMENT_ID, PDF_PAGE)).fetchall()

    if len(saved) != 45:
        raise ValueError(f"Jumlah tersimpan bukan 45: {len(saved)}")

    for expected, actual in zip(rows, saved):
        ref, marker, pn, name, qty = expected
        actual_tuple = (
            int(actual[0]), actual[1], actual[2], actual[3], actual[4]
        )
        if actual_tuple != expected:
            raise ValueError(
                f"Data REF {ref} tidak cocok: {actual_tuple}"
            )

    db.commit()

    print("IMPORT BERHASIL")
    print(f"Machine ID       : {MACHINE_ID}")
    print(f"Source document  : {SOURCE_DOCUMENT_ID}")
    print(f"PDF page         : {PDF_PAGE}")
    print(f"Jumlah REF       : {len(saved)}")
    print("REF               : 1-45")
    print("Marker #01        : REF 1 dan REF 28")
    print("Tabel parts       : tidak diubah")
    print("component_parts   : tidak diubah")

except Exception as exc:
    db.rollback()
    print("IMPORT DIBATALKAN; transaksi di-rollback.")
    print(f"Alasan: {exc}")
    sys.exit(1)

finally:
    db.close()
