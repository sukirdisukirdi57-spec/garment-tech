import sqlite3, shutil, sys
from pathlib import Path
from datetime import datetime

DB=Path("database/garment.db")
TITLE="12. THREAD CLAMP COMPONENTS"
IMAGE="images/mechanisms/juki/ams210en/pdf-page-26.jpg"
URL="https://www.juki.co.jp/industrial_j/download_j/manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
DATA=[
(1,"400-06761","TC_CLAMP","1"),
(2,"WP-0450801-SP","WASHER","1"),
(3,"400-76233","TC_CLAMP_PLATE_ASM","1"),
(4,"400-76235","TC_SIPPORT_PLATE_ASM","1"),
(5,"400-15800","TC_LINK_ASM.","1"),
(6,"WP-0320500-SC","WASHER M3","2"),
(7,"RE-0200000-K0","E-RING","2"),
(8,"SD-0400266-TP","SHOULDER SCREW","1"),
(9,"400-76237","TC_BASE","1"),
(10,"400-06772","TC_CAM_PLATE","1"),
(11,"400-06780","TC_SPRING","1"),
(12,"400-76236","TC_BASE_COVER","1"),
(13,"SM-6020350-SP","SCREW M2 L=2.5","4"),
(14,"400-76239","TC_OPEN_PLATE","1"),
(15,"400-30943","TC_NOTCH_R_H","1"),
(16,"400-76232","TC_OPEN_SPRING","1"),
(17,"400-30942","TC_NOTCH_F_H","1"),
(18,"SM-4020600-SP","SCREW M2 L=6","2"),
(19,"400-06768","TC_JOINT_ASM.","1"),
(20,"SM-2360110-TP","SCREW","2"),
(21,"SM-6040650-TP","SCREW","3"),
(22,"400-10527","TC_DRIVING_ARM_ASM.","1"),
(23,"400-10528","TC_DRIVING_ARM","(1)"),
(24,"400-11152","TC_ARM_SCREW","(2)"),
(25,"SD-0800407-TP","SHOULDER SCREW","1"),
(26,"400-30940","TC_CONNECTING_LINK","1"),
(27,"SD-0350156-TP","SHOULDER SCREW","1"),
(28,"400-33191","SENSOR_SLIT","1"),
(29,"SM-6030502-TP","BOLT M3X5","1"),
(30,"400-85033","STEPPING MOTOR","1"),
(31,"SM-6041202-TP","SCREW M4X0.7 L=12","4"),
(32,"SM-6040602-TP","SCREW M4 L=6","1"),
(33,"400-32508","TH_SENSOR_ASM.","1"),
(34,"400-33190","SENSOR_INSTALLING_BASE","(1)"),
(35,"HD-0020400-0A","SENSOR","(1)"),
(36,"HD-0020400-0B","SENSOR","(1)"),
(37,"SM-6020450-TP","SCREW","2"),
(38,"SD-0350156-TP","SHOULDER SCREW","1"),
(39,"NM-6030003-SC","NUT M3","1"),
]

con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
con.execute("PRAGMA foreign_keys=ON")

mapped={}
missing=[]
for ref,pn,name,qty in DATA:
    rows=con.execute("""
      SELECT * FROM parts
      WHERE machine_id=15 AND part_number=?
      AND CAST(catalog_ref AS INTEGER)=?
    """,(pn,ref)).fetchall()
    if len(rows)>1:
        raise SystemExit(f"PEMETAAN GANDA REF {ref}: {[r['id'] for r in rows]}")
    if rows:
        r=rows[0]
        if "AMS-210EN catalog staging" not in (r["notes"] or ""):
            raise SystemExit(f"REF {ref} bukan staging: ID {r['id']}")
        mapped[ref]=r
    else:
        missing.append(ref)

components=con.execute("""
 SELECT id FROM components WHERE machine_id=15 AND component_name=?
""",(TITLE,)).fetchall()

old_count=con.execute("""
 SELECT COUNT(*) FROM component_parts WHERE component_id=448
""").fetchone()[0]

