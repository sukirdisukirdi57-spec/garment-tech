import re
import sys
import sqlite3
import shutil

from pathlib import Path
from datetime import datetime
from collections import Counter

DB = Path("database/garment.db")
MACHINE_ID = 47
DOCUMENT_ID = 583

SOURCE_URL = (
    "https://www.jukisewingmachines.co.uk/pub/media/"
    "productfileupload/j/u/juki_ams224en_parts_book.pdf"
)

IMAGE_DIR = Path("static/component_images")

SECTIONS = {
    1: {
        "name": "FRAME & MISCELLANEOUS COVER COMPONENTS (1)",
        "txt": Path("tmp/ams224en6030-section1/page7.txt"),
        "image": Path("tmp/ams224en6030-section1/page6.png"),
        "image_name": "ams224en6030_frame_misc_cover_1_page6.png",
        "diagram": 6,
        "baseline": (1132, 23, 1132),
        "target": (1187, 24, 1187),
        "refs": 55,
        "data": [
            (1, "400-32158", "TOP_COVER_FRONT", "1", None),
            (2, "SM-4061255-SP", "SCREW M6 L=12", "4", None),
            (3, "400-26979", "FACE_COVER", "1", None),
            (4, "229-02506", "FACE PLATE", "1", None),
            (5, "SM-4041055-SP", "SCREW", "2", None),
            (6, "400-24999", "PRESSER_COVER", "1", None),
            (7, "SM-4040855-SP", "SCREW", "4", None),
            (8, "400-30828", "THREAD_TAKE_UP_LEVER_COVER", "1", None),
            (9, "SM-4030601-SN", "SCREW M3X6", "2", None),
            (10, "TA-2100904-R0", "RUBBER PLUG", "1", None),
            (11, "400-27971", "MOTOR_COVER", "1", None),
            (12, "262-11904", "THREAD GUIDE PLATE", "2", None),
            (13, "SM-4061255-SP", "SCREW M6 L=12", "2", None),
            (14, "400-25414", "L_SHAPED_THREAD_GUIDE", "1", None),
            (15, "NM-6040000-SN", "NUT M4", "1", None),
            (16, "229-20508", "ARM THREAD GUIDE A", "1", None),
            (17, "SM-6040650-TP", "SCREW", "1", None),
            (18, "SM-6040860-TP", "SCREW M4 L=8", "1", None),
            (19, "B1129-210-000", "FRAME THREAD GUIDE (B)", "1", None),
            (20, "SM-6040650-TP", "SCREW", "1", None),
            (21, "137-05108", "TAKE-UP THREAD GUIDE B", "1", None),
            (22, "SM-6040650-TP", "SCREW", "1", None),
            (23, "TA-0850604-R0", "RUBBER PLUG", "6", None),
            (24, "TA-1050504-R0", "RUBBER PLUG", "1", None),
            (25, "400-73678", "THB SENSOR CABLE ASM.", "1", None),
            (26, "400-32159", "TOP_COVER_REAR", "1", None),
            (27, "TA-2351004-R0", "RUBBER PLUG", "1", None),
            (28, "400-28877", "FACE_COVER_CAP", "1", None),
            (29, "SM-4051055-SP", "SCREW", "4", None),
            (30, "400-28834", "GUIDE_PLATE", "1", None),
            (31, "400-28835", "BUSHING", "1", None),
            (32, "SM-4041055-SP", "SCREW", "4", None),
            (33, "400-73676", "STOP SW ASM", "1", None),
            (34, "SL-6040892-TN", "BOLT", "2", None),
            (35, "105-02300", "THREAD CUTTER", "1", None),
            (36, "SM-4030601-SN", "SCREW M3X6", "1", None),
            (37, "400-06484", "SAFETY PLATE COMPL.", "1", None),
            (38, "SM-4040855-SP", "SCREW", "(2)", None),
            (39, "WP-0450801-SD", "WASHER 4.5X10X0.8", "(2)", None),
            (40, "400-51987", "SAFETY PLATE BASE", "(1)", None),
            (41, "B3120-372-000", "SAFETY PLATE", "(1)", None),
            (42, "SM-4040655-SP", "SCREW M4 L=6", "(2)", None),
            (43, "400-06836", "OIL TANK ASM.", "2", None),
            (44, "SM-6040650-TP", "SCREW", "2", None),
            (45, "400-06840", "RUBBER BUSH", "4", None),
            (46, "141-13468", "BOBBIN THREAD TENSION ASM.", "1", None),
            (47, "110-72402", "THREAD TENSION NUT", "(1)", None),
            (48, "NS-6110310-SP", "NUT 11/64-40", "(1)", None),
            (49, "141-13450", "BOBBIN THREAD TENSION ROD ASM.", "(1)", None),
            (50, "B3126-012-000", "THREAD TENSION DISK", "(2)", None),
            (51, "D7133-555-B00", "CONNECTING ROD SPRING", "(1)", None),
            (52, "WS-0451040-KP", "SPRING WASHER 4.5X8.5X1", "1", None),
            (53, "B1114-280-000", "PIN", "1", None),
            (54, "SM-8040412-TP", "SET SCREW M4 L=4", "2", None),
            (55, "CM-3002000-01", "ATTENTION SEAL", "3", None),
        ],
    },

    2: {
        "name": "FRAME & MISCELLANEOUS COVER COMPONENTS (2)",
        "txt": Path("tmp/ams224en6030-section2/page9.txt"),
        "image": Path("tmp/ams224en6030-section2/page8.png"),
        "image_name": "ams224en6030_frame_misc_cover_2_page8.png",
        "diagram": 8,
        "baseline": (1187, 24, 1187),
        "target": (1228, 25, 1228),
        "refs": 41,
        "data": [
            (1, "CM-3012000-01", "SAFETY LABEL_S", "2", None),
            (2, "SL-4040891-SC", "SCREW M4 L=8", "12", None),
            (3, "229-01805", "GROUND MARK", "1", None),
            (4, "400-28338", "BOBBIN_WINDER_UNIT", "1", None),
            (5, "262-60109", "BTW_BASE", "(1)", None),
            (6, "262-60208", "BTW_CAM_PLATE", "(1)", None),
            (7, "262-60307", "BTW_BASE_SHAFT", "(1)", None),
            (8, "262-60406", "BTW_SHAFT_BASE", "(1)", None),
            (9, "262-60505", "BTW_CAM_LEVER", "(1)", None),
            (10, "262-60604", "BTW_WHEEL", "(1)", None),
            (11, "262-60703", "BTW_TORSION_SPRING", "(1)", None),
            (12, "262-60802", "BTW_BEARING_SPACER", "(1)", None),
            (13, "400-23865", "BTW_SHAFT", "(1)", None),
            (14, "400-23866", "BTW_LEVER_SHAFT", "(1)", None),
            (15, "400-30829", "BTW_LEVER", "(1)", None),
            (16, "262-61206", "BTW_SPACER", "(1)", None),
            (17, "262-61305", "BTW_BEARING", "(2)", None),
            (18, "262-61503", "BTW_WHEEL_RUBBER", "(1)", "☆"),
            (19, "262-61602", "BOBBIN_SPRING", "(1)", "☆"),
            (20, "262-61701", "BTW_SPRING", "(1)", None),
            (21, "RC-0560711-KP", "RETAINING RING", "(1)", None),
            (22, "RE-0400000-K0", "E-RING 4", "(1)", None),
            (23, "WP-0450826-SC", "WASHER 4.5X10X0.8", "(1)", None),
            (24, "SM-5040655-SN", "SCREW", "(1)", None),
            (25, "SM-8050502-TP", "SCREW M5 L=5", "(1)", None),
            (26, "SM-8040802-TP", "SCREW M4X8", "(2)", None),
            (27, "SM-6041150-TP", "SCREW", "3", None),
            (28, "400-31336", "FLAT_BAG", "1", None),
            (29, "400-13640", "JUKI_GREASE_B_TUBE", "1", "☆"),
            (30, "SL-4040891-SC", "SCREW M4 L=8", "1", None),
            (31, "141-15554", "HEAD GROUND CABLE A ASM.", "1", None),
            (32, "CM-1001000-01", "OIL INJECTION PROHIBITION LABEL", "1", None),
            (33, "CM-6001001-01", "WEEE MARK LABEL S", "1", "#01"),
            (34, "HX-0015000-0F", "CABLE CLIP", "4", None),
            (35, "HX-0015000-0D", "CABLE CLIP", "8", None),
            (36, "HX-0015000-0H", "CABLE CLIP", "3", None),
            (37, "EA-9500B01-00", "CABLE BAND", "3", None),
            (38, "EA-9500B02-00", "CABLE BAND 150", "5", None),
            (39, "SM-6040802-TP", "SCREW M4X0.7 L=8", "5", None),
            (40, "SL-6040892-TN", "BOLT", "3", None),
            (41, "HX-0015000-0E", "CORD PRESSER 3-POLE (220/240V)", "2", None),
        ],
    },
}


