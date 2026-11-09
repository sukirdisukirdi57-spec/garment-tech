from pathlib import Path
import re

base = Path("audit_tmp_ddl7000a/machine_detail_accordion_detail.html").read_text(encoding="utf-8")
extra = Path("audit_tmp_ddl7000a/machine_detail_accordion_lainnya.html").read_text(encoding="utf-8")

for section_id in ("documents", "official-alarms", "components"):
    pattern = rf'<section id="{section_id}">.*?</section>'
    match = re.search(pattern, extra, flags=re.S)
    if not match:
        raise RuntimeError(f"Bagian {section_id} tidak ditemukan di proposal kedua")

    base, count = re.subn(pattern, lambda _: match.group(0), base, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Bagian {section_id} tidak ditemukan unik di proposal pertama")

output = Path("audit_tmp_ddl7000a/machine_detail_accordion_gabungan.html")
output.write_text(base, encoding="utf-8")

print("PROPOSAL GABUNGAN BERHASIL")
for name in ("documents", "troubleshooting", "official-alarms", "specifications", "components"):
    print(f"{name}: {'ADA' if f'<section id=\"{name}\"' in base else 'TIDAK ADA'}")
print("Parts List:", "DIPERTAHANKAN" if "ddl7000a" in base else "PERLU DIPERIKSA")
print("Template asli: tidak diubah")
print("Database: tidak diubah")
print("File:", output)