preserved={}
for ref in (22,23,24):
    r=mapped.get(ref)
    if r:
        preserved[ref]=con.execute("""
          SELECT COUNT(*) FROM component_parts WHERE part_id=?
        """,(r["id"],)).fetchone()[0]

print("=== PREFLIGHT SECTION 12 ===")
print("Total REF:",len(DATA))
print("Part terpetakan:",len(mapped))
print("Part baru:",len(missing),missing)
print("Komponen utama sudah ada:",len(components))
print("Relasi lama REF22-24:",preserved)
print("Relasi komponen ID448:",old_count)
print("Gambar tersedia:",Path("static",IMAGE).is_file())

if len(mapped)!=38 or missing!=[38]:
    raise SystemExit("STOP: peta part berubah dari hasil audit.")
if components:
    raise SystemExit("STOP: komponen utama sudah ada.")
if old_count!=15:
    raise SystemExit("STOP: relasi ID448 berubah.")
if preserved!={22:1,23:1,24:1}:
    raise SystemExit("STOP: relasi lama REF22-24 tidak sesuai.")
if not Path("static",IMAGE).is_file():
    raise SystemExit("STOP: gambar tidak ditemukan.")

if "--apply" not in sys.argv:
    print("\nDRY-RUN SAJA. Database belum diubah.")
    con.close()
    raise SystemExit(0)

backup=DB.with_name(
 f"garment-before-ams210en1510-section12-{datetime.now():%Y%m%d-%H%M%S}.db"
)
con.close()
shutil.copy2(DB,backup)
print("\nBackup dibuat:",backup)

con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
con.execute("PRAGMA foreign_keys=ON")
try:
    con.execute("BEGIN IMMEDIATE")

    # Perbarui metadata seluruh 38 record yang telah dipetakan.
    for ref,pn,name,qty in DATA:
        if ref in mapped:
            con.execute("""
             UPDATE parts
             SET source_document_id=136,diagram_page=21,
                 source_url=?,note='COMMON',
                 notes='AMS-210EN catalog staging; section 12'
             WHERE id=?
            """,(URL,mapped[ref]["id"]))

    # REF38 dibuat tersendiri meskipun PN sama dengan REF27.
    con.execute("""
      INSERT INTO parts (
       machine_id,source_document_id,part_number,part_name,
       quantity,catalog_ref,diagram_page,note,source_url,notes,quantity_raw
      ) VALUES (15,136,?,?,?,?,21,'COMMON',?,
       'AMS-210EN catalog staging; section 12',?)
    """,(
      "SD-0350156-TP","SHOULDER SCREW",1,38,URL,"1"
    ))

    cur=con.execute("""
      INSERT INTO components (
       machine_id,component_name,part_number,location,function,
       notes,image_path,source_url,catalog_ref,diagram_page
      ) VALUES (15,?,NULL,?,?,?,?,?,?,?)
    """,(
      TITLE,
      "Mekanisme penjepit benang (thread clamp)",
      "Menjepit dan mengendalikan benang pada mekanisme thread clamp",
      "Section utama katalog Parts List AMS-210EN-1510",
      IMAGE,URL,"12",21
    ))
    cid=cur.lastrowid

    for ref,pn,name,qty in DATA:
        r=con.execute("""
         SELECT id FROM parts WHERE machine_id=15 AND part_number=?
         AND CAST(catalog_ref AS INTEGER)=?
        """,(pn,ref)).fetchone()
        if not r:
            raise RuntimeError(f"REF {ref} tidak ditemukan setelah insert.")
        con.execute("""
         INSERT INTO component_parts
         (component_id,part_id,relation_type,notes)
         VALUES (?,?,'catalog_component_part',?)
        """,(cid,r["id"],f"REF {ref}"))

    con.commit()
    print("APPLY BERHASIL | Component ID:",cid,"| Relasi:",len(DATA))
    print("Backup:",backup)
except Exception:
    con.rollback()
    raise
finally:
    con.close()
