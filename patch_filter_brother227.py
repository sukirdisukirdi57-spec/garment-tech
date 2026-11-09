from pathlib import Path
from datetime import datetime
import py_compile
import shutil
import sys

app = Path("app.py")
source = app.read_text(encoding="utf-8")

old = '''    # Sembunyikan kategori generik dari tampilan publik
    # hanya untuk Brother BAS-311HN-03S (machine_id 227).
    if machine_id == 227:
        conditions.append("components.id NOT IN (530, 531, 532, 533)")
'''

new = '''    # Sembunyikan kategori generik Brother BAS-311HN-03S
    # dari daftar publik, termasuk saat filter mesin belum dipilih.
    conditions.append("components.id NOT IN (530, 531, 532, 533)")
'''

if source.count(old) != 1:
    sys.exit(
        "BATAL: blok lama tidak ditemukan tepat satu kali. "
        "app.py tidak diubah oleh skrip ini."
    )

backup = app.with_name(
    f"app.py.bak_filter_brother227_{datetime.now():%Y%m%d_%H%M%S}"
)
shutil.copy2(app, backup)

app.write_text(source.replace(old, new, 1), encoding="utf-8")

try:
    py_compile.compile("app.py", doraise=True)
except Exception as exc:
    shutil.copy2(backup, app)
    sys.exit(f"Sintaks gagal; app.py dipulihkan. Detail: {exc}")

print("BERHASIL: filter daftar publik diperbarui.")
print("Backup:", backup)
print("Sintaks Python: OK")
print("Database: tidak diubah.")
print("Deployment: tidak dilakukan.")
