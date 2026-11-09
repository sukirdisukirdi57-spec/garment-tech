import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
BACKUP_DIR = Path("database/backups")
MACHINE_ID = 44

SOURCE_URL = (
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_ip420/pdf/partslist.pdf"
)

# part_number, catalog_ref, fungsi teknis sementara
ITEMS = [
    ("400-86363",       1,  "Menggerakkan mekanisme pemotong benang atau wiper; pastikan fungsi rakitan pada diagram."),
    ("401-03969",       1,  "Rakitan motor encoder untuk umpan balik posisi atau gerakan; verifikasi konfigurasi IP."),
    ("400-78000",       3,  "Rakitan meja X-Y khusus model AMS-210EN-2210."),
    ("400-28338",       4,  "Rakitan penggulung benang bobbin."),
    ("400-72009",       4,  "Rakitan roda gigi poros bawah untuk meneruskan gerakan mekanis."),
    ("400-72228",      10,  "Rakitan penghubung mekanisme pemotong benang."),
    ("400-89364",      12,  "Rakitan shuttle untuk pembentukan jahitan."),
    ("401-02213",      20,  "Rakitan motor encoder; fungsi dan posisi harus dicocokkan dengan diagram."),
    ("131-22452",      22,  "Rakitan engkol penggerak mekanisme feed."),
    ("400-10503",      27,  "Rakitan tegangan benang nomor 1."),
    ("141-13468",      28,  "Rakitan pengatur tegangan benang bobbin."),
    ("400-85033",      30,  "Motor stepper; fungsi gerak spesifik perlu diverifikasi pada diagram."),
    ("400-52937",      40,  "Motor servo 550 W sebagai penggerak mesin."),
    ("400-29632",      50,  "Rakitan sakelar STOP."),
    ("B1411-552-0A0",  58,  "Rakitan penghubung batang jarum."),
    ("400-06836",      60,  "Rakitan tangki atau sistem penampung oli."),
    ("400-29776",      63,  "Rakitan safety switch untuk fungsi keselamatan."),
]

NOTE = (
    "Referensi: JUKI AMS-210EN Series Parts List, edisi No.1526-11. "
    "Fungsi merupakan ringkasan teknis sementara berdasarkan nama part; "
    "perlu verifikasi terhadap diagram/manual resmi. "
    "Nomor halaman diagram belum diverifikasi."
)

