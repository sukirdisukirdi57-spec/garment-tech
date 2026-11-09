from pathlib import Path
import sqlite3
import sys

BASE = Path("audit-kelengkapan")
DB = Path("database/garment.db")
OUT = BASE / "matriks_koreksi_teknis_ddl9000cs_revisi3.md"
REV2 = BASE / "matriks_koreksi_teknis_ddl9000cs_revisi2.md"
CORR = BASE / "koreksi_matriks_ddl9000cs_pas_verifikasi.md"

# Lindungi dokumen sebelumnya.
if OUT.exists():
    sys.exit(f"BERHENTI: file sudah ada, tidak ditimpa: {OUT}")

for p in (DB, REV2, CORR):
    if not p.is_file():
        sys.exit(f"BERHENTI: file wajib tidak ditemukan: {p}")

# Baca database tanpa mengizinkan penulisan.
con = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
con.execute("PRAGMA query_only=ON")

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
    machines = con.execute("SELECT COUNT(*) FROM machines").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM troubleshooting").fetchone()[0]

    rows = con.execute("""
        SELECT id, code, problem, symptoms, possible_cause,
               solution, safety_notes, source
        FROM troubleshooting
        WHERE machine_id = 17
        ORDER BY id
    """).fetchall()
finally:
    con.close()

if integrity != "ok":
    sys.exit(f"BERHENTI: integrity_check={integrity}")
if fk_errors:
    sys.exit(f"BERHENTI: ditemukan {len(fk_errors)} foreign key error")
if len(rows) != 43:
    sys.exit(f"BERHENTI: DDL-9000CS memiliki {len(rows)} baris, bukan 43")

codes = [r[1] for r in rows]
if any(not c for c in codes):
    sys.exit("BERHENTI: ditemukan kode kosong")
if len(set(codes)) != 43:
    sys.exit("BERHENTI: kode tidak unik")

rev2 = REV2.read_text(encoding="utf-8")
corr = CORR.read_text(encoding="utf-8")

# Pastikan sumber audit berisi bagian yang diperlukan.
for code in ("E007", "E009", "E971", "E972", "E973", "E974", "E975", "E976"):
    if code not in rev2 or code not in corr:
        sys.exit(f"BERHENTI: kode {code} tidak ditemukan di kedua dokumen sumber")

def clean(value):
    if value is None:
        return ""
    value = str(value)
    return " ".join(value.replace("|", "\\|").split())

