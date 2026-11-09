import csv
from pathlib import Path

out = Path("tools/z8550b_z8560b_gauge_labels_review.csv")

rows = []

def add(section, width, role, code, note, status="REVIEW_REQUIRED"):
    rows.append({
        "section": section,
        "zigzag_width": width,
        "part_role": role,
        "part_number": code,
        "variation_or_context": note,
        "review_status": status,
    })

# Konfigurasi utama sesuai kolom pada tabel Gauge parts list.
for role, code in [
    ("Needle plate", "S48065-001"),
    ("Feed dog", "S48143-101"),
    ("Presser foot assembly", "S48293-201"),
    ("Stopper", "SA9064-001"),
]:
    add("Ga1", "8mm", role, code, "Baris konfigurasi utama 8mm")

for role, code in [
    ("Needle plate", "S48066-001"),
    ("Feed dog", "S06171-101"),
    ("Presser foot assembly", "S48308-201"),
    ("Stopper", "S48074-000"),
]:
    add("Ga2", "5mm", role, code, "Baris konfigurasi utama 5mm")

for role, code in [
    ("Needle plate", "S50684-001"),
    ("Feed dog", "S50686-001"),
    ("Presser foot assembly", "S51227-201"),
    ("Stopper", "S52046-000"),
]:
    add("Ga3", "10mm", role, code, "Baris konfigurasi utama 10mm")

for role, code in [
    ("Needle plate", "S54929-001"),
    ("Feed dog", "S54945-001"),
    ("Presser foot assembly", "S54957-201"),
]:
    add("Ga3", "3mm", role, code, "Baris konfigurasi utama 3mm")

# Kode alternatif yang terlihat pada halaman gauge.
# Perannya tidak dipaksakan jika susunan tabel belum cukup jelas.
alternatives = [
    ("Ga1", "8mm", "S58908-001", "Varian; peran perlu diverifikasi"),
    ("Ga1", "8mm", "S48305-201", "Presser foot alternatif; catatan warna hitam"),
    ("Ga1", "8mm", "S58950-201", "Varian; peran perlu diverifikasi"),
    ("Ga2", "5mm", "S48067-001", "Needle plate alternatif; catatan warna hitam"),
    ("Ga2", "5mm", "S06166-001", "Varian; peran perlu diverifikasi"),
    ("Ga2", "5mm", "S06170-101", "Varian; peran perlu diverifikasi"),
    ("Ga2", "5mm", "S53410-001", "Varian; peran perlu diverifikasi"),
    ("Ga2", "5mm", "S52068-001", "Varian; peran perlu diverifikasi"),
    ("Ga2", "5mm", "S54937-001", "Varian; peran perlu diverifikasi"),
    ("Ga3", "10mm", "S50685-001", "Needle plate alternatif; catatan warna putih salju"),
]
for section, width, code, note in alternatives:
    add(section, width, "UNCONFIRMED", code, note)

# Nama dan ukuran label dari tabel Warning labels.
labels = [
    ("Wa1", "SB8096-001", "Label electrical shock", "36 x 150 mm"),
    ("Wa1", "SA9826-001", "Label caution", "56 x 43 mm"),
    ("Wa1", "SA9957-001", "Injury mark", "L=16"),
    ("Wa1", "S37060-001", "Label grounding", "12"),
    ("Wa1", "S37059-001", "Label, PE", "7.5 x 12.5 mm"),
    ("Wa1", "SB0827-001", "High temp label", "L=16"),
    ("Wa2", "SB1271-101", "Oil warning label JP", "68 x 30 mm"),
    ("Wa2", "SB1270-001", "Oil warning label EN", "68 x 30 mm"),
]
for section, code, name, size in labels:
    add(section, "", "Warning label", code, f"{name}; ukuran sumber: {size}")

fields = [
    "section", "zigzag_width", "part_role", "part_number",
    "variation_or_context", "review_status",
]
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("CSV tinjauan:", out)
print("Total baris tinjauan:", len(rows))
print("Konfigurasi gauge utama:", sum(r["part_role"] != "UNCONFIRMED"
                                      and r["section"].startswith("Ga")
                                      for r in rows))
print("Kode alternatif belum terkonfirmasi:", len(alternatives))
print("Label peringatan:", len(labels))
print("Database tidak diubah.")
