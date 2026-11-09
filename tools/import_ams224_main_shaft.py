import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database")
MACHINE_ID = 47
DOCUMENT_ID = 583
COMPONENT_NAME = "MAIN SHAFT & NEEDLE BAR COMPONENTS"
SOURCE_URL = "https://www.jukisewingmachines.co.uk/pub/media/productfileupload/j/u/juki_ams224en_parts_book.pdf"

# REF | PART NUMBER | PART NAME | QUANTITY RAW
DATA = """
01|SB-1200009-00|BEARING|1
02|236-04200|MAIN SHAFT BEARING SUPPORT|1
03|SM-8060812-TP|SCREW M6 L=8|2
04|SB-1200018-00|BEARING|1
05|400-10415|BEARING_BUSH_A_ASM.|1
06|SB-1200017-00|BEARING|1
07|400-10418|BEARING_BUSH_B_ASM.|1
08|400-72086|MAIN SHAFT|1
09|400-10422|COUNTER_WEIGHT_ASM.|1
10|400-10423|COUNTER_WEIGHT|(1)
11|400-10424|COUNTER_WEIGHT_SCREW_A|(1)
12|400-10425|COUNTER_WEIGHT_SCREW_B|(1)
13|400-10426|COUNTER_WEIGHT_SCREW_C|(1)
14|400-10427|COUNTER_WEIGHT_SCREW_D|(1)
15|WP-0820516-SP|WASHER 11.6X8.2X0.6|1
16|400-78382|THREAD_TAKE_UP_COMPL|1
17|400-06530|THREAD_TAKE_UP_LEVER_ASM.|(1)
18|400-06531|THREAD_TAKE_UP_LEVER|(1)
19|B1908-505-000|THREAD PASS BUSH|(1)
20|SB-1080022-00|BEARING|(2)
21|SB-1040016-00|BEARING|(1)
22|400-78106|NEEDLE_BAR_CRANK_ROD_ALL_ASM|(1)
23|400-06535|NEEDLE_BAR_CRANK_ROD|(1)
24|SB-1080023-00|BEARING|(1)
25|228-91006|NEEDLE BAR CRANK ROD BUSH|(1)
26|400-06532|THREAD_TAKE_UP_CRANK|(1)
27|400-78083|NEEDLE_ROD_CRANK|(1)
28|B1903-552-000|LEFT SCREW|(1)
29|400-78135|PIN|(1)
30|400-96186|PIN|(1)
31|B1705-850-000|STOPPER PIN|(1)
32|400-96209|PIN|(1)
33|400-10434|THRUST_COLLAR_ASM.|1
34|228-91204|BEARING SUPPORT|2
35|400-11902|THREAD_TAKE_UP_CRANK_SHAFT|1
36|SM-8061612-TP|SCREW M6X16|2
37|MDP-170B1800|NEEDLE DPX17 #18|1
38|MC-3720011-00|NEEDLE 135X17 #110|1
39|400-72233|SPROCKET_ASM|1
40|SM-6041602-TP|SCREW M4X0.7 L=16|4
41|SL-6052592-TN|BOLT|4
42|400-51473|COUPLING ASM.|1
43|400-78160|NEEDLE_ROD_METAL_GREASE_COVER|1
44|B1212-210-D00|PULLEY|1
45|B1144-210-000|REVOLVING DIRECTION LABEL|1
46|400-44053|PULLEY SHAFT|1
47|PS-0400142-KH|SPRING PIN 4X14|1
48|A1230-500-000-A|HANDWHEEL SETSCREW|1
49|GAF-01007000|SPRING|1
50|400-06515|GEAR_A|1
51|SM-8040310-SS|SCREW M4 L=3|2
52|400-06516|GEAR_B|1
53|SM-8040310-SS|SCREW M4 L=3|2
54|400-10533|BTW_DRIVING_WHEEL_ASM.|1
55|400-77604|NEEDLE_ROD_METAL|1
56|400-77605|NEEDLE_ROD_LOWER_METAL|1
57|400-26882|NEEDLE_BAR|1
58|B1411-552-0A0|NEEDLE BAR CONNECTING ASM.|1
59|B1414-555-000|SLIDE BLOCK|1
60|400-52937|550W_SERVO_MOTOR|1
61|400-26884|NEEDLE_BAR_SHREAD_GUIDE_H|1
62|229-01409|NEEDLE BAR UPPER BUSH CAP|1
63|SM-8030412-TP|SCREW|1
64|SB-3070002-0A|BEARING|2
65|SB-3070002-0B|BEARING|2
66|SB-3070002-0C|BEARING|2
67|SB-3070002-0D|BEARING|2
"""

