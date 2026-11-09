from pathlib import Path
from datetime import datetime
import shutil
import sys

app_path = Path("app.py")
tpl_path = Path("templates/machine_detail.html")
app = app_path.read_text()
tpl = tpl_path.read_text()

if "section27_parts" in app or "section27-catalog" in tpl:
    sys.exit("ABORT: Section 27 sudah terdeteksi; tidak ada perubahan.")

# Sisipkan query Section 27 sebelum query documents.
marker = "    documents = conn.execute("
if app.count(marker) != 1:
    sys.exit("ABORT: lokasi query documents tidak unik.")

query = [
    "    # Katalog Section 27 khusus JUKI AMS-210EN-2210",
    "    section27_parts = []",
    "    if machine_id == 44:",
    "        section27_parts = conn.execute(",
    '            "SELECT catalog_ref, marker, part_number, part_name, quantity_raw "',
    '            "FROM catalog_occurrences WHERE machine_id = ? AND pdf_page = ? "',
    '            "ORDER BY CAST(catalog_ref AS INTEGER), id",',
    "            (machine_id, 52)",
    "        ).fetchall()",
    "",
    marker
]
app2 = app.replace(marker, "\n".join(query), 1)

arg = "        parts=parts,\n        documents=documents,"
if app2.count(arg) != 1:
    sys.exit("ABORT: lokasi argumen template tidak unik.")
app2 = app2.replace(
    arg,
    "        parts=parts,\n        section27_parts=section27_parts,\n        documents=documents,",
    1
)

nav = '        <a href="#parts-list">📦 Parts</a>'
if tpl.count(nav) != 1:
    sys.exit("ABORT: tautan Parts tidak ditemukan tepat satu kali.")
tpl2 = tpl.replace(
    nav,
    '        <a href="#section27-catalog">📑 Section 27</a>\n' + nav,
    1
)

section_lines = [
    '    {% if machine["id"] == 44 and section27_parts %}',
    '    <section id="section27-catalog">',
    '        <h2>Section 27 — OPTIONAL PART COMPONENTS (3)</h2>',
    '        <p><strong>Total catalog entries:</strong> {{ section27_parts|length }}</p>',
    '        <div style="overflow-x:auto;">',
    '            <table style="width:100%; border-collapse:collapse;">',
    '                <thead><tr><th>REF</th><th>Marker</th><th>Part Number</th><th>Part Name</th><th>Qty</th></tr></thead>',
    '                <tbody>',
    '                {% for item in section27_parts %}',
    '                    <tr>',
    '                        <td>{{ item["catalog_ref"] }}</td>',
    '                        <td>{{ item["marker"] }}</td>',
    '                        <td>{{ item["part_number"] }}</td>',
    '                        <td>{{ item["part_name"] }}</td>',
    '                        <td>{{ item["quantity_raw"] }}</td>',
    '                    </tr>',
    '                {% endfor %}',
    '                </tbody>',
    '            </table>',
    '        </div>',
    '        <p>Source: JUKI AMS-210EN Series PARTS LIST, PDF page 52.</p>',
    '    </section>',
    '    {% endif %}',
    '',
]
section = "\n".join(section_lines)
parts_anchor = '    <section id="parts-list">'
if tpl2.count(parts_anchor) != 1:
    sys.exit("ABORT: anchor Parts List tidak unik.")
tpl2 = tpl2.replace(parts_anchor, section + "\n" + parts_anchor, 1)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
Path("backups").mkdir(exist_ok=True)
shutil.copy2(app_path, f"backups/app.py.before-section27-{stamp}")
shutil.copy2(tpl_path, f"backups/machine_detail.html.before-section27-{stamp}")

app_path.write_text(app2)
tpl_path.write_text(tpl2)
print("PATCH OK")
print("Backup dibuat; database tidak diubah.")