def stop(message):
    raise RuntimeError(message)


def parse_source(path):
    text = path.read_text(encoding="utf-8", errors="replace")

    pattern = re.compile(
        r"^\s*(\d{1,2})\s+"
        r"(☆)?\s*"
        r"(#\d{2})?\s*"
        r"([A-Z0-9-]+)\s+"
        r"(.+?)\s+"
        r"(\(?\d+(?:\.\d+)?\)?)\s*$"
    )

    records = []
    started = False

    for line in text.splitlines():
        if not started:
            if "REF.NO" in line.upper():
                started = True
            continue

        match = pattern.match(line)

        if not match:
            if records:
                break
            continue

        ref, star, note, number, name, qty_raw = match.groups()

        marker = star or note

        records.append((
            int(ref),
            number,
            name.strip(),
            qty_raw.strip(),
            marker,
        ))

    if not started:
        stop(f"Header REF.NO tidak ditemukan: {path}")

    return records


def make_records(data):
    result = []

    for ref, number, name, qty_raw, marker in data:
        numeric = float(qty_raw.strip("()"))
        qty = int(numeric) if numeric.is_integer() else numeric

        result.append({
            "ref": ref,
            "number": number,
            "name": name,
            "qty_raw": qty_raw,
            "qty": qty,
            "marker": marker,
        })

    return result


