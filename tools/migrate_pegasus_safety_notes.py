import argparse
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")

PROPOSALS = {
    1262: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1252: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1257: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1237: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1242: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1247: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1221: (
        "Lakukan penyetelan dengan mesin dalam kondisi aman.",
        "Matikan mesin dan putuskan sumber tenaga sebelum "
        "membersihkan komponen atau melakukan penyetelan.",
    ),
    1222: (
        "Lakukan penyetelan secara bertahap untuk mencegah kerusakan material.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1227: (
        "Lakukan penyetelan secara bertahap.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
    1232: (
        "Lakukan penyetelan secara bertahap.",
        "Hentikan mesin sebelum melakukan penyetelan. "
        "Jauhkan tangan dari jarum dan bagian bergerak.",
    ),
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Terapkan perubahan setelah validasi dan backup",
    )
    args = parser.parse_args()

    if not DB.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB}")

    db_path = DB.resolve()
    con = sqlite3.connect(str(db_path), timeout=30)
    con.row_factory = sqlite3.Row

    try:
        con.execute("PRAGMA busy_timeout = 30000")
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        print("Integritas awal:", integrity)
        if integrity != "ok":
            raise RuntimeError("Integritas awal tidak OK.")

        marks = ",".join("?" for _ in PROPOSALS)
        rows = con.execute(f"""
            SELECT t.id, b.name AS brand, m.model,
                   t.problem, t.safety_notes
            FROM troubleshooting t
            JOIN machines m ON m.id = t.machine_id
            JOIN brands b ON b.id = m.brand_id
            WHERE t.id IN ({marks})
        """, tuple(PROPOSALS)).fetchall()

        found = {r["id"]: r for r in rows}
        if set(found) != set(PROPOSALS):
            raise RuntimeError("Daftar ID tidak cocok dengan target.")

        for tid, (old, new) in PROPOSALS.items():
            r = found[tid]
            if (r["brand"] or "").strip().upper() != "PEGASUS":
                raise RuntimeError(f"ID {tid} bukan milik PEGASUS.")
            if (r["safety_notes"] or "").strip() != old:
                raise RuntimeError(
                    f"Catatan lama ID {tid} berubah; batalkan migrasi."
                )

        print("Validasi target: OK")
        print("Jumlah record:", len(found))
        print("Mode:", "APPLY" if args.apply else "SIMULASI")

        if not args.apply:
            for tid, (old, new) in PROPOSALS.items():
                print(f"\nID {tid}")
                print("LAMA:", old)
                print("BARU:", new)
            print("\nSIMULASI LOLOS — database tidak diubah.")
            return

        backup = db_path.with_name(
            db_path.name
            + ".backup-before-pegasus-safety-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
        )
        shutil.copy2(db_path, backup)

        # Pastikan backup dapat dibuka dan sehat.
        bcon = sqlite3.connect(
            f"file:{backup}?mode=ro", uri=True
        )
        try:
            bcheck = bcon.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            bcon.close()

        if bcheck != "ok":
            backup.unlink(missing_ok=True)
            raise RuntimeError("Backup tidak lolos integrity_check.")

        print("Backup terverifikasi:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")
            for tid, (old, new) in PROPOSALS.items():
                cur = con.execute("""
                    UPDATE troubleshooting
                    SET safety_notes = ?
                    WHERE id = ?
                      AND safety_notes = ?
                      AND machine_id IN (
                          SELECT m.id
                          FROM machines m
                          JOIN brands b ON b.id = m.brand_id
                          WHERE UPPER(b.name) = 'PEGASUS'
                      )
                """, (new, tid, old))

                if cur.rowcount != 1:
                    raise RuntimeError(
                        f"Update ID {tid} tidak tepat satu baris."
                    )

            for tid, (old, new) in PROPOSALS.items():
                actual = con.execute(
                    "SELECT safety_notes FROM troubleshooting WHERE id = ?",
                    (tid,),
                ).fetchone()
                if not actual or actual["safety_notes"] != new:
                    raise RuntimeError(
                        f"Verifikasi pasca-update gagal pada ID {tid}."
                    )

            con.commit()

        except Exception:
            con.rollback()
            raise

        final_check = con.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if final_check != "ok":
            raise RuntimeError(
                "Integritas pasca-commit tidak OK. "
                f"Periksa backup: {backup}"
            )

        print("\nMIGRASI BERHASIL")
        print("Baris diperbarui:", len(PROPOSALS))
        print("Verifikasi seluruh catatan: OK")
        print("Integritas akhir:", final_check)
        print("Backup:", backup)

    finally:
        con.close()

if __name__ == "__main__":
    main()
