from pathlib import Path

src = Path("templates/machine_detail.html")
dst = Path("audit_tmp_ddl7000a/machine_detail_ddl7000a_diagram.html")
base = Path("static")

sections = {
    2: ("Frame & Miscellaneous Cover Components", "section-01-frame_miscellaneous.png"),
    4: ("Bobbin Winder Components", "section-02-bobbin_winder.png"),
    6: ("Main Shaft Components", "section-03-main_shaft.png"),
    8: ("Needle Bar, Upright Shaft & Hook Driving Shaft", "section-04-needle_bar.png"),
    10: ("Hand Lifter Components", "section-05-hand_lifter.png"),
    12: ("Feed Mechanism Components", "section-06-feed_mechanism.png"),
    14: ("Thread Trimmer Components", "section-07-thread_trimmer.png"),
    15: ("Automatic Reverse Feed Components", "section-08-automatic_reverse.png"),
    16: ("Exclusive Parts Type NB", "section-09-exclusive_parts_nb.png"),
    18: ("Oil Lubrication Components", "section-10-oil_lubrication.png"),
    20: ("Oil Reservoir Components", "section-11-oil_reservoir.png"),
    21: ("Accessories Parts Components", "section-12-accessories.png"),
    22: ("Thread Stand Components", "section-13-thread_stand.png"),
    23: ("PSC Unit", "section-14-psc_unit.png"),
}

for page, (_, filename) in sections.items():
    path = base / "images/mechanisms/juki/ddl7000a" / filename
    if not path.is_file():
        raise SystemExit(f"GAGAL: gambar halaman {page} tidak ditemukan: {path}")

text = src.read_text(encoding="utf-8")

start = "                    {% for part in parts %}"
end = "                    {% endfor %}"
a = text.find(start)
b = text.find(end, a)
if a < 0 or b < 0:
    raise SystemExit("GAGAL: loop Parts tidak ditemukan.")
b += len(end)

new_loop = """
                    {% if machine["id"] == 4 %}
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
                    {% set ns = namespace(index=0) %}
                    {% for page, section_parts in parts|groupby("diagram_page") %}
                    {% set section_title = ddl_sections.get(page|int, "Section katalog") %}
                    <tr class="ddl-section-row"
                        data-section-page="{{ page }}"
                        data-expanded="false">
                        <td colspan="6" style="padding:10px; background:#eef3f8;">
                            <button type="button" class="ddl-section-toggle"
                                    aria-expanded="false"
                                    style="width:100%; padding:10px; text-align:left; font-weight:bold;">
                                ▶ Section {{ loop.index }} — {{ section_title }}
                                ({{ section_parts|length }} part)
                            </button>
                        </td>
                    </tr>
                    <tr class="ddl-section-image-row"
                        data-section-page="{{ page }}" style="display:none;">
                        <td colspan="6" style="padding:12px; text-align:center;">
                            <img src="{{ url_for('static', filename='images/mechanisms/juki/ddl7000a/' ~ ddl_images.get(page|int, '')) }}"
                                 alt="Diagram {{ section_title }}"
                                 loading="lazy"
                                 style="display:block; max-width:100%; height:auto; margin:0 auto;">
                        </td>
                    </tr>
                    {% for part in section_parts %}
                    {% set ns.index = ns.index + 1 %}
                    <tr class="part-row"
                        data-section-page="{{ page }}"
                        data-search="{{ part['part_number'] }} {{ part['part_name'] }}"
                        data-catalog="{{ part['catalog_ref'] or '' }}"
                        data-page="{{ part['diagram_page'] or '' }}"
                        style="display:none;">
                        <td style="padding:8px;">{{ ns.index }}</td>
                        <td style="padding:8px;"><strong>{{ part["part_number"] }}</strong></td>
                        <td style="padding:8px;">{{ part["part_name"] }}</td>
                        <td style="padding:8px; text-align:center;">{{ part["quantity"] or "" }}</td>
                        <td style="padding:8px; text-align:center;">{{ part["catalog_ref"] or "" }}</td>
                        <td style="padding:8px; text-align:center;">{{ part["diagram_page"] or "" }}</td>
                    </tr>
                    {% endfor %}
                    {% endfor %}
                    {% else %}
""" + text[a:b] + """
                    {% endif %}"""

