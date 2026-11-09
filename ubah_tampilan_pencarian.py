from pathlib import Path
from datetime import datetime
import shutil
import sys

template = Path("templates/needle_systems.html")
backup_dir = Path("backup/pencarian-katalog")
backup_dir.mkdir(parents=True, exist_ok=True)

if not template.is_file():
    sys.exit("GAGAL: template katalog tidak ditemukan.")

content = template.read_text(encoding="utf-8")

old_end = '''    function filterNeedles() {
        const keyword = searchInput.value.trim().toLocaleLowerCase("id");'''

new_end = '''    function filterNeedles() {
        const keyword = searchInput.value.trim().toLocaleLowerCase("id");
        const hasFilter = Boolean(
            keyword ||
            brandFilter.value.trim() ||
            stitchFilter.value.trim() ||
            machineFilter.value.trim() ||
            seriesFilter.value.trim()
        );'''

if content.count(old_end) != 1:
    sys.exit("GAGAL: fungsi filter tidak ditemukan secara unik.")

old_show = '''            const show = matchesKeyword && matchesBrand &&
                         matchesStitch && matchesMachine && matchesSeries;'''

new_show = '''            const show = hasFilter && matchesKeyword && matchesBrand &&
                         matchesStitch && matchesMachine && matchesSeries;'''

if content.count(old_show) != 1:
    sys.exit("GAGAL: aturan tampilan kartu tidak ditemukan secara unik.")

old_reset = '''        seriesFilter.value = "";
        filterNeedles();'''

new_reset = '''        seriesFilter.value = "";
        filterNeedles();'''

if content.count(old_reset) != 1:
    sys.exit("GAGAL: fungsi Reset tidak ditemukan secara unik.")

if "const hasFilter = Boolean(" in content:
    sys.exit("DIBATALKAN: perubahan tampaknya sudah pernah diterapkan.")

backup = backup_dir / (
    "needle_systems.html.sebelum-sembunyi-"
    + datetime.now().strftime("%Y%m%d-%H%M%S")
)
shutil.copy2(template, backup)

content = content.replace(old_end, new_end, 1)
content = content.replace(old_show, new_show, 1)

template.write_text(content, encoding="utf-8")

print("BERHASIL: kartu katalog disembunyikan sebelum pencarian.")
print("Backup:", backup)
print("Data database tidak diubah.")
