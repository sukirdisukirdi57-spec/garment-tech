from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

app_path = Path("app.py")
tpl_path = Path("templates/component_detail.html")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

app = app_path.read_text(encoding="utf-8")
tpl = tpl_path.read_text(encoding="utf-8")

# Query baru diletakkan sebelum koneksi database ditutup.
app_anchor = '''    conn.close()

    return render_template(
        "component_detail.html",
        component=component,
        sub_parts=sub_parts,
        clamp_d1_parts=clamp_d1_parts,
        clamp_d2_parts=clamp_d2_parts
    )
'''

app_replacement = '''    # Daftar kemunculan part dari katalog resmi JUKI.
    # Data diambil berdasarkan halaman diagram komponen.
    juki_parts = []
    if (
        component["machine_id"] == 43
        and component["diagram_page"] is not None
    ):
        juki_parts = conn.execute(
            """
            SELECT *
            FROM catalog_occurrences
            WHERE machine_id = ?
              AND pdf_page = ?
            ORDER BY CAST(catalog_ref AS INTEGER), id
            """,
            (component["machine_id"], component["diagram_page"])
        ).fetchall()

    conn.close()

    return render_template(
        "component_detail.html",
        component=component,
        sub_parts=sub_parts,
        clamp_d1_parts=clamp_d1_parts,
        clamp_d2_parts=clamp_d2_parts,
        juki_parts=juki_parts
    )
'''

tpl_anchor = '''        {% endif %}


    </section>


    <section class="component-info">
'''

tpl_replacement = '''        {% endif %}

        {% if component["machine_id"] == 43 and juki_parts %}
        <section class="component-info juki-catalog-parts"
                 id="juki-catalog-parts">
            <h2>Daftar Spare Part — PDF {{ component["diagram_page"] }}</h2>
            <p>
                {{ juki_parts|length }} kemunculan part sesuai katalog resmi JUKI.
            </p>
            <div class="component-subparts-wrapper">
                <table class="component-subparts">
                    <thead>
                        <tr>
                            <th>Ref.</th>
                            <th>Part Number</th>
                            <th>Part Name</th>
                            <th>Qty</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for part in juki_parts %}
                        <tr>
                            <td>
                                {{ part["catalog_ref"] }}
                                {% if part["marker"] %}
                                    <span>{{ part["marker"] }}</span>
                                {% endif %}
                            </td>
                            <td><strong>{{ part["part_number"] }}</strong></td>
                            <td>{{ part["part_name"] }}</td>
                            <td>{{ part["quantity_raw"] }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </section>
        {% endif %}

    </section>


    <section class="component-info">
'''

checks = [
    ("app.py route anchor", app.count(app_anchor)),
    ("template diagram anchor", tpl.count(tpl_anchor)),
]

print("=== PEMERIKSAAN ANCHOR ===")
for name, count in checks:
    print(f"{name}: {count}")

if any(count != 1 for _, count in checks):
    print("BATAL: anchor harus ditemukan tepat satu kali. File tidak diubah.")
    sys.exit(1)

# Pastikan tabel katalog sudah tersedia sebelum mengubah kode.
import sqlite3
con = sqlite3.connect("file:database/garment.db?mode=ro", uri=True)
try:
    tables = {
        r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "catalog_occurrences" not in tables:
        print("BATAL: tabel catalog_occurrences tidak ditemukan.")
        sys.exit(1)
finally:
    con.close()

# Backup kedua file terlebih dahulu.
app_backup = Path(f"backups/app_before_juki_parts_{stamp}.py")
tpl_backup = Path(
    f"backups/component_detail_before_juki_parts_{stamp}.html"
)
app_backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(app_path, app_backup)
shutil.copy2(tpl_path, tpl_backup)

new_app = app.replace(app_anchor, app_replacement, 1)
new_tpl = tpl.replace(tpl_anchor, tpl_replacement, 1)

try:
    app_path.write_text(new_app, encoding="utf-8")
    tpl_path.write_text(new_tpl, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", "app.py"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

except Exception as exc:
    shutil.copy2(app_backup, app_path)
    shutil.copy2(tpl_backup, tpl_path)
    print("PATCH GAGAL; kedua file dipulihkan dari backup.")
    print(exc)
    sys.exit(1)

print("\nPATCH BERHASIL.")
print("Backup app:", app_backup)
print("Backup template:", tpl_backup)
print("app.py lolos pemeriksaan sintaks Python.")
print("Tabel JUKI hanya aktif untuk machine_id 43.")
