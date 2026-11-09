from pathlib import Path
from datetime import datetime
import re
import sys

template = Path("templates/components.html")

if not template.is_file():
    sys.exit("BATAL: templates/components.html tidak ditemukan.")

original = template.read_text(encoding="utf-8")

# Jangan mengubah file jika perubahan sudah diterapkan.
if "item['id'] == 530" in original and "machine_id == 227" in original:
    print("Tidak ada perubahan: aturan penyaringan tampaknya sudah ada.")
    sys.exit(0)

pattern = re.compile(
    r"(?P<indent>[ \t]*)\{% for item in component_options %\}"
    r"(?P<body>.*?)"
    r"(?P<end>\{% endfor %\})",
    re.DOTALL,
)

matches = list(pattern.finditer(original))
if len(matches) != 1:
    sys.exit(
        f"BATAL: ditemukan {len(matches)} blok component_options; "
        "periksa template secara manual."
    )

match = matches[0]
block = match.group(0)

if "item['component_name']" not in block or "item['id']" not in block:
    sys.exit("BATAL: struktur blok tidak sesuai; file tidak diubah.")

new_block = """{% for item in component_options %}
    {% if not (machine_id == 227 and item['id'] == 530) %}
    <option value="{{ item['id'] }}"
        {% if component_id == item['id'] %}selected{% endif %}>
        {{ item['component_name'] }}{% if item['part_number'] %} — Part: {{ item['part_number'] }}{% endif %}
    </option>
    {% endif %}
{% endfor %}"""

updated = original[:match.start()] + new_block + original[match.end():]

# Pastikan file berubah hanya pada blok yang dituju.
if updated == original:
    sys.exit("BATAL: tidak ada perubahan yang diperlukan.")

backup = template.with_name(
    f"components.html.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
backup.write_text(original, encoding="utf-8")

try:
    from jinja2 import Environment
    Environment().parse(updated)
except Exception as exc:
    backup.unlink(missing_ok=True)
    sys.exit(f"BATAL: validasi template gagal: {exc}")

template.write_text(updated, encoding="utf-8")

print("Berhasil memperbarui template.")
print(f"Backup: {backup}")
print("Komponen ID 530 disembunyikan hanya untuk mesin ID 227.")
print("Komponen ID 536 tetap ditampilkan; database tidak diubah.")
