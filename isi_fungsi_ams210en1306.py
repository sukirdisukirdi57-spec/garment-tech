import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MODEL_ID = 43
MODEL = "AMS-210EN-1306"

# Fungsi awal berdasarkan nama komponen.
# Komponen yang ambigu diberi catatan agar tidak dianggap
# telah diverifikasi secara spesifik terhadap diagram.
FUNCTIONS = {
    "400-29632": (
        "Rakitan sakelar penghenti; fungsi dan kondisi pemicu "
        "perlu dicocokkan dengan diagram."
    ),
    "400-28338": (
        "Menggulung benang bawah ke bobbin."
    ),
    "141-13468": (
        "Mengatur tegangan benang bawah pada sistem bobbin."
    ),
    "400-06836": (
        "Menampung atau mendukung penyaluran oli pelumasan."
    ),
    "400-29776": (
        "Rakitan sakelar pengaman; fungsi interlock dan kondisi "
        "pemicu perlu diverifikasi pada diagram."
    ),
    "400-52937": (
        "Motor servo 550 W untuk penggerak mesin; fungsi penggerak "
        "spesifik perlu dicocokkan dengan konfigurasi model."
    ),
    "B1411-552-0A0": (
        "Menghubungkan batang jarum dengan mekanisme penggeraknya "
        "untuk meneruskan gerakan jarum."
    ),
    "131-22452": (
        "Rakitan engkol pada mekanisme feed; gerakan dan bagian "
        "yang digerakkan perlu dicocokkan dengan diagram."
    ),
    "401-02213": (
        "Rakitan motor dengan encoder; sumbu atau mekanisme yang "
        "dikendalikan perlu diverifikasi pada diagram."
    ),
    "400-72009": (
        "Rakitan roda gigi poros bawah; meneruskan gerak melalui "
        "mekanisme roda gigi."
    ),
    "400-89364": (
        "Rakitan shuttle/rotary hook untuk membantu membentuk "
        "jahitan kunci bersama benang bawah."
    ),
    "400-86363": (
        "Menggerakkan wiper untuk menyapu atau memindahkan ujung "
        "benang setelah pemotongan."
    ),
    "400-10503": (
        "Rakitan pengatur tegangan benang atas nomor 1."
    ),
    "400-10508": (
        "Rakitan pengatur tegangan benang atas nomor 2; fungsi "
        "pengaturan atau pelepasan spesifik perlu dicocokkan "
        "dengan manual."
    ),
    "400-78001": (
        "Rakitan meja X-Y untuk mendukung gerakan relatif area "
        "kerja mengikuti pola jahitan terprogram."
    ),
    "401-03969": (
        "Rakitan motor dengan encoder bertanda IP; fungsi spesifik "
        "dan mekanisme yang dikendalikan perlu diverifikasi."
    ),
    "400-23638": (
        "Rangka feeding untuk mendukung mekanisme pemakanan atau "
        "penempatan benda kerja; detail geraknya perlu diverifikasi."
    ),
}

parser = argparse.ArgumentParser()
parser.add_argument(
    "--apply",
    action="store_true",
    help="Simpan fungsi setelah membuat backup"
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
        raise SystemExit("Identitas mesin tidak cocok.")

    rows = []
    for part_number, proposed in FUNCTIONS.items():
        row = con.execute("""
            SELECT id, component_name, part_number, function, notes
            FROM components
            WHERE machine_id=? AND part_number=?
        """, (MODEL_ID, part_number)).fetchone()

        if not row:
            raise SystemExit(
                f"Komponen {part_number} tidak ditemukan. "
                "Tidak ada perubahan."
            )
        rows.append((row, proposed))

    print(f"MODEL: {MODEL} (ID {MODEL_ID})")
    print("\n=== PRATINJAU FUNGSI ===")

    to_update = []
    skipped = []

    for row, proposed in rows:
        current = (row["function"] or "").strip()
        if current:
            skipped.append(row)
            print(
                f"[LEWATI - SUDAH ADA] {row['part_number']} | "
                f"{row['component_name']} | fungsi={current}"
            )
        else:
            to_update.append((row, proposed))
            print(
                f"[USULAN] {row['part_number']} | "
                f"{row['component_name']}\n"
                f"  Fungsi: {proposed}"
            )

    print(f"\nFUNGSI KOSONG YANG AKAN DIISI: {len(to_update)}")
    print(f"FUNGSI YANG DIPERTAHANKAN: {len(skipped)}")

    if not args.apply:
        print("\nMODE PRATINJAU. Database belum diubah.")
        print("Periksa fungsi di atas sebelum memakai --apply.")
    else:
        if not to_update:
            print("\nTidak ada fungsi kosong yang perlu diisi.")
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = DB.parent / "backups" / (
                f"garment_before_ams210en1306_functions_{stamp}.db"
            )
            backup.parent.mkdir(parents=True, exist_ok=True)

            con.close()
            shutil.copy2(DB, backup)
            con = sqlite3.connect(DB)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys=ON")

            try:
                con.execute("BEGIN IMMEDIATE")
                updated = 0

                for row, proposed in to_update:
                    cur = con.execute("""
                        UPDATE components
                        SET function=?,
                            notes=CASE
                                WHEN notes IS NULL OR TRIM(notes)=''
                                THEN ?
                                ELSE notes
                            END
                        WHERE id=? AND machine_id=?
                          AND part_number=?
                          AND (function IS NULL OR TRIM(function)='')
                    """, (
                        proposed,
                        "Fungsi awal berdasarkan nama komponen; "
                        "perlu verifikasi terhadap diagram katalog "
                        "dan manual sebelum dianggap final.",
                        row["id"],
                        MODEL_ID,
                        row["part_number"]
                    ))
                    updated += cur.rowcount

                con.commit()

                remaining = con.execute("""
                    SELECT COUNT(*) FROM components
                    WHERE machine_id=?
                      AND part_number IN (
                          SELECT part_number FROM components
                          WHERE machine_id=?
                      )
                      AND (function IS NULL OR TRIM(function)='')
                """, (MODEL_ID, MODEL_ID)).fetchone()[0]

                print("\nBERHASIL.")
                print("Fungsi baru diisi:", updated)
                print("Backup:", backup)
                print(
                    "Catatan: angka fungsi kosong di bawah menghitung "
                    "semua komponen mesin, bukan hanya 17 kandidat."
                )
                print("Komponen dengan fungsi kosong di mesin:", remaining)

            except Exception:
                con.rollback()
                raise
finally:
    con.close()
