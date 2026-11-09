from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

app = Path("app.py")

if not app.is_file():
    sys.exit("BATAL: app.py tidak ditemukan.")

original = app.read_text(encoding="utf-8")

func_marker = "def component_detail(component_id):"
if original.count(func_marker) != 1:
    sys.exit("BATAL: fungsi component_detail tidak ditemukan secara unik.")

start = original.index(func_marker)
match = re.search(r"(?m)^(?:@app\.route|def )", original[start + len(func_marker):])
end = start + len(func_marker) + match.start() if match else len(original)

function_text = original[start:end]

patch_marker = '''    if component is None:
        conn.close()
        return "Komponen tidak ditemukan", 404'''

patch = '''    # Sembunyikan kategori generik Brother BAS-311HN-03S
    # dari halaman detail publik tanpa menghapus data database.
    if (
        component["machine_id"] == 227
        and component["id"] in (530, 531, 532, 533)
    ):
        conn.close()
        return "Komponen tidak ditemukan", 404'''

if "Sembunyikan kategori generik Brother BAS-311HN-03S" in function_text:
    sys.exit("BATAL: patch tampaknya sudah ada pada fungsi ini.")

if function_text.count(patch_marker) != 1:
    sys.exit("BATAL: penanda di dalam fungsi tidak ditemukan secara unik.")

new_function = function_text.replace(
    patch_marker, patch_marker + "\n\n" + patch, 1
)
updated = original[:start] + new_function + original[end:]

try:
    compile(updated, str(app), "exec")
except SyntaxError as e:
    sys.exit(f"BATAL: hasil patch gagal diperiksa: {e}")

backup = Path(
    "app.py.bak_sebelum_filter_detail_brother227_v2_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
)
shutil.copy2(app, backup)

try:
    app.write_text(updated, encoding="utf-8")
    compile(app.read_text(encoding="utf-8"), str(app), "exec")
except Exception as e:
    shutil.copy2(backup, app)
    sys.exit(
        f"GAGAL: perubahan dibatalkan dan app.py dipulihkan. Detail: {e}"
    )

print("BERHASIL: patch hanya dipasang di component_detail().")
print(f"Backup: {backup}")
print("Pemeriksaan sintaks: OK")
print("Database: tidak diubah")
print("Deployment: tidak dilakukan")