def get_counts(con):
    return (
        con.execute(
            "SELECT COUNT(*) FROM parts WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],

        con.execute(
            "SELECT COUNT(*) FROM components WHERE machine_id=?",
            (MACHINE_ID,)
        ).fetchone()[0],

        con.execute("""
            SELECT COUNT(*)
            FROM component_parts cp
            JOIN components c ON c.id=cp.component_id
            WHERE c.machine_id=?
        """, (MACHINE_ID,)).fetchone()[0],
    )


def snapshot(con):
    return [
        tuple(row)
        for row in con.execute("""
            SELECT c.id, c.component_name, c.diagram_page,
                   c.image_path, COUNT(cp.id)
            FROM components c
            LEFT JOIN component_parts cp
                ON cp.component_id=c.id
            WHERE c.machine_id=?
            GROUP BY c.id
            ORDER BY c.id
        """, (MACHINE_ID,))
    ]


def run(section_number, apply):
    cfg = SECTIONS[section_number]

    txt = cfg["txt"]
    image_src = cfg["image"]
    image_name = cfg["image_name"]
    image_dst = IMAGE_DIR / image_name
    image_db_path = "component_images/" + image_name

    if not DB.is_file():
        stop("Database aktif tidak ditemukan")

    if not txt.is_file():
        stop(f"Teks sumber tidak ditemukan: {txt}")

    if not image_src.is_file():
        stop(f"Diagram sumber tidak ditemukan: {image_src}")

    if image_dst.exists():
        stop(f"Diagram tujuan sudah ada: {image_dst}")

    source_records = parse_source(txt)
    expected_data = cfg["data"]

    if source_records != expected_data:
        stop(
            "Data hasil ekstraksi tidak sama dengan data katalog "
            f"yang diverifikasi untuk Section {section_number}.\n"
            f"Jumlah terbaca: {len(source_records)}\n"
            f"Jumlah diharapkan: {len(expected_data)}"
        )

    records = make_records(expected_data)
    refs = [r["ref"] for r in records]

    if len(records) != cfg["refs"]:
        stop("Jumlah REF tidak sesuai")

    if refs != list(range(1, cfg["refs"] + 1)):
        stop("REF tidak berurutan atau tidak lengkap")

    counts = Counter(r["number"] for r in records)
    duplicates = {k: v for k, v in counts.items() if v > 1}

    print(f"\n=== VALIDASI SECTION {section_number} ===")
    print("Judul:", cfg["name"])
    print("Jumlah REF:", len(records))
    print("REF berurutan:", True)
    print("Nomor part unik:", len(counts))
    print("Duplikasi:", duplicates)
    print("Marker katalog:", {
        k: sum(1 for r in records if r["marker"] == k)
        for k in ("☆", "#01")
        if any(r["marker"] == k for r in records)
    })
    print("Nama, nomor part, quantity, marker: VALID")
    print("Diagram page:", cfg["diagram"])

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    image_copied = False

    try:
        machine = con.execute("""
            SELECT id, model FROM machines WHERE id=?
        """, (MACHINE_ID,)).fetchone()

        if not machine or machine["model"] != "AMS-224EN-6030":
            stop("Machine ID 47 bukan AMS-224EN-6030")

        document = con.execute("""
            SELECT id FROM documents
            WHERE id=? AND machine_id=?
        """, (DOCUMENT_ID, MACHINE_ID)).fetchone()

        if not document:
            stop("Dokumen sumber ID 583 tidak ditemukan")

        current = get_counts(con)
        print("Kondisi database:", current)

        if current != cfg["baseline"]:
            stop(
                f"Baseline harus {cfg['baseline']}, "
                f"aktual {current}"
            )

        existing = con.execute("""
            SELECT id, component_name, catalog_ref
            FROM components
            WHERE machine_id=?
              AND (
                  component_name=?
                  OR catalog_ref=?
              )
        """, (
            MACHINE_ID,
            cfg["name"],
            str(section_number),
        )).fetchone()

        if existing:
            stop(
                "Komponen sudah ada: "
                f"ID {existing['id']} {existing['component_name']}"
            )

        before = snapshot(con)

        if not apply:
            print("\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Part baru:", len(records))
            print("Komponen baru: 1")
            print("Relasi baru:", len(records))
            print("Target database:", cfg["target"])
            print("Diagram sumber:", image_src)
            print("Diagram tujuan:", image_dst)
            print("\nLanjutkan --apply hanya jika hasil ini benar.")
            return

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        backup = Path(
            "database/garment-before-section"
            + str(section_number)
            + "-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".db"
        )

        if backup.exists():
            stop(f"Backup sudah ada: {backup}")

        backup_con = sqlite3.connect(backup)
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()

        print("BACKUP:", backup)

        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO components (
                machine_id, component_name, location, function,
                notes, source_url, catalog_ref, diagram_page, image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            MACHINE_ID,
            cfg["name"],
            None,
            None,
            f"Official JUKI AMS-224EN-6030 parts catalog, Section {section_number}.",
            SOURCE_URL,
            str(section_number),
            cfg["diagram"],
            image_db_path,
        ))

        component_id = cur.lastrowid

        for r in records:
            cur = con.execute("""
                INSERT INTO parts (
                    machine_id, source_document_id, part_number,
                    part_name, quantity, catalog_ref, diagram_page,
                    note, source_url, notes, quantity_raw
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
            """, (
                MACHINE_ID,
                DOCUMENT_ID,
                r["number"],
                r["name"],
                r["qty"],
                str(r["ref"]),
                r["marker"],
                SOURCE_URL,
                f"AMS-224EN-6030 section: {cfg['name']}",
                r["qty_raw"],
            ))

            part_id = cur.lastrowid

            con.execute("""
                INSERT INTO component_parts (
                    component_id, part_id, relation_type, notes
                )
                VALUES (?, ?, ?, ?)
            """, (
                component_id,
                part_id,
                "catalog_component_part",
                f"REF {r['ref']}",
            ))

        new_counts = get_counts(con)

        inserted = con.execute("""
            SELECT p.part_number, p.part_name, p.quantity,
                   p.quantity_raw, p.note, cp.notes,
                   cp.relation_type
            FROM component_parts cp
            JOIN parts p ON p.id=cp.part_id
            WHERE cp.component_id=?
            ORDER BY CAST(REPLACE(cp.notes, 'REF ', '') AS INTEGER)
        """, (component_id,)).fetchall()

        expected_inserted = [
            (
                r["number"],
                r["name"],
                r["qty"],
                r["qty_raw"],
                r["marker"],
                f"REF {r['ref']}",
                "catalog_component_part",
            )
            for r in records
        ]

        if new_counts != cfg["target"]:
            stop(f"Total database salah: {new_counts}")

        if [tuple(row) for row in inserted] != expected_inserted:
            stop("Hasil INSERT tidak sama dengan data sumber")

        linked_refs = [
            int(row["notes"].replace("REF ", ""))
            for row in con.execute("""
                SELECT notes FROM component_parts
                WHERE component_id=?
                ORDER BY CAST(REPLACE(notes, 'REF ', '') AS INTEGER)
            """, (component_id,))
        ]

        if linked_refs != list(range(1, cfg["refs"] + 1)):
            stop("REF relasi tidak lengkap")

        expected_snapshot = before + [
            (
                component_id,
                cfg["name"],
                cfg["diagram"],
                image_db_path,
                len(records),
            )
        ]

        if snapshot(con) != expected_snapshot:
            stop("Snapshot komponen tidak sesuai")

        shutil.copy2(image_src, image_dst)
        image_copied = True

        if not image_dst.is_file() or image_dst.stat().st_size == 0:
            stop("File diagram hasil salin tidak valid")

        print("\n=== PREFLIGHT FINAL ===")
        print("Total parts:", new_counts[0])
        print("Total komponen:", new_counts[1])
        print("Total relasi:", new_counts[2])
        print("REF valid:", len(linked_refs))
        print("Data part dan quantity_raw valid:", True)
        print("Marker valid:", True)
        print("Komponen lama tidak berubah:", True)
        print("Diagram:", image_db_path)
        print("Ukuran diagram:", image_dst.stat().st_size)

        con.commit()

        print(f"\n=== IMPOR SECTION {section_number} BERHASIL ===")
        print("Component ID:", component_id)
        print("Nama:", cfg["name"])
        print("REF:", len(linked_refs))
        print("Database:", new_counts)
        print("Backup:", backup)

    except Exception as exc:
        con.rollback()

        if image_copied and image_dst.exists():
            image_dst.unlink()

        print("\n=== IMPOR DIBATALKAN ===")
        print("Alasan:", exc)
        raise

    finally:
        con.close()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("1", "2"):
        raise SystemExit(
            "Gunakan: python tools/import_ams224_sections1_2.py 1 "
            "[--apply] atau ... 2 [--apply]"
        )

    section_number = int(sys.argv[1])
    apply = "--apply" in sys.argv

    run(section_number, apply)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nGAGAL:", exc)
        sys.exit(1)
