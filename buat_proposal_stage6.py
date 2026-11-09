import csv
import sqlite3
from pathlib import Path

db = Path("database/garment.db")
out = Path("tmp/lbh1790an/proposal_error_codes_stage6.csv")
out.parent.mkdir(parents=True, exist_ok=True)

rows = [
    (6, "E905", "Suhu heatsink papan kontrol servo tidak normal",
     "Panel menampilkan E905; suhu heatsink papan kontrol servo mencapai batas deteksi.",
     "Suhu heatsink papan kontrol servo mencapai 85°C atau lebih.",
     "Matikan daya mesin. Biarkan peralatan mendingin dan minta teknisi memeriksa ventilasi serta papan kontrol servo jika kode berulang.",
     "Putuskan sumber daya sebelum pemeriksaan fisik. Jangan membuka panel listrik saat masih bertegangan.",
     "JUKI LBH-1790A Instruction Manual, Error Code List, hlm. cetak 75; verifikasi revisi AN diperlukan"),
    (6, "E907", "Kegagalan pencarian posisi awal motor ayun jarum",
     "Panel menampilkan E907 saat pencarian posisi awal; sinyal sensor posisi awal tidak terdeteksi.",
     "Sinyal sensor posisi awal tidak masuk saat proses pencarian posisi awal motor ayun jarum.",
     "Matikan daya. Jika kode berulang, minta teknisi memeriksa sensor posisi awal, kabel, dan mekanisme terkait sesuai manual servis.",
     "Jauhkan tangan dari jarum dan bagian bergerak. Putuskan sumber daya sebelum memeriksa konektor.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E908", "Kegagalan pencarian posisi awal motor gerak Y",
     "Panel menampilkan E908; sinyal sensor posisi awal tidak terdeteksi saat pencarian posisi awal.",
     "Sinyal sensor posisi awal tidak masuk saat proses pencarian posisi awal motor gerak Y.",
     "Matikan daya. Jika kode berulang, minta teknisi memeriksa sensor, kabel, dan mekanisme gerak Y.",
     "Jauhkan tangan dari bagian bergerak dan putuskan sumber daya sebelum pemeriksaan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E909", "Kegagalan pencarian posisi awal motor pemotong benang jarum",
     "Panel menampilkan E909; sinyal sensor posisi awal tidak terdeteksi saat pencarian posisi awal.",
     "Sinyal sensor posisi awal tidak masuk saat proses pencarian posisi awal motor pemotong benang jarum.",
     "Matikan daya. Minta teknisi memeriksa sensor, kabel, dan mekanisme pemotong benang jarum jika kode berulang.",
     "Pisau dan bagian bergerak dapat melukai. Putuskan sumber daya sebelum pemeriksaan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E910", "Kegagalan pencarian posisi awal motor sepatu penekan",
     "Panel menampilkan E910; sinyal sensor posisi awal tidak terdeteksi saat pencarian posisi awal.",
     "Sinyal sensor posisi awal tidak masuk saat proses pencarian posisi awal motor sepatu penekan.",
     "Matikan daya. Minta teknisi memeriksa sensor posisi awal, kabel, dan mekanisme sepatu penekan.",
     "Jauhkan tangan dari mekanisme penekan. Putuskan sumber daya sebelum pemeriksaan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E911", "Kegagalan pencarian posisi awal motor pemotong benang bobbin",
     "Panel menampilkan E911; sinyal sensor posisi awal tidak terdeteksi saat pencarian posisi awal.",
     "Sinyal sensor posisi awal tidak masuk saat proses pencarian posisi awal motor pemotong benang bobbin.",
     "Matikan daya. Minta teknisi memeriksa sensor, kabel, dan mekanisme pemotong benang bobbin.",
     "Jauhkan tangan dari pisau dan bagian bergerak. Putuskan sumber daya sebelum pemeriksaan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E915", "Gangguan komunikasi antara panel operasi dan CPU utama",
     "Panel menampilkan E915; terjadi gangguan komunikasi antara panel operasi dan CPU utama.",
     "Komunikasi data antara panel operasi dan CPU utama tidak berlangsung normal.",
     "Matikan daya mesin. Jika kode berulang, minta teknisi memeriksa konektor, kabel komunikasi, dan papan terkait.",
     "Putuskan sumber daya sebelum memeriksa konektor. Jangan membuka panel listrik saat bertegangan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E916", "Gangguan komunikasi antara CPU utama dan CPU poros utama",
     "Panel menampilkan E916; terjadi gangguan komunikasi antara CPU utama dan CPU poros utama.",
     "Komunikasi data antara CPU utama dan CPU poros utama tidak berlangsung normal.",
     "Matikan daya mesin. Jika kode berulang, minta teknisi memeriksa konektor, kabel komunikasi, dan papan terkait.",
     "Putuskan sumber daya sebelum memeriksa konektor. Jangan membuka panel listrik saat bertegangan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E918", "Suhu heatsink papan kontrol utama tidak normal",
     "Panel menampilkan E918; suhu heatsink papan kontrol utama mencapai batas deteksi.",
     "Suhu heatsink papan kontrol utama mencapai 85°C atau lebih.",
     "Matikan daya mesin. Biarkan peralatan mendingin. Jika kode berulang, minta teknisi memeriksa ventilasi dan papan kontrol utama.",
     "Putuskan sumber daya sebelum pemeriksaan. Jangan menyentuh komponen panas atau membuka panel bertegangan.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E943", "Gangguan penulisan EEPROM papan kontrol utama",
     "Panel menampilkan E943; data tidak dapat ditulis ke EEPROM papan kontrol utama.",
     "Proses penulisan data ke EEPROM papan kontrol utama gagal.",
     "Matikan daya. Jika kode berulang, minta teknisi memeriksa papan kontrol dan memori sesuai prosedur servis. Jangan melakukan penulisan ulang data tanpa prosedur resmi.",
     "Putuskan sumber daya sebelum pemeriksaan internal. Perubahan data konfigurasi dilakukan teknisi kompeten.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E946", "Gangguan penulisan EEPROM papan relay kepala mesin",
     "Panel menampilkan E946; data tidak dapat ditulis ke EEPROM papan relay kepala mesin.",
     "Proses penulisan data ke EEPROM papan relay kepala mesin gagal.",
     "Matikan daya. Jika kode berulang, minta teknisi memeriksa papan relay kepala mesin dan memori sesuai prosedur servis.",
     "Putuskan sumber daya sebelum pemeriksaan internal. Jangan mengganti papan atau mengubah data tanpa kompetensi yang sesuai.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
    (6, "E999", "Pisau pemotong kain gagal kembali ke posisi semula",
     "Panel menampilkan E999 ketika pisau pemotong kain tidak kembali dalam waktu yang ditentukan atau sinyal sensor tidak aktif saat pisau naik dalam keadaan siaga.",
     "Pisau pemotong kain tidak kembali dalam waktu yang ditentukan atau sensor tidak aktif pada kondisi yang dipantau.",
     "Matikan daya mesin. Jangan memaksa pisau bergerak. Minta teknisi memeriksa mekanisme pisau dan sensor posisi.",
     "Pisau tajam dan mekanisme bergerak berbahaya. Putuskan sumber daya sebelum pemeriksaan dan jauhkan tangan dari area pisau.",
     "JUKI LBH-1790AN/1795AN Instruction Manual, VIII. Error Code List, hlm. cetak 79"),
]

fields = [
    "machine_id", "code", "problem", "symptoms",
    "possible_cause", "solution", "safety_notes", "source"
]
codes = [r[1] for r in rows]
if len(rows) != 12 or len(set(codes)) != 12:
    raise SystemExit("Daftar proposal tidak valid.")

con = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True)
try:
    count = con.execute(
        "SELECT COUNT(*) FROM troubleshooting WHERE machine_id=6"
    ).fetchone()[0]
    coded = con.execute(
        """SELECT COUNT(*) FROM troubleshooting
           WHERE machine_id=6 AND code IS NOT NULL AND TRIM(code)<>''"""
    ).fetchone()[0]
    uncoded = con.execute(
        """SELECT COUNT(*) FROM troubleshooting
           WHERE machine_id=6 AND (code IS NULL OR TRIM(code)='')"""
    ).fetchone()[0]
    if (count, coded, uncoded) != (73, 65, 8):
        raise SystemExit(f"Kondisi database tidak sesuai: {(count,coded,uncoded)}")

    existing = {
        r[0] for r in con.execute(
            "SELECT code FROM troubleshooting WHERE machine_id=6 AND code IS NOT NULL"
        )
    }
    clashes = existing.intersection(codes)
    if clashes:
        raise SystemExit(f"Ada kode bentrok: {sorted(clashes)}")
    if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise SystemExit("Integritas SQLite gagal.")
finally:
    con.close()

if out.exists():
    raise SystemExit(f"Proposal sudah ada; tidak ditimpa: {out}")

with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(fields)
    w.writerows(rows)

with out.open(encoding="utf-8-sig", newline="") as f:
    check = list(csv.DictReader(f))
if len(check) != 12 or [r["code"] for r in check] != codes:
    out.unlink(missing_ok=True)
    raise SystemExit("Validasi CSV gagal.")

print("PROPOSAL TAHAP 6 DIBUAT")
print("File:", out)
print("Jumlah baris data:", len(check))
print("Kode:", ", ".join(codes))
print("Benturan kode: 0")
print("Database tetap: 73 entri")
print("Integritas SQLite: ok")
print("Status: proposal saja, belum diimpor.")
