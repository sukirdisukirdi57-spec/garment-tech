from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

path = Path("templates/component_detail.html")
text = path.read_text(encoding="utf-8")
original = text

# 1. Hapus judul kecil yang menduplikasi judul halaman utama.
label = '        <div class="component-hero-label">🔩 DETAIL COMPONENT</div>'
if text.count(label) != 1:
    sys.exit("BATAL: label hero tidak ditemukan tepat satu kali. File tidak diubah.")
text = text.replace(label, "", 1)

# 2. Hapus detail teknis yang berulang di dalam hero.
# Informasi yang sama tetap tersedia di bagian Informasi Teknis.
start_marker = '        {% if component["part_number"] %}'
end_marker = '    </section>\n\n\n    <div class="component-middle-navigation">'

start = text.find(start_marker)
end = text.find(end_marker, start + len(start_marker))
if start < 0 or end < 0:
    sys.exit("BATAL: batas blok detail hero tidak ditemukan. File tidak diubah.")

duplicate_block = text[start:end]
required_fields = [
    'component["part_number"]',
    'component["catalog_ref"]',
    'component["diagram_page"]',
    'component["function"]',
    'component["notes"]',
]
if not all(field in duplicate_block for field in required_fields):
    sys.exit("BATAL: isi blok tidak sesuai perkiraan. File tidak diubah.")

text = text[:start] + text[end:]

# 3. Hapus navigasi tengah yang mengulang tautan di bagian bawah.
middle_start = '    <div class="component-middle-navigation">'
middle_end = '    <section class="component-info">'
start = text.find(middle_start)
end = text.find(middle_end, start + len(middle_start))
if start < 0 or end < 0:
    sys.exit("BATAL: batas navigasi tengah tidak ditemukan. File tidak diubah.")

middle_block = text[start:end]
if middle_block.count('component-middle-button') != 2:
    sys.exit("BATAL: jumlah tombol navigasi tengah tidak sesuai. File tidak diubah.")

text = text[:start] + text[end:]

if text == original:
    sys.exit("Tidak ada perubahan yang diperlukan.")

# Pastikan viewer diagram tetap utuh sebelum menulis.
for marker in (
    '<!-- component-diagram-viewer-v1 -->',
    '<!-- end component-diagram-viewer-v1 -->',
    'id="diagram-viewer"',
    'id="diagram-open"',
):
    if original.count(marker) != text.count(marker):
        sys.exit(f"BATAL: marker {marker!r} berubah. File tidak diubah.")

backup = path.with_name(
    path.name + ".bak_rapikan_" + datetime.now().strftime("%Y%m%d_%H%M%S")
)
shutil.copy2(path, backup)
path.write_text(text, encoding="utf-8")

print("PATCH BERHASIL")
print("Backup:", backup)
print("Judul hero tersisa:", text.count('component-hero-label'))
print("Blok navigasi tengah tersisa:", text.count('component-middle-navigation'))
print("Viewer diagram:", text.count('<!-- component-diagram-viewer-v1 -->'), "marker awal")
print("Informasi Teknis:", text.count("<h2>📋 Informasi Teknis</h2>"))
