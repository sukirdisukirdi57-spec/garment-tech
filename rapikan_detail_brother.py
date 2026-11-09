from pathlib import Path
from datetime import datetime
import shutil
import sys

p = Path("templates/component_detail.html")
s = p.read_text(encoding="utf-8")
original = s

changes = [
    (
        '{% if component["id"] == 526 %}\n'
        '        <section class="component-info bas311hn-mechanism-diagram">',
        '{% if component["id"] == 526 and component["machine_id"] != 227 %}\n'
        '        <section class="component-info bas311hn-mechanism-diagram">',
        "Diagram bawah khusus ID 526",
    ),
    (
        '{% if component["id"] in bas311hn_diagrams and component["id"] != 526 %}',
        '{% if component["id"] in bas311hn_diagrams and component["id"] != 526 and component["machine_id"] != 227 %}',
        "Diagram bawah Brother BAS-311HN",
    ),
    (
        '{% if component["id"] in [527, 529, 534, 535, 536, 537, 541] and sub_parts %}',
        '{% if component["id"] in [527, 529, 534, 535, 536, 537, 541] and sub_parts and component["machine_id"] != 227 %}',
        "Tabel relasi kedua Brother BAS-311HN",
    ),
]

for old, new, label in changes:
    count = s.count(old)
    if count != 1:
        print(f"GAGAL: pola '{label}' ditemukan {count} kali, harus tepat 1.")
        print("Tidak ada perubahan yang disimpan.")
        sys.exit(1)
    s = s.replace(old, new, 1)

if s == original:
    print("Tidak ada perubahan.")
    sys.exit(1)

backup = p.with_name(
    f"component_detail_before_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
)
shutil.copy2(p, backup)

try:
    from jinja2 import Environment
    Environment().parse(s)
except Exception as e:
    print("GAGAL uji sintaks template:", e)
    print("File asli belum diubah. Backup:", backup)
    sys.exit(1)

p.write_text(s, encoding="utf-8")
print("BERHASIL merapikan template.")
print("Backup:", backup)
for _, _, label in changes:
    print(" -", label, "disembunyikan untuk machine_id 227")
print("Diagram atas, viewer zoom, dan tabel pertama tidak diubah.")
