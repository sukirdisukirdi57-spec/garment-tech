from pathlib import Path
from datetime import datetime
from jinja2 import Environment
import re
import sys

path = Path("templates/components.html")

if not path.is_file():
    sys.exit("BATAL: templates/components.html tidak ditemukan.")

original = path.read_text(encoding="utf-8")

# Hindari menerapkan aturan yang sama berulang kali.
if all(f"item['id'] == {i}" in original for i in (531, 532, 533)):
    print("Aturan untuk ID 531, 532, dan 533 sudah ada.")
    sys.exit(0)

pattern = re.compile(
    r"\{% for item in component_options %\}.*?\{% endfor %\}",
    re.DOTALL,
)

matches = list(pattern.finditer(original))
if len(matches) != 1:
    sys.exit(
        f"BATAL: ditemukan {len(matches)} blok component_options. "
        "Tidak ada file yang diubah."
    )

new_block = """{% for item in component_options %}
        {% if not (machine_id == 227 and item['id'] in [530, 531, 532, 533]) %}
        <option value="{{ item['id'] }}" {% if component_id == item['id'] %}selected{% endif %}>{{ item['component_name'] }}{% if item['part_number'] %} — Part: {{ item['part_number'] }}{% endif %}</option>
        {% endif %}
        {% endfor %}"""

match = matches[0]
updated = original[:match.start()] + new_block + original[match.end():]

try:
    Environment().parse(updated)
except Exception as exc:
    sys.exit(f"BATAL: validasi template gagal: {exc}")

backup = path.with_name(
    f"components.html.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
backup.write_text(original, encoding="utf-8")
path.write_text(updated, encoding="utf-8")

print("Template berhasil diperbarui.")
print(f"Backup: {backup}")
print("Disembunyikan pada mesin 227: ID 530, 531, 532, 533.")
print("Komponen katalog lainnya tetap ditampilkan.")
print("Database dan relasi suku cadang tidak diubah.")
