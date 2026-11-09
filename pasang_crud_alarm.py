from pathlib import Path
from datetime import datetime
import sqlite3
import shutil
import py_compile
import os
import re
import sys

ROOT = Path.cwd()
APP = ROOT / "app.py"
DETAIL = ROOT / "templates" / "machine_detail.html"
FORM = ROOT / "templates" / "machine_alarm_form.html"
DB = ROOT / "database" / "garment.db"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = ROOT / "backup" / f"sebelum-crud-alarm-{stamp}"

files = [APP, DETAIL]
if not all(p.is_file() for p in files):
    sys.exit("GAGAL: app.py atau machine_detail.html tidak ditemukan.")
if not DB.is_file():
    sys.exit("GAGAL: database/garment.db tidak ditemukan.")
if FORM.exists():
    sys.exit("BERHENTI: machine_alarm_form.html sudah ada. Periksa dahulu.")

# Pemeriksaan struktur database sebelum perubahan
conn = sqlite3.connect(DB)
try:
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(machine_alarms)")
    }
    required = {
        "id", "machine_id", "alarm_code", "alarm_name",
        "possible_cause", "solution", "manual_title",
        "manual_version", "manual_chapter", "manual_page",
        "source_url", "source_note"
    }
    if integrity != "ok" or not required.issubset(columns):
        sys.exit("GAGAL: integritas atau struktur tabel machine_alarms tidak sesuai.")
    before_count = conn.execute(
        "SELECT COUNT(*) FROM machine_alarms"
    ).fetchone()[0]
    before_troubleshooting = conn.execute(
        "SELECT COUNT(*) FROM troubleshooting"
    ).fetchone()[0]
finally:
    conn.close()

app_text = APP.read_text()
detail_text = DETAIL.read_text()

csrf_anchor = '''        or re.fullmatch(
            r"/admin/needle-systems/\\d+/(?:edit|delete)",
            path,
        )
'''
detail_heading = '<h2>🚨 Alarm Resmi Mesin</h2>'
alarm_heading = '<h3>{{ alarm["alarm_code"] }} — {{ alarm["alarm_name"] }}</h3>'
route_anchor = '@app.route("/specifications")'

if app_text.count(csrf_anchor) != 1:
    sys.exit("GAGAL: bagian CSRF tidak cocok atau jumlahnya bukan satu.")
if detail_text.count(detail_heading) != 1:
    sys.exit("GAGAL: judul bagian Alarm Resmi tidak ditemukan tepat satu kali.")
if detail_text.count(alarm_heading) != 1:
    sys.exit("GAGAL: judul kartu alarm tidak ditemukan tepat satu kali.")
if app_text.count(route_anchor) != 1:
    sys.exit("GAGAL: lokasi pemasangan route tidak ditemukan tepat satu kali.")

# Siapkan backup sebelum mengubah file apa pun
backup.mkdir(parents=True, exist_ok=False)
shutil.copy2(APP, backup / "app.py")
shutil.copy2(DETAIL, backup / "machine_detail.html")

source = sqlite3.connect(DB)
target = sqlite3.connect(backup / "garment.db")
try:
    source.backup(target)
finally:
    target.close()
    source.close()

check = sqlite3.connect(backup / "garment.db")
try:
    if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("Backup database tidak lolos integrity_check.")
finally:
    check.close()

