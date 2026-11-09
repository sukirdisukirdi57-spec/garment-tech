from pathlib import Path
import shutil
import sys

app_path = Path("app.py")
form_path = Path("templates/needle_add.html")
app = app_path.read_text()
form = form_path.read_text()

start = app.find('def add_needle():')
end = app.find('@app.route("/admin/needle/<int:needle_id>/edit"', start)
if start < 0 or end < 0:
    sys.exit("BERHENTI: batas route tambah/edit tidak ditemukan.")

route = app[start:end]

old_validation = '''            if values["verification_status"] not in status_options:
                values["verification_status"] = "Belum diverifikasi"
'''
new_validation = '''            if values["verification_status"] not in status_options:
                values["verification_status"] = "Belum diverifikasi"

            verification_notes = request.form.get(
                "verification_notes", ""
            ).strip()

            if values["verification_status"] == "Terverifikasi" and (
                not values["source_url"] or not verification_notes
            ):
                return (
                    "Untuk memverifikasi data, URL sumber dan catatan bukti "
                    "verifikasi wajib diisi.",
                    400,
                )

            verified_at = None
            if values["verification_status"] == "Terverifikasi":
                verified_at = __import__("datetime").datetime.now().astimezone().isoformat(
                    timespec="seconds"
                )
'''
if old_validation not in route:
    sys.exit("BERHENTI: blok validasi status tidak cocok; tidak ada file diubah.")

route = route.replace(old_validation, new_validation, 1)

old_sql = '''                    verification_status, size_nm_value,
                    manufacturer_size
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
new_sql = '''                    verification_status, size_nm_value,
                    manufacturer_size, verification_notes, verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
if old_sql not in route:
    sys.exit("BERHENTI: pola INSERT tidak cocok; tidak ada file diubah.")
route = route.replace(old_sql, new_sql, 1)

old_values = '''                values["verification_status"],
                nm_value,
                manufacturer_size or None,
            ))'''
new_values = '''                values["verification_status"],
                nm_value,
                manufacturer_size or None,
                verification_notes or None,
                verified_at,
            ))'''
if old_values not in route:
    sys.exit("BERHENTI: daftar nilai INSERT tidak cocok; tidak ada file diubah.")
route = route.replace(old_values, new_values, 1)

old_form = '''            <label>Status verifikasi data jarum
                <select name="verification_status">
                    <option selected>Belum diverifikasi</option>
                    <option>Terverifikasi</option>
                </select>
            </label>
'''
new_form = old_form + '''            <label>Catatan bukti verifikasi
                <textarea name="verification_notes" rows="4" maxlength="2000" placeholder="Catat bagian katalog, halaman manual, atau bukti spesifikasi yang diperiksa"></textarea>
            </label>
            <p class="needle-help">Jika memilih Terverifikasi, URL sumber dan catatan bukti wajib diisi.</p>
'''
if old_form not in form:
    sys.exit("BERHENTI: blok status pada form tambah tidak cocok; tidak ada file diubah.")

backup_app = Path("backups/app.py.before-needle-add-verification")
backup_form = Path("backups/needle_add.html.before-needle-add-verification")
backup_app.parent.mkdir(exist_ok=True)
if not backup_app.exists():
    shutil.copy2(app_path, backup_app)
if not backup_form.exists():
    shutil.copy2(form_path, backup_form)

app = app[:start] + route + app[end:]
form = form.replace(old_form, new_form, 1)

app_path.write_text(app)
form_path.write_text(form)
print("Patch validasi route tambah dan form berhasil diterapkan.")
print("Backup:", backup_app)
print("Backup:", backup_form)
