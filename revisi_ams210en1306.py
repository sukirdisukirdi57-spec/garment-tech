import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MACHINE_ID = 43
EXPECTED_IDS = [371, 372, 373, 374, 375, 376]

MANUAL = (
    "Manual instruksi JUKI AMS-210EN-1306/7450: "
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ams210en/menu/ams210en_hl1306_7450/pdf/instruction_3k.pdf"
)
PRODUCT = "Informasi produk resmi JUKI: https://juki.com/ams-210en-1306-7450"

REVISI = {
    371: {
        "symptoms": (
            "Bentuk atau urutan jahitan berbeda dari pola yang "
            "dipilih pada panel kontrol."
        ),
        "possible_cause": (
            "Pola yang dipilih tidak sesuai pekerjaan, data pola "
            "yang digunakan berbeda dari yang diharapkan, atau "
            "parameter jahitan tidak sesuai."
        ),
        "solution": (
            "Periksa nama atau nomor pola pada panel kontrol dan "
            "cocokkan dengan pola kerja yang dimaksud. Periksa "
            "parameter yang terlihat pada layar sebelum memulai "
            "siklus. Jika pola tetap berbeda, hentikan produksi "
            "dan minta petugas yang berwenang memeriksa data pola."
        ),
        "safety_notes": (
            "Hentikan siklus sebelum mengubah pilihan atau parameter "
            "pola. Jangan mengubah parameter servis atau melewati "
            "interlock keselamatan tanpa prosedur yang berwenang."
        ),
        "source": MANUAL,
    },
    372: {
        "symptoms": (
            "Posisi jahitan menyimpang dari posisi pola yang "
            "diharapkan pada material."
        ),
        "possible_cause": (
            "Material bergeser atau tidak ditempatkan dengan benar, "
            "feeding frame tidak menjepit material secara konsisten, "
            "atau pola yang dipilih tidak sesuai."
        ),
        "solution": (
            "Hentikan mesin. Periksa penempatan material dan "
            "pastikan material terjepit dengan benar oleh frame "
            "sesuai prosedur operasi. Pastikan pola yang dipilih "
            "benar dan lakukan uji pada potongan material. Jika "
            "posisi tetap bergeser, minta teknisi memeriksa sistem "
            "feeding dan posisi gerak."
        ),
        "safety_notes": (
            "Jangan menahan atau menggeser material dengan tangan "
            "saat siklus berjalan. Matikan mesin sebelum memeriksa "
            "area gerak frame atau jarum."
        ),
        "source": MANUAL,
    },
    373: {
        "symptoms": (
            "Feeding frame tidak bergerak, gerakannya tidak lengkap, "
            "atau berhenti pada posisi yang tidak diharapkan."
        ),
        "possible_cause": (
            "Terdapat hambatan pada area gerak, kondisi awal atau "
            "operasi pedal belum sesuai, atau mekanisme penggerak "
            "frame mengalami gangguan."
        ),
        "solution": (
            "Hentikan siklus dan matikan mesin sebelum memeriksa "
            "hambatan yang terlihat di area frame. Pastikan area "
            "bebas dari benda yang menghalangi dan ikuti prosedur "
            "operasi untuk mengembalikan mesin ke kondisi siap. "
            "Jika frame tetap tidak bergerak normal, minta teknisi "
            "memeriksa sistem penggeraknya."
        ),
        "safety_notes": (
            "Jauhkan tangan dari titik jepit frame. Jangan menarik "
            "atau memaksa frame bergerak. Pemeriksaan aktuator, "
            "kelistrikan, dan mekanisme internal dilakukan teknisi."
        ),
        "source": MANUAL,
    },
    374: {
        "symptoms": (
            "Intermediate presser tidak bergerak seperti yang "
            "diharapkan atau tinggi tekanannya tidak sesuai "
            "dengan material."
        ),
        "possible_cause": (
            "Pengaturan tinggi atau stroke tidak sesuai dengan "
            "material, parameter yang dipilih tidak cocok, atau "
            "mekanisme penggerak mengalami gangguan."
        ),
        "solution": (
            "Periksa pengaturan yang tersedia pada panel kontrol "
            "dan pastikan sesuai dengan ketebalan material serta "
            "petunjuk operasi. Jangan mengubah parameter servis "
            "atau membongkar mekanisme. Jika presser tidak bergerak "
            "normal, hentikan penggunaan dan minta teknisi memeriksa "
            "mekanisme serta pengaturannya."
        ),
        "safety_notes": (
            "Matikan mesin sebelum memeriksa area presser. Jauhkan "
            "jari dari titik jepit. Penyetelan mekanisme internal "
            "harus mengikuti manual servis yang sesuai."
        ),
        "source": MANUAL + " | Fitur presser: " + PRODUCT,
    },
    375: {
        "symptoms": (
            "Formasi jahitan tidak konsisten, tegangan benang tampak "
            "tidak seimbang, atau jahitan berubah selama siklus."
        ),
        "possible_cause": (
            "Jalur benang atau pemasangan jarum tidak benar, "
            "parameter tegangan tidak sesuai material, jarum rusak, "
            "atau kondisi material berubah."
        ),
        "solution": (
            "Matikan mesin. Periksa kondisi dan pemasangan jarum "
            "serta jalur benang sesuai manual. Periksa parameter "
            "tegangan yang digunakan untuk pekerjaan dan lakukan "
            "uji pada material yang sama. Ubah parameter secara "
            "bertahap hanya sesuai prosedur operasi. Jika masalah "
            "tetap terjadi, minta teknisi memeriksa sistem tegangan "
            "dan pembentukan jahitan."
        ),
        "safety_notes": (
            "Matikan mesin sebelum mengganti jarum atau menangani "
            "jalur benang. Jangan menyetel timing hook atau komponen "
            "internal tanpa prosedur servis."
        ),
        "source": MANUAL,
    },
    376: {
        "symptoms": (
            "Siklus jahit berhenti sebelum pola selesai dijalankan."
        ),
        "possible_cause": (
            "Kondisi awal operasi belum terpenuhi, pilihan pola atau "
            "urutan operasi tidak sesuai, atau sistem kontrol "
            "menghentikan siklus karena mendeteksi kondisi tertentu."
        ),
        "solution": (
            "Catat pesan atau indikator yang tampil pada panel "
            "kontrol. Periksa pola yang dipilih, penempatan material, "
            "dan kondisi frame sesuai prosedur operasi. Ikuti "
            "petunjuk manual untuk pesan yang tampil. Jika siklus "
            "tetap berhenti, catat pesan tersebut dan hubungi "
            "teknisi; jangan menebak kode error atau mengulang "
            "siklus tanpa memahami penyebabnya."
        ),
        "safety_notes": (
            "Jangan menonaktifkan atau melewati sistem pengaman. "
            "Matikan mesin sebelum pemeriksaan mekanis. Pemeriksaan "
            "sistem kontrol dan kelistrikan dilakukan teknisi."
        ),
        "source": MANUAL,
    },
}

