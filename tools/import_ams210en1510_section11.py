import sqlite3, shutil, re, sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-24.jpg"
URL = "https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
TITLE = "11. THREAD TRIMMER MECHANISM COMPONENTS"
MACHINE_ID = 15
DOCUMENT_ID = 136
PAGE = 19

# REF, part number, official description, quantity_raw, catalog note
DATA = [
(1,"400-30936","THREAD_TRIMMER_CAM","1","COMMON"),
(2,"SM-8050592-TP","SCREW","2","COMMON"),
(3,"SM-1040650-TP","SCREW","4","COMMON"),
(4,"235-17501","NEEDLE CAM ROLLER A","1","#01"),
(5,"235-17600","NEEDLE CAM ROLLER B","1","#01"),
(6,"235-17709","NEEDLE CAM ROLLER C","1","#01"),
(7,"235-17808","NEEDLE CAM ROLLER D","1","#01"),
(8,"400-40256","ROLLER_SHAFT","1","COMMON"),
(9,"NM-6040001-SP","NUT M4X0.7","2","COMMON"),
(10,"400-72228","THREAD_TRIMMER_LINK_ASM","1","COMMON"),
(11,"SD-0800327-TP","SHOULDER SCREW","1","COMMON"),
(12,"NM-6050001-SP","NUT M5","1","COMMON"),
(13,"400-23624","THREAD_TRIMMER_SHAFT","1","COMMON"),
(14,"SM-8060812-TP","SCREW M6 L=8","2","COMMON"),
(15,"400-30935","CONNECTING_BAR","1","COMMON"),
(16,"400-30932","NEEDLE_PLATE_ASM.","1","#03"),
(17,"400-30933","NEEDLE_PLATE_H_ASM.","1","#02"),
(18,"400-73085","NEEDLE_PLATE_H_2.4_ASM.","1","#04"),
(19,"SS-6110430-TP","SCREW 11/64-40 L=4.0","(1)","COMMON"),
(20,"B2423-280-00D","MOVING KNIFE WASHER D","(1)","#01"),
(21,"B2423-280-00C","MOVING KNIFE WASHER C","(1)","#01"),
(22,"B2423-280-00A","MOVING KNIFE WASHER A","(1)","#01"),
(23,"B2423-280-00B","MOVING KNIFE WASHER B","(1)","#01"),
(24,"400-30934","NEEDLE_PLATE","(1)","COMMON"),
(25,"B2424-210-000","COUNTER KNIFE","(1)","COMMON"),
(26,"B2426-210-00A","NEEDLE HOLE GUIDE D=1.6","(1)","☆ #03"),
(27,"B2426-210-00B","NEEDLE HOLE GUIDE D=2.0","(1)","☆ #02"),
(28,"B2426-210-00D","NEEDLE HOLE GUIDE D=2.4","(1)","☆ #04"),
(29,"B2421-210-AA0","MOVING KNIFE COMPL.","(1)","☆"),
(30,"B2418-280-000","MOVING KNIFE LINK","(1)","COMMON"),
(31,"B2416-280-000","THREAD CUTTING LEVER RING","(1)","COMMON"),
(32,"B2415-280-0A0","THREAD CUTTER LEVER ASM. SMALL","(1)","COMMON"),
(33,"SS-7090410-SP","SCREW 9/64-40 L=3.5","(1)","COMMON"),
(34,"B2414-280-0A0","THREAD CUTTER LEVER ASM. LARGE","(1)","COMMON"),
(35,"SS-1060210-TP","SCREW 3/32-56 L=2.2","(2)","COMMON"),
(36,"B2417-210-000","MOVING KNIFE HINGE SCREW","(1)","COMMON"),
(37,"WP-0450846-SP","WASHER","(1)","COMMON"),
(38,"B2417-280-000","THREAD CUTTER LEVER SHAFT","(1)","COMMON"),
(39,"SS-7110740-TP","SCREW 11/64-40 L=7","(1)","COMMON"),
(40,"401-56892","STAINLESS_NEEDLE_PLATE_H_ASSY","1","#05"),
(41,"402-39626","STAINLESS_NEEDLE_PLATE_S_ASSY","1","#06"),
(42,"401-56890","STAINLESS_NEEDLE_PLATE","(1)","#07"),
]

def quantity_number(raw):
    m = re.search(r"\d+", raw)
    return int(m.group()) if m else None

if not DB.exists():
    raise SystemExit(f"DB tidak ditemukan: {DB}")

if not (Path("static") / IMAGE).is_file():
    raise SystemExit(f"Gambar tidak ditemukan: {IMAGE}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys=ON")

