from pathlib import Path

src = Path("templates/machine_detail.html")
dst = Path("audit_tmp_ddl7000a/machine_detail_accordion_detail.html")

html = src.read_text(encoding="utf-8")

trouble_start = html.index('<section id="troubleshooting">')
trouble_end = html.index('<section id="official-alarms">', trouble_start)

trouble = '''
<style>
#troubleshooting details.machine-card > summary,
#specifications details.machine-card > summary {
    cursor: pointer;
    list-style: none;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-weight: 600;
}
#troubleshooting details.machine-card > summary::-webkit-details-marker,
#specifications details.machine-card > summary::-webkit-details-marker {
    display: none;
}
#troubleshooting details.machine-card > summary::after,
#specifications details.machine-card > summary::after {
    content: "＋";
    margin-left: auto;
    font-size: 1.1rem;
}
#troubleshooting details.machine-card[open] > summary::after,
#specifications details.machine-card[open] > summary::after {
    content: "−";
}
#troubleshooting .accordion-detail,
#specifications .accordion-detail {
    padding-top: 12px;
}
</style>

<section id="troubleshooting">
    <h2>🔧 Troubleshooting Mesin</h2>
    {% if troubleshooting_data %}
        {% for item in troubleshooting_data %}
        <details class="machine-card">
            <summary>
                <span>{{ item["problem"] }}</span>
                {% if item["code"] %}
                <span class="troubleshooting-code">
                    Kode: {{ item["code"] }}
                </span>
                {% endif %}
            </summary>
            <div class="accordion-detail">
                {% if item["symptoms"] %}
                <p><strong>Gejala:</strong><br>{{ item["symptoms"] }}</p>
                {% endif %}
                {% if item["possible_cause"] %}
                <p><strong>Kemungkinan Penyebab:</strong><br>{{ item["possible_cause"] }}</p>
                {% endif %}
                {% if item["solution"] %}
                <p><strong>Solusi:</strong><br>{{ item["solution"] }}</p>
                {% endif %}
                {% if item["safety_notes"] %}
                <p><strong>⚠️ Catatan Keselamatan:</strong><br>{{ item["safety_notes"] }}</p>
                {% endif %}
                {% if item["source"] %}
                <p><strong>Sumber:</strong><br>{{ item["source"] }}</p>
                {% endif %}
            </div>
        </details>
        {% endfor %}
    {% else %}
        <p>Belum ada data troubleshooting untuk mesin ini.</p>
    {% endif %}
</section>

'''

html = html[:trouble_start] + trouble + html[trouble_end:]

spec_start = html.index('<section id="specifications">')
spec_end = html.index('</section>', spec_start) + len('</section>')

spec = '''
<section id="specifications">
    <h2>⚙️ Spesifikasi</h2>
    {% if session.get("admin_logged_in") %}
    <p>
        <a href="/add-specification/{{ machine['id'] }}" class="add-button">
            ➕ Tambah Spesifikasi
        </a>
    </p>
    {% endif %}

    {% if specifications %}
        {% for spec in specifications %}
        <details class="machine-card">
            <summary>
                <span>{{ spec["specification"] }}</span>
                <span>Nilai: {{ spec["value"] or "Belum ada nilai" }}</span>
            </summary>
            <div class="accordion-detail">
                {% if spec["notes"] %}
                <p><strong>Catatan:</strong><br>{{ spec["notes"] }}</p>
                {% endif %}
                {% if spec["description"] %}
                <p><strong>Deskripsi:</strong><br>{{ spec["description"] }}</p>
                {% endif %}

                {% if session.get("admin_logged_in") %}
                <p>
                    <a href="/edit-specification/{{ spec['id'] }}"
                       class="add-button">✏️ Edit</a>
                    <form method="POST"
                          action="/delete-specification/{{ spec['id'] }}"
                          style="display:inline;"
                          onsubmit="return confirm('Hapus spesifikasi ini?');">
                        <button type="submit" class="add-button">
                            🗑️ Hapus
                        </button>
                    </form>
                </p>
                {% endif %}
            </div>
        </details>
        {% endfor %}
    {% else %}
        <p>Belum ada data spesifikasi.</p>
    {% endif %}
</section>
'''

html = html[:spec_start] + spec + html[spec_end:]

dst.write_text(html, encoding="utf-8")

print("PROPOSAL ACCORDION DETAIL BERHASIL DIBUAT")
print("Troubleshooting: accordion per data")
print("Spesifikasi: accordion per data")
print("Tombol admin Edit/Hapus dipertahankan")
print("Parts List: tetap dipertahankan")
print("Template asli: tidak diubah")
print("Database: tidak diubah")
print("File:", dst)