routes = r'''
@app.route("/admin/machine-alarms/add/<int:machine_id>", methods=["GET", "POST"])
@admin_required
def add_machine_alarm(machine_id):
    conn = get_db()
    try:
        machine = conn.execute(
            "SELECT * FROM machines WHERE id = ?", (machine_id,)
        ).fetchone()
        if machine is None:
            return "Mesin tidak ditemukan.", 404

        error = None
        if request.method == "POST":
            data = {
                "alarm_code": request.form.get("alarm_code", "").strip(),
                "alarm_name": request.form.get("alarm_name", "").strip(),
                "possible_cause": request.form.get("possible_cause", "").strip(),
                "solution": request.form.get("solution", "").strip(),
                "manual_title": request.form.get("manual_title", "").strip(),
                "manual_version": request.form.get("manual_version", "").strip(),
                "manual_chapter": request.form.get("manual_chapter", "").strip(),
                "source_url": request.form.get("source_url", "").strip(),
                "source_note": request.form.get("source_note", "").strip(),
            }
            page_text = request.form.get("manual_page", "").strip()

            if not data["alarm_code"] or not data["alarm_name"] or not data["manual_title"]:
                error = "Kode alarm, nama alarm, dan judul manual wajib diisi."
            else:
                try:
                    manual_page = int(page_text) if page_text else None
                    if manual_page is not None and manual_page < 1:
                        raise ValueError
                except ValueError:
                    error = "Nomor halaman harus berupa bilangan bulat positif."

            if error is None:
                try:
                    conn.execute(
                        """
                        INSERT INTO machine_alarms (
                            machine_id, alarm_code, alarm_name,
                            possible_cause, solution, manual_title,
                            manual_version, manual_chapter, manual_page,
                            source_url, source_note
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            machine_id, data["alarm_code"], data["alarm_name"],
                            data["possible_cause"], data["solution"],
                            data["manual_title"], data["manual_version"],
                            data["manual_chapter"], manual_page,
                            data["source_url"], data["source_note"],
                        ),
                    )
                    conn.commit()
                    return redirect(f"/machine/{machine_id}#official-alarms")
                except sqlite3.IntegrityError:
                    error = "Kode alarm tersebut sudah tercatat untuk mesin ini."

            return render_template(
                "machine_alarm_form.html", machine=machine, alarm=data,
                error=error, form_title="Tambah Alarm Resmi",
                submit_label="Simpan Alarm"
            ), 400

        return render_template(
            "machine_alarm_form.html", machine=machine, alarm=None,
            error=None, form_title="Tambah Alarm Resmi",
            submit_label="Simpan Alarm"
        )
    finally:
        conn.close()


@app.route("/admin/machine-alarms/<int:alarm_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_machine_alarm(alarm_id):
    conn = get_db()
    try:
        alarm = conn.execute(
            "SELECT * FROM machine_alarms WHERE id = ?", (alarm_id,)
        ).fetchone()
        if alarm is None:
            return "Alarm tidak ditemukan.", 404

        machine = conn.execute(
            "SELECT * FROM machines WHERE id = ?", (alarm["machine_id"],)
        ).fetchone()
        if machine is None:
            return "Mesin tidak ditemukan.", 404

        error = None
        if request.method == "POST":
            data = {
                "alarm_code": request.form.get("alarm_code", "").strip(),
                "alarm_name": request.form.get("alarm_name", "").strip(),
                "possible_cause": request.form.get("possible_cause", "").strip(),
                "solution": request.form.get("solution", "").strip(),
                "manual_title": request.form.get("manual_title", "").strip(),
                "manual_version": request.form.get("manual_version", "").strip(),
                "manual_chapter": request.form.get("manual_chapter", "").strip(),
                "source_url": request.form.get("source_url", "").strip(),
                "source_note": request.form.get("source_note", "").strip(),
            }
            page_text = request.form.get("manual_page", "").strip()

            if not data["alarm_code"] or not data["alarm_name"] or not data["manual_title"]:
                error = "Kode alarm, nama alarm, dan judul manual wajib diisi."
            else:
                try:
                    manual_page = int(page_text) if page_text else None
                    if manual_page is not None and manual_page < 1:
                        raise ValueError
                except ValueError:
                    error = "Nomor halaman harus berupa bilangan bulat positif."

            if error is None:
                try:
                    conn.execute(
                        """
                        UPDATE machine_alarms SET
                            alarm_code = ?, alarm_name = ?,
                            possible_cause = ?, solution = ?,
                            manual_title = ?, manual_version = ?,
                            manual_chapter = ?, manual_page = ?,
                            source_url = ?, source_note = ?
                        WHERE id = ?
                        """,
                        (
                            data["alarm_code"], data["alarm_name"],
                            data["possible_cause"], data["solution"],
                            data["manual_title"], data["manual_version"],
                            data["manual_chapter"], manual_page,
                            data["source_url"], data["source_note"], alarm_id,
                        ),
                    )
                    conn.commit()
                    return redirect(
                        f"/machine/{alarm['machine_id']}#official-alarms"
                    )
                except sqlite3.IntegrityError:
                    error = "Kode alarm tersebut sudah digunakan pada mesin ini."

            alarm = data.copy()
            alarm["manual_page"] = page_text
            return render_template(
                "machine_alarm_form.html", machine=machine, alarm=alarm,
                error=error, form_title="Edit Alarm Resmi",
                submit_label="Simpan Perubahan"
            ), 400

        return render_template(
            "machine_alarm_form.html", machine=machine, alarm=alarm,
            error=None, form_title="Edit Alarm Resmi",
            submit_label="Simpan Perubahan"
        )
    finally:
        conn.close()


@app.route("/admin/machine-alarms/<int:alarm_id>/delete", methods=["POST"])
@admin_required
def delete_machine_alarm(alarm_id):
    conn = get_db()
    try:
        alarm = conn.execute(
            "SELECT machine_id FROM machine_alarms WHERE id = ?",
            (alarm_id,)
        ).fetchone()
        if alarm is None:
            return "Alarm tidak ditemukan.", 404

        machine_id = alarm["machine_id"]
        conn.execute("DELETE FROM machine_alarms WHERE id = ?", (alarm_id,))
        conn.commit()
        return redirect(f"/machine/{machine_id}#official-alarms")
    finally:
        conn.close()


'''

