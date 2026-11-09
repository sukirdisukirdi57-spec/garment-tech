from pathlib import Path

src = Path("templates/machine_detail.html")
dst = Path("audit_tmp_ddl7000a/machine_detail_ddl7000a_ringan.html")

text = src.read_text(encoding="utf-8")

start = "                    {% for part in parts %}"
end = "                    {% endfor %}"
a = text.find(start)
b = text.find(end, a)

if a < 0 or b < 0:
    raise SystemExit("GAGAL: loop Parts tidak ditemukan.")

b += len(end)

sections = {
    2: "Frame & Miscellaneous Cover Components",
    4: "Bobbin Winder Components",
    6: "Main Shaft Components",
    8: "Needle Bar, Upright Shaft & Hook Driving Shaft",
    10: "Hand Lifter Components",
    12: "Feed Mechanism Components",
    14: "Thread Trimmer Components",
    15: "Automatic Reverse Feed Components",
    16: "Exclusive Parts Type NB",
    18: "Oil Lubrication Components",
    20: "Oil Reservoir Components",
    21: "Accessories Parts Components",
    22: "Thread Stand Components",
    23: "PSC Unit",
}

meta = "{\n" + ",\n".join(
    f"            {page}: '{title}'"
    for page, title in sections.items()
) + "\n        }"

new_loop = f'''                    {{% if machine["id"] == 4 %}}
                    {{% set ddl_sections = {meta} %}}
                    {{% set ns = namespace(index=0) %}}
                    {{% for page, section_parts in parts|groupby("diagram_page") %}}
                    {{% set section_title = ddl_sections.get(page|int, "Section katalog") %}}
                    <tr class="ddl-section-row"
                        data-section-page="{{{{ page }}}}"
                        data-expanded="false">
                        <td colspan="6" style="padding:10px; background:#eef3f8;">
                            <button type="button"
                                    class="ddl-section-toggle"
                                    aria-expanded="false"
                                    style="width:100%; padding:10px; text-align:left; font-weight:bold;">
                                ▶ Section {{{{ loop.index }}}} — {{{{ section_title }}}}
                                ({{{{ section_parts|length }}}} part)
                            </button>
                        </td>
                    </tr>
                    {{% for part in section_parts %}}
                    {{% set ns.index = ns.index + 1 %}}
                    <tr class="part-row"
                        data-section-page="{{{{ page }}}}"
                        data-search="{{{{ part['part_number'] }}}} {{{{ part['part_name'] }}}}"
                        data-catalog="{{{{ part['catalog_ref'] or '' }}}}"
                        data-page="{{{{ part['diagram_page'] or '' }}}}"
                        style="display:none;">
                        <td style="padding:8px;">{{{{ ns.index }}}}</td>
                        <td style="padding:8px;"><strong>{{{{ part["part_number"] }}}}</strong></td>
                        <td style="padding:8px;">{{{{ part["part_name"] }}}}</td>
                        <td style="padding:8px; text-align:center;">{{{{ part["quantity"] or "" }}}}</td>
                        <td style="padding:8px; text-align:center;">{{{{ part["catalog_ref"] or "" }}}}</td>
                        <td style="padding:8px; text-align:center;">{{{{ part["diagram_page"] or "" }}}}</td>
                    </tr>
                    {{% endfor %}}
                    {{% endfor %}}
                    {{% else %}}
''' + text[a:b] + '''
                    {% endif %}'''

text = text[:a] + new_loop + text[b:]

needle = '''            const rows = Array.from(
                document.querySelectorAll("#parts-table .part-row")
            );'''

replacement = needle + '''
            const sectionHeaders = Array.from(
                document.querySelectorAll("#parts-table .ddl-section-row")
            );

            const sectionMap = new Map(
                sectionHeaders.map(function(header) {
                    return [header.dataset.sectionPage, header];
                })
            );'''

if needle not in text:
    raise SystemExit("GAGAL: lokasi daftar baris JavaScript tidak ditemukan.")

text = text.replace(needle, replacement, 1)

old_start = "            function filterParts() {"
old_end = "            searchInput.addEventListener("
x = text.find(old_start)
y = text.find(old_end, x)

if x < 0 or y < 0:
    raise SystemExit("GAGAL: fungsi filter tidak ditemukan.")

new_filter = '''            function filterParts() {
                const search = searchInput.value.trim().toLowerCase();
                const catalog = catalogSelect.value;
                const page = pageSelect.value;
                const hasFilter = Boolean(search || catalog || page);

                let visible = 0;

                const matches = new Map();

                rows.forEach(function(row) {
                    const match =
                        (!search || row.dataset.search.toLowerCase().includes(search)) &&
                        (!catalog || row.dataset.catalog === catalog) &&
                        (!page || row.dataset.page === page);

                    matches.set(row, match);
                    if (match) visible++;
                });

                sectionHeaders.forEach(function(header) {
                    const sectionPage = header.dataset.sectionPage;
                    const hasVisibleParts = rows.some(function(row) {
                        return row.dataset.sectionPage === sectionPage &&
                               matches.get(row);
                    });

                    if (hasFilter) {
                        header.dataset.expanded = hasVisibleParts ? "true" : "false";
                    }

                    const expanded = header.dataset.expanded === "true";
                    const button = header.querySelector(".ddl-section-toggle");

                    button.setAttribute("aria-expanded", String(expanded));
                    button.textContent =
                        (expanded ? "▼ " : "▶ ") + button.textContent.replace(/^[▶▼] /, "");

                    header.style.display = hasFilter && !hasVisibleParts ? "none" : "";
                });

                rows.forEach(function(row) {
                    const header = sectionMap.get(row.dataset.sectionPage);
                    const expanded = header &&
                        header.dataset.expanded === "true";

                    row.style.display =
                        matches.get(row) && expanded ? "" : "none";
                });

                resultCount.textContent = visible;
                emptyMessage.style.display = visible === 0 ? "block" : "none";
            }

'''
text = text[:x] + new_filter + text[y:]

needle2 = '''            pageSelect.addEventListener(
                "change",
                filterParts
            );'''

replacement2 = needle2 + '''

            sectionHeaders.forEach(function(header) {
                const button = header.querySelector(".ddl-section-toggle");

                button.addEventListener("click", function() {
                    header.dataset.expanded =
                        header.dataset.expanded === "true" ? "false" : "true";
                    filterParts();
                });
            });

            filterParts();'''

if needle2 not in text:
    raise SystemExit("GAGAL: event filter halaman tidak ditemukan.")

text = text.replace(needle2, replacement2, 1)

dst.write_text(text, encoding="utf-8")

print("PROPOSAL RINGAN BERHASIL DIBUAT")
print("File:", dst)
print("Section:", len(sections))
print("Diagram tambahan: tidak ada")
print("Semua filter: dipertahankan")
print("Template asli: tidak diubah")
print("Database: tidak diubah")
