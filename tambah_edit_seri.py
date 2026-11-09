from pathlib import Path
import re
import shutil
import sys

app_file = Path("app.py")
template_file = Path("templates/needle_series_edit.html")

if not app_file.exists():
    sys.exit("GAGAL: app.py tidak ditemukan.")

if not template_file.exists():
    sys.exit("GAGAL: template edit seri jarum tidak ditemukan.")

source = app_file.read_text()
backup = Path("app.py.backup-before-edit-needle-series-auto")

if 'def edit_needle_series(series_id):' in source:
    sys.exit("Rute edit seri sudah ada. Tidak ada perubahan.")

marker = '@app.route("/needle-systems")'

if source.count(marker) != 1:
    sys.exit("GAGAL: penanda rute katalog tidak ditemukan secara unik.")

csrf_marker = 'or path == "/admin/needle-series"'

if source.count(csrf_marker) != 1:
    sys.exit("GAGAL: pemeriksaan CSRF tidak cocok.")

route = '''

@app.route(
    "/admin/needle-series/<int:series_id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_needle_series(series_id):
    fields = (
        "series_code",
        "series_name",
        "description",
        "verification_notes",
    )

    conn = get_db()
    try:
        item = conn.execute(
            "SELECT * FROM needle_series WHERE id = ?",
            (series_id,),
        ).fetchone()

        if item is None:
            return "Seri jarum tidak ditemukan.", 404

        values = {
            field: (
                request.form.get(field, "").strip()
                if request.method == "POST"
                else (item[field] or "")
            )
            for field in fields
        }
        error = None

        if request.method == "POST":
            code = values["series_code"]
            name = values["series_name"]

            if not code:
                error = "Kode seri wajib diisi."
            elif len(code) > 50:
                error = "Kode seri maksimal 50 karakter."
            elif not name:
                error = "Nama seri wajib diisi."
            elif len(name) > 120:
                error = "Nama seri maksimal 120 karakter."
            else:
                duplicate = conn.execute("""
                    SELECT id FROM needle_series
                    WHERE LOWER(TRIM(series_code)) =
                          LOWER(TRIM(?))
                      AND id != ?
                    LIMIT 1
                """, (code, series_id)).fetchone()

                if duplicate:
                    error = "Kode seri tersebut sudah terdaftar."
                else:
                    conn.execute("""
                        UPDATE needle_series
                        SET series_code = ?,
                            series_name = ?,
                            description = ?,
                            verification_notes = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        code,
                        name,
                        values["description"] or None,
                        values["verification_notes"] or None,
                        series_id,
                    ))
                    conn.commit()
                    return redirect(
                        "/admin/needle-series?edited=1"
                    )

        return render_template(
            "needle_series_edit.html",
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

csrf_addition = '''
        or re.fullmatch(
            r"/admin/needle-series/\\d+/edit",
            path,
        )'''

new_source = source.replace(
    csrf_marker,
    csrf_marker + csrf_addition,
    1,
)
new_source = new_source.replace(
    marker,
    route + "\n" + marker,
    1,
)

try:
    compile(new_source, str(app_file), "exec")
except SyntaxError as exc:
    sys.exit(f"GAGAL: pemeriksaan sintaks: {exc}")

if not backup.exists():
    shutil.copy2(app_file, backup)

app_file.write_text(new_source)

print("BERHASIL: rute edit seri ditambahkan.")
print(f"Cadangan: {backup}")
print("CSRF: rute edit seri ikut dilindungi.")
print("Berikutnya: jalankan python -m py_compile app.py")
