import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MODEL_ID = 43
MODEL = "AMS-210EN-1306"
SOURCE_ID = 153
SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/"
    "manual_j/ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

# ID dan nama harus cocok dengan hasil audit parts target.
CANDIDATES = [
    (5851, "STOP SW ASM."),
    (5868, "BOBBIN_WINDER_UNIT"),
    (5891, "BOBBIN THREAD TENSION ASM."),
    (5949, "OIL TANK ASM."),
    (5952, "SAFTY_SW_ASM."),
    (6001, "SERVO MOTOR 550W"),
    (6017, "NEEDLE BAR CONNECTING ASM."),
    (6064, "FEED BRANCH CRANK ASM."),
    (6127, "ENCODER MOTOR ASM"),
    (6172, "LOWEW_SHAFT_GEAR_ASM"),
    (6180, "SHUTTLE_ASM."),
    (6212, "WIPER_ASM"),
    (6276, "THREAD_TENSION_1_ASM."),
    (6281, "THREAD_TENSION_2_ASM."),
    (6365, "X-Y_TABLE_ASM_1306"),
    (6400, "ENCODER MOTOR ASM.(IP)"),
    (6447, "FEEDING FRAME"),
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--apply",
    action="store_true",
    help="Terapkan perubahan setelah membuat backup"
)
args = parser.parse_args()

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

try:
    machine = con.execute(
        "SELECT id, model FROM machines WHERE id=?",
        (MODEL_ID,)
    ).fetchone()

    if not machine or machine["model"] != MODEL:
        raise SystemExit(
            "Identitas mesin tidak cocok. Tidak ada perubahan."
        )

    source = con.execute(
        "SELECT id, title FROM documents WHERE id=? AND machine_id=?",
        (SOURCE_ID, MODEL_ID)
    ).fetchone()

    if not source:
        raise SystemExit(
            "Dokumen parts list ID 153 tidak ditemukan "
            "untuk mesin target."
        )

    # Pastikan semua ID dan nama part masih cocok.
    parts = []
    for part_id, expected_name in CANDIDATES:
        p = con.execute("""
            SELECT id, machine_id, part_number, part_name, catalog_ref
            FROM parts
            WHERE id=? AND machine_id=?
        """, (part_id, MODEL_ID)).fetchone()

        if not p or p["part_name"] != expected_name:
            raise SystemExit(
                f"Validasi gagal untuk part ID {part_id}. "
                "Database tidak diubah."
            )
        parts.append(p)

    print(f"MODEL: {machine['model']} (ID {MODEL_ID})")
    print(f"SOURCE: {source['title']}")
    print(f"KANDIDAT: {len(parts)}")

    new_parts = []
    existing_parts = []

    for p in parts:
        existing = con.execute("""
            SELECT id, component_name
            FROM components
            WHERE machine_id=? AND part_number=?
        """, (MODEL_ID, p["part_number"])).fetchone()

        if existing:
            existing_parts.append((p, existing))
        else:
            new_parts.append(p)

    print("\n=== PRATINJAU KOMPONEN BARU ===")
    for p in new_parts:
        print(
            f"Part ID {p['id']} | {p['part_number']} | "
            f"{p['part_name']} | katalog={p['catalog_ref']}"
        )

    print("\n=== SUDAH ADA / AKAN DILEWATI ===")
    for p, c in existing_parts:
        print(
            f"Part ID {p['id']} | {p['part_number']} | "
            f"komponen ID {c['id']}: {c['component_name']}"
        )

    print(f"\nBARU: {len(new_parts)}")
    print(f"DILEWATI: {len(existing_parts)}")

    if not args.apply:
        print("\nMODE PRATINJAU. Database belum diubah.")
        print("Jika daftar sudah benar, jalankan dengan --apply.")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = DB.parent / "backups" / (
            f"garment_before_ams210en1306_components_{timestamp}.db"
        )
        backup.parent.mkdir(parents=True, exist_ok=True)

        con.close()
        shutil.copy2(DB, backup)
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")

        try:
            con.execute("BEGIN IMMEDIATE")

            # Validasi ulang setelah backup.
            check = con.execute(
                "SELECT model FROM machines WHERE id=?",
                (MODEL_ID,)
            ).fetchone()
            if not check or check["model"] != MODEL:
                raise RuntimeError("Identitas mesin berubah.")

            inserted = 0
            linked = 0

            for part_id, expected_name in CANDIDATES:
                p = con.execute("""
                    SELECT id, machine_id, part_number, part_name,
                           catalog_ref
                    FROM parts
                    WHERE id=? AND machine_id=?
                """, (part_id, MODEL_ID)).fetchone()

                if not p or p["part_name"] != expected_name:
                    raise RuntimeError(
                        f"Part {part_id} tidak lolos validasi ulang."
                    )

                c = con.execute("""
                    SELECT id FROM components
                    WHERE machine_id=? AND part_number=?
                """, (MODEL_ID, p["part_number"])).fetchone()

                if not c:
                    cur = con.execute("""
                        INSERT INTO components (
                            machine_id, component_name, part_number,
                            function, notes, source_url, catalog_ref
                        ) VALUES (?, ?, ?, NULL, ?, ?, ?)
                    """, (
                        MODEL_ID,
                        p["part_name"],
                        p["part_number"],
                        (
                            "Kandidat komponen dari daftar parts. "
                            "Fungsi dan status assembly perlu verifikasi "
                            "lebih lanjut pada diagram katalog."
                        ),
                        SOURCE_URL,
                        str(p["catalog_ref"])
                        if p["catalog_ref"] is not None else None
                    ))
                    component_id = cur.lastrowid
                    inserted += 1
                else:
                    component_id = c["id"]

                relation = con.execute("""
                    SELECT 1 FROM component_parts
                    WHERE component_id=? AND part_id=?
                """, (component_id, p["id"])).fetchone()

                if not relation:
                    con.execute("""
                        INSERT INTO component_parts (
                            component_id, part_id, relation_type, notes
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        component_id,
                        p["id"],
                        "matched_catalog_part",
                        "Nomor part cocok dengan parts pada mesin target."
                    ))
                    linked += 1

            con.commit()

            count = con.execute("""
                SELECT COUNT(*) FROM components WHERE machine_id=?
            """, (MODEL_ID,)).fetchone()[0]

            rel_count = con.execute("""
                SELECT COUNT(*)
                FROM component_parts cp
                JOIN components c ON c.id=cp.component_id
                WHERE c.machine_id=?
            """, (MODEL_ID,)).fetchone()[0]

            print("\nBERHASIL.")
            print("Komponen baru:", inserted)
            print("Relasi part baru:", linked)
            print("Total komponen mesin:", count)
            print("Total relasi komponen-part:", rel_count)
            print("Backup:", backup)

        except Exception:
            con.rollback()
            raise

finally:
    con.close()
