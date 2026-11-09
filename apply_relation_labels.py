from pathlib import Path
from datetime import datetime
import shutil
import sys

path = Path("templates/machine_detail.html")
if not path.is_file():
    sys.exit("BATAL: template tidak ditemukan.")

source = path.read_text(encoding="utf-8")

old = '''                {% if component_subparts %}
                <div class="component-subparts">
                    <strong>🔩 Sub-part:</strong>
                    <ul>
                        {% for subpart in component_subparts %}
                        <li>
                            <strong>{{ subpart["part_number"] }}</strong>
                            — {{ subpart["part_name"] }}

                            {% if subpart["relation_type"] %}
                            <small>
                                ({{ subpart["relation_type"] }})
                            </small>
                            {% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}'''

new = '''                {% if component_subparts %}
                <div class="component-subparts">
                    <strong>🔗 Relasi part:</strong>
                    <ul>
                        {% for subpart in component_subparts %}
                        <li>
                            <strong>{{ subpart["part_number"] or "—" }}</strong>
                            — {{ subpart["part_name"] or "Nama part belum tersedia" }}

                            {% if subpart["relation_type"] == "catalog_section" %}
                            <small>(📖 Bagian katalog)</small>
                            {% elif subpart["relation_type"] == "catalog_option" %}
                            <small>(⚠️ Opsi katalog — verifikasi sebelum pemesanan)</small>
                            {% elif subpart["relation_type"] %}
                            <small>(Relasi: {{ subpart["relation_type"] }})</small>
                            {% endif %}

                            {% if subpart["relation_notes"] %}
                            <div><small>{{ subpart["relation_notes"] }}</small></div>
                            {% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}'''

count = source.count(old)
if count != 1:
    sys.exit(
        f"BATAL: blok lama ditemukan {count} kali; "
        "template tidak diubah."
    )

backup = path.with_name(
    path.name + ".bak_relation_labels_" +
    datetime.now().strftime("%Y%m%d_%H%M%S")
)

if backup.exists():
    sys.exit(f"BATAL: file cadangan sudah ada: {backup}")

# Cadangkan file asli sebelum perubahan.
shutil.copy2(path, backup)

try:
    path.write_text(source.replace(old, new, 1), encoding="utf-8")
    check = path.read_text(encoding="utf-8")
    if new not in check or old in check:
        raise RuntimeError("Verifikasi perubahan gagal.")
except Exception as exc:
    shutil.copy2(backup, path)
    sys.exit(
        f"GAGAL: template dipulihkan dari cadangan. Detail: {exc}"
    )

print("BERHASIL: patch tampilan diterapkan.")
print(f"Template : {path}")
print(f"Cadangan : {backup}")
print("Database dan CSV: tidak diubah.")
