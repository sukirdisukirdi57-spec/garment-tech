from pathlib import Path
import sqlite3

base = Path("audit-kelengkapan")
src = base / "matriks_koreksi_teknis_ddl9000cs.md"
dst = base / "matriks_koreksi_teknis_ddl9000cs_revisi1.md"
db = Path("database/garment.db")

if not src.is_file() or not db.is_file():
    raise SystemExit("GAGAL: matriks sumber atau database tidak ditemukan.")
if dst.exists():
    raise SystemExit(f"GAGAL: {dst} sudah ada; tidak ditimpa.")

con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
try:
    con.execute("PRAGMA query_only=ON")
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
    rows = con.execute("""
        SELECT id, code FROM troubleshooting
        WHERE machine_id=17 ORDER BY id
    """).fetchall()
finally:
    con.close()

codes = [r[1] for r in rows]
if integrity != "ok" or fk_errors:
    raise SystemExit("GAGAL: pemeriksaan integritas database tidak lolos.")
if len(rows) != 43 or len(set(codes)) != 43 or any(not c for c in codes):
    raise SystemExit("GAGAL: data harus berisi 43 kode unik dan tidak kosong.")

original = src.read_text(encoding="utf-8")

section = """
---

## Revisi 1 — temuan manual dan tindak lanjut

Tanggal audit: 2026-10-21

Status: DRAF. Belum disetujui sebagai perubahan data produksi.

Manual pembanding:
- JUKI DDL-9000C-S Instruction Manual, bagian 4-6, daftar error.
  https://juki.com/pub/media/wysiwyg/products/DDL9000CSeries_manual.pdf
- Halaman produk JUKI DDL-9000C Series:
  https://juki.com/ddl-9000c-series

Kesesuaian manual dengan varian fisik DDL-9000CS serta control box harus
dipastikan sebelum prosedur teknis dianggap tervalidasi.

| Kode | Temuan pembanding | Tindak lanjut | Status |
|---|---|---|---|
| E000 | Inisialisasi data; manual menyatakan bukan error. | Kategorikan sebagai informasi/status, bukan kerusakan. Jelaskan dampak inisialisasi sebelum menyarankannya. | Didukung manual; redaksi ditinjau |
| E007 | Deskripsi manual menyebut motor overload; penggantian kepala mesin muncul sebagai konteks penyebab. | Cocokkan penyebab dan tindakan di database dengan manual yang sesuai; jangan menyimpulkan motor rusak hanya dari kode. | Perlu tinjau pemetaan |
| E009 | Solenoid energized terlalu lama. Item pemeriksaan mencakup pulley terlilit benang, konektor keluaran motor, dan kelancaran putaran pulley. | Cocokkan solusi yang tersimpan dengan daftar manual. Matikan dan amankan daya sebelum pemeriksaan fisik; kelistrikan oleh teknisi. | Deskripsi dan pemeriksaan didukung manual |
| E072 | Motor overload saat thread trimmer bekerja; manual instruksi tidak memberi item pemeriksaan spesifik pada baris tersebut. | Jangan mengarang prosedur. Catat kondisi error dan eskalasikan ke teknisi. | Prosedur lanjutan belum tersedia |
| E904 | Gangguan catu daya 24 V; tidak ada item pemeriksaan spesifik yang terkonfirmasi pada baris manual instruksi. | Jangan menyarankan pengguna memeriksa tegangan internal; rujuk teknisi kompeten. | Perlu dokumentasi servis |
| E922 | Kegagalan kontrol poros utama; tindakan khusus belum terkonfirmasi. | Jangan menetapkan komponen rusak atau menyarankan penggantian tanpa bukti. | Perlu verifikasi manual/servis |
| E924 | Gangguan driver motor; tindakan khusus belum terkonfirmasi. | Verifikasi dokumentasi servis sesuai control box; jangan langsung menyimpulkan driver harus diganti. | Perlu verifikasi manual/servis |
| E971 | Proteksi arus berlebih IPM motor feed horizontal; prosedur khusus belum terkonfirmasi. | Jangan menambahkan prosedur kelistrikan tanpa sumber; eskalasi diagnosis ke teknisi. | Perlu verifikasi manual/servis |
| E973 | Proteksi arus berlebih IPM motor feed vertikal; prosedur khusus belum terkonfirmasi. | Jangan menambahkan prosedur kelistrikan tanpa sumber; eskalasi diagnosis ke teknisi. | Perlu verifikasi manual/servis |
| E975 | Proteksi arus berlebih IPM motor presser; prosedur khusus belum terkonfirmasi. | Jangan menambahkan prosedur kelistrikan tanpa sumber; eskalasi diagnosis ke teknisi. | Perlu verifikasi manual/servis |

### Aturan revisi

1. Jangan mengubah kode berdasarkan dugaan.
2. Pisahkan deskripsi error, kemungkinan penyebab, item pemeriksaan manual,
   dan tindakan teknisi.
3. Jika manual instruksi tidak menyebut tindakan, catat keterbatasan sumber.
4. Pastikan varian mesin, control box, dan versi manual sesuai.
5. Semua entri tetap berstatus draf sampai verifikasi teknis disetujui.
6. Dokumen ini tidak mengubah database SQLite.

### Ringkasan pemeriksaan

- Baris troubleshooting machine_id 17: 43
- Kode unik: 43
- SQLite integrity_check: ok
- Foreign-key error: 0
- Database diubah: tidak
"""

dst.write_text(original.rstrip() + "\n" + section, encoding="utf-8")
out = dst.read_text(encoding="utf-8")
required = [
    "Revisi 1", "E000", "E007", "E009", "E072", "E904",
    "E922", "E924", "E971", "E973", "E975"
]
missing = [x for x in required if x not in out]
if missing:
    dst.unlink(missing_ok=True)
    raise SystemExit("GAGAL: bagian tidak ditemukan: " + ", ".join(missing))

print("BERHASIL:", dst)
print("Baris DDL-9000CS:", len(rows))
print("Kode unik:", len(set(codes)))
print("Kode prioritas ditinjau:", len(required) - 1)
print("Integritas SQLite:", integrity)
print("Foreign-key error:", len(fk_errors))
print("Database diubah: TIDAK")
print("Ukuran file:", dst.stat().st_size, "byte")
