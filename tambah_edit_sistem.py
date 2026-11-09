from pathlib import Path
import shutil

app_path = Path("app.py")
catalog_path = Path("templates/needle_systems.html")
form_path = Path("templates/needle_system_edit.html")

app = app_path.read_text()
catalog = catalog_path.read_text()

route_marker = '@app.route("/needle-systems")'
card_marker = '    <article class="system-card">'
closing_marker = '    </article>\n    {% else %}'

if 'def edit_needle_system(' in app:
    raise SystemExit("BERHENTI: route edit sudah ada.")

if route_marker not in app:
    raise SystemExit("GAGAL: route katalog tidak ditemukan.")

if card_marker not in catalog or closing_marker not in catalog:
    raise SystemExit("GAGAL: struktur kartu katalog tidak sesuai.")

if 'needle-systems/{{ item[\'id\'] }}/edit' in catalog:
    raise SystemExit("BERHENTI: tombol edit sudah ada.")

# Cadangkan file sebelum mengubahnya.
shutil.copy2(app_path, "app.py.backup-before-edit-needle-system")
shutil.copy2(
    catalog_path,
    "templates/needle_systems.html.backup-before-edit-needle-system"
)

route = r'''
@app.route("/admin/needle-systems/<int:system_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_needle_system(system_id):
    fields = (
        "system_code", "alternative_names", "manufacturer",
        "stitch_type", "machine_category", "description",
        "source_url", "reference_url", "verification_notes",
    )

    conn = get_db()
    try:
        item = conn.execute(
            "SELECT * FROM needle_systems WHERE id = ?",
            (system_id,),
        ).fetchone()

        if item is None:
            return "Data sistem jarum tidak ditemukan.", 404

        values = {
            field: (
                request.form.get(field, item[field] or "").strip()
                if request.method == "POST"
                else (item[field] or "")
            )
            for field in fields
        }
        error = None

        if request.method == "POST":
            code = values["system_code"]

            if not code:
                error = "Kode sistem jarum wajib diisi."
            elif len(code) > 100:
                error = "Kode sistem terlalu panjang."
            elif any(
                values[field] and not values[field].startswith(("https://", "http://"))
                for field in ("source_url", "reference_url")
            ):
                error = "URL harus diawali http:// atau https://."
            else:
                duplicate = conn.execute("""
                    SELECT id FROM needle_systems
                    WHERE LOWER(TRIM(system_code)) = LOWER(TRIM(?))
                      AND id != ?
                    LIMIT 1
                """, (code, system_id)).fetchone()

                if duplicate:
                    error = "Kode sistem tersebut sudah digunakan."
                else:
                    notes = values["verification_notes"] or (
                        "Belum diverifikasi; periksa katalog resmi dan "
                        "manual mesin sebelum menyimpulkan kompatibilitas."
                    )

                    conn.execute("""
                        UPDATE needle_systems SET
                            system_code = ?,
                            alternative_names = ?,
                            manufacturer = ?,
                            stitch_type = ?,
                            machine_category = ?,
                            description = ?,
                            source_url = ?,
                            reference_url = ?,
                            verification_notes = ?
                        WHERE id = ?
                    """, (
                        code,
                        values["alternative_names"] or None,
                        values["manufacturer"] or None,
                        values["stitch_type"] or None,
                        values["machine_category"] or None,
                        values["description"] or None,
                        values["source_url"] or None,
                        values["reference_url"] or None,
                        notes,
                        system_id,
                    ))
                    conn.commit()
                    return redirect("/needle-systems?edited=1")

        return render_template(
            "needle_system_edit.html",
            item=item,
            values=values,
            error=error,
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


'''

template = r'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Edit Sistem Jarum | Garment Tech</title>
<style>
body{font-family:Arial,sans-serif;background:#f3f5f7;color:#222;margin:0;padding:16px;line-height:1.6}
main{max-width:720px;margin:auto}
section{background:white;padding:20px;border-radius:10px}
label{display:block;font-weight:bold;margin-top:14px}
input,select,textarea{width:100%;box-sizing:border-box;padding:11px;border:1px solid #aaa;border-radius:6px;font-size:16px}
textarea{min-height:90px}
button{margin-top:18px;padding:12px 18px;background:#075bb5;color:white;border:0;border-radius:6px;font-size:16px}
.note{background:#fff1cc;padding:12px;border-radius:6px}
.error{background:#ffe7e7;padding:12px;border-radius:6px;color:#8b0000}
</style>
</head>
<body>
<main>
<p><a href="/needle-systems">← Kembali ke katalog</a></p>
<section>
<h1>Edit Sistem Jarum</h1>
<p class="note">Formulir ini tidak mengubah status verifikasi. Periksa manual resmi sebelum menyatakan kompatibilitas.</p>
{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
<form method="post">
<label for="system_code">Kode sistem jarum *</label>
<input id="system_code" name="system_code" maxlength="100" required value="{{ values.system_code }}">

<label for="manufacturer">Merek / produsen</label>
<input id="manufacturer" name="manufacturer" value="{{ values.manufacturer }}">

<label for="alternative_names">Nama alternatif</label>
<input id="alternative_names" name="alternative_names" value="{{ values.alternative_names }}">

<label for="stitch_type">Jenis jahitan</label>
<select id="stitch_type" name="stitch_type">
<option value="">Belum ditentukan</option>
{% for option in ["Lockstitch", "Chainstitch"] %}
<option value="{{ option }}" {% if values.stitch_type == option %}selected{% endif %}>{{ option }}</option>
{% endfor %}
</select>

<label for="machine_category">Kategori mesin</label>
<input id="machine_category" name="machine_category" value="{{ values.machine_category }}">

<label for="description">Deskripsi</label>
<textarea id="description" name="description">{{ values.description }}</textarea>

<label for="source_url">Sumber utama (URL)</label>
<input id="source_url" name="source_url" type="url" value="{{ values.source_url }}" placeholder="https://...">

<label for="reference_url">Referensi silang (URL)</label>
<input id="reference_url" name="reference_url" type="url" value="{{ values.reference_url }}" placeholder="https://...">

<label for="verification_notes">Catatan verifikasi</label>
<textarea id="verification_notes" name="verification_notes">{{ values.verification_notes }}</textarea>

<p><strong>Status saat ini:</strong> {{ item["verification_status"] or "Belum diverifikasi" }}</p>
<button type="submit">Simpan Perubahan</button>
</form>
</section>
</main>
</body>
</html>
'''

# Tombol edit khusus admin.
button = '''        {% if session.get("admin_logged_in") %}
        <p>
            <a href="/admin/needle-systems/{{ item['id'] }}/edit"
               style="display:inline-block;padding:9px 14px;background:#075bb5;color:white;border-radius:6px;text-decoration:none;">
                Edit Sistem Jarum
            </a>
        </p>
        {% endif %}
'''

# Letakkan tombol sebelum penutup setiap kartu.
catalog = catalog.replace(
    closing_marker,
    button + closing_marker,
    1
)

app = app.replace(route_marker, route + route_marker, 1)

app_path.write_text(app)
catalog_path.write_text(catalog)
form_path.write_text(template)

print("BERHASIL: route edit ditambahkan.")
print("BERHASIL: tombol edit admin ditambahkan.")
print("BERHASIL: formulir edit dibuat.")
print("Cadangan app.py dan katalog telah dibuat.")
