from pathlib import Path

p = Path("app.py")
t = Path("templates/component_detail.html")
a = p.read_text()
h = t.read_text()

old1 = '    clamp_d1_parts = []\n'
new1 = '    clamp_d1_parts = []\n    clamp_d2_parts = []\n'
old2 = '        clamp_d1_parts = conn.execute("SELECT * FROM parts WHERE machine_id = ? AND diagram_page = ? ORDER BY CAST(catalog_ref AS INTEGER), id", (227, 23)).fetchall()\n'
new2 = old2 + '        clamp_d2_parts = conn.execute("SELECT * FROM parts WHERE machine_id = ? AND diagram_page = ? ORDER BY CAST(catalog_ref AS INTEGER), id", (227, 25)).fetchall()\n'
old3 = '        clamp_d1_parts=clamp_d1_parts\n'
new3 = '        clamp_d1_parts=clamp_d1_parts,\n        clamp_d2_parts=clamp_d2_parts\n'

assert a.count(old1) == 1, "Baris inisialisasi D1 tidak unik."
assert a.count(old2) == 1, "Baris query D1 tidak unik."
assert a.count(old3) == 1, "Baris render D1 tidak unik."
assert "clamp_d2_parts" not in a, "Variabel D2 sudah ada di app.py."
marker = '<section class="component-navigation">'
assert h.count(marker) == 1, "Penanda sisipan template tidak unik."
assert "Daftar Spare Part D2" not in h, "Bagian D2 sudah ada di template."

d2 = '''{% if component["machine_id"] == 227 and component["component_name"] == "Sistem Penjepit Bahan (Clamp)" and clamp_d2_parts %}

<section class="component-info clamp-d1-section">
    <h2>📐 D2 — Work Clamp Lifter Mechanism</h2>
    <p>Diagram resmi Brother, halaman katalog 25. Ketuk gambar untuk melihat ukuran penuh.</p>
    <div class="clamp-d1-layout">
        <div class="clamp-d1-diagram">
            <a href="{{ url_for('static', filename='images/mechanisms/brother/bas311hn/d2-work-clamp-lifter.png') }}" target="_blank" rel="noopener noreferrer">
                <img src="{{ url_for('static', filename='images/mechanisms/brother/bas311hn/d2-work-clamp-lifter.png') }}" alt="Diagram D2 Work Clamp Lifter Mechanism Brother BAS-311HN">
            </a>
        </div>
        <div class="clamp-d1-table">
            <h3>Daftar Spare Part D2 ({{ clamp_d2_parts|length }} part)</h3>
            <div class="component-subparts-wrapper">
                <table class="component-subparts">
                    <thead><tr><th>Ref.</th><th>Part Number</th><th>Nama Part</th><th>Qty</th></tr></thead>
                    <tbody>
                    {% for part in clamp_d2_parts %}
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
        </div>
    </div>
</section>
{% endif %}'''

a = a.replace(old1, new1, 1)
a = a.replace(old2, new2, 1)
a = a.replace(old3, new3, 1)
h = h.replace(marker, d2 + marker, 1)

t.write_text(h)
p.write_text(a)
print("Berhasil menambahkan query D2 dan tampilan 59 spare part.")
