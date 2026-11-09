from pathlib import Path
import sqlite3
import shutil
import sys

root = Path.cwd()
app_path = root / "app.py"
detail_path = root / "templates/needle_detail.html"
edit_path = root / "templates/needle_edit.html"
db_path = root / "database/garment.db"

app = app_path.read_text()
detail = detail_path.read_text()

if "def edit_needle(" in app:
    print("BERHENTI: route edit_needle sudah ada. Tidak ada perubahan.")
    sys.exit(1)

marker = '\nif __name__ == "__main__":'
if marker not in app:
    print("BERHENTI: titik pemasangan route tidak ditemukan.")
    sys.exit(1)

if "verification_notes" in app or "verified_at" in app:
    print("BERHENTI: sebagian perubahan verifikasi tampaknya sudah ada.")
    sys.exit(1)

if "session.get('admin_logged_in')" not in app and 'session.get("admin_logged_in")' not in app:
    print("PERINGATAN: pastikan session admin tersedia sebelum melanjutkan.")

backup_dir = root / "backups"
backup_dir.mkdir(exist_ok=True)
for source in (app_path, detail_path, db_path):
    target = backup_dir / (source.name + ".before-needle-edit-v2")
    if target.exists():
        print(f"Backup sudah ada, tidak ditimpa: {target}")
    else:
        shutil.copy2(source, target)
        print(f"Backup: {target}")

route = r'''

@app.route("/admin/needle/<int:needle_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_needle(needle_id):
    conn = get_db()
    try:
        needle = conn.execute(
            "SELECT * FROM needles WHERE id = ?", (needle_id,)
        ).fetchone()

        if needle is None:
            return "Data jarum tidak ditemukan.", 404

        if request.method == "POST":
            fields = (
                "brand", "needle_system", "size_nm", "point_code",
                "point_description", "material_application", "product_code",
                "description", "source_url", "verification_status",
            )
            values = {
                field: request.form.get(field, "").strip()
                for field in fields
            }
            notes = request.form.get("verification_notes", "").strip()
            status = values["verification_status"]

            if status not in ("Belum diverifikasi", "Terverifikasi"):
                return "Status verifikasi tidak valid.", 400

            if status == "Terverifikasi" and (
                not values["source_url"] or not notes
            ):
                return (
                    "Untuk memverifikasi data, URL sumber dan catatan bukti "
                    "verifikasi wajib diisi.",
                    400,
                )

            nm_text = request.form.get("size_nm_value", "").strip()
            manufacturer_size = request.form.get(
                "manufacturer_size", ""
            ).strip()
            nm_value = None
            if nm_text:
                try:
                    nm_value = float(nm_text.replace(",", "."))
                except ValueError:
                    return "Ukuran NM harus berupa angka.", 400
                if not 1 <= nm_value <= 500:
                    return "Periksa kembali ukuran NM.", 400

            old_status = needle["verification_status"]
            verified_at = needle["verified_at"]

            if status == "Terverifikasi":
                if old_status != "Terverifikasi" or not verified_at:
                    verified_at = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
            else:
                verified_at = None

            conn.execute("""
                UPDATE needles SET
                    brand = ?, needle_system = ?, size_nm = ?,
                    point_code = ?, point_description = ?,
                    material_application = ?, product_code = ?,
                    description = ?, source_url = ?,
                    verification_status = ?, size_nm_value = ?,
                    manufacturer_size = ?, verification_notes = ?,
                    verified_at = ?
                WHERE id = ?
            """, (
                values["brand"] or None,
                values["needle_system"] or None,
                values["size_nm"] or None,
                values["point_code"] or None,
                values["point_description"] or None,
                values["material_application"] or None,
                values["product_code"] or None,
                values["description"] or None,
                values["source_url"] or None,
                status,
                nm_value,
                manufacturer_size or None,
                notes or None,
                verified_at,
                needle_id,
            ))
            conn.commit()
            return redirect(f"/needle/{needle_id}")

        return render_template("needle_edit.html", needle=needle)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
'''
app = app.replace(marker, route + marker, 1)

if "from flask import" not in app:
    print("BERHENTI: import Flask tidak ditemukan.")
    sys.exit(1)

edit_template = r'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Edit Data Jarum | GarmentTech</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body class="needle-catalog-page">
<header>
    <h1>Edit Data Jarum</h1>
    <p>Garment Machine Tech Database</p>
