from pathlib import Path
from datetime import datetime
import shutil
import sys

path = Path("templates/component_detail.html")

if not path.is_file():
    sys.exit(f"GAGAL: file tidak ditemukan: {path}")

source = path.read_text(encoding="utf-8")

# Cegah tabel ditambahkan dua kali.
if 'id="brother-catalog-parts"' in source:
    sys.exit("Tidak ada perubahan: tabel Brother sudah ada.")

# Pastikan blok katalog JUKI ditemukan.
juki_end = '''        {% endif %}

    </section>
'''

marker = 'id="juki-catalog-parts"'
pos = source.find(marker)

if pos == -1:
    sys.exit("GAGAL: blok katalog JUKI tidak ditemukan.")

end = source.find(juki_end, pos)

if end == -1:
    sys.exit(
        "GAGAL: batas blok JUKI tidak cocok. "
        "Template belum diubah."
    )

insert_at = end + len('        {% endif %}\n')

brother_block = '''
        {% if component["machine_id"] == 227 and brother_parts %}
        <section class="component-info brother-catalog-parts"
                 id="brother-catalog-parts">
            <h2>Daftar Spare Part — Halaman {{ component["diagram_page"] }}</h2>
            <p>{{ brother_parts|length }} baris part dari katalog Brother.</p>

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
                    {% for part in brother_parts %}
                        <tr>
                            <td>{{ part["catalog_ref"] }}</td>
                            <td><strong>{{ part["part_number"] }}</strong></td>
                            <td>{{ part["part_name"] }}</td>
                            <td>{{ part["quantity_raw"] or part["quantity"] or "" }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </section>
        {% endif %}
'''

updated = source[:insert_at] + brother_block + source[insert_at:]

# Backup hanya setelah semua pemeriksaan pola berhasil.
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_name(
    f"component_detail_before_brother_table_{stamp}.html"
)
shutil.copy2(path, backup)

path.write_text(updated, encoding="utf-8")

print("OK: tabel katalog Brother berhasil ditambahkan.")
print(f"Backup template: {backup}")