text = text[:a] + new_loop + text[b:]

needle = """            const rows = Array.from(
                document.querySelectorAll("#parts-table .part-row")
            );"""
replacement = needle + """
            const sectionHeaders = Array.from(
                document.querySelectorAll("#parts-table .ddl-section-row")
            );
            const imageRows = Array.from(
                document.querySelectorAll("#parts-table .ddl-section-image-row")
            );
            const sectionMap = new Map(
                sectionHeaders.map(header => [header.dataset.sectionPage, header])
            );"""
if needle not in text:
    raise SystemExit("GAGAL: daftar baris JavaScript tidak ditemukan.")
text = text.replace(needle, replacement, 1)

x = text.find("            function filterParts() {")
y = text.find("            searchInput.addEventListener(", x)
if x < 0 or y < 0:
    raise SystemExit("GAGAL: fungsi filter tidak ditemukan.")

new_filter = """            function filterParts() {
                const search = searchInput.value.trim().toLowerCase();
                const catalog = catalogSelect.value;
                const page = pageSelect.value;
                const hasFilter = Boolean(search || catalog || page);
                const matches = new Map();
                let visible = 0;

                rows.forEach(row => {
                    const match =
                        (!search || row.dataset.search.toLowerCase().includes(search)) &&
                        (!catalog || row.dataset.catalog === catalog) &&
                        (!page || row.dataset.page === page);
                    matches.set(row, match);
                    if (match) visible++;
                });

                sectionHeaders.forEach(header => {
                    const sectionPage = header.dataset.sectionPage;
                    const hasVisibleParts = rows.some(row =>
                        row.dataset.sectionPage === sectionPage && matches.get(row)
                    );

                    if (hasFilter) {
                        header.dataset.expanded = hasVisibleParts ? "true" : "false";
                    }

                    const expanded = header.dataset.expanded === "true";
                    const button = header.querySelector(".ddl-section-toggle");
                    button.setAttribute("aria-expanded", String(expanded));
                    button.textContent =
                        (expanded ? "▼ " : "▶ ") +
                        button.textContent.replace(/^[▶▼] /, "");
                    header.style.display =
                        hasFilter && !hasVisibleParts ? "none" : "";
                });

                imageRows.forEach(imageRow => {
                    const header = sectionMap.get(imageRow.dataset.sectionPage);
                    imageRow.style.display =
                        header && header.dataset.expanded === "true" ? "" : "none";
                });

                rows.forEach(row => {
                    const header = sectionMap.get(row.dataset.sectionPage);
                    const expanded = header && header.dataset.expanded === "true";
                    row.style.display =
                        matches.get(row) && expanded ? "" : "none";
                });

                resultCount.textContent = visible;
                emptyMessage.style.display = visible === 0 ? "block" : "none";
            }

"""
text = text[:x] + new_filter + text[y:]

needle2 = """            pageSelect.addEventListener(
                "change",
                filterParts
            );"""
replacement2 = needle2 + """

            sectionHeaders.forEach(header => {
                const button = header.querySelector(".ddl-section-toggle");
                button.addEventListener("click", function() {
                    header.dataset.expanded =
                        header.dataset.expanded === "true" ? "false" : "true";
                    filterParts();
                });
            });

            filterParts();"""
if needle2 not in text:
    raise SystemExit("GAGAL: event filter halaman tidak ditemukan.")
text = text.replace(needle2, replacement2, 1)

dst.write_text(text, encoding="utf-8")

print("PROPOSAL DENGAN DIAGRAM BERHASIL DIBUAT")
print("Section:", len(sections))
print("Gambar terverifikasi:", len(sections))
print("Diagram tampil saat section dibuka.")
print("Template asli: tidak diubah")
print("Database: tidak diubah")
print("File proposal:", dst)
