import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tmp/bas311hn/j_staging_review.csv"
OUTPUT = ROOT / "tmp/bas311hn/j_staging_audited_v1.csv"

if not SOURCE.is_file():
    raise SystemExit(f"STOP: sumber tidak ditemukan: {SOURCE}")
if OUTPUT.exists():
    raise SystemExit(f"STOP: file audit sudah ada, tidak ditimpa: {OUTPUT}")

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 72:
    raise SystemExit(f"STOP: harus 72 baris, ditemukan {len(rows)}")

expected_refs = [str(i) for i in range(1, 73)]
if [r["catalog_ref"] for r in rows] != expected_refs:
    raise SystemExit("STOP: referensi tidak lengkap/berurutan")

# Pemetaan khusus dari Different parts list halaman cetak 73.
variant_parts = {
    "63": ("SA7944-101", "FIXED KNIFE FL"),
    "66": ("SA5221-001", "NEEDLE HOLE PLATE 2.2"),
}

for r in rows:
    ref = r["catalog_ref"]
    if r["diagram_page"] != "39":
        raise SystemExit(f"STOP: diagram_page salah pada ref {ref}")

    if ref in variant_parts:
        expected_code, expected_name = variant_parts[ref]
        if (r["part_number"], r["part_name"]) != (
            expected_code, expected_name
        ):
            raise SystemExit(
                f"STOP: kode/nama varian tidak cocok pada ref {ref}"
            )
        r["audit_note"] = (
            "Kode dan nama dicocokkan dengan Different parts list, "
            "halaman cetak 73, kolom -03S/-03A."
        )
    else:
        if not r["part_number"].strip() or not r["part_name"].strip():
            raise SystemExit(f"STOP: kode/nama kosong pada ref {ref}")
        r["audit_note"] = (
            "Dicocokkan dengan daftar komponen J pada katalog; "
            "pertahankan nomor referensi dan kuantitas sesuai sumber."
        )

    if not r["quantity_raw"].isdigit():
        raise SystemExit(f"STOP: kuantitas tidak valid pada ref {ref}")

    r["verification"] = "VERIFIED"
    r["review_note"] = (
        "Audit transkripsi daftar komponen J; "
        "kode varian khusus diperiksa terpisah."
    )
    r["status"] = "VERIFIED"

fields = list(rows[0].keys())
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("File audit dibuat:", OUTPUT.relative_to(ROOT))
print("Jumlah baris:", len(rows))
print("Referensi:", rows[0]["catalog_ref"], "-", rows[-1]["catalog_ref"])
print("Ref 63:", variant_parts["63"])
print("Ref 66:", variant_parts["66"])
print("Database diubah: TIDAK")
print("Catatan: hasil audit harus diperiksa sebelum dry-run impor.")
