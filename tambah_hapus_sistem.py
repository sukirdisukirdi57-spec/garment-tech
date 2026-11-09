from pathlib import Path
import shutil

app_path = Path("app.py")
catalog_path = Path("templates/needle_systems.html")

app = app_path.read_text()
catalog = catalog_path.read_text()

route_marker = '@app.route("/needle-systems")'

edit_button = '''        {% if session.get("admin_logged_in") %}
        <p>
            <a href="/admin/needle-systems/{{ item['id'] }}/edit"
               style="display:inline-block;padding:9px 14px;background:#075bb5;color:white;border-radius:6px;text-decoration:none;">
                Edit Sistem Jarum
            </a>
        </p>
        {% endif %}
'''

if 'def delete_needle_system(' in app:
    raise SystemExit("BERHENTI: fungsi hapus sudah ada.")

if route_marker not in app:
    raise SystemExit("GAGAL: route katalog tidak ditemukan.")

if edit_button not in catalog:
    raise SystemExit("GAGAL: tombol edit tidak ditemukan persis. File tidak diubah.")

if 'name="confirm-delete-needle"' in catalog:
    raise SystemExit("BERHENTI: tombol hapus tampaknya sudah ada.")

route = r'''
@app.route("/admin/needle-systems/<int:system_id>/delete", methods=["POST"])
@admin_required
def delete_needle_system(system_id):
    conn = get_db()
    try:
        item = conn.execute(
            "SELECT id FROM needle_systems WHERE id = ?",
            (system_id,),
        ).fetchone()

        if item is None:
            return "Data sistem jarum tidak ditemukan.", 404

        conn.execute(
            "DELETE FROM needle_systems WHERE id = ?",
            (system_id,),
        )
        conn.commit()
        return redirect("/needle-systems?deleted=1")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


'''

notice_marker = '''    {% if request.args.get("edited") == "1" %}
    <div class="note" role="status" style="background:#e7f7e9;color:#17652b;padding:12px;border-radius:6px;margin:12px 0;">
        ✓ Perubahan sistem jarum berhasil disimpan.
    </div>
    {% endif %}
'''

if notice_marker not in catalog:
    raise SystemExit("GAGAL: lokasi notifikasi edit tidak ditemukan. File tidak diubah.")

delete_notice = notice_marker + '''
    {% if request.args.get("deleted") == "1" %}
    <div class="note" role="status" style="background:#e7f7e9;color:#17652b;padding:12px;border-radius:6px;margin:12px 0;">
        ✓ Sistem jarum berhasil dihapus.
    </div>
    {% endif %}
'''

delete_button = edit_button + '''
        <form method="post"
              action="/admin/needle-systems/{{ item['id'] }}/delete"
              onsubmit="return confirm('Yakin ingin menghapus sistem jarum {{ item['system_code']|e }}? Data yang dihapus tidak dapat dipulihkan dari halaman ini.');"
              style="margin-top:8px;">
            <button type="submit" name="confirm-delete-needle" value="1"
                    style="padding:9px 14px;background:#b42318;color:white;border:0;border-radius:6px;">
                Hapus Sistem Jarum
            </button>
        </form>
'''

# Pastikan semua pemeriksaan lolos sebelum mengubah file.
shutil.copy2(app_path, "app.py.backup-before-delete-needle-system")
shutil.copy2(
    catalog_path,
    "templates/needle_systems.html.backup-before-delete-needle-system"
)

app = app.replace(route_marker, route + route_marker, 1)
catalog = catalog.replace(notice_marker, delete_notice, 1)
catalog = catalog.replace(edit_button, delete_button, 1)

app_path.write_text(app)
catalog_path.write_text(catalog)

print("BERHASIL: route hapus khusus admin ditambahkan.")
print("BERHASIL: tombol hapus dengan konfirmasi ditambahkan.")
print("BERHASIL: notifikasi penghapusan ditambahkan.")
print("Cadangan app.py dan template katalog telah dibuat.")