def main():
    if not DB.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB.resolve()}")

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row

    try:
        # Pastikan struktur tabel yang dibutuhkan tersedia.
        required = {
            "machines": {"id"},
            "parts": {"id", "machine_id", "part_number", "part_name", "catalog_ref"},
            "components": {
                "id", "machine_id", "component_name", "part_number",
                "catalog_ref", "diagram_page", "function", "notes", "source_url"
            },
            "component_parts": {"id", "component_id", "part_id", "relation_type", "notes"},
        }

        for table, needed in required.items():
            cols = {
                row["name"]
                for row in con.execute(f"PRAGMA table_info({table})")
            }
            missing = needed - cols
            if missing:
                raise SystemExit(
                    f"Kolom tabel {table} tidak cocok; kolom hilang: {sorted(missing)}"
                )

        machine = con.execute(
            "SELECT id, model FROM machines WHERE id = ?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine:
            raise SystemExit(f"Mesin id={MACHINE_ID} tidak ditemukan.")

        print(f"Database : {DB.resolve()}")
        print(f"Mesin    : id={machine['id']} | model={machine['model']}")
        print(f"Kandidat : {len(ITEMS)} komponen")
        print("\n=== PEMERIKSAAN AWAL ===")

        resolved = []
        errors = []

        for pn, expected_ref, function in ITEMS:
            parts = con.execute(
                """
                SELECT id, part_number, part_name, catalog_ref
                FROM parts
                WHERE machine_id = ? AND part_number = ?
                """,
                (MACHINE_ID, pn)
            ).fetchall()

            if len(parts) != 1:
                errors.append(
                    f"{pn}: ditemukan {len(parts)} baris parts; seharusnya tepat 1."
                )
                continue

            part = parts[0]
            if part["catalog_ref"] != expected_ref:
                errors.append(
                    f"{pn}: catalog_ref database={part['catalog_ref']}, "
                    f"yang diharapkan={expected_ref}."
                )
                continue

            existing = con.execute(
                """
                SELECT id, component_name, catalog_ref
                FROM components
                WHERE machine_id = ? AND part_number = ?
                """,
                (MACHINE_ID, pn)
            ).fetchall()

            if len(existing) > 1:
                errors.append(
                    f"{pn}: ada lebih dari satu komponen dengan nomor part tersebut."
                )
                continue

            if existing and existing[0]["catalog_ref"] not in (None, expected_ref):
                errors.append(
                    f"{pn}: komponen yang sudah ada memiliki catalog_ref "
                    f"{existing[0]['catalog_ref']}, bukan {expected_ref}."
                )
                continue

            resolved.append((part, function, existing[0] if existing else None))

            status = "SUDAH ADA" if existing else "BARU"
            print(
                f"[{status}] part_id={part['id']} | REF {expected_ref:>2} | "
                f"{pn} | {part['part_name']}"
            )

        if errors:
            print("\nDIBATALKAN — ada masalah pada pemeriksaan:")
            for err in errors:
                print(" -", err)
            raise SystemExit(1)

        new_components = sum(1 for _, _, existing in resolved if not existing)
        print(f"\nKomponen baru yang akan ditambahkan: {new_components}")

        if new_components == 0:
            print("Semua komponen sudah ada. Tidak ada komponen baru untuk ditambahkan.")
            # Tetap periksa relasi di bawah; mungkin ada yang belum terhubung.

        answer = input(
            "\nJika hasil cocok, ketik YA untuk membuat backup dan menerapkan perubahan: "
        ).strip()

        if answer != "YA":
            print("Dibatalkan oleh pengguna. Database tidak diubah.")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"garment_before_ams210en2210_components_{stamp}.db"

        # Backup konsisten menggunakan mekanisme backup SQLite.
        backup_con = sqlite3.connect(backup_path)
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()

        print(f"\nBackup dibuat: {backup_path}")

        inserted = 0
        linked = 0
        con.execute("BEGIN IMMEDIATE")

        try:
            for part, function, existing in resolved:
                pn = part["part_number"]

                if existing:
                    component_id = existing["id"]
                else:
                    cur = con.execute(
                        """
                        INSERT INTO components (
                            machine_id, component_name, part_number,
                            catalog_ref, diagram_page, function, notes, source_url
                        )
                        VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                        """,
                        (
                            MACHINE_ID,
                            part["part_name"],
                            pn,
                            part["catalog_ref"],
                            function,
                            NOTE,
                            SOURCE_URL,
                        )
                    )
                    component_id = cur.lastrowid
                    inserted += 1

                # UNIQUE(component_id, part_id) tidak boleh menghasilkan duplikat.
                relation = con.execute(
                    """
                    SELECT id
                    FROM component_parts
                    WHERE component_id = ? AND part_id = ?
                    """,
                    (component_id, part["id"])
                ).fetchone()

                if not relation:
                    con.execute(
                        """
                        INSERT INTO component_parts (
                            component_id, part_id, relation_type, notes
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            component_id,
                            part["id"],
                            "matched_catalog_part",
                            "Dicocokkan berdasarkan nomor part pada katalog JUKI.",
                        )
                    )
                    linked += 1

            con.commit()
        except Exception:
            con.rollback()
            raise

        # Verifikasi setelah commit.
        print("\n=== VERIFIKASI AKHIR ===")
        total = con.execute(
            "SELECT COUNT(*) FROM components WHERE machine_id = ?",
            (MACHINE_ID,)
        ).fetchone()[0]

        verified = con.execute(
            """
            SELECT COUNT(*)
            FROM components c
            JOIN component_parts cp ON cp.component_id = c.id
            JOIN parts p ON p.id = cp.part_id
            WHERE c.machine_id = ?
              AND p.machine_id = ?
              AND c.part_number = p.part_number
            """,
            (MACHINE_ID, MACHINE_ID)
        ).fetchone()[0]

        missing_links = []
        for part, _, existing in resolved:
            row = con.execute(
                """
                SELECT c.id
                FROM components c
                JOIN component_parts cp ON cp.component_id = c.id
                WHERE c.machine_id = ?
                  AND c.part_number = ?
                  AND cp.part_id = ?
                """,
                (MACHINE_ID, part["part_number"], part["id"])
            ).fetchone()
            if not row:
                missing_links.append(part["part_number"])

        print(f"Komponen baru ditambahkan : {inserted}")
        print(f"Relasi baru dibuat        : {linked}")
        print(f"Total komponen mesin 44   : {total}")
        print(f"Relasi cocok terverifikasi: {verified}")
        print(f"Relasi kandidat hilang    : {len(missing_links)}")
        print(f"Backup                    : {backup_path}")

        if missing_links:
            print("Nomor part belum terhubung:", ", ".join(missing_links))
            raise SystemExit("PERINGATAN: verifikasi relasi belum lengkap.")

        print("\nSelesai. Tidak ada data yang dihapus atau ditimpa.")

    finally:
        con.close()

if __name__ == "__main__":
    main()
