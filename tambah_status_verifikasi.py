from pathlib import Path
import shutil
import re
import sys

app = Path("app.py")
tpl = Path("templates/needle_series_edit.html")

if not app.exists() or not tpl.exists():
    sys.exit("GAGAL: app.py atau template edit tidak ditemukan.")

a = app.read_text()
t = tpl.read_text()

# Jangan menerapkan perubahan dua kali.
if 'name="verification_status"' in t:
    sys.exit("Pilihan status tampaknya sudah ada. Tidak ada file yang diubah.")

route_start = a.find("def edit_needle_series(series_id):")
route_end = a.find('\n\n@app.route("/needle-systems")', route_start)

if route_start < 0 or route_end < 0:
    sys.exit("GAGAL: batas fungsi edit seri tidak ditemukan.")

route = a[route_start:route_end]

if 'verification_status' in route:
    sys.exit("GAGAL: fungsi edit sudah menyebut verification_status.")

# Tambahkan status ke data formulir.
route = route.replace(
    '        "verification_notes",\n',
    '        "verification_notes",\n        "verification_status",\n',
    1,
)

# Validasi pilihan status.
route = route.replace(
    '            if not code:\n',
    '''            allowed_statuses = {
                "Perlu diverifikasi",
                "Terverifikasi",
                "Perlu koreksi",
            }

            if values["verification_status"] not in allowed_statuses:
                error = "Status verifikasi tidak valid."
            elif not code:
''',
    1,
)

# Simpan status yang dipilih ke database.
route = route.replace(
    '                            verification_notes = ?,\n'
    '                            updated_at = CURRENT_TIMESTAMP\n',
    '                            verification_notes = ?,\n'
    '                            verification_status = ?,\n'
    '                            updated_at = CURRENT_TIMESTAMP\n',
    1,
)

route = route.replace(
    '                        values["verification_notes"] or None,\n'
    '                        series_id,\n',
    '                        values["verification_notes"] or None,\n'
    '                        values["verification_status"],\n'
    '                        series_id,\n',
    1,
)

if "verification_status = ?," not in route:
    sys.exit("GAGAL: bagian penyimpanan status tidak cocok.")

# Tambahkan pilihan pada template sebelum tombol simpan.
marker = '<button type="submit">Simpan Perubahan</button>'
if marker not in t:
    sys.exit("GAGAL: tombol simpan tidak ditemukan pada template.")

status_field = '''<label for="verification_status">Status verifikasi *</label>
    <select id="verification_status" name="verification_status" required>
        {% for status in ["Perlu diverifikasi", "Terverifikasi", "Perlu koreksi"] %}
        <option value="{{ status }}"
            {% if values["verification_status"] == status %}selected{% endif %}>
            {{ status }}
        </option>
        {% endfor %}
    </select>

    '''

new_t = t.replace(marker, status_field + marker, 1)

# Pastikan semua perubahan penting cocok sebelum menulis file.
if '"verification_status",' not in route:
    sys.exit("GAGAL: status belum masuk ke data formulir.")
if "allowed_statuses" not in route:
    sys.exit("GAGAL: validasi status belum ditambahkan.")
if new_t == t:
    sys.exit("GAGAL: template tidak berubah.")

backup_a = Path("app.py.backup-before-status-verifikasi")
backup_t = Path("templates/needle_series_edit.html.backup-before-status-verifikasi")

if not backup_a.exists():
    shutil.copy2(app, backup_a)
if not backup_t.exists():
    shutil.copy2(tpl, backup_t)

new_a = a[:route_start] + route + a[route_end:]

# Uji sintaks sebelum menulis app.py.
import ast
try:
    ast.parse(new_a)
except SyntaxError as exc:
    sys.exit(f"GAGAL: perubahan app.py tidak valid: {exc}")

app.write_text(new_a)
tpl.write_text(new_t)

print("BERHASIL: pilihan status verifikasi ditambahkan.")
print(f"Cadangan app.py: {backup_a}")
print(f"Cadangan template: {backup_t}")
print("Berikutnya: python -m py_compile app.py")
