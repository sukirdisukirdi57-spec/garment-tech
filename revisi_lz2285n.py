import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 35
EXPECTED_IDS = [293, 294, 295, 296, 297, 298]

REVISI = {
    293: {
        "symptoms": "Pola fagoting tidak terbentuk konsisten atau bentuk zigzag menyimpang dari pola yang diharapkan.",
        "possible_cause": "Pemilihan atau pengaturan pola tidak sesuai; jalur benang keliru; jarum bermasalah; atau material tidak terfeeding stabil.",
        "solution": "Periksa jalur benang, kondisi dan pemasangan jarum, serta posisi material. Pastikan pengaturan pola sesuai petunjuk manual LZ-2285N. Uji pada potongan material yang sama. Jika pola tetap tidak benar, minta teknisi memeriksa mekanisme needle throwing.",
        "safety_notes": "Matikan mesin dan pastikan motor berhenti sebelum pemeriksaan. Jangan membongkar atau menyetel mekanisme pola tanpa prosedur servis yang sesuai.",
        "source": "Panduan pemeriksaan dasar berdasarkan gejala; pengaturan mekanisme harus dikonfirmasi pada manual JUKI LZ-2285N."
    },
    294: {
        "symptoms": "Lebar ayunan pola fagoting lebih kecil atau lebih besar dari hasil yang diharapkan, atau berubah selama menjahit.",
        "possible_cause": "Pengaturan lebar zigzag tidak sesuai, pengunci pengaturan tidak mantap, atau mekanisme pengatur lebar mengalami gangguan.",
        "solution": "Dengan mesin berhenti, periksa pengaturan lebar zigzag dan penguncinya sesuai manual. Jangan memaksakan knob. Jika lebar berubah sendiri atau mekanisme macet, minta teknisi memeriksa pengatur lebar.",
        "safety_notes": "Matikan mesin sebelum pemeriksaan atau penyetelan. Jangan menjalankan mesin jika mekanisme pengatur terasa macet.",
        "source": "Panduan pemeriksaan dasar; rentang dan prosedur penyetelan perlu diverifikasi pada manual JUKI LZ-2285N."
    },
    295: {
        "symptoms": "Jarak antara kedua sisi material yang disambung berubah-ubah sehingga hasil fagoting tidak seragam.",
        "possible_cause": "Posisi atau jarak material tidak konsisten, material bergeser saat dijahit, atau feeding tidak stabil.",
        "solution": "Periksa penempatan dan keselarasan kedua sisi material sebelum menjahit. Gunakan panduan atau alat bantu yang sesuai dengan pekerjaan dan uji pada potongan material yang sama. Jika material tetap bergeser, periksa feeding dan alat bantu penempatan.",
        "safety_notes": "Hentikan mesin sebelum mengatur material di dekat jarum. Jauhkan jari dari area jarum saat mesin beroperasi.",
        "source": "Panduan pemeriksaan umum aplikasi fagoting; metode penempatan mengikuti kebutuhan material dan perlengkapan yang digunakan."
    },
    296: {
        "symptoms": "Material bergerak tersendat atau tidak konsisten sehingga posisi dan bentuk pola fagoting berubah.",
        "possible_cause": "Feed dog kotor atau aus, area feeding terhalang, tekanan sepatu atau pengaturan feeding tidak sesuai, atau material tidak diarahkan dengan stabil.",
        "solution": "Matikan mesin. Periksa kebersihan feed dog dan area feeding yang dapat dijangkau, lalu bersihkan sesuai manual. Pastikan material diarahkan secara konsisten. Jika masalah berlanjut, minta teknisi memeriksa pengaturan dan komponen feeding.",
        "safety_notes": "Matikan mesin sebelum membersihkan area feeding. Jauhkan tangan dari jarum dan komponen bergerak. Jangan menyetel mekanisme internal tanpa prosedur servis.",
        "source": "Panduan pemeriksaan umum mekanisme feeding; spesifikasi dan penyetelan harus mengacu pada manual LZ-2285N."
    },
    297: {
        "symptoms": "Sebagian bagian pola fagoting tidak terbentuk sehingga jahitan tampak terputus atau tidak lengkap.",
        "possible_cause": "Jarum rusak atau tidak sesuai, pemasangan jarum keliru, jalur benang tidak benar, atau terdapat gangguan pada area hook maupun timing.",
        "solution": "Matikan mesin. Periksa kondisi dan pemasangan jarum serta jalur benang sesuai manual. Jika jahitan loncat tetap terjadi, hentikan penggunaan untuk pemeriksaan teknisi pada area hook dan timing.",
        "safety_notes": "Matikan mesin sebelum menangani jarum atau area hook. Jangan mengubah timing hook tanpa prosedur servis yang sesuai.",
        "source": "Panduan diagnosis umum jahitan loncat; tipe jarum dan prosedur timing harus dikonfirmasi pada manual JUKI LZ-2285N."
    },
    298: {
        "symptoms": "Jarum patah berulang kali selama proses jahit fagoting.",
        "possible_cause": "Jarum bengkok, rusak atau tidak sesuai; pemasangan jarum keliru; material tertarik; atau jarum bersentuhan dengan presser foot, throat plate, atau hook akibat gangguan mekanis.",
        "solution": "Matikan mesin dan periksa jarum dari kerusakan serta pemasangannya sesuai manual. Tipe jarum yang tepat belum diverifikasi; jangan menetapkan 438SUK (Nm80) sebagai spesifikasi pasti sebelum memeriksa manual model ini. Jika jarum membentur komponen atau kembali patah, hentikan penggunaan dan minta teknisi memeriksa clearance serta timing.",
        "safety_notes": "Matikan mesin dan pastikan motor berhenti sebelum pemeriksaan. Jangan menjalankan mesin jika jarum berpotensi membentur komponen. Pemeriksaan clearance dan timing internal diserahkan kepada teknisi.",
        "source": "Panduan keselamatan dan diagnosis umum jarum patah; tipe jarum dan clearance harus diverifikasi pada manual resmi JUKI LZ-2285N."
    }
}

