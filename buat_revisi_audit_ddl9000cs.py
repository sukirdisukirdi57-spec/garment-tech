import csv
from pathlib import Path

src = Path("audit-kelengkapan/draf_ddl9000cs_manual_revisi.csv")
dst = Path("audit-kelengkapan/draf_ddl9000cs_audit2.csv")

if not src.exists():
    raise SystemExit(f"File sumber tidak ditemukan: {src}")

with src.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or not rows:
    raise SystemExit("CSV kosong atau header tidak ditemukan.")

by_code = {r.get("code", "").strip(): r for r in rows}
if len(by_code) != len(rows):
    raise SystemExit("Ada kode duplikat; revisi dibatalkan.")

# E302: nyatakan larangan operasi yang disebut dalam manual.
r = by_code.get("E302")
if r:
    r["safety_notes"] = (
        "DRAF_PERLU_VERIFIKASI_TEKNIS. Manual menyatakan pengoperasian "
        "mesin dilarang ketika kondisi sakelar keselamatan ini aktif. "
        "Pastikan kondisi aman sebelum pemeriksaan. Isolasi sumber daya "
        "sebelum pemeriksaan fisik yang memerlukannya. Pemeriksaan PCB "
        "dan rangkaian internal hanya oleh teknisi kompeten. "
        "Cocokkan varian mesin terlebih dahulu."
    )

# E303: pertahankan nama sensor asli agar tidak salah diterjemahkan.
r = by_code.get("E303")
if r:
    r["problem"] = "Kesalahan sensor meniskus (meniscus sensor)"

# E811/E813: uraian lebih spesifik berdasarkan daftar penyebab manual.
r = by_code.get("E811")
if r:
    r["possible_cause"] = (
        "Tegangan masukan mencapai atau melampaui batas yang dijamin. "
        "Manual juga menyebut ketidakcocokan konfigurasi, termasuk "
        "suplai 200 V pada konfigurasi 100 V, 220 V pada kotak "
        "JA:120 V, atau 400 V pada kotak CE:230 V."
    )
    r["solution"] = (
        "Manual: teknisi kompeten memeriksa kesesuaian tegangan suplai "
        "dengan spesifikasi dan konektor pemilih 100 V/200 V. "
        "Jangan mengubah konfigurasi tegangan tanpa prosedur servis resmi."
    )

r = by_code.get("E813")
if r:
    r["possible_cause"] = (
        "Tegangan masukan berada pada atau di bawah batas yang dijamin. "
        "Manual juga menyebut konfigurasi yang tidak sesuai, termasuk "
        "suplai 100 V pada konfigurasi 200 V atau 120 V pada kotak "
        "JUS:220 V, serta kemungkinan kerusakan rangkaian internal "
        "akibat tegangan berlebih."
    )
    r["solution"] = (
        "Manual: teknisi kompeten memeriksa kesesuaian tegangan suplai "
        "dengan spesifikasi dan konektor pemilih 100 V/200 V. "
        "Jangan mengubah konfigurasi tegangan tanpa prosedur servis resmi."
    )

# Semua data tetap draf; tidak mengubah status menjadi disetujui.
for r in rows:
    if "review_status" in r:
        r["review_status"] = "DRAF_PERLU_VERIFIKASI_TEKNIS"

with dst.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

# Validasi hasil yang ditulis.
with dst.open(newline="", encoding="utf-8-sig") as f:
    check = list(csv.DictReader(f))

codes = [r.get("code", "").strip() for r in check]
assert len(check) == 43, f"Jumlah baris tidak sesuai: {len(check)}"
assert len(set(codes)) == 43, "Kode duplikat terdeteksi"
assert set(codes) == set(by_code), "Daftar kode berubah"
assert all(
    r.get("review_status") == "DRAF_PERLU_VERIFIKASI_TEKNIS"
    for r in check
), "Status draf berubah"

print("Salinan revisi dibuat:", dst)
print("Jumlah baris:", len(check))
print("Kode unik:", len(set(codes)))
print("Status: seluruhnya masih draf")
print("Database tidak dibuka atau diubah.")
