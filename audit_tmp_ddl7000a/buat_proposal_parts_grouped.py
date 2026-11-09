from pathlib import Path

src = Path("templates/machine_detail.html")
dst = Path("audit_tmp_ddl7000a/machine_detail_ddl7000a_proposal.html")

text = src.read_text(encoding="utf-8")

start = "                    {% for part in parts %}"
end = "                    {% endfor %}"
a = text.find(start)
b = text.find(end, a)

if a < 0 or b < 0:
    raise SystemExit("GAGAL: blok loop Parts tidak ditemukan.")

b += len(end)

sections = {
    2:  (1, "Frame & Miscellaneous Cover Components", "section-01-frame_miscellaneous.png"),
    4:  (2, "Bobbin Winder Components", "section-02-bobbin_winder.png"),
    6:  (3, "Main Shaft Components", "section-03-main_shaft.png"),
    8:  (4, "Needle Bar, Upright Shaft & Hook Driving Shaft", "section-04-needle_bar.png"),
    10: (5, "Hand Lifter Components", "section-05-hand_lifter.png"),
    12: (6, "Feed Mechanism Components", "section-06-feed_mechanism.png"),
    14: (7, "Thread Trimmer Components", "section-07-thread_trimmer.png"),
    15: (8, "Automatic Reverse Feed Components", "section-08-automatic_reverse.png"),
    16: (9, "Exclusive Parts Type NB", "section-09-exclusive_parts_nb.png"),
    18: (10, "Oil Lubrication Components", "section-10-oil_lubrication.png"),
    20: (11, "Oil Reservoir Components", "section-11-oil_reservoir.png"),
    21: (12, "Accessories Parts Components", "section-12-accessories.png"),
    22: (13, "Thread Stand Components", "section-13-thread_stand.png"),
    23: (14, "PSC Unit", "section-14-psc_unit.png"),
}

meta = "{\n" + ",\n".join(
    f"            {p}: {{'number': {n}, 'title': '{title}', 'image': 'images/mechanisms/juki/ddl7000a/{img}'}}"
    for p, (n, title, img) in sections.items()
) + "\n        }"

new_loop = f'''                    {{% if machine["id"] == 4 %}}
                    {{% set ddl_sections = {meta} %}}
                    {{% set ns = namespace(index=0) %}}
                    {{% for page, section_parts in parts|groupby("diagram_page") %}}
                    {{% set section = ddl_sections.get(page|int) %}}
                    <tr class="ddl-section-row" data-section-page="{{{{ page }}}}">
                        <td colspan="6" style="padding:14px; background:#eef3f8;">
                            <h3 style="margin:4px 0 8px;">Section {{{{ section.number if section else "" }}}} — {{{{ section.title if section else "Section katalog" }}}}</h3>
                            <p style="margin:4px 0 10px;">Halaman katalog: {{{{ page }}}}</p>
                            {{% if section %}}
                            <img src="{{{{ url_for('static', filename=section.image) }}}}"
                                 alt="Diagram {{{{ section.title }}}}"
                                 loading="lazy"
                                 style="display:block; max-width:100%; max-height:420px; object-fit:contain; background:white; border:1px solid #ddd;">
                            {{% endif %}}
                        </td>
                    </tr>
                    {{% for part in section_parts %}}
                    {{% set ns.index = ns.index + 1 %}}
                    <tr class="part-row"
                        data-search="{{{{ part['part_number'] }}}} {{{{ part['part_name'] }}}}"
                        data-catalog="{{{{ part['catalog_ref'] or '' }}}}"
                        data-page="{{{{ part['diagram_page'] or '' }}}}">
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
addition = needle + '''
            const sectionHeaders = Array.from(
                document.querySelectorAll("#parts-table .ddl-section-row")
            );'''
if needle not in text:
    raise SystemExit("GAGAL: lokasi JavaScript rows tidak ditemukan.")
text = text.replace(needle, addition, 1)

needle2 = '''                resultCount.textContent = visible;'''
addition2 = '''                sectionHeaders.forEach(function(header) {
                    const page = header.dataset.sectionPage;
                    const hasVisibleParts = rows.some(function(row) {
                        return row.dataset.page === page &&
                               row.style.display !== "none";
                    });
                    header.style.display = hasVisibleParts ? "" : "none";
                });

                resultCount.textContent = visible;'''
if needle2 not in text:
    raise SystemExit("GAGAL: lokasi pembaruan jumlah hasil tidak ditemukan.")
text = text.replace(needle2, addition2, 1)

dst.write_text(text, encoding="utf-8")

print("PROPOSAL BERHASIL DIBUAT")
print("File:", dst)
print("Section dipetakan:", len(sections))
print("Halaman:", ", ".join(map(str, sections.keys())))
print("Template asli: tidak diubah")
print("Database: tidak diubah")