FIELDS = [
    "symptoms", "possible_cause", "solution",
    "safety_notes", "source"
]

def main():
    apply = "--apply" in sys.argv
    if any(a != "--apply" for a in sys.argv[1:]):
        print("Gunakan: python revisi_ams210en1306.py [--apply]")
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

        if not machine or machine["model"] != "AMS-210EN-1306":
            print("GAGAL: identitas mesin tidak cocok.")
            print(dict(machine) if machine else "Mesin tidak ditemukan")
            return 1

        rows = con.execute("""
            SELECT id, machine_id, code, problem, symptoms,
                   possible_cause, solution, safety_notes, source
            FROM troubleshooting
            WHERE machine_id = ?
            ORDER BY id
        """, (MACHINE_ID,)).fetchall()

        ids = [r["id"] for r in rows]
        if ids != EXPECTED_IDS:
            print("GAGAL: ID entri tidak sesuai:", ids)
            print("Tidak ada perubahan dilakukan.")
            return 1

        if any(r["code"] is not None for r in rows):
            print("GAGAL: ada code yang bukan NULL.")
            print("Tidak ada perubahan dilakukan.")
            return 1

        changes = [
            (r["id"], field, REVISI[r["id"]][field])
            for r in rows
            for field in FIELDS
            if (r[field] or "") != REVISI[r["id"]][field]
        ]

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
        backup = backup_dir / f"garment_before_ams210en1306_{stamp}.db"

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
                    raise RuntimeError(f"Update gagal pada ID {entry_id}")

            check = con.execute("""
                SELECT id, code, symptoms, possible_cause,
                       solution, safety_notes, source
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
                for f in FIELDS:
                    if r[f] != REVISI[r["id"]][f]:
                        raise RuntimeError(
                            f"Verifikasi {f} gagal pada ID {r['id']}"
                        )

            con.commit()
            print("\nBERHASIL: enam entri AMS-210EN-1306 diperbarui.")
            print("ID tetap:", [r["id"] for r in check])
            print("Code tetap NULL:", all(r["code"] is None for r in check))
            print("Backup tersimpan:", backup)
            return 0

        except Exception:
            con.rollback()
            print("GAGAL: perubahan dibatalkan (rollback).")
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
