from pathlib import Path
from datetime import datetime
import shutil
import sys

path = Path("templates/component_detail.html")
if not path.is_file():
    sys.exit("GAGAL: template tidak ditemukan.")

text = path.read_text(encoding="utf-8")
marker = '<section class="component-navigation">'
block_id = 'id="bas311hn-thread-trimmer-parts"'

if block_id in text:
    sys.exit("DIBATALKAN: blok tabel J sudah ada.")
if text.count(marker) != 1:
    sys.exit("DIBATALKAN: penanda navigasi tidak unik; file tidak diubah.")

block = r'''
{% if component["id"] == 538
      and component["machine_id"] == 227
      and component["component_name"] == "J - Thread trimmer mechanism"
      and sub_parts %}
<section class="component-info" id="bas311hn-thread-trimmer-parts">
    <h2>📋 Daftar Suku Cadang — J. Thread Trimmer Mechanism</h2>
    <p>Brother BAS-311HN-03S · Parts Book, halaman katalog 39.</p>
    <p>Periksa kecocokan nomor part dengan varian mesin sebelum pemesanan.</p>
    <div class="component-subparts-wrapper">
        <table class="component-subparts">
            <thead>
                <tr><th>Ref.</th><th>Part Number</th><th>Nama Part</th><th>Qty</th></tr>
            </thead>
            <tbody>
                {% for part in sub_parts %}
                <tr>
                    <td>{{ part["catalog_ref"] if part["catalog_ref"] is not none else "—" }}</td>
                    <td><strong>{{ part["part_number"] or "—" }}</strong></td>
                    <td>{{ part["part_name"] or "—" }}</td>
                    <td>{{ part["quantity_raw"] or part["quantity"] or "—" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</section>
{% endif %}

'''

backup = path.with_name(
    path.name + ".before-j-display-" + datetime.now().strftime("%Y%m%d-%H%M%S")
)
shutil.copy2(path, backup)
path.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")

print("TEMPLATE DIPERBARUI.")
print("Cadangan:", backup)