lines = [
    "# Matriks Koreksi Teknis JUKI DDL-9000CS — Revisi 3",
    "",
    "Status: DRAF AUDIT — BELUM DISETUJUI UNTUK PERUBAHAN DATABASE",
    "",
    "## 1. Validasi database saat penyusunan",
    "",
    f"- Total mesin: {machines}",
    f"- Total troubleshooting: {total}",
    f"- Baris DDL-9000CS (machine_id=17): {len(rows)}",
    f"- Kode unik: {len(set(codes))}",
    f"- Integrity check: {integrity}",
    f"- Foreign key errors: {len(fk_errors)}",
    "- Database dibuka dalam mode read-only.",
    "",
    "## 2. Koreksi hasil pencocokan manual",
    "",
    "### E007 — ID 1416",
    "- Manual menyebut motor overload dan mengaitkannya dengan kondisi penggantian kepala mesin.",
    "- Temuan lama yang menyatakan teks belum dicocokkan perlu dianggap usang.",
    "- Manual tidak memberikan langkah pemeriksaan khusus pada baris yang diperiksa.",
    "",
    "### E009 — ID 1417",
    "- Manual mencantumkan solenoid energized terlalu lama.",
    "- Penyebab yang dicatat meliputi kepala terkunci, bahan terlalu berat, motor tidak berputar, atau masalah motor/driver.",
    "- Pemeriksaan pulley yang terlilit benang, konektor output motor, dan kelancaran putaran motor memang tercantum dalam uraian kode ini.",
    "- Temuan lama yang meminta penyelarasan ulang deskripsi dan pemeriksaan perlu diperbarui.",
    "",
    "## 3. Catatan kode tambahan",
    "",
    "| Kode | Hasil pembacaan manual | Batasan audit |",
    "|---|---|---|",
    "| E081 | Motor penggerak feed terkunci; periksa kelancaran gerak motor. | Konfirmasi nomenklatur varian. |",
    "| E733 | Putaran terbalik pada 500 sti/min atau lebih; periksa kabel encoder dan kabel daya motor poros utama. | Pemeriksaan kabel oleh teknisi. |",
    "| E946 | Kegagalan penulisan EEPROM kepala mesin; periksa koneksi INT PCB. | Pekerjaan PCB oleh teknisi. |",
    "| E955 | Arus motor poros utama melebihi nilai yang diperkirakan; periksa koneksi kabel daya motor. | Jangan menyimpulkan sensor pasti rusak. |",
    "| E961 | Motor pitch gagal karena beban berlebih; periksa kelancaran motor. | Isolasi energi sebelum pemeriksaan. |",
    "| E962 | Motor presser gagal karena beban berlebih; periksa kelancaran motor. | Pastikan istilah sesuai varian. |",
    "| E971 | Proteksi arus berlebih IPM motor feed horizontal; penyebab terkait operasi motor pitch tidak normal. | Tidak ada langkah pemeriksaan khusus pada baris manual yang diperiksa. |",
    "| E972 | Feed horizontal overload; manual mengaitkan beban berlebih dengan motor pitch dan menyebut pemeriksaan kelancaran motor pitch. | Pertahankan sesuai manual; jangan mengoreksi berdasarkan dugaan. |",
    "| E973 | Proteksi arus berlebih IPM motor feed vertikal; penyebab terkait operasi motor feed tidak normal. | Tidak ada langkah pemeriksaan khusus pada baris manual yang diperiksa. |",
    "| E974 | Feed vertikal overload; periksa kelancaran motor penggerak feed. | Pertahankan pasangan sebab dan tindakan sesuai manual. |",
    "| E975 | Proteksi arus berlebih IPM motor presser; penyebab terkait operasi motor presser tidak normal. | Tidak ada langkah pemeriksaan khusus pada baris manual yang diperiksa. |",
    "| E976 | Motor presser horizontal overload; periksa kelancaran motor presser. | Pertahankan pasangan sebab dan tindakan sesuai manual. |",
    "| E985 | Motor pitch atau motor feed gagal kembali ke titik asal; periksa penyetelan titik asal motor terkait. | Konfirmasi prosedur untuk varian yang terpasang. |",
    "",
    "## 4. Data database yang diaudit",
    "",
    "Bagian berikut merupakan salinan nilai aktual yang dibaca dari database. Data tidak diubah.",
    "",
    "| ID | Kode | Problem | Symptoms | Possible cause | Solution | Safety notes | Source/status |",
    "|---:|---|---|---|---|---|---|---|",
]

for row in rows:
    rid, code, problem, symptoms, cause, solution, safety, source = row
    vals = [rid, code, problem, symptoms, cause, solution, safety, source]
    lines.append("| " + " | ".join(clean(v) for v in vals) + " |")

lines += [
    "",
    "## 5. Keselamatan dan batasan",
    "",
    "- Semua 43 entri tetap berstatus draf sampai disetujui oleh pemeriksa teknis.",
    "- Cocokkan varian kepala mesin, panel operasi, kotak kontrol, diagram kabel, dan versi sistem dengan manual yang benar.",
    "- Jangan menambahkan solusi untuk kode yang tidak memiliki langkah pemeriksaan spesifik di manual.",
    "- Pemeriksaan tegangan, PCB, motor driver, encoder, dan rangkaian internal hanya oleh teknisi kompeten dengan prosedur isolasi energi yang tepat.",
    "- Catatan ini merupakan dokumentasi audit, bukan sertifikasi teknis.",
    "",
    "## 6. Sumber dan jejak audit",
    "",
    "- Manual resmi JUKI DDL-9000C-S, bagian 4-6, List of errors, halaman cetak 52–54.",
    "- https://www.juki.co.jp/industrial_j/download_j/manual_j/ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf",
    "- Matriks sumber: `matriks_koreksi_teknis_ddl9000cs_revisi2.md`.",
    "- Catatan koreksi: `koreksi_matriks_ddl9000cs_pas_verifikasi.md`.",
    "- Revisi ini tidak mengubah database dan tidak menyetujui impor atau koreksi isi database.",
    "",
]

# Buat file baru secara eksklusif; gagal jika file muncul lebih dulu.
with OUT.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("BERHASIL:", OUT)
print("Baris data dimasukkan:", len(rows))
print("Total mesin:", machines)
print("Total troubleshooting:", total)
print("Integritas:", integrity)
print("Foreign key errors:", len(fk_errors))
print("Database tidak diubah.")