FIELDS = ["symptoms", "possible_cause", "solution", "safety_notes", "source"]

def main():
    apply = "--apply" in sys.argv
    if any(a != "--apply" for a in sys.argv[1:]):
        print("Gunakan: python revisi_lz2285n.py [--apply]")
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
        if not machine or machine["model"] != "LZ-2285N":
            print("GAGAL: identitas mesin tidak cocok.")
            print(dict(machine) if machine else "Mesin tidak ditemukan")
            return 1

        rows = con.execute("""
            SELECT id, machine_id, code, symptoms, possible_cause,
                   solution, safety_notes, source
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
        """, (MACHINE_ID,)).fetchall()

        ids = [r["id"] for r in rows]
        if ids != EXPECTED_IDS:
            print("GAGAL: ID tidak cocok:", ids)
            return 1
        if any(r["code"] is not None for r in rows):
            print("GAGAL: ditemukan code yang bukan NULL.")
            return 1

        changes = []
        for r in rows:
            for f in FIELDS:
                if (r[f] or "") != REVISI[r["id"]][f]:
                    changes.append((r["id"], f, REVISI[r["id"]][f]))

        print("MESIN:", machine["model"], "| ID:", MACHINE_ID)
        print("JUMLAH ENTRI:", len(rows))
        print("CODE SEMUA NULL:", all(r["code"] is None for r in rows))
        print("JUMLAH FIELD YANG AKAN BERUBAH:", len(changes))
        for entry_id, field, value in changes:
            print(f"\n--- ID {entry_id} | {field} ---")
            print("BARU:", value)

        if not apply:
            print("\nMODE PRATINJAU: database tidak diubah.")
            return 0

        backup_dir = Path("database/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backup_dir / f"garment_before_lz2285n_{stamp}.db"
        backup_con = sqlite3.connect(str(backup))
        try:
            con.backup(backup_con)
        finally:
            backup_con.close()
        print("\nBACKUP:", backup)

        try:
            con.execute("BEGIN IMMEDIATE")
            for entry_id in EXPECTED_IDS:
                v = REVISI[entry_id]
                cur = con.execute("""
                    UPDATE troubleshooting
                    SET symptoms = ?, possible_cause = ?, solution = ?,
                        safety_notes = ?, source = ?
                    WHERE id = ? AND machine_id = ? AND code IS NULL
                """, (
                    v["symptoms"], v["possible_cause"], v["solution"],
                    v["safety_notes"], v["source"], entry_id, MACHINE_ID
                ))
                if cur.rowcount != 1:
                    raise RuntimeError(f"Update gagal untuk ID {entry_id}")

            check = con.execute("""
                SELECT id, code, symptoms, possible_cause, solution,
                       safety_notes, source
                FROM troubleshooting
                WHERE machine_id = ?
                ORDER BY id
            """, (MACHINE_ID,)).fetchall()

            if [r["id"] for r in check] != EXPECTED_IDS:
                raise RuntimeError("Verifikasi ID gagal.")
            if any(r["code"] is not None for r in check):
                raise RuntimeError("Kolom code berubah.")
            for r in check:
                if any(not r[f] or not r[f].strip() for f in FIELDS):
                    raise RuntimeError(f"Field kosong pada ID {r['id']}")
                if any(r[f] != REVISI[r["id"]][f] for f in FIELDS):
                    raise RuntimeError(f"Verifikasi teks gagal pada ID {r['id']}")

            con.commit()
            print("\nBERHASIL: enam entri LZ-2285N diperbarui.")
            print("ID tetap:", [r["id"] for r in check])
            print("Code tetap NULL:", all(r["code"] is None for r in check))
            print("Backup tersimpan:", backup)
            return 0
        except Exception:
            con.rollback()
            print("GAGAL: transaksi dibatalkan.")
            print("Backup tetap tersedia:", backup)
            raise
    finally:
        con.close()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
