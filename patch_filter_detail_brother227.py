from pathlib import Path
from datetime import datetime
import py_compile
import shutil
import sys

app = Path("app.py")
if not app.is_file():
    sys.exit("GAGAL: app.py tidak ditemukan.")

source = app.read_text(encoding="utf-8")

marker = '''    if component is None:
        conn.close()
        return "Komponen tidak ditemukan", 404
'''

patch = marker + '''
    # Sembunyikan kategori generik Brother BAS-311HN-03S
    # dari halaman detail publik tanpa menghapus data database.
    if (
        component["machine_id"] == 227
        and component["id"] in (530, 531, 532, 533)
    ):
        conn.close()
        return "Komponen tidak ditemukan", 404
'''

if "Sembunyikan kategori generik Brother BAS-311HN-03S" in source:
    sys.exit("BATAL: patch tampaknya sudah ada. Tidak ada perubahan.")

if source.count(marker) != 1:
    sys.exit(
        "BATAL: titik penyisipan tidak ditemukan secara unik. "
        "app.py tidak diubah."
    )

backup = Path(
    "app.py.bak_sebelum_filter_detail_brother227_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)

shutil.copy2(app, backup)
updated = source.replace(marker, patch, 1)

try:
    compile(updated, str(app), "exec")
except SyntaxError as exc:
    backup.unlink(missing_ok=True)
    sys.exit(f"GAGAL: pemeriksaan sintaks: {exc}")

app.write_text(updated, encoding="utf-8")

try:
    py_compile.compile(str(app), doraise=True)
except py_compile.PyCompileError as exc:
    app.write_text(source, encoding="utf-8")
    sys.exit(
        f"GAGAL: sintaks setelah penulisan. "
        f"app.py dipulihkan dari isi awal.\n{exc}"
    )

print("BERHASIL: patch dipasang.")
print(f"Cadangan: {backup}")
print("Sintaks Python: OK")
print("Database: tidak diubah.")
print("Deployment: tidak dilakukan.")
