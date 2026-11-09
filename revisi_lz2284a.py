import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 33
EXPECTED_IDS = [281, 282, 283, 284, 285, 286]

# Revisi dibatasi pada teks troubleshooting.
# Tidak mengubah problem, code, machine_id, atau ID.
REVISI = {
    281: {
        "symptoms": (
            "Lebar ayunan jarum tidak sesuai dengan pengaturan, "
            "atau lebar pola berubah selama proses menjahit."
        ),
        "possible_cause": (
            "Pengaturan lebar zigzag tidak sesuai kebutuhan, "
            "pengunci pengaturan tidak mantap, atau mekanisme "
            "pengatur lebar mengalami gangguan."
        ),
        "solution": (
            "Matikan mesin dan periksa posisi pengatur lebar serta "
            "penguncinya sesuai manual LZ-2284A. Jika pengaturan "
            "berubah sendiri atau mekanisme terasa macet, minta "
            "teknisi memeriksa mekanismenya."
        ),
        "safety_notes": (
            "Matikan mesin dan pastikan motor berhenti sebelum "
            "memeriksa pengaturan. Jangan membongkar mekanisme "
            "atau memaksakan knob."
        ),
        "source": (
            "Pemeriksaan dasar berdasarkan gejala; prosedur "
            "penyetelan harus dikonfirmasi pada manual JUKI LZ-2284A."
        ),
    },
    282: {
        "symptoms": (
            "Pola 3-step zigzag tidak terbentuk sesuai pola yang "
            "diharapkan atau hasil jahitan menjadi tidak beraturan."
        ),
        "possible_cause": (
            "Pemilihan mode pola belum sesuai, mekanisme changeover "
            "belum berada pada posisi yang benar, atau terdapat "
            "gangguan pada mekanisme pembentuk pola."
        ),
        "solution": (
            "Matikan mesin. Periksa pemilihan mode standard zigzag "
            "atau 3-step zigzag dan posisi mekanisme changeover "
            "sesuai petunjuk manual model ini. Jangan memaksa lock pin. "
            "Jika pola tetap salah, minta teknisi memeriksa mekanisme."
        ),
        "safety_notes": (
            "Pastikan mesin berhenti sebelum memeriksa changeover. "
            "Posisi lock pin dan positioning hole harus dikonfirmasi "
            "melalui manual yang sesuai dengan model."
        ),
        "source": (
            "Pemeriksaan dasar berdasarkan gejala; posisi changeover "
            "dan lock pin perlu diverifikasi pada manual JUKI LZ-2284A."
        ),
    },
    283: {
        "symptoms": (
            "Kain bergerak tidak lancar sehingga panjang atau posisi "
            "jahitan berubah-ubah selama proses menjahit."
        ),
        "possible_cause": (
            "Feed dog kotor atau aus, jalur feeding terhalang, "
            "tekanan sepatu atau pengaturan feeding tidak sesuai, "
            "atau kain tidak diarahkan dengan stabil."
        ),
        "solution": (
            "Matikan mesin. Periksa kebersihan feed dog dan area "
            "feeding yang dapat dijangkau pengguna, lalu bersihkan "
            "sesuai petunjuk manual. Pastikan kain diarahkan dengan "
            "stabil. Jika masalah berlanjut, minta teknisi memeriksa "
            "pengaturan dan komponen feeding."
        ),
        "safety_notes": (
            "Matikan mesin sebelum membersihkan area feeding. "
            "Jauhkan tangan dari jarum dan bagian bergerak. "
            "Jangan menyetel mekanisme internal tanpa prosedur servis."
        ),
        "source": (
            "Panduan pemeriksaan umum mekanisme feeding; spesifikasi "
            "dan penyetelan harus mengacu pada manual LZ-2284A."
        ),
    },
    284: {
        "symptoms": (
            "Jahitan zigzag ke kiri dan kanan tampak tidak seimbang, "
            "atau titik masuk jarum tidak sesuai dengan pola."
        ),
        "possible_cause": (
            "Pengaturan pola atau posisi jarum tidak sesuai, "
            "atau mekanisme pengubah posisi jarum mengalami gangguan."
        ),
        "solution": (
            "Periksa pengaturan pola dan hasil jahitan dengan mesin "
            "berhenti. Jangan mengubah penyetelan mekanisme needle "
            "position tanpa prosedur manual yang tepat. Jika posisi "
            "jarum tetap tidak simetris, minta teknisi memeriksa "
            "mekanisme dan penyetelannya."
        ),
        "safety_notes": (
            "Matikan mesin sebelum pemeriksaan. Penyetelan mekanisme "
            "needle position harus dilakukan sesuai manual atau oleh "
            "teknisi yang kompeten."
        ),
        "source": (
            "Pemeriksaan dasar berdasarkan gejala; prosedur needle "
            "position perlu diverifikasi pada manual JUKI LZ-2284A."
        ),
    },
    285: {
        "symptoms": (
            "Sebagian tusukan tidak membentuk jahitan sehingga "
            "terjadi jahitan loncat atau pola zigzag tidak lengkap."
        ),
        "possible_cause": (
            "Jarum rusak atau tidak terpasang benar, tipe jarum tidak "
            "sesuai, benang salah jalur, atau terdapat gangguan pada "
            "area hook maupun sinkronisasi mekanisme."
        ),
        "solution": (
            "Matikan mesin. Periksa kondisi dan pemasangan jarum "
            "serta jalur benang sesuai manual. Jika masalah tetap "
            "terjadi setelah pemeriksaan dasar, minta teknisi "
            "memeriksa area hook dan timing."
        ),
        "safety_notes": (
            "Matikan mesin sebelum menangani jarum atau area hook. "
            "Jangan menyetel timing hook tanpa prosedur servis "
            "dan peralatan yang sesuai."
        ),
        "source": (
            "Panduan diagnosis umum jahitan loncat; spesifikasi jarum "
            "dan prosedur timing harus dikonfirmasi pada manual "
            "JUKI LZ-2284A."
        ),
    },
    286: {
        "symptoms": (
            "Jarum patah berulang kali, terutama ketika bergerak "
            "ke sisi kiri atau kanan pada pola zigzag."
        ),
        "possible_cause": (
            "Jarum bengkok, rusak atau tidak sesuai; pemasangan jarum "
            "kurang tepat; kain tertarik; atau jarum bersentuhan "
            "dengan presser foot, throat plate, atau hook akibat "
            "pengaturan maupun gangguan mekanis."
        ),
        "solution": (
            "Matikan mesin dan periksa jarum dari kerusakan. Pastikan "
            "tipe dan pemasangannya sesuai manual. Dengan mesin "
            "tetap mati, putar handwheel perlahan hanya jika diizinkan "
            "manual untuk memastikan tidak ada benturan. Jika jarum "
            "menyentuh komponen atau kembali patah, hentikan penggunaan "
            "dan minta teknisi memeriksa clearance serta timing."
        ),
        "safety_notes": (
            "Matikan mesin dan pastikan motor berhenti. Jangan "
            "menjalankan mesin jika jarum berpotensi membentur "
            "komponen. Pemeriksaan clearance dan timing internal "
            "diserahkan kepada teknisi."
        ),
        "source": (
            "Panduan keselamatan dan diagnosis umum jarum patah; "
            "tipe jarum serta clearance harus diverifikasi pada "
            "manual JUKI LZ-2284A."
        ),
    },
}