def parse_data():
    result = []
    for line in DATA.strip().splitlines():
        ref, number, name, qty_raw = line.split("|")
        qty = int(float(qty_raw.strip("()")))
        result.append({
            "ref": int(ref),
            "number": number.strip(),
            "name": name.strip(),
            "qty_raw": qty_raw.strip(),
            "qty": qty,
        })
    return result

def table_columns(con, table):
    return {
        row["name"]: row
        for row in con.execute(f"PRAGMA table_info({table})")
    }

def main():
    if not DB.exists():
        raise SystemExit(f"Database tidak ditemukan: {DB}")

    rows = parse_data()

    # Validasi data sumber sebelum menyentuh database.
    refs = [r["ref"] for r in rows]
    if len(rows) != 67 or refs != list(range(1, 68)):
        raise SystemExit("GAGAL: data harus berisi REF 01-67 lengkap.")

    if len({r["number"] for r in rows}) != 66:
        raise SystemExit("GAGAL: jumlah nomor part unik tidak sesuai.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"garment-before-main-shaft-{timestamp}.db"

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        # PRE-FLIGHT
        old_parts = con.execute("""
            SELECT COUNT(*) FROM parts
            WHERE machine_id=? AND source_document_id=?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        old_components = con.execute("""
            SELECT COUNT(*) FROM components WHERE machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        old_relations = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        if old_parts != 187:
            raise RuntimeError(
                f"Preflight gagal: part lama {old_parts}, seharusnya 187."
            )

        if old_components != 2 or old_relations != 187:
            raise RuntimeError(
                "Preflight gagal: kondisi komponen/relasi lama berubah. "
                f"Komponen={old_components}, relasi={old_relations}"
            )

        exists = con.execute("""
            SELECT id FROM components
            WHERE machine_id=? AND component_name=?
        """, (MACHINE_ID, COMPONENT_NAME)).fetchone()

        if exists:
            raise RuntimeError(
                f"Komponen sudah ada dengan ID {exists['id']}. Impor dibatalkan."
            )

        # Simpan identitas dan jumlah relasi komponen lama.
        old_component_snapshot = [
            tuple(r) for r in con.execute("""
                SELECT c.id, c.component_name, c.diagram_page,
                       COUNT(cp.id) AS relation_count
                FROM components c
                LEFT JOIN component_parts cp ON cp.component_id=c.id
                WHERE c.machine_id=?
                GROUP BY c.id
                ORDER BY c.id
            """, (MACHINE_ID,))
        ]

        # BACKUP SQLITE ONLINE API
        backup_con = sqlite3.connect(backup)
        con.backup(backup_con)
        backup_con.close()

        print(f"BACKUP: {backup}")
        print("PRE-FLIGHT LULUS")
        print(f"Part lama      : {old_parts}")
        print(f"Komponen lama  : {old_components}")
        print(f"Relasi lama    : {old_relations}")

        con.execute("BEGIN IMMEDIATE")

        # Buat komponen baru.
        component_values = {
            "machine_id": MACHINE_ID,
            "component_name": COMPONENT_NAME,
            "part_number": None,
            "location": COMPONENT_NAME,
            "function": COMPONENT_NAME,
            "notes": (
                "Official JUKI AMS-224EN/IP-420 Parts List No.1575-03; "
                "diagram page 14; parts list page 15; model 6030."
            ),
            "image_path": None,
            "source_url": SOURCE_URL,
            "catalog_ref": None,
            "diagram_page": 14,
        }

        component_cols = table_columns(con, "components")
        insert_component = {
            k: v for k, v in component_values.items()
            if k in component_cols
        }

        required_component_fields = {
            "machine_id", "component_name", "notes", "diagram_page"
        }
        if not required_component_fields.issubset(insert_component):
            raise RuntimeError(
                "Kolom wajib komponen tidak lengkap: "
                f"{required_component_fields - set(insert_component)}"
            )

        keys = list(insert_component)
        sql = (
            f"INSERT INTO components ({','.join(keys)}) "
            f"VALUES ({','.join('?' for _ in keys)})"
        )
        cur = con.execute(sql, [insert_component[k] for k in keys])
        component_id = cur.lastrowid

        # Tambahkan 67 occurrence baru, satu baris untuk setiap REF.
        part_ids = []
        for r in rows:
            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id,
                    part_number, part_name, quantity,
                    catalog_ref, diagram_page, note,
                    source_url, notes, quantity_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                DOCUMENT_ID,
                r["number"],
                r["name"],
                r["qty"],
                r["ref"],
                None,
                None,
                SOURCE_URL,
                f"AMS-224EN-6030 section: {COMPONENT_NAME}",
                r["qty_raw"],
            ))
            part_ids.append(cur.lastrowid)

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                ) VALUES (?, ?, ?, ?)
            """, (
                component_id,
                cur.lastrowid,
                "catalog_component_part",
                f"Catalog REF {r['ref']:02d}",
            ))

        # VERIFIKASI DALAM TRANSAKSI
        imported_parts = con.execute("""
            SELECT COUNT(*) FROM parts
            WHERE machine_id=? AND source_document_id=?
        """, (MACHINE_ID, DOCUMENT_ID)).fetchone()[0]

        imported_relations = con.execute("""
            SELECT COUNT(*) FROM component_parts
            WHERE component_id=?
        """, (component_id,)).fetchone()[0]

        imported_refs = [
            r[0] for r in con.execute("""
                SELECT p.catalog_ref
                FROM parts p
                JOIN component_parts cp ON cp.part_id=p.id
                WHERE cp.component_id=?
                ORDER BY p.catalog_ref
            """, (component_id,))
        ]

        if imported_parts != 254:
            raise RuntimeError(
                f"Jumlah part akhir salah: {imported_parts}, seharusnya 254."
            )

        if imported_relations != 67:
            raise RuntimeError(
                f"Jumlah relasi baru salah: {imported_relations}."
            )

        if imported_refs != list(range(1, 68)):
            raise RuntimeError("REF hasil impor tidak lengkap/berurutan.")

        # Pastikan dua komponen lama tidak berubah.
        new_component_snapshot = [
            tuple(r) for r in con.execute("""
                SELECT c.id, c.component_name, c.diagram_page,
                       COUNT(cp.id) AS relation_count
                FROM components c
                LEFT JOIN component_parts cp ON cp.component_id=c.id
                WHERE c.machine_id=? AND c.id != ?
                GROUP BY c.id
                ORDER BY c.id
            """, (MACHINE_ID, component_id))
        ]

        if new_component_snapshot != old_component_snapshot:
            raise RuntimeError(
                "Komponen lama berubah. Transaksi dibatalkan."
            )

        final_components = con.execute("""
            SELECT COUNT(*) FROM components WHERE machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        final_relations = con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0]

        if final_components != 3 or final_relations != 254:
            raise RuntimeError(
                "Jumlah komponen/relasi akhir tidak sesuai."
            )

        con.commit()

        print("\n=== IMPOR BERHASIL ===")
        print(f"Component ID : {component_id}")
        print(f"Nama         : {COMPONENT_NAME}")
        print(f"Diagram page : 14")
        print(f"REF diimpor  : {len(rows)}")
        print(f"Part total   : {imported_parts}")
        print(f"Relasi total : {final_relations}")
        print(f"Komponen     : {final_components}")
        print("Komponen 598 dan 599: TIDAK BERUBAH")
        print("STATUS: COMMIT BERHASIL")

    except Exception as e:
        if con.in_transaction:
            con.rollback()
        print("\n=== IMPOR DIBATALKAN ===")
        print(str(e))
        print("Transaksi di-ROLLBACK. Database tidak menerima perubahan.")
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