form_template = r'''{% extends "base.html" %}
{% block content %}
<div class="container">
    <h2>{{ form_title }}</h2>
    <p>Mesin: <strong>{{ machine["model"] }}</strong></p>

    {% if error %}
        <p style="color: #b00020;"><strong>{{ error }}</strong></p>
    {% endif %}

    <form method="POST">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">

        <label>Kode alarm *</label>
        <input type="text" name="alarm_code" required
               value="{{ alarm['alarm_code'] if alarm else '' }}">

        <label>Nama alarm *</label>
        <input type="text" name="alarm_name" required
               value="{{ alarm['alarm_name'] if alarm else '' }}">

        <label>Kemungkinan penyebab</label>
        <textarea name="possible_cause" rows="4">{{ alarm['possible_cause'] if alarm else '' }}</textarea>

        <label>Solusi / tindakan</label>
        <textarea name="solution" rows="5">{{ alarm['solution'] if alarm else '' }}</textarea>

        <label>Judul manual *</label>
        <input type="text" name="manual_title" required
               value="{{ alarm['manual_title'] if alarm else '' }}">

        <label>Versi manual</label>
        <input type="text" name="manual_version"
               value="{{ alarm['manual_version'] if alarm else '' }}">

        <label>Bab manual</label>
        <input type="text" name="manual_chapter"
               value="{{ alarm['manual_chapter'] if alarm else '' }}">

        <label>Halaman manual</label>
        <input type="number" min="1" name="manual_page"
               value="{{ alarm['manual_page'] if alarm and alarm['manual_page'] is not none else '' }}">

        <label>URL sumber manual</label>
        <input type="url" name="source_url"
               value="{{ alarm['source_url'] if alarm else '' }}">

        <label>Catatan sumber</label>
        <textarea name="source_note" rows="3">{{ alarm['source_note'] if alarm else '' }}</textarea>

        <button type="submit">{{ submit_label }}</button>
        <a href="/machine/{{ machine['id'] }}#official-alarms">Batal</a>
    </form>
</div>
{% endblock %}
'''

try:
    # Tambahkan perlindungan CSRF untuk ketiga pola route alarm.
    new_csrf = csrf_anchor + '''        or re.fullmatch(
            r"/admin/machine-alarms/add/\\d+",
            path,
        )
        or re.fullmatch(
            r"/admin/machine-alarms/\\d+/(?:edit|delete)",
            path,
        )
'''
    app_text = app_text.replace(csrf_anchor, new_csrf, 1)

    # Sisipkan route setelah fungsi detail mesin.
    app_text = app_text.replace(route_anchor, routes + route_anchor, 1)

    # Tombol tambah hanya terlihat oleh admin.
    detail_text = detail_text.replace(
        detail_heading,
        detail_heading + '''
        {% if session.get("admin_logged_in") %}
        <p><a href="/admin/machine-alarms/add/{{ machine['id'] }}">+ Tambah Alarm Resmi</a></p>
        {% endif %}''',
        1
    )

    # Tombol edit dan hapus di setiap kartu alarm.
    detail_text = detail_text.replace(
        alarm_heading,
        alarm_heading + '''
                {% if session.get("admin_logged_in") %}
                <p>
                    <a href="/admin/machine-alarms/{{ alarm['id'] }}/edit">Edit</a>
                </p>
                <form method="POST"
                      action="/admin/machine-alarms/{{ alarm['id'] }}/delete"
                      onsubmit="return confirm('Hapus alarm resmi ini?');">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
                    <button type="submit">Hapus Alarm</button>
                </form>
                {% endif %}''',
        1
    )

    # Tulis file setelah semua pemeriksaan anchor berhasil.
    temp_app = APP.with_suffix(".py.tmp")
    temp_detail = DETAIL.with_suffix(".html.tmp")
    temp_app.write_text(app_text)
    temp_detail.write_text(detail_text)
    FORM.write_text(form_template)
    os.replace(temp_app, APP)
    os.replace(temp_detail, DETAIL)

    py_compile.compile(str(APP), doraise=True)

    # Pemeriksaan ulang database: tidak boleh ada data yang berubah.
    conn = sqlite3.connect(DB)
    try:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Integritas database gagal.")
        after_count = conn.execute(
            "SELECT COUNT(*) FROM machine_alarms"
        ).fetchone()[0]
        after_troubleshooting = conn.execute(
            "SELECT COUNT(*) FROM troubleshooting"
        ).fetchone()[0]
        if after_count != before_count:
            raise RuntimeError("Jumlah alarm berubah saat pemasangan.")
        if after_troubleshooting != before_troubleshooting:
            raise RuntimeError("Jumlah troubleshooting berubah.")
    finally:
        conn.close()

    print("\nPEMASANGAN CRUD ALARM BERHASIL")
    print("Backup:", backup.relative_to(ROOT))
    print("Kompilasi app.py: OK")
    print("Template formulir: dibuat")
    print("Perlindungan CSRF: ditambahkan")
    print("Jumlah alarm tetap:", after_count)
    print("Jumlah troubleshooting tetap:", after_troubleshooting)
    print("Database integrity: ok")

except Exception as exc:
    print("\nPEMASANGAN GAGAL:", exc)
    print("Memulihkan file aplikasi dari backup...")
    if (backup / "app.py").exists():
        shutil.copy2(backup / "app.py", APP)
    if (backup / "machine_detail.html").exists():
        shutil.copy2(backup / "machine_detail.html", DETAIL)
    if FORM.exists():
        FORM.unlink()
    print("Pemulihan file selesai. Backup:", backup)
    raise