</header>
<main class="needle-main">
    <nav class="needle-nav">
        <a href="/needle/{{ needle['id'] }}">← Kembali ke detail jarum</a>
        <a href="/needle-catalog">Katalog Jarum</a>
    </nav>
    <section class="needle-panel">
        <p>Isi berdasarkan referensi yang dapat diperiksa. Jangan mengubah status menjadi Terverifikasi tanpa bukti yang jelas.</p>
        <form method="post" class="needle-form">
            <label>Merek jarum
                <input name="brand" maxlength="120" value="{{ needle['brand'] or '' }}">
            </label>
            <label>Sistem jarum
                <input name="needle_system" maxlength="120" value="{{ needle['needle_system'] or '' }}">
            </label>
            <label>Ukuran NM (angka)
                <input name="size_nm_value" type="number" min="1" max="500" step="any"
                       value="{{ needle['size_nm_value'] if needle['size_nm_value'] is not none else '' }}">
            </label>
            <label>Nomor ukuran dari produsen
                <input name="manufacturer_size" maxlength="80" value="{{ needle['manufacturer_size'] or '' }}">
            </label>
            <label>Ukuran asli dari data
                <input name="size_nm" maxlength="120" value="{{ needle['size_nm'] or '' }}">
            </label>
            <label>Kode ujung
                <input name="point_code" maxlength="80" value="{{ needle['point_code'] or '' }}">
            </label>
            <label>Deskripsi ujung
                <input name="point_description" maxlength="200" value="{{ needle['point_description'] or '' }}">
            </label>
            <label>Bahan / aplikasi
                <input name="material_application" maxlength="200" value="{{ needle['material_application'] or '' }}">
            </label>
            <label>Kode produk
                <input name="product_code" maxlength="120" value="{{ needle['product_code'] or '' }}">
            </label>
            <label>Keterangan
                <textarea name="description" rows="4" maxlength="2000">{{ needle['description'] or '' }}</textarea>
            </label>
            <label>URL sumber data jarum
                <input type="url" name="source_url" maxlength="1000" value="{{ needle['source_url'] or '' }}">
            </label>
            <label>Status verifikasi
                <select name="verification_status">
                    <option value="Belum diverifikasi" {% if needle['verification_status'] != 'Terverifikasi' %}selected{% endif %}>Belum diverifikasi</option>
                    <option value="Terverifikasi" {% if needle['verification_status'] == 'Terverifikasi' %}selected{% endif %}>Terverifikasi</option>
                </select>
            </label>
            <label>Catatan bukti verifikasi
                <textarea name="verification_notes" rows="4" maxlength="2000">{{ needle['verification_notes'] or '' }}</textarea>
            </label>
            <p class="needle-help">Jika memilih Terverifikasi, isi URL sumber dan catatan yang menjelaskan apa yang diperiksa, misalnya nomor halaman katalog atau spesifikasi yang cocok.</p>
            <button type="submit">Simpan Perubahan</button>
        </form>
    </section>
</main>
</body>
</html>
'''

if "verification_notes" not in detail:
    old = '''        <p class="needle-muted">Dibuat: {{ needle['created_at'] }}</p>'''
    new = '''        {% if needle['verification_notes'] %}
        <p><strong>Bukti verifikasi:</strong> {{ needle['verification_notes'] }}</p>
        {% endif %}
        {% if needle['verified_at'] %}
        <p><strong>Waktu verifikasi:</strong> {{ needle['verified_at'] }}</p>
        {% endif %}
        {% if session.get('admin_logged_in') %}
        <p><a href="/admin/needle/{{ needle['id'] }}/edit">Edit data jarum (admin)</a></p>
        {% endif %}
        <p class="needle-muted">Dibuat: {{ needle['created_at'] }}</p>'''
    if old not in detail:
        print("BERHENTI: lokasi penyisipan di template detail tidak ditemukan.")
        sys.exit(1)
    detail = detail.replace(old, new, 1)

# Pastikan database mendukung kolom yang dipakai route.
con = sqlite3.connect(db_path)
try:
    cols = {r[1] for r in con.execute("PRAGMA table_info(needles)")}
    if "verification_notes" not in cols:
        con.execute("ALTER TABLE needles ADD COLUMN verification_notes TEXT")
    if "verified_at" not in cols:
        con.execute("ALTER TABLE needles ADD COLUMN verified_at TEXT")
    con.commit()
finally:
    con.close()

app_path.write_text(app)
detail_path.write_text(detail)
edit_path.write_text(edit_template)

print("Patch ditulis.")
