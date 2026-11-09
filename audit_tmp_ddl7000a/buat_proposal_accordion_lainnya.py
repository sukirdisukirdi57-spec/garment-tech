from pathlib import Path
import re

src = Path("templates/machine_detail.html")
dst = Path("audit_tmp_ddl7000a/machine_detail_accordion_lainnya.html")

html = src.read_text(encoding="utf-8")

def replace_section(text, section_id, replacement):
    pattern = rf'<section id="{section_id}">.*?</section>'
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Bagian {section_id} tidak ditemukan secara unik")
    return result

documents = r'''
<section id="documents">
    <style>
    #documents details.machine-card > summary,
    #official-alarms details.machine-card > summary,
    #components details.machine-card > summary {
        cursor: pointer;
        list-style: none;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        font-weight: 600;
    }
    #documents summary::-webkit-details-marker,
    #official-alarms summary::-webkit-details-marker,
    #components summary::-webkit-details-marker {
        display: none;
    }
    #documents summary::after,
    #official-alarms summary::after,
    #components summary::after {
        content: "＋";
        margin-left: auto;
        font-size: 1.1rem;
    }
    #documents details[open] > summary::after,
    #official-alarms details[open] > summary::after,
    #components details[open] > summary::after {
        content: "−";
    }
    #documents .accordion-detail,
    #official-alarms .accordion-detail,
    #components .accordion-detail {
        padding-top: 12px;
    }
    </style>

    <h2>📚 Dokumen & Referensi</h2>

    {% if documents %}
        {% for document in documents %}
        <details class="machine-card">
            <summary>{{ document["title"] }}</summary>
            <div class="accordion-detail">
                {% if document["document_type"] %}
                <p><strong>Jenis:</strong> {{ document["document_type"] }}</p>
                {% endif %}

                {% if document["notes"] %}
                <p><strong>Keterangan:</strong><br>{{ document["notes"] }}</p>
                {% endif %}

                {% if document["source_url"] %}
                <p>
                    <a href="{{ document["source_url"] }}"
                       target="_blank" rel="noopener noreferrer"
                       class="add-button">🔗 Buka Dokumen</a>
                </p>
                {% endif %}

                {% if document["local_file"] %}
                <p>
                    <a href="{{ url_for('local_file', filename=document['local_file']) }}"
                       target="_blank" rel="noopener noreferrer"
                       class="add-button">📄 Buka File Lokal</a>
                </p>
                {% endif %}
            </div>
        </details>
        {% endfor %}
    {% else %}
        <p>Belum ada dokumen atau referensi.</p>
    {% endif %}
</section>
'''

alarms = r'''
<section id="official-alarms">
    <h2>🚨 Alarm Resmi Mesin</h2>

    {% if session.get("admin_logged_in") %}
    <p class="official-alarm-add-action">
        <a class="add-button" href="/admin/machine-alarms/add/{{ machine['id'] }}">
            + Tambah Alarm Resmi
        </a>
    </p>
    {% endif %}

    {% if machine_alarms_data %}
        {% for alarm in machine_alarms_data %}
        <details class="machine-card">
            <summary>
                {{ alarm["alarm_code"] }} — {{ alarm["alarm_name"] }}
            </summary>
            <div class="accordion-detail">
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
                {% endif %}

                {% if alarm["possible_cause"] %}
                <p><strong>Kemungkinan penyebab:</strong><br>
                    {{ alarm["possible_cause"] }}</p>
                {% endif %}

                {% if alarm["solution"] %}
                <p><strong>Tindakan:</strong><br>
                    {{ alarm["solution"] }}</p>
                {% endif %}

                <p>
                    <strong>Referensi:</strong>
                    {{ alarm["manual_title"] }},
                    versi {{ alarm["manual_version"] }},
                    {{ alarm["manual_chapter"] }},
                    halaman {{ alarm["manual_page"] }}.
                </p>

                {% if alarm["source_url"] %}
                <p>
                    <a href="{{ alarm["source_url"] }}"
                       target="_blank" rel="noopener noreferrer">
                        Buka sumber manual
                    </a>
                </p>
                {% endif %}
            </div>
        </details>
        {% endfor %}
    {% else %}
        <p>Belum ada alarm resmi yang tercatat untuk mesin ini.</p>
    {% endif %}
</section>
'''

components = r'''
<section id="components">
    <h2>🔩 Komponen</h2>

    {% if session.get("admin_logged_in") %}
    <p>
        <a href="/add-component/{{ machine['id'] }}" class="add-button">
            ➕ Tambah Komponen
        </a>
    </p>
    {% endif %}

    {% if components %}
        {% for component in components %}
        <details class="machine-card">
            <summary>
                {{ component["component_name"] }}
                {% if component["part_number"] %}
                — {{ component["part_number"] }}
                {% endif %}
            </summary>
            <div class="accordion-detail">
                {% if component["catalog_ref"] %}
                <p><strong>📖 Ref. Katalog:</strong>
                    {{ component["catalog_ref"] }}</p>
                {% endif %}

                {% if component["diagram_page"] %}
                <p><strong>📄 Halaman Diagram:</strong>
                    {{ component["diagram_page"] }}</p>
                {% endif %}

                {% if component["location"] %}
                <p><strong>Lokasi:</strong>
                    {{ component["location"] }}</p>
                {% endif %}

                {% if component["function"] %}
                <p><strong>Fungsi:</strong><br>
                    {{ component["function"] }}</p>
                {% endif %}

                {% if component["notes"] %}
                <p><strong>Catatan:</strong><br>
                    {{ component["notes"] }}</p>
                {% endif %}

                {% set component_subparts = component_parts
                    | selectattr("component_id", "equalto", component["id"])
                    | list %}

                {% if component_subparts %}
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
                {% endif %}

                {% if session.get("admin_logged_in") %}
                <p>
                    <a href="/edit-component/{{ component['id'] }}"
                       class="add-button">✏️ Edit</a>

                    <form method="POST"
                          action="/delete-component/{{ component['id'] }}"
                          style="display:inline;"
                          onsubmit="return confirm('Hapus komponen ini?');">
                        <button type="submit" class="add-button">🗑️ Hapus</button>
                    </form>
                </p>
                {% endif %}
            </div>
        </details>
        {% endfor %}
    {% else %}
        <p>Belum ada data komponen.</p>
    {% endif %}
</section>
'''

html = replace_section(html, "documents", documents)
html = replace_section(html, "official-alarms", alarms)
html = replace_section(html, "components", components)

dst.write_text(html, encoding="utf-8")

print("PROPOSAL BERHASIL DIBUAT")
print("Dokumen       : accordion")
print("Alarm resmi   : accordion")
print("Komponen      : accordion")
print("Parts List    : dipertahankan")
print("Troubleshoot  : dipertahankan")
print("Spesifikasi   : dipertahankan")
print("Template asli : tidak diubah")
print("Database      : tidak diubah")
print("File:", dst)
