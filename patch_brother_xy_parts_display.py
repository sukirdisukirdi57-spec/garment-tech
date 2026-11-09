from pathlib import Path
from datetime import datetime
from jinja2 import Environment

path = Path("templates/component_detail.html")
original = path.read_text(encoding="utf-8")

anchor = '<section class="component-navigation">'

block = r'''
{% if component["id"] in [527, 529] and sub_parts %}
<section class="component-info" id="brother-xy-catalog-parts">
    <h2>📋 Daftar Relasi Part — Bagian Katalog</h2>
    <p>
        Daftar ini mengikuti relasi katalog yang tercatat pada sistem.
        Kecocokan dengan konfigurasi aktual mesin harus diverifikasi
        sebelum memesan atau mengganti suku cadang.
    </p>

    <div class="component-subparts-wrapper">
        <table class="component-subparts">
            <thead>
                <tr>
                    <th>Ref. Katalog</th>
                    <th>Nomor Part</th>
                    <th>Nama Part</th>
                    <th>Qty</th>
                    <th>Jenis Relasi</th>
                    <th>Catatan</th>
                </tr>
            </thead>
            <tbody>
                {% for part in sub_parts %}
                <tr>
                    <td>{{ part["catalog_ref"] if part["catalog_ref"] is not none else "—" }}</td>
                    <td><strong>{{ part["part_number"] or "—" }}</strong></td>
                    <td>{{ part["part_name"] or "—" }}</td>
                    <td>{{ part["quantity_raw"] or part["quantity"] or "—" }}</td>
                    <td>{{ part["relation_type"] or "—" }}</td>
                    <td>{{ part["relation_notes"] or "—" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</section>
{% endif %}

'''

count = original.count(anchor)
if count != 1:
    raise SystemExit(
        f"DIHENTIKAN: titik penyisipan ditemukan {count} kali; file tidak diubah."
    )

updated = original.replace(anchor, block + anchor, 1)

# Validasi sebelum menyimpan
Environment().parse(updated)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_name(path.name + f".bak_brother_xy_parts_{stamp}")
backup.write_text(original, encoding="utf-8")

path.write_text(updated, encoding="utf-8")

# Validasi ulang hasil yang tersimpan
Environment().parse(path.read_text(encoding="utf-8"))

print("BERHASIL: blok daftar relasi part ditambahkan.")
print(f"Backup: {backup}")
print("Validasi Jinja: LULUS")
print("Database dan CSV: tidak diubah.")
