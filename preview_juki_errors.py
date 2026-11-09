import sqlite3
from pathlib import Path

DB = Path("database/garment.db")
CODE_FILE = Path("daftar-kode-juki.txt")
OUT_FILE = Path("tmp/ddl8000csm-audit/pratinjau.txt")

def main():
    if not DB.exists():
        print("Database tidak ditemukan:", DB)
        return

    if not CODE_FILE.exists():
        print("Daftar kode tidak ditemukan:", CODE_FILE)
        return

    codes = [
        x.strip()
        for x in CODE_FILE.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]

    con = sqlite3.connect(DB)
    try:
        machines = con.execute(
            "SELECT id, model FROM machines WHERE id IN (16, 225)"
        ).fetchall()

        counts = dict(con.execute(
            """
            SELECT machine_id, COUNT(*)
            FROM troubleshooting
            WHERE machine_id IN (16, 225)
            GROUP BY machine_id
            """
        ).fetchall())

        lines = [
            "PRATINJAU KODE TROUBLESHOOTING JUKI",
            "=" * 40,
            f"Jumlah kode: {len(codes)}",
            "MODE: BACA SAJA - TIDAK ADA DATA DIIMPOR",
            "",
            "DAFTAR KODE:",
            ", ".join(codes),
            "",
            "STATUS MESIN:"
        ]

        for machine_id, model in machines:
            lines.append(
                f"ID {machine_id} - {model}: "
                f"{counts.get(machine_id, 0)} catatan saat ini"
            )

        lines.extend([
            "",
            "CATATAN KOMPATIBILITAS:",
            "Manual yang digunakan adalah manual seri DDL-8000C.",
            "Kesesuaian setiap kode pada masing-masing varian",
            "harus diperiksa sebelum impor.",
            "",
            "CATATAN KESELAMATAN:",
            "Pemeriksaan listrik, motor, encoder, dan kotak kontrol",
            "diserahkan kepada teknisi yang kompeten.",
            "E71 dapat melibatkan pemulihan pengaturan pabrik.",
            "Jangan melakukannya tanpa konfirmasi dan persetujuan.",
            "",
            "Tidak ada INSERT, UPDATE, atau DELETE."
        ])

        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8"
        )

        print("\n".join(lines))
        print(f"\nFile tersimpan: {OUT_FILE}")

    finally:
        con.close()

if __name__ == "__main__":
    main()
