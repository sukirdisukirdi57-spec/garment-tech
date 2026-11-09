from pathlib import Path

source = Path("templates/machine_detail.html")
target = Path("templates/machine_detail.html.proposed")

original = source.read_text(encoding="utf-8")
text = original

start_marker = '    <section id="components">'
end_marker = '\n\n\n    {% if machine["id"] == 44 and section27_parts %}'
parts_start = '    <section id="parts-list">'
notes_marker = '\n    <section id="technician-notes">'
zoom_old = 'document.querySelectorAll(".machine43-diagram-open")'
zoom_new = 'document.querySelectorAll(".machine43-diagram-open, .ddl7000a-diagram-open")'

checks = {
    "awal komponen": text.count(start_marker) == 1,
    "batas akhir komponen": text.count(end_marker) == 1,
    "awal Parts List": text.count(parts_start) == 1,
    "awal Catatan Teknisi": text.count(notes_marker) == 1,
    "selector zoom": text.count(zoom_old) == 1,
}

for name, ok in checks.items():
    print(("OK   " if ok else "GAGAL ") + name)

if not all(checks.values()):
    raise SystemExit("Pemeriksaan gagal. Template asli tidak diubah.")

component_start = text.index(start_marker)
component_end = text.index(end_marker, component_start)

new_components = r'''
    {% if machine["id"] == 4 %}
    <section id="components" class="ddl7000a-components">
        <h2>🔩 Komponen</h2>

        {% if session.get("admin_logged_in") %}
        <p>
            <a href="/add-component/{{ machine['id'] }}" class="add-button">
                ➕ Tambah Komponen
            </a>
        </p>
        {% endif %}

        <div class="machine-card">
            <p>
                <label for="ddl7000a-search"><strong>🔎 Cari Part:</strong></label>
                <input id="ddl7000a-search" type="search"
                       placeholder="Nomor part atau nama part..."
                       style="width:100%; padding:10px; margin-top:5px;">
            </p>
            <p>
                <label for="ddl7000a-catalog"><strong>📖 Ref. Katalog:</strong></label>
                <select id="ddl7000a-catalog"
                        style="width:100%; padding:10px; margin-top:5px;">
                    <option value="">Semua Ref. Katalog</option>
                </select>
            </p>
            <p>
                <label for="ddl7000a-page"><strong>📄 Halaman Diagram:</strong></label>
                <select id="ddl7000a-page"
                        style="width:100%; padding:10px; margin-top:5px;">
                    <option value="">Semua Halaman</option>
                </select>
            </p>
            <p><strong>Hasil:</strong>
                <span id="ddl7000a-result">{{ parts|length }}</span>
                dari {{ parts|length }} part
            </p>
        </div>

        {% set ddl_sections = {
            2: 'Frame & Miscellaneous Cover Components',
            4: 'Bobbin Winder Components',
            6: 'Main Shaft Components',
            8: 'Needle Bar, Upright Shaft & Hook Driving Shaft',
            10: 'Hand Lifter Components',
            12: 'Feed Mechanism Components',
            14: 'Thread Trimmer Components',
            15: 'Automatic Reverse Feed Components',
            16: 'Exclusive Parts Type NB',
            18: 'Oil Lubrication Components',
            20: 'Oil Reservoir Components',
            21: 'Accessories Parts Components',
            22: 'Thread Stand Components',
            23: 'PSC Unit'
        } %}

        {% set ddl_images = {
            2: 'section-01-frame_miscellaneous.png',
            4: 'section-02-bobbin_winder.png',
            6: 'section-03-main_shaft.png',
            8: 'section-04-needle_bar.png',
            10: 'section-05-hand_lifter.png',
            12: 'section-06-feed_mechanism.png',
            14: 'section-07-thread_trimmer.png',
            15: 'section-08-automatic_reverse.png',
            16: 'section-09-exclusive_parts_nb.png',
            18: 'section-10-oil_lubrication.png',
            20: 'section-11-oil_reservoir.png',
            21: 'section-12-accessories.png',
            22: 'section-13-thread_stand.png',
            23: 'section-14-psc_unit.png'
        } %}

        {% if parts %}
            {% for page, section_parts in parts|groupby("diagram_page") %}
            {% set page_number = page|int %}
            {% set section_title = ddl_sections.get(page_number, "Section katalog") %}

            <details class="machine-card ddl7000a-section">
                <summary>
                    Section {{ loop.index }} — {{ section_title }}
                    <small>({{ section_parts|length }} part)</small>
                </summary>

                <div class="accordion-detail">
                    <div class="component-image">
                        <button type="button"
                                class="diagram-open ddl7000a-diagram-open"
                                data-diagram-src="{{ url_for('static', filename='images/mechanisms/juki/ddl7000a/' ~ ddl_images.get(page_number, '')) }}"
                                aria-label="Perbesar diagram {{ section_title }}">
                            <img
                                src="{{ url_for('static', filename='images/mechanisms/juki/ddl7000a/' ~ ddl_images.get(page_number, '')) }}"
                                alt="Diagram {{ section_title }}"
                                loading="lazy"
                                style="display:block; max-width:100%; height:auto; margin:0 auto;">
                            <span>🔍 Ketuk gambar untuk memperbesar</span>
                        </button>
                    </div>

                    <h3>📦 Parts List — Section {{ loop.index }}</h3>
                    <div style="overflow-x:auto;">
                        <table style="width:100%; border-collapse:collapse;">
                            <thead>
                                <tr>
                                    <th style="padding:8px;">No</th>
                                    <th style="padding:8px;">Nomor Part</th>
                                    <th style="padding:8px;">Nama Part</th>
                                    <th style="padding:8px;">Qty</th>
                                    <th style="padding:8px;">Ref.</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for part in section_parts %}
                                <tr class="ddl7000a-part-row"
                                    data-search="{{ part['part_number'] }} {{ part['part_name'] }}"
                                    data-catalog="{{ part['catalog_ref'] or '' }}"
                                    data-page="{{ part['diagram_page'] or '' }}">
                                    <td style="padding:8px;">{{ loop.index }}</td>
                                    <td style="padding:8px;">
                                        <strong>{{ part["part_number"] }}</strong>
                                    </td>
                                    <td style="padding:8px;">{{ part["part_name"] }}</td>
                                    <td style="padding:8px; text-align:center;">
                                        {{ part["quantity"] or "" }}
                                    </td>
                                    <td style="padding:8px; text-align:center;">
                                        {{ part["catalog_ref"] or "" }}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    <h3>🔧 Komponen Terkait</h3>
                    {% set component_ns = namespace(count=0) %}

                    {% for component in components %}
                        {% if component["diagram_page"]|int == page_number %}
                        {% set component_ns.count = component_ns.count + 1 %}

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
                                            {% if subpart["relation_type"] %}
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
                        {% endif %}
                    {% endfor %}

                    {% if component_ns.count == 0 %}
                    <p><small>Belum ada komponen terdaftar untuk Section ini.</small></p>
                    {% endif %}
                </div>
            </details>
            {% endfor %}
        {% else %}
            <p>Belum ada Parts List untuk mesin ini.</p>
        {% endif %}

        <p id="ddl7000a-empty" style="display:none;">
            Tidak ada part yang sesuai dengan filter.
        </p>
    </section>

    <script>
    (function () {
        const root = document.getElementById("components");
        if (!root) return;

        const search = root.querySelector("#ddl7000a-search");
        const catalog = root.querySelector("#ddl7000a-catalog");
        const page = root.querySelector("#ddl7000a-page");
        const result = root.querySelector("#ddl7000a-result");
        const empty = root.querySelector("#ddl7000a-empty");
        const rows = Array.from(root.querySelectorAll(".ddl7000a-part-row"));
        const sections = Array.from(root.querySelectorAll(".ddl7000a-section"));

        function addOptions(select, values, prefix) {
            [...values].sort((a, b) => Number(a) - Number(b)).forEach(value => {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = prefix + " " + value;
                select.appendChild(option);
            });
        }

        const catalogs = new Set();
        const pages = new Set();

        rows.forEach(row => {
            if (row.dataset.catalog) catalogs.add(row.dataset.catalog);
            if (row.dataset.page) pages.add(row.dataset.page);
        });

        addOptions(catalog, catalogs, "Ref.");
        addOptions(page, pages, "Halaman");

        function filterParts() {
            const term = search.value.trim().toLowerCase();
            const selectedCatalog = catalog.value;
            const selectedPage = page.value;
            const active = Boolean(term || selectedCatalog || selectedPage);
            let visible = 0;

            sections.forEach(section => {
                const sectionRows = Array.from(
                    section.querySelectorAll(".ddl7000a-part-row")
                );
                let sectionVisible = 0;

                sectionRows.forEach(row => {
                    const match =
                        (!term || row.dataset.search.toLowerCase().includes(term)) &&
                        (!selectedCatalog || row.dataset.catalog === selectedCatalog) &&
                        (!selectedPage || row.dataset.page === selectedPage);

                    row.hidden = !match;
                    if (match) {
                        visible++;
                        sectionVisible++;
                    }
                });

                if (active) {
                    section.open = sectionVisible > 0;
                }

                section.hidden = active && sectionVisible === 0;
            });

            result.textContent = visible;
            empty.style.display = visible === 0 ? "block" : "none";
        }

        search.addEventListener("input", filterParts);
        catalog.addEventListener("change", filterParts);
        page.addEventListener("change", filterParts);
    })();
    </script>
    {% else %}
''' + original[component_start:component_end] + r'''
    {% endif %}
'''