# Pastikan semua pasangan PN + REF tepat dan tidak ambigu.
mapped = {}
missing = []
for ref, pn, name, qty, note in DATA:
    rows = con.execute("""
        SELECT * FROM parts
        WHERE machine_id=?
          AND part_number=?
          AND CAST(catalog_ref AS INTEGER)=?
    """, (MACHINE_ID, pn, ref)).fetchall()

    if len(rows) > 1:
        raise SystemExit(f"PEMETAAN GANDA REF {ref}: {[r['id'] for r in rows]}")
    if rows:
        row = rows[0]
        if "AMS-210EN catalog staging" not in (row["notes"] or ""):
            raise SystemExit(
                f"REF {ref} bukan record staging: ID {row['id']} notes={row['notes']!r}"
            )
        mapped[ref] = row
    else:
        missing.append(ref)

components = con.execute("""
    SELECT * FROM components
    WHERE machine_id=? AND component_name=?
""", (MACHINE_ID, TITLE)).fetchall()

old = con.execute("""
    SELECT id, component_name FROM components
    WHERE id=452 AND machine_id=?
""", (MACHINE_ID,)).fetchone()

old_relations = con.execute("""
    SELECT COUNT(*) FROM component_parts WHERE component_id=452
""").fetchone()[0]

print("=== PREFLIGHT IMPORT SECTION 11 ===")
print("Total REF:", len(DATA))
print("Part terpetakan:", len(mapped))
print("Part baru:", len(missing))
print("REF belum ada:", missing)
print("Komponen utama sudah ada:", len(components))
print("Komponen lama ID452:", dict(old) if old else None)
print("Relasi ID452 sebelum:", old_relations)
print("Gambar tersedia:", (Path("static") / IMAGE).is_file())

if len(DATA) != 42 or len(mapped) != 25 or len(missing) != 17:
    raise SystemExit("STOP: jumlah pemetaan tidak sesuai preflight yang diharapkan.")
if components:
    raise SystemExit("STOP: komponen utama Section 11 sudah ada.")
if not old or old_relations != 14:
    raise SystemExit("STOP: komponen lama ID452 tidak sesuai audit.")
if not all("AMS-210EN catalog staging" in (r["notes"] or "") for r in mapped.values()):
    raise SystemExit("STOP: ditemukan record terpetakan yang bukan staging.")

if "--apply" not in sys.argv:
    print("\nDRY-RUN SAJA. Belum ada perubahan database.")
    con.close()
    raise SystemExit(0)

backup = DB.with_name(
    f"garment-before-ams210en1510-section11-{datetime.now():%Y%m%d-%H%M%S}.db"
)
con.close()
shutil.copy2(DB, backup)
print("\nBackup dibuat:", backup)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.execute("PRAGMA foreign_keys=ON")

try:
    con.execute("BEGIN IMMEDIATE")

    # Perbarui metadata 25 record staging yang sudah ada.
    for ref, pn, name, qty, note in DATA:
        if ref not in mapped:
            continue
        part_id = mapped[ref]["id"]
        con.execute("""
            UPDATE parts
            SET source_document_id=?, diagram_page=?, source_url=?,
                note=?, notes=?
            WHERE id=?
        """, (
            DOCUMENT_ID, PAGE, URL, note,
            "AMS-210EN catalog staging; section 11", part_id
        ))

    # Tambahkan 17 record yang belum tersedia.
    for ref, pn, name, qty, note in DATA:
        if ref in mapped:
            continue
        con.execute("""
            INSERT INTO parts (
                machine_id, source_document_id, part_number, part_name,
                quantity, catalog_ref, diagram_page, note, source_url,
                notes, quantity_raw
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            MACHINE_ID, DOCUMENT_ID, pn, name,
            quantity_number(qty), ref, PAGE, note, URL,
            "AMS-210EN catalog staging; section 11", qty
        ))

    cur = con.execute("""
        INSERT INTO components (
            machine_id, component_name, part_number, location, function,
            notes, image_path, source_url, catalog_ref, diagram_page
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        MACHINE_ID, TITLE, None,
        "Mekanisme pemotong benang (thread trimmer)",
        "Menggerakkan mekanisme pemotong benang dan komponen needle plate",
        "Section utama katalog Parts List AMS-210EN-1510",
        IMAGE, URL, "11", PAGE
    ))
    component_id = cur.lastrowid

    # Hubungkan seluruh REF 1–42 ke komponen utama.
    for ref, pn, name, qty, note in DATA:
        part = con.execute("""
            SELECT id FROM parts
            WHERE machine_id=? AND part_number=?
              AND CAST(catalog_ref AS INTEGER)=?
        """, (MACHINE_ID, pn, ref)).fetchone()
        if not part:
            raise RuntimeError(f"Part REF {ref} gagal ditemukan setelah insert.")

        con.execute("""
            INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
            VALUES (?,?,?,?)
        """, (component_id, part["id"], "catalog_component_part", f"REF {ref}"))

    con.commit()
    print("\nAPPLY BERHASIL")
    print("Component ID:", component_id)
    print("Relasi utama:", len(DATA))
    print("Backup:", backup)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
