import re
import sqlite3
from pathlib import Path

db_path = Path("database/garment.db")

if not db_path.exists():
    raise SystemExit("Database tidak ditemukan.")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

try:
    conn.execute("BEGIN")

    # 1. Buat tabel master seri jarum.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS needle_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_code TEXT NOT NULL COLLATE NOCASE UNIQUE,
            series_name TEXT NOT NULL,
            description TEXT,
            verification_status TEXT NOT NULL
                DEFAULT 'Perlu diverifikasi',
            verification_notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        )
    """)

    # 2. Hubungkan sistem jarum dengan master seri.
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(needle_systems)"
        )
    }

    if "series_id" not in columns:
        conn.execute("""
            ALTER TABLE needle_systems
            ADD COLUMN series_id INTEGER
                REFERENCES needle_series(id)
        """)

    # 3. Isi empat seri awal dari kelompok yang sudah
    #    dikenali oleh filter katalog saat ini.
    initial_series = [
        (
            "134",
            "Seri 134",
            "Kelompok sementara untuk sistem berkode 134.",
        ),
        (
            "DB",
            "Seri DB",
            "Kelompok sementara untuk sistem berawalan DB.",
        ),
        (
            "DC",
            "Seri DC",
            "Kelompok sementara untuk sistem berawalan DC.",
        ),
        (
            "UY",
            "Seri UY",
            "Kelompok sementara untuk sistem berawalan UY.",
        ),
    ]

    note = (
        "Pengelompokan awal berdasarkan kode sistem "
        "di katalog. Periksa referensi resmi produsen "
        "sebelum menetapkan kecocokan teknis."
    )

    for code, name, description in initial_series:
        conn.execute("""
            INSERT OR IGNORE INTO needle_series (
                series_code,
                series_name,
                description,
                verification_status,
                verification_notes
            )
            VALUES (?, ?, ?, 'Perlu diverifikasi', ?)
        """, (code, name, description, note))

    # 4. Hubungkan tujuh sistem yang sudah ada.
    systems = conn.execute("""
        SELECT id, system_code
        FROM needle_systems
    """).fetchall()

    linked = 0

    for system in systems:
        code = system["system_code"].strip().upper()
        normalized = code.replace("×", "X")
        series_code = None

        if re.match(r"^DB(?:X|\b)", normalized):
            series_code = "DB"
        elif re.match(r"^DC(?:X|\b)", normalized):
            series_code = "DC"
        elif re.match(r"^UY(?:\s|X|\b)", normalized):
            series_code = "UY"
        elif re.match(r"^134(?:\s|$|\()", normalized):
            series_code = "134"

        if series_code:
            series = conn.execute("""
                SELECT id
                FROM needle_series
                WHERE series_code = ?
            """, (series_code,)).fetchone()

            if series:
                conn.execute("""
                    UPDATE needle_systems
                    SET series_id = ?
                    WHERE id = ?
                """, (series["id"], system["id"]))
                linked += 1

    conn.commit()

    print("MIGRASI MASTER SERI BERHASIL")
    print("\n=== MASTER SERI JARUM ===")

    for row in conn.execute("""
        SELECT id, series_code, series_name,
               verification_status
        FROM needle_series
        ORDER BY series_code
    """):
        print(
            row["id"],
            "|", row["series_code"],
            "|", row["series_name"],
            "|", row["verification_status"],
        )

    print("\n=== HUBUNGAN SISTEM DAN SERI ===")
    for row in conn.execute("""
        SELECT ns.system_code, s.series_code
        FROM needle_systems ns
        LEFT JOIN needle_series s ON s.id = ns.series_id
        ORDER BY ns.system_code
    """):
        print(
            row["system_code"],
            "->",
            row["series_code"] or "Belum dikelompokkan",
        )

    print("\nJumlah sistem yang diproses:", len(systems))
    print("Hubungan sistem-seri yang dibuat:", linked)

    needle_count = conn.execute(
        "SELECT COUNT(*) FROM needles"
    ).fetchone()[0]
    print("Jumlah data jarum tetap:", needle_count)

except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