text = (
    text[:component_start]
    + new_components
    + text[component_end:]
)

# Sembunyikan Parts List global hanya untuk DDL-7000A.
parts_start_index = text.index(parts_start)
notes_index = text.index(notes_marker, parts_start_index)
text = (
    text[:parts_start_index]
    + '    {% if machine["id"] != 4 %}\n'
    + text[parts_start_index:notes_index]
    + '\n    {% endif %}\n'
    + text[notes_index:]
)

# Perluas zoom agar diagram DDL-7000A juga dapat diperbesar.
if text.count(zoom_old) != 1:
    raise SystemExit("Selector zoom tidak cocok. File usulan tidak dibuat.")

text = text.replace(zoom_old, zoom_new, 1)

# Pemeriksaan akhir sebelum membuat file usulan.
if text.count('id="components"') != 2:
    raise SystemExit("Pemeriksaan ID components gagal.")
if text.count('id="parts-list"') != 1:
    raise SystemExit("Pemeriksaan ID parts-list gagal.")
if 'machine["id"] != 4' not in text:
    raise SystemExit("Pemeriksaan pembungkus Parts List gagal.")
if zoom_new not in text:
    raise SystemExit("Pemeriksaan selector zoom gagal.")

target.write_text(text, encoding="utf-8")

print("\nFILE USULAN BERHASIL DIBUAT")
print("Sumber :", source)
print("Usulan :", target)
print("Ukuran :", target.stat().st_size, "bytes")
print("Template asli: TIDAK DIUBAH")
print("Database: TIDAK DIUBAH")
print("app.py: TIDAK DIUBAH")
print("PythonAnywhere: TIDAK DIUBAH")