def main():
    apply = "--apply" in sys.argv

    if any(arg not in ("--apply",) for arg in sys.argv[1:]):
        print("Gunakan: python revisi_lz2284a.py [--apply]")
        return 2

    if not DB.is_file():
        print("GAGAL: database tidak ditemukan:", DB)
        return 1

    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id = ?",
            (MACHINE_ID,)
        ).fetchone()

        if not machine or machine["model"] != "LZ-2284A":
            print("GAGAL: identitas mesin tidak cocok:", 
                  dict(machine) if machine else "tidak ditemukan")
            return 1

        rows = con.execute("""
            SELECT id, machine_id, code, problem, symptoms,
                   possible_cause, solution, safety_notes, source
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
        """, (MACHINE_ID,)).fetchall()

        actual_ids = [r["id"] for r in rows]
        if actual_ids != EXPECTED_IDS:
            print("GAGAL: ID entri tidak sesuai.")
            print("Diharapkan:", EXPECTED_IDS)
            print("Ditemukan :", actual_ids)
            print("Tidak ada perubahan dilakukan.")
            return 1

        if any(r["code"] is not None for r in rows):
            print("GAGAL: ada code yang tidak NULL.")
            print("Tidak ada perubahan dilakukan.")
            return 1

        fields = [
            "symptoms", "possible_cause", "solution",
            "safety_notes", "source"
        ]

        changes = []
        for r in rows:
            for field in fields:
                old = r[field] or ""
                new = REVISI[r["id"]][field]
                if old != new:
                    changes.append((r["id"], field, old, new))

        print("MESIN:", machine["model"], "| ID:", MACHINE_ID)
        print("JUMLAH ENTRI:", len(rows))
        print("CODE SEMUA NULL:", all(r["code"] is None for r in rows))
        print("JUMLAH FIELD YANG AKAN BERUBAH:", len(changes))

        for entry_id, field, old, new in changes:
            print(f"\n--- ID {entry_id} | {field} ---")
            print("LAMA:", old)
            print("BARU:", new)

        if not apply:
            print("\nMODE PRATINJAU: database tidak diubah.")
            print("Periksa hasil di atas sebelum menjalankan --apply.")
            return 0

        # Buat backup konsisten sebelum perubahan.
        backup_dir = Path("database/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"garment_before_lz2284a_{stamp}.db"

        backup_con = sqlite3.connect(str(backup_path))
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()

        print("\nBACKUP:", backup_path)

        try:
            con.execute("BEGIN IMMEDIATE")

            for r in rows:
                values = REVISI[r["id"]]
                con.execute("""
                    UPDATE troubleshooting
                    SET symptoms = ?,
                        possible_cause = ?,
                        solution = ?,
                        safety_notes = ?,
                        source = ?
                    WHERE id = ? AND machine_id = ? AND code IS NULL
                """, (
                    values["symptoms"],
                    values["possible_cause"],
                    values["solution"],
                    values["safety_notes"],
                    values["source"],
                    r["id"],
                    MACHINE_ID,
                ))

                if con.execute("SELECT changes()").fetchone()[0] != 1:
                    raise RuntimeError(
                        f"Update tidak cocok untuk ID {r['id']}"
                    )

            verify = con.execute("""
                SELECT id, code, symptoms, possible_cause,
                       solution, safety_notes, source
                FROM troubleshooting
                WHERE machine_id = ?
                ORDER BY id
            """, (MACHINE_ID,)).fetchall()

            if [r["id"] for r in verify] != EXPECTED_IDS:
                raise RuntimeError("Verifikasi ID gagal.")

            if any(r["code"] is not None for r in verify):
                raise RuntimeError("Kolom code berubah.")

            for r in verify:
                for field in fields:
                    if r[field] != REVISI[r["id"]][field]:
                        raise RuntimeError(
                            f"Verifikasi {field} gagal pada ID {r['id']}"
                        )

            con.commit()
            print("\nBERHASIL: enam entri LZ-2284A diperbarui.")
            print("ID tetap:", [r["id"] for r in verify])
            print("Code tetap NULL:", all(r["code"] is None for r in verify))
            print("Backup tersimpan:", backup_path)
            return 0

        except Exception:
            con.rollback()
            print("\nGAGAL: perubahan dibatalkan (rollback).")
            print("Backup tetap tersedia:", backup_path)
            raise

    finally:
        con.close()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
