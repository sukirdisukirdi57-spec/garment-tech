import csv
import re
from pathlib import Path
from collections import Counter

root = Path.cwd()
source = root / "tools/z8550b_z8560b_parts_candidates.csv"
target = root / "tools/z8550b_z8560b_gauge_staging.csv"

# page, section, width, role, part number, standard, variant, source note
data = [
("53","Ga1","8 mm","needle_plate","S48065-001","YES","Standard","Needle plate; B ref 52+"),
("53","Ga1","8 mm","feed_dog","S48143-101","YES","Standard","Kode sesuai tabel Ga1"),
("53","Ga1","8 mm","presser_foot_assy","S48293-201","YES","Standard","D ref 6+"),
("53","Ga1","8 mm","stopper","SA9064-001","YES","Standard","B ref 59+"),
("53","Ga1","8 mm","feed_dog","S58908-001","NO","Alternative marked *","E ref 115 juga memuat kode ini"),
("53","Ga1","8 mm","presser_foot_assy","S48305-201","NO","Black color","Alternatif warna hitam"),
("53","Ga1","8 mm","presser_foot_assy","S58950-201","NO","With tape guide","Alternatif tape guide"),

("54","Ga2","5 mm","needle_plate","S48066-001","YES","Standard","Tabel Ga2"),
("54","Ga2","5 mm","feed_dog","S06171-101","YES","Standard","Tabel Ga2"),
("54","Ga2","5 mm","presser_foot_assy","S48308-201","YES","Standard","Tabel Ga2"),
("54","Ga2","5 mm","stopper","S48074-000","YES","Standard","Z ref 49"),
("54","Ga2","5 mm","needle_plate","S48067-001","NO","Black color","Alternatif needle plate"),
("54","Ga2","5 mm","feed_dog","S06166-001","NO","Alternative feed dog","Varian; verifikasi konfigurasi"),
("54","Ga2","5 mm","feed_dog","S06170-101","NO","Alternative feed dog","Varian; verifikasi konfigurasi"),
("54","Ga2","5 mm","feed_dog","S53410-001","NO","Alternative feed dog","Varian; verifikasi konfigurasi"),
("54","Ga2","5 mm","feed_dog","S52068-001","NO","Alternative feed dog","Varian; verifikasi konfigurasi"),
("54","Ga2","5 mm","feed_dog","S54937-001","NO","Alternative feed dog","Varian; verifikasi konfigurasi"),

("55","Ga3","10 mm","needle_plate","S50684-001","YES","Standard","B ref 52+"),
("55","Ga3","10 mm","feed_dog","S50686-001","YES","Standard","Gunakan kode tabel; gambar menunjukkan S48143"),
("55","Ga3","10 mm","presser_foot_assy","S51227-201","YES","Standard","D ref 6+"),
("55","Ga3","10 mm","stopper","S52046-000","YES","Standard","B ref 59+"),
("55","Ga3","10 mm","needle_plate","S50685-001","NO","Snow-white color","Alternatif warna snow-white"),

("55","Ga3","3 mm","needle_plate","S54929-001","YES","Standard","Konfigurasi 3 mm"),
("55","Ga3","3 mm","feed_dog","S54945-001","YES","Standard","Konfigurasi 3 mm"),
("55","Ga3","3 mm","presser_foot_assy","S54957-201","YES","Standard","Tidak ada stopper 3 mm pada tabel"),

("56","Wa1","","warning_label","SB8096-001","N/A","Electrical shock; 36 x 150 mm","Juga kandidat utama Q1 ref 10"),
("56","Wa1","","warning_label","SA9826-001","N/A","Caution; 56 x 43 mm","Juga kandidat utama A ref 27"),
("56","Wa1","","warning_label","SA9957-001","N/A","Injury mark; L=16","Juga kandidat utama A ref 30"),
("56","Wa1","","warning_label","S37060-001","N/A","Grounding label","Juga kandidat utama A ref 31 dan Q1 ref 8"),
("56","Wa1","","warning_label","S37059-001","N/A","PE label; 7.5 x 12.5 mm","Juga kandidat utama Q1 ref 9"),
("56","Wa1","","warning_label","SB0827-001","N/A","High temperature; L=16","Juga kandidat utama G ref 13 dan J ref 82"),
("57","Wa2","","warning_label","SB1271-101","N/A","Oil warning label JP; 68 x 30 mm","Label bahasa Jepang"),
("57","Wa2","","warning_label","SB1270-001","N/A","Oil warning label EN; 68 x 30 mm","Label bahasa Inggris"),
]

if not source.exists():
    raise SystemExit(f"ERROR: CSV sumber tidak ditemukan: {source}")

with source.open(newline="", encoding="utf-8-sig") as f:
    main = list(csv.DictReader(f))

if not main or "part_number" not in main[0]:
    raise SystemExit("ERROR: kolom part_number tidak ditemukan")

def norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())

main_codes = {norm(r["part_number"]) for r in main if r.get("part_number")}

fields = [
    "printed_catalog_page", "section_code", "zigzag_width",
    "part_role", "part_number", "is_standard",
    "variant_description", "source_note", "review_status"
]

out_rows = []
for page, section, width, role, code, standard, variant, note in data:
    status = (
        "EXISTS_IN_MAIN_CANDIDATES"
        if norm(code) in main_codes
        else "NOT_FOUND_IN_MAIN_CANDIDATES"
    )
    out_rows.append({
        "printed_catalog_page": page,
        "section_code": section,
        "zigzag_width": width,
        "part_role": role,
        "part_number": code,
        "is_standard": standard,
        "variant_description": variant,
        "source_note": note,
        "review_status": status,
    })

assert len(out_rows) == 33, f"Jumlah tidak sesuai: {len(out_rows)}"

with target.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(out_rows)

with target.open(newline="", encoding="utf-8-sig") as f:
    check = list(csv.DictReader(f))

assert len(check) == 33
assert all(r["part_number"] for r in check)
assert len({(r["section_code"], r["part_number"]) for r in check}) == 33

print("=== HASIL STAGING GAUGE & LABEL ===")
print("Kandidat utama :", len(main), "baris")
print("Staging baru   :", target)
print("Total staging  :", len(check), "baris")
print("Per bagian     :", dict(Counter(r["section_code"] for r in check)))
print("Status kode    :", dict(Counter(r["review_status"] for r in check)))
print("OK - 33 baris berhasil ditulis dan dibaca ulang")
print("OK - File review lama tidak ditimpa")
print("OK - Database tidak diubah")
