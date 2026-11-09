from pathlib import Path
from datetime import datetime
import shutil

app_path = Path("app.py")
template_path = Path("templates/needle_series_admin.html")

app = app_path.read_text(encoding="utf-8")

csrf_old = '''        or path == "/admin/needle-systems/add"
        or re.fullmatch('''

csrf_new = '''        or path == "/admin/needle-systems/add"
        or path == "/admin/needle-series"
        or re.fullmatch('''

route_marker = '''@app.route("/needle-systems")
def needle_systems_catalog():'''

route_code = '''@app.route("/admin/needle-series", methods=["GET", "POST"])
@admin_required
def manage_needle_series():
    fields = (
        "series_code",
        "series_name",
        "description",
        "verification_notes",
    )

    values = {
        field: request.form.get(field, "").strip()
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
            conn = get_db()
            try:
                duplicate = conn.execute("""
                    SELECT id FROM needle_series
                    WHERE LOWER(TRIM(series_code)) =
                          LOWER(TRIM(?))
                    LIMIT 1
                """, (code,)).fetchone()

                if duplicate:
                    error = "Kode seri tersebut sudah terdaftar."
                else:
                    conn.execute("""
                        INSERT INTO needle_series (
                            series_code,
                            series_name,
                            description,
                            verification_status,
                            verification_notes
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        code,
                        name,
                        values["description"] or None,
                        "Perlu diverifikasi",
                        values["verification_notes"] or (
                            "Seri baru ditambahkan melalui admin. "
                            "Periksa referensi resmi sebelum "
                            "menetapkan status verifikasi."
                        ),
                    ))
                    conn.commit()
                    return redirect("/admin/needle-series?added=1")
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    conn = get_db()
    try:
        series = conn.execute("""
            SELECT
                s.id,
                s.series_code,
                s.series_name,
                s.description,
                s.verification_status,
                s.verification_notes,
                COUNT(ns.id) AS system_count
            FROM needle_series s
            LEFT JOIN needle_systems ns
                ON ns.series_id = s.id
            GROUP BY s.id
            ORDER BY s.series_code
        """).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_series_admin.html",
        series=series,
        values=values,
        error=error,
        added=request.args.get("added") == "1",
    )


'''

if app.count(csrf_old) != 1:
    raise SystemExit(
        "GAGAL: pola pemeriksaan CSRF tidak ditemukan "
        "tepat satu kali. app.py tidak diubah."
    )

if route_marker not in app:
    raise SystemExit(
        "GAGAL: lokasi pemasangan route tidak ditemukan. "
        "app.py tidak diubah."
    )

if 'def manage_needle_series():' in app:
    raise SystemExit(
        "Route master seri tampaknya sudah ada. "
        "Tidak ada perubahan dilakukan."
    )

if not template_path.parent.exists():
    raise SystemExit("Folder templates tidak ditemukan.")

backup = app_path.with_name(
    "app.py.backup-master-seri-" +
    datetime.now().strftime("%Y%m%d-%H%M%S")
)
shutil.copy2(app_path, backup)

app = app.replace(csrf_old, csrf_new, 1)
app = app.replace(route_marker, route_code + route_marker, 1)
app_path.write_text(app, encoding="utf-8")

template = r'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Master Seri Jarum | Garment Tech</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 16px;
            background: #f3f5f7;
            color: #222;
            line-height: 1.6;
        }
        main {
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 22px;
            border-radius: 10px;
            box-shadow: 0 2px 7px rgba(0,0,0,.08);
        }
        h1 { font-size: 25px; }
        h2 { font-size: 20px; margin-top: 28px; }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .field { margin: 15px 0; }
        input, textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 11px;
            border: 1px solid #bbb;
            border-radius: 6px;
            font-size: 16px;
            font-family: inherit;
        }
        textarea { min-height: 80px; }
        button {
            padding: 12px 18px;
            border: 0;
            border-radius: 6px;
            background: #075bb5;
            color: white;
            font-size: 16px;
        }
        .notice {
            padding: 12px;
            border-radius: 6px;
            background: #eef5ff;
            margin: 12px 0;
        }
        .error { background: #fff0f0; color: #8b1515; }
        .entry {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 14px;
            margin: 12px 0;
        }
        .muted { color: #555; font-size: 14px; }
        a { color: #075bb5; }
    </style>
</head>
<body>
<main>
    <a href="/needle-systems">← Katalog sistem jarum</a>
    <h1>🪡 Master Seri Jarum</h1>
    <p>
        Daftar seri dikelola terpisah dari sistem jarum dan ukuran
        jarum. Seri baru otomatis berstatus Perlu diverifikasi.
    </p>

    {% if added %}
    <div class="notice" role="status">
        Seri jarum berhasil ditambahkan.
    </div>
    {% endif %}

    {% if error %}
    <div class="notice error" role="alert">{{ error }}</div>
    {% endif %}

    <h2>Tambah seri baru</h2>
    <form method="post">
        <input type="hidden" name="_csrf_token"
               value="{{ csrf_token() }}">

        <div class="field">
            <label for="series_code">Kode seri *</label>
            <input id="series_code" name="series_code"
                   maxlength="50" required
                   value="{{ values.get('series_code', '') }}"
                   placeholder="Contoh: DB">
        </div>

        <div class="field">
            <label for="series_name">Nama seri *</label>
            <input id="series_name" name="series_name"
                   maxlength="120" required
                   value="{{ values.get('series_name', '') }}"
                   placeholder="Contoh: Seri DB">
        </div>

        <div class="field">
            <label for="description">Deskripsi</label>
            <textarea id="description" name="description"
                      placeholder="Keterangan seri berdasarkan referensi">{{ values.get('description', '') }}</textarea>
        </div>

        <div class="field">
            <label for="verification_notes">Catatan verifikasi</label>
            <textarea id="verification_notes"
                      name="verification_notes"
                      placeholder="Sumber atau hal yang perlu diperiksa">{{ values.get('verification_notes', '') }}</textarea>
        </div>

        <button type="submit">Simpan Seri</button>
    </form>

    <h2>Daftar seri tersimpan ({{ series|length }})</h2>
    {% for item in series %}
    <section class="entry">
        <strong>{{ item["series_code"] }}</strong>
        — {{ item["series_name"] }}
        <p class="muted">
            Status: {{ item["verification_status"] }}
            <br>
            Sistem jarum terhubung: {{ item["system_count"] }}
        </p>
        {% if item["description"] %}
        <p>{{ item["description"] }}</p>
        {% endif %}
        {% if item["verification_notes"] %}
        <p class="muted">{{ item["verification_notes"] }}</p>
        {% endif %}
    </section>
    {% else %}
    <p>Belum ada seri yang tersimpan.</p>
    {% endfor %}
</main>
</body>
</html>
'''

template_path.write_text(template, encoding="utf-8")

print("Pemasangan selesai.")
print("Cadangan app.py:", backup)
print("Template dibuat:", template_path)
