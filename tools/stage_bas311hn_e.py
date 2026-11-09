import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tmp/bas311hn/e_staging_review.csv"

# E. Lower shaft mechanism, katalog cetak halaman 29.
# Transkripsi awal; seluruh baris harus ditinjau sebelum impor.
rows = [
    (1, "SA3226001", 1, "SHOULDER SCREW", "Komponen mekanisme poros bawah"),
    (2, "SA3227001", 1, "NUT(FT),M6", "Pengikat"),
    (3, "SA3228101", 1, "ROCK GEAR", "Mekanisme poros bawah"),
    (4, "SA4782001", 1, "ROCK GEAR SHAFT", "Mekanisme poros bawah"),
    (5, "SA3231001", 1, "SET SCREW COLLAR,B", "Pengikat/penyetel"),
    (6, "012060536", 2, "SET SCREW, SOCKET (FT) M6X5", "Pengikat"),
    (7, "SA3233101", 1, "SET SCREW COLLAR", "Pengikat/penyetel"),
    (8, "S23651001", 2, "SET SCREW SOCKET (FT) M6X6", "Pengikat"),
    (9, "012060636", 3, "SET SCREW SOCKET (FT) M6X6", "Pengikat"),
    (10, "SA4783101", 1, "LOWER SHAFT ASSY", "Rakitan poros bawah"),
    (11, "SB4187101", 1, "LOWER SHAFT BUSH", "Bushing poros bawah"),
    (12, "012060636", 1, "SET SCREW SOCKET (FT) M6X6", "Pengikat; kode berulang pada ref 9"),
    (13, "SA3238401", 1, "ADJUSTING STUD", "Penyetel"),
    (14, "081003670", 1, "O RING PW3", "Seal"),
    (15, "SB4508101", 1, "SHUTTLE RACE BASE SET H", "Rakitan area shuttle; verifikasi varian"),
    (16, "SB4509001", 1, "SHUTTLE RACE BASE ASSY H", "Rakitan area shuttle; verifikasi varian"),
    (17, "S02429201", 1, "SHUTTLE RACE THREAD GUIDE", "Area shuttle"),
    (18, "SA4199001", 2, "SCREW M3X4", "Pengikat"),
    (19, "SA3241001", 2, "S-RACE BASE SETTING CLAW", "Area shuttle"),
    (20, "152684101", 2, "COMPRESSION SPRING", "Area shuttle"),
    (21, "402887001", 2, "WASHER, 3.2", "Pengikat"),
    (22, "062300616", 2, "SCREW PAN M3X6", "Pengikat"),
    (23, "SA9396001", 2, "FELT", "Pelumasan"),
    (24, "S59886001", 1, "FELT, L=360", "Pelumasan"),
    (25, "SA9397001", 2, "RUBBER CAP 5.5", "Penutup"),
    (26, "SA9793001", 1, "VINYL TUBE L=160", "Saluran pelumasan"),
    (27, "S50557000", 1, "OIL TUBE", "Saluran pelumasan"),
    (28, "SB3511001", 1, "VINYL TUBE", "Saluran pelumasan"),
    (29, "SB4392001", 1, "OIL TUBE L=380", "Saluran pelumasan"),
    (30, "SB4464101", 1, "FELT ASSY", "Pelumasan"),
    (31, "SA3242001", 1, "FELT HOLDER", "Pelumasan"),
    (32, "SA9191001", 2, "SCREW M3X5.5", "Pengikat"),
    (33, "SA3274101", 1, "FELT HOLDER", "Pelumasan"),
    (34, "S47307001", 2, "SCREW, M3X4", "Pengikat"),
    (35, "012060636", 1, "SET SCREW SOCKET (FT) M6X6", "Pengikat; kode berulang pada ref 9 dan 12"),
    (36, "", 1, "DRIVER", "VARIANT_OPTION: halaman 73; target -03S kandidat SA6448-301; perlu verifikasi"),
    (37, "018501232", 1, "BOLT SOCKET M5X12", "Pengikat"),
    (38, "048070342", 1, "RETAINING RING E7", "Pengikat"),
    (39, "", 1, "SHUTTLE RACE BASE", "VARIANT_OPTION: halaman 73; target -03S kandidat 152682-201; perlu verifikasi"),
    (40, "", 1, "SHUTTLE HOOK ASSY W/BOX", "VARIANT_OPTION: halaman 73; target -03S kandidat SA2173-301; perlu verifikasi"),
    (41, "", 1, "BOBBIN CASE ASSY", "VARIANT_OPTION: halaman 73; target -03S kandidat S59221-301; perlu verifikasi"),
    (42, "", 1, "TENSION SPRING", "VARIANT_OPTION: halaman 73; target -03S kandidat S48664-001; perlu verifikasi"),
    (43, "", 1, "BOBBIN CASE SPRING SCREW", "VARIANT_OPTION: kode target -03S belum dipastikan dari tabel yang terbaca"),
    (44, "", 1, "ANTI-SPIN SPRING", "VARIANT_OPTION: kode target -03S belum dipastikan dari tabel yang terbaca"),
    (45, "", 1, "BOBBIN", "VARIANT_OPTION: halaman 73; target -03S kandidat S44633-001; perlu verifikasi"),
    (46, "SA3283101", 1, "SET SCREW COLLAR,R", "Pengikat/penyetel"),
    (47, "012500536", 1, "SET SCREW SOCKET (FT) M5X5", "Pengikat"),
    (48, "SA8707001", 1, "FELT", "Pelumasan"),
    (49, "108802001", 1, "WICK, 4X4 L=250", "Pelumasan"),
    (50, "SA3238401", 1, "ADJUSTING STUD", "Penyetel; kode berulang pada ref 13"),
    (51, "081003670", 1, "O RING PW3", "Seal; kode berulang pada ref 14"),
]

fields = [
    "catalog_ref", "part_number", "quantity_raw", "part_name",
    "diagram_page", "mechanism", "verification", "review_note",
]

if len(rows) != 51:
    raise SystemExit(f"STOP: jumlah referensi {len(rows)}, seharusnya 51")

refs = [r[0] for r in rows]
if refs != list(range(1, 52)):
    raise SystemExit("STOP: referensi katalog tidak lengkap/berurutan")

for ref, code, qty, name, note in rows:
    if not name.strip() or qty < 1:
        raise SystemExit(f"STOP: data tidak valid pada ref {ref}")
    if ref not in (36, 39, 40, 41, 42, 43, 44, 45) and not code.strip():
        raise SystemExit(f"STOP: kode kosong pada ref standar {ref}")

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for ref, code, qty, name, note in rows:
        writer.writerow({
            "catalog_ref": ref,
            "part_number": code,
            "quantity_raw": qty,
            "part_name": name,
            "diagram_page": 29,
            "mechanism": "E Lower shaft mechanism (BAS-311HN/326H)",
            "verification": (
                "VARIANT_OPTION_REVIEW"
                if ref in (36, 39, 40, 41, 42, 43, 44, 45)
                else "REVIEW_REQUIRED"
            ),
            "review_note": note,
        })

print("Staging dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah referensi:", len(rows))
print("Halaman katalog cetak: 29 (E)")
print("Opsi varian yang perlu diperiksa: 36, 39–45")
print("Database diubah: TIDAK")
print("Status: BELUM SIAP IMPOR")
