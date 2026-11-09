from pathlib import Path
from datetime import datetime
import shutil
import sys

path = Path("app.py")
source = path.read_text(encoding="utf-8")
updated = source

# Batasi perubahan pada bagian route daftar komponen.
start = updated.find('if component_id:\n        conditions.append("components.id = ?")')
end = updated.find("# Ambil seluruh spare part yang terhubung ke mekanisme terpilih.", start)

if start < 0 or end < 0:
    sys.exit("BATAL: batas blok pencarian komponen tidak ditemukan.")

block = updated[start:end]

old_loop = "        for word in search.split():"
if block.count(old_loop) != 1:
    sys.exit("BATAL: pola loop pencarian komponen tidak cocok.")

block = block.replace(
    old_loop,
    '        search_terms = [w for w in search.replace("—", " ").replace("–", " ").split() if w]\n'
    '        for word in search_terms:',
    1
)

old_sql = '''                "brands.name LIKE ?"
                ")"
            )
            params.extend([pattern] * 7)'''

new_sql = '''                "brands.name LIKE ? OR "
                "EXISTS ("
                "SELECT 1 FROM component_parts cp "
                "JOIN parts p ON p.id = cp.part_id "
                "WHERE cp.component_id = components.id "
                "AND (p.part_number LIKE ? OR p.part_name LIKE ?)"
                ")"
                ")"
            )
            params.extend([pattern] * 9)'''

if block.count(old_sql) != 1:
    sys.exit("BATAL: pola SQL komponen tidak cocok; app.py tidak diubah.")

block = block.replace(old_sql, new_sql, 1)
updated = updated[:start] + block + updated[end:]

# Normalisasi tanda pisah pada pencarian spare part juga.
marker = "# Pencarian langsung juga mencakup tabel spare part."
pos = updated.find(marker)
if pos < 0:
    sys.exit("BATAL: blok pencarian spare part tidak ditemukan.")

tail = updated[pos:]
if tail.count(old_loop) < 1:
    sys.exit("BATAL: loop pencarian spare part tidak ditemukan.")

tail = tail.replace(
    old_loop,
    '        search_terms = [w for w in search.replace("—", " ").replace("–", " ").split() if w]\n'
    '        for word in search_terms:',
    1
)
updated = updated[:pos] + tail

backup = Path(
    "app.py.before-part-search-" + datetime.now().strftime("%Y%m%d-%H%M%S")
)
shutil.copy2(path, backup)

try:
    path.write_text(updated, encoding="utf-8")
except Exception:
    shutil.copy2(backup, path)
    raise

print("BERHASIL: pencarian komponen dan spare part diperbarui.")
print("Cadangan:", backup)
