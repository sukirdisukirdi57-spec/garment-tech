from pathlib import Path
from datetime import datetime
import ast
import sys

path = Path("app.py")
source = path.read_text(encoding="utf-8")

old = '''    if machine_id:
        conditions.append("components.machine_id = ?")
        params.append(machine_id)
    if component_id:
'''

new = '''    if machine_id:
        conditions.append("components.machine_id = ?")
        params.append(machine_id)

    # Sembunyikan kategori generik dari tampilan publik
    # hanya untuk Brother BAS-311HN-03S (machine_id 227).
    if machine_id == 227:
        conditions.append("components.id NOT IN (530, 531, 532, 533)")

    if component_id:
'''

if "components.id NOT IN (530, 531, 532, 533)" in source:
    print("Aturan penyaringan sudah ada. Tidak ada perubahan.")
    sys.exit(0)

count = source.count(old)
if count != 1:
    sys.exit(
        f"BATAL: pola target ditemukan {count} kali, bukan 1. "
        "app.py tidak diubah."
    )

updated = source.replace(old, new, 1)

try:
    ast.parse(updated)
except SyntaxError as exc:
    sys.exit(f"BATAL: validasi sintaks gagal: {exc}")

backup = path.with_name(
    f"app.py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)
backup.write_text(source, encoding="utf-8")
path.write_text(updated, encoding="utf-8")

print("Berhasil memperbarui app.py.")
print(f"Backup: {backup}")
print("Penyaringan berlaku hanya saat machine_id == 227.")
print("ID 530–533 tidak dihapus dari database.")
print("Sintaks Python valid; database tidak diubah.")
