from pathlib import Path
from datetime import datetime
import ast
import re
import shutil
import sys

ap = Path("app.py")
hp = Path("templates/index.html")
app = ap.read_text()
html = hp.read_text()

start = '@app.route("/")\ndef index():'
end = '@app.route("/add-machine", methods=["GET", "POST"])'

if app.count(start) != 1 or app.count(end) != 1:
    sys.exit("BATAL: batas route index tidak cocok.")

old_route = app[app.index(start):app.index(end)]

new_route = '''@app.route("/")
def index():
    brand_id = request.args.get("brand_id", type=int)
    model_search = request.args.get("model", "").strip()

    conn = get_db()
    try:
        brands = conn.execute(
            "SELECT * FROM brands ORDER BY name"
        ).fetchall()
        machine_types = conn.execute(
            "SELECT * FROM machine_types ORDER BY name"
        ).fetchall()

        selected_brand_name = None
        if brand_id is not None:
            selected_brand = conn.execute(
                "SELECT name FROM brands WHERE id = ?", (brand_id,)
            ).fetchone()
            if selected_brand:
                selected_brand_name = selected_brand["name"]
            else:
                brand_id = None

        statistics = {
            "brands": conn.execute(
                "SELECT COUNT(*) FROM brands"
            ).fetchone()[0],
            "machines": conn.execute(
                "SELECT COUNT(*) FROM machines"
            ).fetchone()[0],
            "documents": conn.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0],
            "components": conn.execute(
                "SELECT COUNT(*) FROM components"
            ).fetchone()[0],
            "parts": conn.execute(
                "SELECT COUNT(*) FROM parts"
            ).fetchone()[0]
        }

        conditions = []
        params = []

        if brand_id is not None:
            conditions.append("machines.brand_id = ?")
            params.append(brand_id)

        if model_search:
            conditions.append(
                "UPPER(COALESCE(machines.model, '')) LIKE ?"
            )
            params.append(model_search.upper() + "%")

        where_clause = (
            " WHERE " + " AND ".join(conditions)
            if conditions else ""
        )

        machines = conn.execute(f"""
            SELECT machines.*,
                   brands.name AS brand_name,
                   machine_types.name AS type_name,
                   (SELECT COUNT(*) FROM specifications
                    WHERE machine_id = machines.id)
                       AS specifications_count,
                   (SELECT COUNT(*) FROM components
                    WHERE machine_id = machines.id)
                       AS components_count,
                   (SELECT COUNT(*) FROM parts
                    WHERE machine_id = machines.id)
                       AS parts_count,
                   (SELECT COUNT(*) FROM troubleshooting
                    WHERE machine_id = machines.id)
                       AS troubleshooting_count,
                   (SELECT COUNT(*) FROM documents
                    WHERE machine_id = machines.id)
                       AS documents_count
            FROM machines
            LEFT JOIN brands ON machines.brand_id = brands.id
            LEFT JOIN machine_types
                ON machines.machine_type_id = machine_types.id
            {where_clause}
            ORDER BY brands.name, machines.model
        """, params).fetchall()
    finally:
        conn.close()

    return render_template(
        "index.html",
        brands=brands,
        machine_types=machine_types,
        machines=machines,
        brand_id=brand_id,
        selected_brand_name=selected_brand_name,
        model_search=model_search,
        statistics=statistics
    )


'''

filter_section = new_route.split("conditions = []", 1)[1].split(
    "where_clause =", 1
)[0]
assert "machines.brand_id = ?" in filter_section
assert "UPPER(COALESCE(machines.model, '')) LIKE ?" in filter_section
assert "EXISTS" not in filter_section
for forbidden in ("troubleshooting", "specifications", "components", "parts"):
    assert forbidden not in filter_section

new_app = app.replace(old_route, new_route, 1)
ast.parse(new_app)

form_pattern = re.compile(
    r'<form method="GET" action="/" class="industrial-search">.*?</form>',
    re.S
)
forms = list(form_pattern.finditer(html))
if len(forms) != 1 or 'name="search"' not in forms[0].group():
    sys.exit("BATAL: form pencarian lama tidak cocok.")

new_form = '''<form method="GET" action="/" class="industrial-search">
            <select name="brand_id" aria-label="Pilih merek mesin">
                <option value="">Semua Merek</option>
                {% for brand in brands %}
                <option value="{{ brand['id'] }}" {% if brand_id == brand['id'] %}selected{% endif %}>{{ brand['name'] }}</option>
                {% endfor %}
            </select>
            <input
                type="text"
                name="model"
                value="{{ model_search }}"
                placeholder="Seri / model, contoh AMS, DDL, DLN, KE, HE"
                aria-label="Cari seri atau model mesin"
            >
            <button type="submit">Cari Mesin</button>
        </form>'''

heading_pattern = re.compile(
    r'(?m)^([ \t]*)\{% if search %\}[ \t]*\n'
    r'[ \t]*<section>[ \t]*\n'
    r'[ \t]*<h2>🔎 Hasil pencarian: "\{\{ search \}\}"</h2>'
)
if len(list(heading_pattern.finditer(html))) != 1:
    sys.exit("BATAL: heading hasil pencarian tidak cocok.")

new_html = form_pattern.sub(lambda m: new_form, html, count=1)
new_heading = (
    r'\1{% if brand_id or model_search %}' + '\n'
    r'    <section>' + '\n'
    r'        <h2>🔎 Hasil pencarian mesin'
    r'{% if selected_brand_name %} — {{ selected_brand_name }}{% endif %}'
    r'{% if model_search %} — {{ model_search }}{% endif %}</h2>'
)
new_html = heading_pattern.sub(lambda m: new_heading, new_html, count=1)

if 'name="search"' in new_html or '{{ search }}' in new_html:
    sys.exit("BATAL: referensi pencarian lama masih tersisa.")
if 'name="brand_id"' not in new_html or 'name="model"' not in new_html:
    sys.exit("BATAL: validasi form gagal.")
if "{% if brand_id or model_search %}" not in new_html:
    sys.exit("BATAL: validasi heading gagal.")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
ab = Path(f"app.py.backup-search-final-{stamp}")
hb = Path(f"templates/index.html.backup-search-final-{stamp}")

shutil.copy2(ap, ab)
shutil.copy2(hp, hb)
ap.write_text(new_app)
hp.write_text(new_html)

print("PATCH BERHASIL")
print("Backup app      :", ab)
print("Backup template :", hb)
print("Filter          : merek + awalan model saja")
print("Database        : tidak diubah")
