from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

app_path = Path("app.py")
template_path = Path("templates/needle_systems.html")

if not app_path.is_file() or not template_path.is_file():
    sys.exit("GAGAL: app.py atau template katalog tidak ditemukan.")

app_text = app_path.read_text(encoding="utf-8")
html_text = template_path.read_text(encoding="utf-8")

# 1. Ganti route katalog agar membaca relasi master seri dari database.
old_route = '''@app.route("/needle-systems")
def needle_systems_catalog():
    conn = get_db()
    try:
        systems = conn.execute("""
            SELECT *
            FROM needle_systems
            ORDER BY manufacturer, system_code
        """).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_systems.html",
        systems=systems
    )
'''

new_route = '''@app.route("/needle-systems")
def needle_systems_catalog():
    conn = get_db()
    try:
        systems = conn.execute("""
            SELECT ns.*,
                   s.series_code AS master_series_code,
                   s.series_name AS master_series_name
            FROM needle_systems AS ns
            LEFT JOIN needle_series AS s
                ON ns.series_id = s.id
            ORDER BY ns.manufacturer, ns.system_code
        """).fetchall()

        series = conn.execute("""
            SELECT series_code, series_name
            FROM needle_series
            ORDER BY series_code COLLATE NOCASE
        """).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_systems.html",
        systems=systems,
        series=series
    )
'''

if app_text.count(old_route) != 1:
    sys.exit(
        "GAGAL: route katalog tidak cocok persis atau jumlahnya bukan satu. "
        "Tidak ada file yang diubah."
    )

new_app = app_text.replace(old_route, new_route, 1)

# 2. Isi pilihan filter seri dari tabel master seri.
old_select = '''            <select id="seriesFilter"
                    style="width:100%;box-sizing:border-box;padding:12px;border:1px solid #bbb;border-radius:6px;font-size:16px;">
                <option value="">Semua seri</option>
            </select>'''

new_select = '''            <select id="seriesFilter"
                    style="width:100%;box-sizing:border-box;padding:12px;border:1px solid #bbb;border-radius:6px;font-size:16px;">
                <option value="">Semua seri</option>
                {% for item in series %}
                <option value="{{ item['series_code']|lower }}">
                    {{ item["series_code"] }} — {{ item["series_name"] }}
                </option>
                {% endfor %}
            </select>'''

if html_text.count(old_select) != 1:
    sys.exit(
        "GAGAL: bagian pilihan filter seri tidak cocok persis. "
        "Tidak ada file yang diubah."
    )

new_html = html_text.replace(old_select, new_select, 1)

# 3. Tambahkan tautan pengelolaan master seri di area admin.
old_admin_link = '''            + Tambah Sistem Jarum
        </a>
    </p>'''

new_admin_link = '''            + Tambah Sistem Jarum
        </a>
        <a href="/admin/needle-series"
           style="display:inline-block;padding:10px 14px;background:#17652b;color:white;border-radius:6px;text-decoration:none;margin-left:6px;">
            Kelola Master Seri
        </a>
    </p>'''

if new_html.count(old_admin_link) != 1:
    sys.exit(
        "GAGAL: lokasi tautan admin tidak cocok persis. "
        "Tidak ada file yang diubah."
    )

new_html = new_html.replace(old_admin_link, new_admin_link, 1)

# 4. Simpan kode master seri pada kartu masing-masing sistem jarum.
old_article = '    <article class="system-card">\n        <h2>{{ item["system_code"] }}</h2>'

new_article = '''    <article class="system-card"
             data-series-code="{{ item['master_series_code'] or '' }}">
        <h2>{{ item["system_code"] }}</h2>'''

if new_html.count(old_article) != 1:
    sys.exit(
        "GAGAL: bagian kartu sistem jarum tidak cocok persis. "
        "Tidak ada file yang diubah."
    )

new_html = new_html.replace(old_article, new_article, 1)

# 5. Hapus fungsi tebakan seri berdasarkan awalan kode.
pattern_function = re.compile(
    r'    function getNeedleSeries\(code\) \{.*?'
    r'    const resultText = document\.getElementById\("searchResult"\);',
    re.S
)

replacement_function = (
    '    const resultText = document.getElementById("searchResult");'
)

new_html, function_count = pattern_function.subn(
    replacement_function, new_html, count=1
)

if function_count != 1:
    sys.exit(
        "GAGAL: fungsi getNeedleSeries tidak ditemukan dengan pola yang "
        "diharapkan. Tidak ada file yang diubah."
    )

# 6. Hapus pembuatan opsi seri dari JavaScript.
pattern_options = re.compile(
    r'    // Isi pilihan seri berdasarkan kode sistem yang ada pada kartu\.\n'
    r'    const seriesOptions = new Map\(\);.*?'
    r'    function filterNeedles\(\) \{',
    re.S
)

new_html, options_count = pattern_options.subn(
    '    function filterNeedles() {', new_html, count=1
)

if options_count != 1:
    sys.exit(
        "GAGAL: blok pembuatan opsi seri tidak ditemukan. "
        "Tidak ada file yang diubah."
    )

# 7. Filter kartu berdasarkan nilai relasi master seri.
old_card_series = (
    '            const code = card.querySelector("h2")?.textContent || "";\n'
    '            const cardSeries = getNeedleSeries(code).toLocaleLowerCase("id");'
)

new_card_series = (
    '            const cardSeries = (card.dataset.seriesCode || "")'
    '.trim().toLocaleLowerCase("id");'
)

if new_html.count(old_card_series) != 1:
    sys.exit(
        "GAGAL: bagian pencocokan seri pada filter tidak cocok. "
        "Tidak ada file yang diubah."
    )

new_html = new_html.replace(old_card_series, new_card_series, 1)

# Semua pemeriksaan harus lolos sebelum membuat cadangan dan menulis file.
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
app_backup = app_path.with_name(f"app.py.backup-filter-seri-{stamp}")
html_backup = template_path.with_name(
    f"needle_systems.html.backup-filter-seri-{stamp}"
)

shutil.copy2(app_path, app_backup)
shutil.copy2(template_path, html_backup)

try:
    app_path.write_text(new_app, encoding="utf-8")
    template_path.write_text(new_html, encoding="utf-8")
except Exception as exc:
    shutil.copy2(app_backup, app_path)
    shutil.copy2(html_backup, template_path)
    sys.exit(f"GAGAL menyimpan perubahan; file dipulihkan dari cadangan: {exc}")

print("Pemasangan filter master seri selesai.")
print(f"Cadangan app.py: {app_backup}")
print(f"Cadangan template: {html_backup}")
print("Filter seri sekarang membaca tabel needle_series.")
print("Data jarum tidak diubah oleh skrip pemasangan ini.")
