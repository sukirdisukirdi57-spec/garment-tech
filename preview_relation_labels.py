from pathlib import Path
import difflib
import sys

path = Path("templates/machine_detail.html")
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
    print(f"PRATINJAU DIBATALKAN: blok ditemukan {count} kali; harus tepat 1.")
    sys.exit(1)

preview = source.replace(old, new, 1)

print("PRATINJAU SAJA — FILE APLIKASI TIDAK DIUBAH")
sys.stdout.writelines(difflib.unified_diff(
    source.splitlines(keepends=True),
    preview.splitlines(keepends=True),
    fromfile="versi saat ini",
    tofile="usulan",
))
