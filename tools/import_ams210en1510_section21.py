import sqlite3
import argparse
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
IMAGE = "images/mechanisms/juki/ams210en/pdf-page-42.jpg"
SOURCE = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)
TITLE = "21. CONTROL BOX COMPONENTS"
SECTION_NOTE = "AMS-210EN-1510 Parts List; Section 21"

ROWS = [
(1,  "400-81561",     "MC-587 BOX A",                         "1",   "#01"),
(2,  "400-81562",     "MC-587 BOX B",                         "1",   "#02"),
(3,  "400-81563",     "MC-587 BOX C",                         "1",   "#03"),
(4,  "400-55355",     "CONTROL BOX",                          "(1)", None),
(5,  "400-55366",     "CONTROL BOX FRONT COVER",              "(1)", None),
(6,  "400-55357",     "CONTROL BOX REAR COVER",               "(1)", None),
(7,  "SL-4040891-SC", "SCREW M4 L=8",                         "(6)", None),
(8,  "SL-4040891-SC", "SCREW M4 L=8",                         "(4)", None),
(9,  "M3801-476-000", "TRANSMISSION BOX FITTING PLATE",       "(1)", None),
(10, "SL-6083092-TN", "SCREW",                               "(4)", None),
(11, "HX-0032600-0K", "GROMMET",                             "(1)", None),
(12, "SL-4040891-SC", "SCREW M4 L=8",                         "(4)", None),
(13, "NM-6080001-SC", "NUT M8X1.25",                         "(8)", None),
(14, "M4206-461-000", "WASHER",                              "(4)", None),
(15, "402-68712",     "MAIN PCB A ASSY",                     "(1)", None),
(16, "SL-4040881-SC", "SCREW M4 L=8",                         "(6)", "#05"),
(17, "400-82758",     "SDC PCB A ASSY",                      "(1)", None),
(18, "SL-4040881-SC", "SCREW M4 L=8",                        "(10)", None),
(19, "400-00056",     "FLT-T PCB A ASS'Y",                   "(1)", "#01"),
(20, "SL-4040881-SC", "SCREW M4 L=8",                         "(6)", "#05"),
(21, "HX-0033900-00", "STUD",                                "(6)", None),
(22, "NM-3040520-SC", "NUT M4",                              "(6)", None),
(23, "400-05401",     "FAN MOTOR ASS'Y",                     "(1)", None),
(24, "KM-0000004-80", "FAN MOTOR",                           "(1)", None),
(25, "SL-4043591-SC", "SCREW",                               "(4)", None),
(26, "NM-3040520-SC", "NUT M4",                              "(4)", None),
(27, "400-05706",     "MAIN PCB HOLDER PLATE",               "(1)", None),
(28, "SL-4040881-SC", "SCREW M4 L=8",                         "(5)", None),
(29, "HX-0040700-00", "BUSH",                                "(1)", None),
(30, "178-45009",     "CORD FITTING PLATE",                  "(1)", None),
(31, "SL-4041091-SC", "SCREW M4 L=10",                        "(2)", None),
(32, "400-86465",     "POWER CORD 3P ASSY",                  "(1)", "#01"),
(33, "HX-0041000-0A", "STRAIN RELIEF BUSHING",               "(1)", None),
(34, "400-05393",     "FLT-SDC CORD P ASS'Y",               "(1)", "#05"),
(35, "400-05394",     "FLT-SDC CORD S ASS'Y",               "(1)", None),
(36, "400-05726",     "SDC-MAIN CORD P ASS'Y",              "(1)", None),
(37, "400-05727",     "SDC-MAIN CORD S ASS'Y",              "(1)", None),
(38, "HX-0051100-00", "WIRE SADDLE",                        "(3)", None),
(39, "E9607-603-000", "STICKER (SMALL)",                    "(1)", None),
(40, "E9567-319-000", "EARTH MARK",                         "(1)", None),
(41, "400-03458",     "MASK SEAL",                          "(15)", None),
(42, "WP-0841601-SC", "WASHER 8.4X17.4X1.6",                "(4)", None),
(43, "401-62838",     "FLT-CE PCB A ASSY",                   "(1)", "#02"),
(44, "400-86466",     "POWER CORD JE ASSY",                  "(1)", "#03"),
(45, "400-86467",     "POWER CORD 1P ASSY",                  "(1)", "#04"),
(46, "CM-2001000-01", "PE MARK LABEL",                       "(1)", "#03"),
(47, "KX-0000002-10", "SADDLE TYPE TIE MOUNT",               "(1)", None),
(48, "KX-0000002-30", "RELEASIBLE CABLE TIE",                "(1)", None),
(49, "SL-4040881-SC", "SCREW M4 L=8",                         "(1)", None),
(50, "HN-0024600-00", "CORES",                               "(1)", "#03"),
(51, "HN-0028400-00", "CORES",                               "(1)", "#03"),
(52, "HN-0014900-00", "CLAMP FILTER(L)",                     "(1)", None),
(53, "400-73659",     "SW RELAY CORD ASM",                   "(1)", None),
(54, "EA-9500B01-00", "CABLE BAND",                         "(1)", None),
(55, "M9029-580-0A0", "FDD EARTH CORD ASM.",                "(1)", None),
(56, "SL-4041081-SC", "SCREW M4 L=10",                       "(1)", "#03"),
(57, "CM-6001001-01", "WEEE MARK LABEL S",                   "(1)", "#03"),
(58, "400-51640",     "ELECTRICAL_RATING_LABEL_UNIVERSAL",   "(1)", "#05"),
(59, "400-57278",     "ELECTRICAL_RATING_LABEL_CE_UNIVERSAL","(1)", "#03"),
(60, "HX-0033900-0M", "SPACER",                              "(5)", "#03"),
(61, "SL-4040881-SC", "SCREW M4 L=8",                         "(1)", "#03"),
(62, "SL-4041091-SC", "SCREW M4 L=10",                        "(5)", "#03"),
(63, "SL-4040881-SC", "SCREW M4 L=8",                         "(5)", "#03"),
(64, "SL-4041081-SC", "SCREW M4 L=10",                        "(1)", "#03"),
(65, "401-63025",     "REACTOR CORD ASSY",                   "(1)", "#03"),
(66, "SL-4040891-SC", "SCREW M4 L=8",                         "(2)", "#03"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not DB.is_file():
        raise SystemExit("ERROR: database tidak ditemukan")
    if not Path("static", IMAGE).is_file():
        raise SystemExit(f"ERROR: diagram tidak ditemukan: {IMAGE}")

    refs = [r[0] for r in ROWS]
    if refs != list(range(1, 67)):
        raise SystemExit("ERROR: REF tidak lengkap/berurutan")
    if any(not pn or not name for _, pn, name, _, _ in ROWS):
        raise SystemExit("ERROR: nomor part/nama kosong")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id=15"
        ).fetchone()
        doc = con.execute(
            "SELECT id, title FROM documents WHERE id=136 AND machine_id=15"
        ).fetchone()

        print("=== PREFLIGHT SECTION 21 ===")
        print("Machine:", dict(machine) if machine else None)
        print("Dokumen:", dict(doc) if doc else None)
        print("Judul:", TITLE)
        print("REF katalog:", len(ROWS))
        print("Gambar:", IMAGE, "| OK")

        if not machine or machine["model"] != "AMS-210EN-1510":
            raise SystemExit("ERROR: machine tidak sesuai")
        if not doc:
            raise SystemExit("ERROR: dokumen Parts List tidak ditemukan")

        existing = con.execute("""
            SELECT id FROM components
            WHERE machine_id=15 AND component_name=?
        """, (TITLE,)).fetchone()
        if existing:
            raise SystemExit(
                f"STOP: komponen sudah ada, ID {existing['id']}"
            )

        print("\n=== DAFTAR PART ===")
        for ref, pn, name, qty, marker in ROWS:
            print(
                f"REF{ref:02d} | {pn:15} | Qty {qty:5} | "
                f"NOTE {marker or '-':4} | {name}"
            )

        by_pn = {}
        for ref, pn, *_ in ROWS:
            by_pn.setdefault(pn, []).append(ref)
        print("\nNomor part duplikat:")
        for pn, rr in by_pn.items():
            if len(rr) > 1:
                print(pn, rr)

        markers = {}
        for ref, pn, name, qty, marker in ROWS:
            if marker:
                markers.setdefault(marker, []).append(ref)
        print("Distribusi marker:", markers)

        old_pns = sorted(by_pn)
        placeholders = ",".join("?" for _ in old_pns)
        old = con.execute(f"""
            SELECT id, catalog_ref, part_number, part_name,
                   quantity_raw, note, notes
            FROM parts
            WHERE machine_id=15 AND part_number IN ({placeholders})
            ORDER BY part_number, id
        """, old_pns).fetchall()
        print("\nPart lama dengan nomor sama:", len(old))
        for r in old:
            print(dict(r))
        print("Data lama digunakan ulang: tidak")
        print("Part baru:", len(ROWS))
        print("Relasi baru:", len(ROWS))

        if not args.apply:
            print("\nDRY-RUN: database tidak diubah.")
            return

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = Path(f"database/garment-before-ams210en1510-section21-{stamp}.db")
        backup.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(backup)
        con.backup(target)
        target.close()
        print("\nBackup:", backup)

        con.execute("BEGIN IMMEDIATE")
        cur = con.execute("""
            INSERT INTO components
            (machine_id, component_name, notes, image_path,
             source_url, catalog_ref, diagram_page)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (15, TITLE, SECTION_NOTE, IMAGE, SOURCE, "21", 37))
        component_id = cur.lastrowid

        for ref, pn, name, qty_raw, marker in ROWS:
            quantity = int(qty_raw.strip("()"))
            notes = SECTION_NOTE
            con.execute("""
                INSERT INTO parts
                (machine_id, source_document_id, part_number, part_name,
                 quantity, quantity_raw, catalog_ref, diagram_page,
                 note, source_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                15, 136, pn, name, quantity, qty_raw, ref, 37,
                marker, SOURCE, notes
            ))
            part_id = con.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]
            con.execute("""
                INSERT INTO component_parts
                (component_id, part_id, relation_type, notes)
                VALUES (?, ?, ?, ?)
            """, (
                component_id, part_id,
                "catalog_component_part", f"REF {ref}"
            ))

        con.commit()
        print("\nAPPLY BERHASIL")
        print("Component ID:", component_id)
        print("Part dibuat:", len(ROWS))
        print("Relasi dibuat:", len(ROWS))
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    main()
