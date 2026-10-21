from juki_importer import ambil_spesifikasi_ddl8700
from flask import Response, Flask, render_template, request, redirect, send_file, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import csv
import os
import hmac
import re
import secrets
import sqlite3

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = generate_csrf_token


@app.before_request
def validate_admin_csrf():
    if request.method != "POST":
        return None

    path = request.path
    protected = (
        path == "/admin/login"
        or path == "/admin/needle-systems/add"
        or path == "/admin/needle-series"
        or re.fullmatch(
            r"/admin/needle-series/\d+/edit",
            path,
        )
        or re.fullmatch(
            r"/admin/needle-systems/\d+/(?:edit|delete)",
            path,
        )
    )

    if not protected:
        return None

    expected = session.get("_csrf_token")
    supplied = request.form.get("_csrf_token", "")

    if (
        not isinstance(expected, str)
        or not supplied
        or not hmac.compare_digest(expected, supplied)
    ):
        return (
            "Permintaan ditolak: token CSRF tidak valid. "
            "Muat ulang halaman dan coba lagi.",
            400,
        )


from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated_function


# Menyajikan file lokal yang berada di dalam folder assets.
@app.route("/local-file/<path:filename>")
def local_file(filename):
    assets_root = os.path.abspath(os.path.join(app.root_path, "assets"))
    requested_path = os.path.abspath(os.path.join(assets_root, filename))

    # Cegah path traversal keluar dari folder assets.
    if os.path.commonpath([assets_root, requested_path]) != assets_root:
        return "Akses file ditolak.", 403

    if not os.path.isfile(requested_path):
        return "File tidak ditemukan.", 404

    return send_file(requested_path)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            session["admin_logged_in"] = True
            return redirect("/")

        return render_template("admin_login.html", error="Username atau password salah.")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/")


DATABASE = "database/garment.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
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


@app.route("/add-machine", methods=["GET", "POST"])
@admin_required
def add_machine():

    conn = get_db()

    brands = conn.execute(
        "SELECT * FROM brands ORDER BY name"
    ).fetchall()

    machine_types = conn.execute(
        "SELECT * FROM machine_types ORDER BY name"
    ).fetchall()

    if request.method == "POST":

        brand_id = request.form["brand_id"]
        machine_type_id = request.form["machine_type_id"]
        model = request.form["model"].strip()
        function = request.form["function"].strip()
        description = request.form["description"].strip()
        notes = request.form.get("notes", "").strip()

        conn.execute(
            """
            INSERT INTO machines
            (brand_id, machine_type_id, model, function, description, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                brand_id,
                machine_type_id,
                model,
                function,
                description,
                notes
            )
        )

        conn.commit()
        conn.close()

        return redirect("/")

    conn.close()

    return render_template(
        "add_machine.html",
        brands=brands,
        machine_types=machine_types
    )


@app.route("/troubleshooting")
def troubleshooting():
    conn = get_db()

    search = request.args.get("search", "").strip()
    brand_id = request.args.get("brand_id", "").strip()
    machine_id = request.args.get("machine_id", "").strip()

    brands = conn.execute(
        "SELECT id, name FROM brands ORDER BY name"
    ).fetchall()

    machines = conn.execute("""
        SELECT machines.id, machines.model, machines.brand_id,
               brands.name AS brand_name
        FROM machines
        LEFT JOIN brands ON machines.brand_id = brands.id
        ORDER BY brands.name, machines.model
    """).fetchall()

    valid_brand_ids = {str(b["id"]) for b in brands}
    valid_machine_ids = {str(m["id"]) for m in machines}

    if brand_id not in valid_brand_ids:
        brand_id = ""

    if machine_id not in valid_machine_ids:
        machine_id = ""

    selected_machine = next(
        (m for m in machines if str(m["id"]) == machine_id), None
    )

    if selected_machine:
        selected_brand = str(selected_machine["brand_id"] or "")
        if not brand_id:
            brand_id = selected_brand
        elif brand_id != selected_brand:
            machine_id = ""

    query = """
        SELECT troubleshooting.*,
               machines.model AS machine_model,
               brands.name AS brand_name
        FROM troubleshooting
        LEFT JOIN machines ON troubleshooting.machine_id = machines.id
        LEFT JOIN brands ON machines.brand_id = brands.id
    """
    params = []
    troubleshooting_data = []

    if brand_id and machine_id:
        query += " WHERE troubleshooting.machine_id = ?"
        params.append(int(machine_id))

        if search:
            conditions = []
            for word in search.split():
                pattern = f"%{word}%"
                conditions.append(
                    "("
                    "troubleshooting.code LIKE ? OR "
                    "troubleshooting.problem LIKE ? OR "
                    "troubleshooting.symptoms LIKE ? OR "
                    "troubleshooting.possible_cause LIKE ? OR "
                    "troubleshooting.solution LIKE ? OR "
                    "troubleshooting.safety_notes LIKE ? OR "
                    "troubleshooting.source LIKE ? OR "
                    "machines.model LIKE ? OR brands.name LIKE ?"
                    ")"
                )
                params.extend([pattern] * 9)

            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY troubleshooting.id DESC"
        troubleshooting_data = conn.execute(query, params).fetchall()

    conn.close()

    return render_template(
        "troubleshooting.html",
        troubleshooting_data=troubleshooting_data,
        search=search,
        brand_id=brand_id,
        machine_id=machine_id,
        brands=brands,
        machines=machines
    )


@app.route("/add-troubleshooting", methods=["GET", "POST"])
@admin_required
def add_troubleshooting():

    conn = get_db()

    machines = conn.execute(
        """
        SELECT
            machines.id,
            machines.model,
            brands.name AS brand_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        ORDER BY brands.name, machines.model
        """
    ).fetchall()

    if request.method == "POST":

        machine_id = request.form["machine_id"]
        problem = request.form["problem"].strip()
        symptoms = request.form["symptoms"].strip()
        possible_cause = request.form["possible_cause"].strip()
        solution = request.form["solution"].strip()
        safety_notes = request.form["safety_notes"].strip()
        source = request.form["source"].strip()

        conn.execute(
            """
            INSERT INTO troubleshooting
            (
                machine_id,
                problem,
                symptoms,
                possible_cause,
                solution,
                safety_notes,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id,
                problem,
                symptoms,
                possible_cause,
                solution,
                safety_notes,
                source
            )
        )

        conn.commit()
        conn.close()

        return redirect("/troubleshooting")

    conn.close()

    return render_template(
        "add_troubleshooting.html",
        machines=machines
    )


@app.route("/import-troubleshooting-csv", methods=["GET", "POST"])
@admin_required
def import_troubleshooting_csv():

    if request.method == "GET":
        return "Gunakan POST untuk mengimpor troubleshooting.csv."

    conn = get_db()

    inserted = 0
    skipped = 0

    try:
        with open("troubleshooting.csv", "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            required_columns = [
                "Mesin",
                "Masalah",
                "Gejala",
                "Kemungkinan Penyebab",
                "Solusi",
                "Catatan Keselamatan",
                "Sumber"
            ]

            if reader.fieldnames != required_columns:
                conn.close()
                return "Format CSV tidak sesuai. Periksa header troubleshooting.csv.", 400

            for row in reader:

                machine_text = row["Mesin"].strip()
                problem = row["Masalah"].strip()

                if not machine_text or not problem:
                    skipped += 1
                    continue

                parts = machine_text.split(" ", 1)

                if len(parts) != 2:
                    skipped += 1
                    continue

                brand_name = parts[0].strip()
                model = parts[1].strip()

                machine = conn.execute(
                    """
                    SELECT
                        machines.id
                    FROM machines
                    JOIN brands
                        ON machines.brand_id = brands.id
                    WHERE LOWER(brands.name) = LOWER(?)
                      AND LOWER(machines.model) = LOWER(?)
                    """,
                    (brand_name, model)
                ).fetchone()

                if machine is None:
                    skipped += 1
                    continue

                existing = conn.execute(
                    """
                    SELECT id
                    FROM troubleshooting
                    WHERE machine_id = ?
                      AND LOWER(problem) = LOWER(?)
                    """,
                    (machine["id"], problem)
                ).fetchone()

                if existing:
                    skipped += 1
                    continue

                conn.execute(
                    """
                    INSERT INTO troubleshooting
                    (
                        machine_id,
                        problem,
                        symptoms,
                        possible_cause,
                        solution,
                        safety_notes,
                        source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        machine["id"],
                        problem,
                        row["Gejala"].strip(),
                        row["Kemungkinan Penyebab"].strip(),
                        row["Solusi"].strip(),
                        row["Catatan Keselamatan"].strip(),
                        row["Sumber"].strip()
                    )
                )

                inserted += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        conn.close()
        return f"Gagal import CSV: {e}", 500

    conn.close()

    return (
        f"Import selesai. Data baru: {inserted}. "
        f"Data dilewati: {skipped}. "
        f"<br><br><a href='/troubleshooting'>Kembali ke Troubleshooting</a>"
    )


@app.route("/components")
def components_list():
    conn = get_db()

    search = request.args.get("search", "").strip()
    brand_id = request.args.get("brand_id", type=int)
    machine_id = request.args.get("machine_id", type=int)
    component_id = request.args.get("component_id", type=int)
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = 25

    # Validasi merek.
    if brand_id and not conn.execute(
        "SELECT 1 FROM brands WHERE id = ?", (brand_id,)
    ).fetchone():
        brand_id = None
        machine_id = None
        component_id = None

    # Validasi seri mesin terhadap merek yang dipilih.
    if machine_id:
        machine_row = conn.execute(
            "SELECT brand_id FROM machines WHERE id = ?", (machine_id,)
        ).fetchone()
        if not machine_row or (
            brand_id and machine_row["brand_id"] != brand_id
        ):
            machine_id = None
            component_id = None
        else:
            brand_id = machine_row["brand_id"]

    # Validasi komponen terhadap mesin yang dipilih.
    if component_id:
        comp_row = conn.execute(
            "SELECT machine_id FROM components WHERE id = ?",
            (component_id,)
        ).fetchone()
        if not comp_row or (
            machine_id and comp_row["machine_id"] != machine_id
        ):
            component_id = None
        else:
            machine_id = comp_row["machine_id"]
            machine_row = conn.execute(
                "SELECT brand_id FROM machines WHERE id = ?",
                (machine_id,)
            ).fetchone()
            if not machine_row:
                machine_id = None
                component_id = None
            elif brand_id and machine_row["brand_id"] != brand_id:
                machine_id = None
                component_id = None
            else:
                brand_id = machine_row["brand_id"]

    brands = conn.execute(
        "SELECT id, name FROM brands ORDER BY name"
    ).fetchall()

    machine_options = []
    if brand_id:
        machine_options = conn.execute(
            """SELECT id, model FROM machines
               WHERE brand_id = ? ORDER BY model""",
            (brand_id,)
        ).fetchall()

    component_options = []
    if machine_id:
        component_options = conn.execute(
            """SELECT id, component_name, part_number
               FROM components
               WHERE machine_id = ?
               ORDER BY component_name, part_number""",
            (machine_id,)
        ).fetchall()

    from_sql = """
        FROM components
        LEFT JOIN machines ON components.machine_id = machines.id
        LEFT JOIN brands ON machines.brand_id = brands.id
    """
    conditions = []
    params = []

    if brand_id:
        conditions.append("machines.brand_id = ?")
        params.append(brand_id)
    if machine_id:
        conditions.append("components.machine_id = ?")
        params.append(machine_id)
    if component_id:
        conditions.append("components.id = ?")
        params.append(component_id)

    if search:
        search_terms = [w for w in search.replace("—", " ").replace("–", " ").split() if w]
        for word in search_terms:
            pattern = f"%{word}%"
            conditions.append(
                "("
                "components.component_name LIKE ? OR "
                "components.part_number LIKE ? OR "
                "components.location LIKE ? OR "
                "components.function LIKE ? OR "
                "components.notes LIKE ? OR "
                "machines.model LIKE ? OR "
                "brands.name LIKE ? OR "
                "EXISTS ("
                "SELECT 1 FROM component_parts cp "
                "JOIN parts p ON p.id = cp.part_id "
                "WHERE cp.component_id = components.id "
                "AND (p.part_number LIKE ? OR p.part_name LIKE ?)"
                ")"
                ")"
            )
            params.extend([pattern] * 9)

    where_sql = (
        " WHERE " + " AND ".join(conditions) if conditions else ""
    )

    total_count = conn.execute(
        "SELECT COUNT(*) " + from_sql + where_sql, params
    ).fetchone()[0]

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    query = """
        SELECT components.*,
               machines.model AS machine_model,
               brands.name AS brand_name
    """ + from_sql + where_sql + """
        ORDER BY brands.name, machines.model, components.component_name
        LIMIT ? OFFSET ?
    """
    components_data = conn.execute(
        query, params + [per_page, offset]
    ).fetchall()

    # Ambil seluruh spare part yang terhubung ke mekanisme terpilih.
    mechanism_parts = []
    selected_mechanism = None

    if component_id:
        selected_mechanism = conn.execute(
            "SELECT id, component_name FROM components WHERE id = ?",
            (component_id,)
        ).fetchone()

        mechanism_parts = conn.execute(
            """
            SELECT
                parts.*,
                component_parts.relation_type,
                component_parts.notes AS relation_notes,
                components.component_name AS mechanism_name
            FROM component_parts
            JOIN parts
                ON parts.id = component_parts.part_id
            JOIN components
                ON components.id = component_parts.component_id
            WHERE component_parts.component_id = ?
            ORDER BY
                CASE WHEN parts.catalog_ref IS NULL THEN 1 ELSE 0 END,
                CAST(parts.catalog_ref AS INTEGER),
                parts.part_number
            """,
            (component_id,)
        ).fetchall()

    # Pencarian langsung juga mencakup tabel spare part.
    parts_search_data = []

    if search:
        parts_from_sql = """
            FROM parts
            LEFT JOIN machines ON parts.machine_id = machines.id
            LEFT JOIN brands ON machines.brand_id = brands.id
        """
        parts_conditions = []
        parts_params = []

        if brand_id:
            parts_conditions.append("machines.brand_id = ?")
            parts_params.append(brand_id)

        if machine_id:
            parts_conditions.append("parts.machine_id = ?")
            parts_params.append(machine_id)

        search_terms = [w for w in search.replace("—", " ").replace("–", " ").split() if w]
        for word in search_terms:
            pattern = f"%{word}%"
            parts_conditions.append(
                "("
                "parts.part_number LIKE ? OR "
                "parts.part_name LIKE ? OR "
                "COALESCE(parts.note, '') LIKE ? OR "
                "COALESCE(parts.notes, '') LIKE ? OR "
                "machines.model LIKE ? OR "
                "brands.name LIKE ?"
                ")"
            )
            parts_params.extend([pattern] * 6)

        parts_where = (
            " WHERE " + " AND ".join(parts_conditions)
            if parts_conditions else ""
        )

        parts_search_data = conn.execute(
            """
            SELECT parts.*,
                   machines.model AS machine_model,
                   brands.name AS brand_name
            """ + parts_from_sql + parts_where + """
            ORDER BY brands.name, machines.model, parts.part_number
            LIMIT 100
            """,
            parts_params
        ).fetchall()

    conn.close()

    return render_template(
        "components.html",
        components_data=components_data,
        search=search,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        brands=brands,
        machine_options=machine_options,
        component_options=component_options,
        brand_id=brand_id,
        machine_id=machine_id,
        component_id=component_id,
        mechanism_parts=mechanism_parts,
        selected_mechanism=selected_mechanism,
        parts_search_data=parts_search_data
    )


@app.route("/machine/<int:machine_id>")
def machine_detail(machine_id):

    conn = get_db()

    machine = conn.execute(
        """
        SELECT
            machines.*,
            brands.name AS brand_name,
            machine_types.name AS type_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        LEFT JOIN machine_types
            ON machines.machine_type_id = machine_types.id
        WHERE machines.id = ?
        """,
        (machine_id,)
    ).fetchone()

    if machine is None:
        conn.close()
        return "Mesin tidak ditemukan", 404

    troubleshooting_data = conn.execute(
        """
        SELECT *
        FROM troubleshooting
        WHERE machine_id = ?
        ORDER BY id DESC
        """,
        (machine_id,)
    ).fetchall()

    specifications = conn.execute(
        """
        SELECT *
        FROM specifications
        WHERE machine_id = ?
        ORDER BY id
        """,
        (machine_id,)
    ).fetchall()

    components = conn.execute(
        """
        SELECT *
        FROM components
        WHERE machine_id = ?
        ORDER BY id
        """,
        (machine_id,)
    ).fetchall()

    component_parts = conn.execute(
        """
        SELECT
            component_parts.component_id,
            component_parts.part_id,
            component_parts.relation_type,
            component_parts.notes AS relation_notes,
            parts.part_number,
            parts.part_name
        FROM component_parts
        JOIN parts
            ON component_parts.part_id = parts.id
        JOIN components
            ON component_parts.component_id = components.id
        WHERE components.machine_id = ?
        ORDER BY component_parts.component_id, parts.id
        """,
        (machine_id,)
    ).fetchall()

    parts = conn.execute(
        """
        SELECT *
        FROM parts
        WHERE machine_id = ?
        ORDER BY id
        """,
        (machine_id,)
    ).fetchall()

    documents = conn.execute(
        """
        SELECT *
        FROM documents
        WHERE machine_id = ?
        ORDER BY id DESC
        """,
        (machine_id,)
    ).fetchall()

    technician_notes = conn.execute(
        """
        SELECT *
        FROM technician_notes
        WHERE machine_id = ?
        ORDER BY id DESC
        """,
        (machine_id,)
    ).fetchall()

    needle_compatibility_data = conn.execute(
        """
        SELECT
            n.id AS needle_id,
            n.brand AS needle_brand,
            n.needle_system,
            n.size_nm,
            n.size_nm_value,
            n.manufacturer_size,
            nc.compatibility_status,
            nc.source_url,
            nc.notes
        FROM needle_machine_compatibility nc
        JOIN needles n ON n.id = nc.needle_id
        WHERE nc.machine_id = ?
        ORDER BY n.brand, n.needle_system, n.size_nm_value, n.id
        """,
        (machine_id,)
    ).fetchall()


    conn.close()

    return render_template(
        "machine_detail.html",
        machine=machine,
        troubleshooting_data=troubleshooting_data,
        specifications=specifications,
        components=components,
        component_parts=component_parts,
        parts=parts,
        documents=documents,
        technician_notes=technician_notes,
        needle_compatibility_data=needle_compatibility_data
    )

@app.route("/specifications")
def specifications_list():
    brand_id = request.args.get("brand_id", type=int)
    model_search = request.args.get("model", "").strip()
    spec_search = request.args.get("specification", "").strip()

    conn = get_db()
    try:
        brands = conn.execute(
            "SELECT id, name FROM brands ORDER BY name"
        ).fetchall()

        conditions = []
        params = []

        if brand_id is not None:
            conditions.append("machines.brand_id = ?")
            params.append(brand_id)

        if model_search:
            conditions.append("LOWER(COALESCE(machines.model, '')) LIKE ?")
            params.append("%" + model_search.lower() + "%")

        if spec_search:
            conditions.append(
                "(LOWER(COALESCE(specifications.specification, '')) LIKE ? "
                "OR LOWER(COALESCE(specifications.value, '')) LIKE ? "
                "OR LOWER(COALESCE(specifications.description, '')) LIKE ? "
                "OR LOWER(COALESCE(specifications.notes, '')) LIKE ?)"
            )
            keyword = "%" + spec_search.lower() + "%"
            params.extend([keyword, keyword, keyword, keyword])

        where_clause = (
            " WHERE " + " AND ".join(conditions)
            if conditions else " WHERE 1=0"
        )

        rows = conn.execute(
            """
            SELECT
                specifications.id,
                specifications.machine_id,
                specifications.specification,
                specifications.value,
                specifications.notes,
                specifications.description,
                machines.model,
                brands.name AS brand_name
            FROM specifications
            JOIN machines
                ON specifications.machine_id = machines.id
            LEFT JOIN brands
                ON machines.brand_id = brands.id
            """
            + where_clause
            + """
            ORDER BY brands.name, machines.model,
                     specifications.specification
            """,
            params
        ).fetchall()

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM specifications
            JOIN machines ON specifications.machine_id = machines.id
            """
        ).fetchone()[0]
    finally:
        conn.close()

    return render_template(
        "specifications.html",
        brands=brands,
        rows=rows,
        brand_id=brand_id,
        model_search=model_search,
        spec_search=spec_search,
        total=total
    )


@app.route("/add-specification/<int:machine_id>", methods=["GET", "POST"])
@admin_required
def add_specification(machine_id):

    conn = get_db()

    machine = conn.execute(
        """
        SELECT
            machines.*,
            brands.name AS brand_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE machines.id = ?
        """,
        (machine_id,)
    ).fetchone()

    if machine is None:
        conn.close()
        return "Mesin tidak ditemukan", 404

    if request.method == "POST":

        specification = request.form["specification"].strip()
        value = request.form["value"].strip()
        notes = request.form["notes"].strip()
        description = request.form["description"].strip()


        conn.execute(
            """
            INSERT INTO specifications
            (machine_id, specification, value, notes, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (machine_id, specification, value, notes, description)
        )

        conn.commit()
        conn.close()

        return redirect(f"/machine/{machine_id}")

    conn.close()

    return render_template(
        "add_specification.html",
        machine=machine
    )

@app.route("/delete-specification/<int:spec_id>", methods=["POST"])
@admin_required
def delete_specification(spec_id):

    conn = get_db()

    specification = conn.execute(
        """
        SELECT machine_id
        FROM specifications
        WHERE id = ?
        """,
        (spec_id,)
    ).fetchone()

    if specification is None:
        conn.close()
        return "Spesifikasi tidak ditemukan", 404

    machine_id = specification["machine_id"]

    conn.execute(
        """
        DELETE FROM specifications
        WHERE id = ?
        """,
        (spec_id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/machine/{machine_id}")


@app.route("/edit-specification/<int:spec_id>", methods=["GET", "POST"])
@admin_required
def edit_specification(spec_id):

    conn = get_db()

    specification = conn.execute(
        """
        SELECT
            specifications.*,
            machines.model,
            brands.name AS brand_name
        FROM specifications
        JOIN machines
            ON specifications.machine_id = machines.id
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE specifications.id = ?
        """,
        (spec_id,)
    ).fetchone()

    if specification is None:
        conn.close()
        return "Spesifikasi tidak ditemukan", 404

    if request.method == "POST":

        specification_name = request.form["specification"].strip()
        value = request.form["value"].strip()
        notes = request.form["notes"].strip()
        description = request.form["description"].strip()


        conn.execute(
            """
            UPDATE specifications
            SET
                specification = ?,
                value = ?,
                description = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                specification_name,
                value,
                description,
                notes,
                spec_id
            )
        )

        conn.commit()

        machine_id = specification["machine_id"]

        conn.close()

        return redirect(f"/machine/{machine_id}")

    conn.close()

    return render_template(
        "edit_specification.html",
        specification=specification
    )


@app.route("/component/<int:component_id>")
def component_detail(component_id):

    conn = get_db()

    component = conn.execute(
        """
        SELECT
            components.*,
            machines.model AS machine_model,
            brands.name AS brand_name,
            machine_types.name AS type_name
        FROM components
        LEFT JOIN machines
            ON components.machine_id = machines.id
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        LEFT JOIN machine_types
            ON machines.machine_type_id = machine_types.id
        WHERE components.id = ?
        """,
        (component_id,)
    ).fetchone()

    if component is None:
        conn.close()
        return "Komponen tidak ditemukan", 404

    if (
        component["machine_model"] == "S-6200A"
        and component["component_name"] == "G. Rotary hook mechanism"
    ):
        sub_parts = conn.execute(
            """
            SELECT
                parts.*,
                component_parts.relation_type,
                component_parts.notes AS relation_notes
            FROM component_parts
            INNER JOIN parts
                ON component_parts.part_id = parts.id
            WHERE component_parts.component_id = ?
            ORDER BY
                CASE
                    WHEN LOWER(REPLACE(REPLACE(COALESCE(component_parts.notes, ''), ' ', ''), '-', '')) LIKE '%for[]03%' THEN 0
                    WHEN LOWER(REPLACE(REPLACE(COALESCE(component_parts.notes, ''), ' ', ''), '-', '')) LIKE '%for[]05%' THEN 1
                    ELSE 2
                END,
                CAST(parts.catalog_ref AS INTEGER),
                parts.id
            """,
            (component_id,)
        ).fetchall()
    else:
        sub_parts = conn.execute(
            """
            SELECT
                parts.*,
                component_parts.relation_type,
                component_parts.notes AS relation_notes
            FROM component_parts
            INNER JOIN parts
                ON component_parts.part_id = parts.id
            WHERE component_parts.component_id = ?
            ORDER BY parts.catalog_ref IS NULL,
                     CAST(parts.catalog_ref AS INTEGER),
                     parts.id
            """,
            (component_id,)
        ).fetchall()

    clamp_d1_parts = []
    clamp_d2_parts = []
    if component["machine_id"] == 227 and component["component_name"] == "Sistem Penjepit Bahan (Clamp)":
        clamp_d1_parts = conn.execute("SELECT * FROM parts WHERE machine_id = ? AND diagram_page = ? ORDER BY CAST(catalog_ref AS INTEGER), id", (227, 23)).fetchall()
        clamp_d2_parts = conn.execute("SELECT * FROM parts WHERE machine_id = ? AND diagram_page = ? ORDER BY CAST(catalog_ref AS INTEGER), id", (227, 25)).fetchall()

    conn.close()

    return render_template(
        "component_detail.html",
        component=component,
        sub_parts=sub_parts,
        clamp_d1_parts=clamp_d1_parts,
        clamp_d2_parts=clamp_d2_parts
    )


@app.route("/part/<int:part_id>")
def part_detail(part_id):

    conn = get_db()

    part = conn.execute(
        """
        SELECT
            parts.*,
            machines.model AS machine_model,
            brands.name AS brand_name
        FROM parts
        LEFT JOIN machines
            ON parts.machine_id = machines.id
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE parts.id = ?
        """,
        (part_id,)
    ).fetchone()

    if part is None:
        conn.close()
        return "Part tidak ditemukan", 404

    components = conn.execute(
        """
        SELECT
            components.id,
            components.component_name,
            components.part_number,
            components.location,
            component_parts.relation_type,
            component_parts.notes AS relation_notes
        FROM component_parts
        INNER JOIN components
            ON component_parts.component_id = components.id
        WHERE component_parts.part_id = ?
        ORDER BY components.id
        """,
        (part_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "part_detail.html",
        part=part,
        components=components
    )


@app.route("/add-component/<int:machine_id>", methods=["GET", "POST"])
@admin_required
def add_component(machine_id):

    conn = get_db()

    machine = conn.execute(
        """
        SELECT
            machines.*,
            brands.name AS brand_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE machines.id = ?
        """,
        (machine_id,)
    ).fetchone()

    if machine is None:
        conn.close()
        return "Mesin tidak ditemukan", 404

    if request.method == "POST":

        component_name = request.form["component_name"].strip()
        part_number = request.form["part_number"].strip()
        location = request.form["location"].strip()
        function = request.form["function"].strip()
        notes = request.form["notes"].strip()

        image = request.files.get("image")

        image_path = None

        if image and image.filename:

            allowed_extensions = {
                "jpg",
                "jpeg",
                "png",
                "webp"
            }

            extension = image.filename.rsplit(".", 1)[-1].lower()

            if extension not in allowed_extensions:
                conn.close()
                return "Format foto tidak didukung. Gunakan JPG, JPEG, PNG, atau WEBP.", 400

            filename = secure_filename(image.filename)

            base_name = os.path.splitext(filename)[0]
            filename = f"{machine_id}_{base_name}_{os.getpid()}.{extension}"

            upload_folder = os.path.join(
                app.root_path,
                "static",
                "component_images"
            )

            os.makedirs(upload_folder, exist_ok=True)

            image.save(
                os.path.join(upload_folder, filename)
            )

            image_path = f"component_images/{filename}"

        conn.execute(
            """
            INSERT INTO components
            (
                machine_id,
                component_name,
                part_number,
                location,
                function,
                notes,
                image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id,
                component_name,
                part_number,
                location,
                function,
                notes,
                image_path
            )
        )

        conn.commit()
        conn.close()

        return redirect(f"/machine/{machine_id}")

    conn.close()

    return render_template(
        "add_component.html",
        machine=machine
    )


@app.route("/edit-component/<int:component_id>", methods=["GET", "POST"])
@admin_required
def edit_component(component_id):

    conn = get_db()

    component = conn.execute(
        """
        SELECT
            components.*,
            machines.model,
            brands.name AS brand_name
        FROM components
        JOIN machines
            ON components.machine_id = machines.id
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE components.id = ?
        """,
        (component_id,)
    ).fetchone()

    if component is None:
        conn.close()
        return "Komponen tidak ditemukan", 404

    if request.method == "POST":

        component_name = request.form["component_name"].strip()
        part_number = request.form["part_number"].strip()
        location = request.form["location"].strip()
        function = request.form["function"].strip()
        notes = request.form["notes"].strip()

        conn.execute(
            """
            UPDATE components
            SET
                component_name = ?,
                part_number = ?,
                location = ?,
                function = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                component_name,
                part_number,
                location,
                function,
                notes,
                component_id
            )
        )

        conn.commit()

        machine_id = component["machine_id"]

        conn.close()

        return redirect(f"/machine/{machine_id}")

    conn.close()

    return render_template(
        "edit_component.html",
        component=component
    )


@app.route("/delete-component/<int:component_id>", methods=["POST"])
@admin_required
def delete_component(component_id):

    conn = get_db()

    component = conn.execute(
        """
        SELECT machine_id
        FROM components
        WHERE id = ?
        """,
        (component_id,)
    ).fetchone()

    if component is None:
        conn.close()
        return "Komponen tidak ditemukan", 404

    machine_id = component["machine_id"]

    conn.execute(
        """
        DELETE FROM components
        WHERE id = ?
        """,
        (component_id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/machine/{machine_id}")


@app.route("/add-document/<int:machine_id>", methods=["GET", "POST"])
@admin_required
def add_document(machine_id):

    conn = get_db()

    machine = conn.execute(
        """
        SELECT
            machines.*,
            brands.name AS brand_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE machines.id = ?
        """,
        (machine_id,)
    ).fetchone()

    if machine is None:
        conn.close()
        return "Mesin tidak ditemukan", 404

    if request.method == "POST":

        document_type = request.form["document_type"].strip()
        title = request.form["title"].strip()
        source_url = request.form["source_url"].strip()
        local_file = request.form["local_file"].strip()
        notes = request.form["notes"].strip()

        conn.execute(
            """
            INSERT INTO documents
            (
                machine_id,
                document_type,
                title,
                source_url,
                local_file,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id,
                document_type,
                title,
                source_url,
                local_file,
                notes
            )
        )

        conn.commit()
        conn.close()

        return redirect(f"/machine/{machine_id}")

    conn.close()

    return render_template(
        "add_document.html",
        machine=machine
    )


@app.route("/add-technician-note/<int:machine_id>", methods=["GET", "POST"])
@admin_required
def add_technician_note(machine_id):

    conn = get_db()

    machine = conn.execute(
        """
        SELECT
            machines.*,
            brands.name AS brand_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE machines.id = ?
        """,
        (machine_id,)
    ).fetchone()

    if machine is None:
        conn.close()
        return "Mesin tidak ditemukan", 404

    if request.method == "POST":

        problem = request.form["problem"].strip()
        diagnosis = request.form["diagnosis"].strip()
        action_taken = request.form["action_taken"].strip()
        result = request.form["result"].strip()
        technician = request.form["technician"].strip()

        conn.execute(
            """
            INSERT INTO technician_notes
            (
                machine_id,
                problem,
                diagnosis,
                action_taken,
                result,
                technician
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id,
                problem,
                diagnosis,
                action_taken,
                result,
                technician
            )
        )

        conn.commit()
        conn.close()

        return redirect(f"/machine/{machine_id}")

    conn.close()

    return render_template(
        "add_technician_note.html",
        machine=machine
    )


@app.route("/import-juki/<int:machine_id>", methods=["POST"])
@admin_required
def import_juki(machine_id):
    conn = get_db()

    machine = conn.execute(
        """
        SELECT machines.id, machines.model,
               brands.name AS brand_name
        FROM machines
        JOIN brands ON machines.brand_id = brands.id
        WHERE machines.id = ?
        """,
        (machine_id,)
    ).fetchone()

    if machine is None:
        conn.close()
        return "Mesin tidak ditemukan", 404

    if machine["brand_name"].upper() != "JUKI":
        conn.close()
        return "Import hanya untuk mesin JUKI.", 400

    if machine["model"].upper() != "DDL-8700":
        conn.close()
        return "Importer saat ini hanya untuk JUKI DDL-8700.", 400

    try:
        specs = ambil_spesifikasi_ddl8700()
    except Exception as e:
        conn.close()
        return f"Gagal mengambil data JUKI: {e}", 502

    inserted = 0

    existing_specs = {
        row["specification"]
        for row in conn.execute(
            """
            SELECT specification
            FROM specifications
            WHERE machine_id = ?
            """,
            (machine_id,)
        ).fetchall()
    }

    for specification, value in specs:

        if specification in existing_specs:
            continue

        conn.execute(
            """
            INSERT INTO specifications
            (
                machine_id,
                specification,
                value,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                machine_id,
                specification,
                value,
                "Sumber resmi JUKI"
            )
        )

        existing_specs.add(specification)
        inserted += 1

    conn.commit()
    conn.close()

    return redirect(f"/machine/{machine_id}")


@app.route("/brand/<int:brand_id>")
def brand_machines(brand_id):
    conn = get_db()

    brand = conn.execute(
        "SELECT * FROM brands WHERE id = ?",
        (brand_id,)
    ).fetchone()

    if not brand:
        conn.close()
        return "Merek tidak ditemukan", 404

    machines = conn.execute(
        """
        SELECT machines.*, machine_types.name AS machine_type_name
        FROM machines
        LEFT JOIN machine_types
            ON machines.machine_type_id = machine_types.id
        WHERE machines.brand_id = ?
        ORDER BY machines.model
        """,
        (brand_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "brand_machines.html",
        brand=brand,
        machines=machines
    )


@app.route("/type/<int:type_id>")
def type_machines(type_id):
    conn = get_db()

    machine_type = conn.execute(
        "SELECT * FROM machine_types WHERE id = ?",
        (type_id,)
    ).fetchone()

    if not machine_type:
        conn.close()
        return "Jenis mesin tidak ditemukan", 404

    machines = conn.execute(
        """
        SELECT machines.*, brands.name AS brand_name
        FROM machines
        LEFT JOIN brands
            ON machines.brand_id = brands.id
        WHERE machines.machine_type_id = ?
        ORDER BY brands.name, machines.model
        """,
        (type_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "type_machines.html",
        machine_type=machine_type,
        machines=machines
    )



@app.route("/robots.txt")
def robots():
    content = """User-agent: *
Allow: /

Disallow: /admin/
Disallow: /add-machine
Disallow: /add-troubleshooting
Disallow: /import-troubleshooting-csv
Disallow: /add-specification/
Disallow: /delete-specification/
Disallow: /edit-specification/
Disallow: /add-component/
Disallow: /edit-component/
Disallow: /delete-component/
Disallow: /add-document/
Disallow: /add-technician-note/
Disallow: /import-juki/

Sitemap: https://bangirdigarmenttech.pythonanywhere.com/sitemap.xml
"""
    return Response(content, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    urls = []

    # Halaman utama
    urls.append("/")

    # Halaman utama lainnya
    urls.append("/troubleshooting")
    urls.append("/components")
    urls.append("/needle-catalog")

    # Semua halaman mesin dari database
    cur.execute("SELECT id FROM machines ORDER BY id")
    machines = cur.fetchall()

    for machine in machines:
        urls.append(f"/machine/{machine['id']}")

    # Halaman katalog khusus setiap merek jarum
    cur.execute("""
        SELECT DISTINCT brand FROM needles
        WHERE TRIM(COALESCE(brand, '')) <> ''
        ORDER BY brand COLLATE NOCASE
    """)
    for row in cur.fetchall():
        slug = row["brand"].strip().lower().replace(" ", "-")
        urls.append(f"/needle-brand/{slug}")

    conn.close()

    base_url = "https://bangirdigarmenttech.pythonanywhere.com"

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    )

    for path in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{base_url}{path}</loc>")
        xml.append("  </url>")

    xml.append("</urlset>")

    return Response(
        "\n".join(xml),
        mimetype="application/xml"
    )





@app.route("/needle-catalog")
def needle_catalog():
    conn = get_db()
    search = request.args.get("search", "").strip()
    rows = []

    try:
        brands = conn.execute("""
            SELECT brand, COUNT(*) AS jumlah
            FROM needles
            WHERE TRIM(COALESCE(brand, '')) <> ''
            GROUP BY brand
            ORDER BY brand COLLATE NOCASE
        """).fetchall()

        total_needles = conn.execute("SELECT COUNT(*) FROM needles").fetchone()[0]

        if search:
            conditions = []
            params = []
            for term in search.split():
                pattern = f"%{term}%"
                conditions.append("""
                    (
                        COALESCE(n.brand, '') LIKE ?
                        OR COALESCE(n.needle_system, '') LIKE ?
                        OR COALESCE(n.size_nm, '') LIKE ?
                        OR CAST(COALESCE(n.size_nm_value, '') AS TEXT) LIKE ?
                        OR COALESCE(n.manufacturer_size, '') LIKE ?
                        OR COALESCE(n.point_code, '') LIKE ?
                        OR COALESCE(n.point_description, '') LIKE ?
                        OR COALESCE(n.material_application, '') LIKE ?
                        OR COALESCE(n.product_code, '') LIKE ?
                        OR COALESCE(n.description, '') LIKE ?
                        OR EXISTS (
                            SELECT 1
                            FROM needle_machine_compatibility nc
                            JOIN machines m ON m.id = nc.machine_id
                            JOIN brands b ON b.id = m.brand_id
                            WHERE nc.needle_id = n.id
                              AND (b.name LIKE ? OR m.model LIKE ?)
                        )
                    )
                """)
                params.extend([pattern] * 12)

            rows = conn.execute("""
                SELECT n.* FROM needles n
                WHERE """ + " AND ".join(conditions) + """
                ORDER BY n.brand, n.needle_system,
                         n.size_nm_value, n.id DESC
            """, params).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_catalog.html",
        brands=brands,
        brand_count=len(brands),
        total_needles=total_needles,
        needles=rows,
        search=search
    )


@app.route("/needle-brand/<brand_slug>")
def needle_brand(brand_slug):
    conn = get_db()
    search = request.args.get("search", "").strip()

    try:
        brand_rows = conn.execute("""
            SELECT brand, COUNT(*) AS jumlah
            FROM needles
            WHERE LOWER(REPLACE(TRIM(brand), ' ', '-')) = ?
            GROUP BY brand
            LIMIT 1
        """, (brand_slug.lower(),)).fetchone()

        if brand_rows is None:
            return "Merek jarum tidak ditemukan.", 404

        params = [brand_rows["brand"]]
        sql = "SELECT n.* FROM needles n WHERE n.brand = ?"

        if search:
            conditions = []
            for term in search.split():
                pattern = f"%{term}%"
                conditions.append("""
                    (
                        COALESCE(n.needle_system, '') LIKE ?
                        OR COALESCE(n.size_nm, '') LIKE ?
                        OR CAST(COALESCE(n.size_nm_value, '') AS TEXT) LIKE ?
                        OR COALESCE(n.manufacturer_size, '') LIKE ?
                        OR COALESCE(n.point_code, '') LIKE ?
                        OR COALESCE(n.point_description, '') LIKE ?
                        OR COALESCE(n.material_application, '') LIKE ?
                        OR COALESCE(n.product_code, '') LIKE ?
                        OR COALESCE(n.description, '') LIKE ?
                    )
                """)
                params.extend([pattern] * 9)
            sql += " AND " + " AND ".join(conditions)

        sql += """
            ORDER BY n.needle_system, n.size_nm_value, n.id
        """
        needles = conn.execute(sql, params).fetchall()
        brand_name = brand_rows["brand"]

        system_summaries = conn.execute("""
            SELECT
                needle_system,
                COUNT(*) AS jumlah_ukuran,
                MIN(size_nm_value) AS nm_min,
                MAX(size_nm_value) AS nm_max
            FROM needles
            WHERE brand = ?
            GROUP BY needle_system
            ORDER BY needle_system COLLATE NOCASE
        """, (brand_name,)).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_brand.html",
        brand=brand_name,
        needles=needles,
        system_summaries=system_summaries,
        search=search
    )


@app.route("/needle/<int:needle_id>")
def needle_detail(needle_id):
    conn = get_db()

    try:
        needle = conn.execute(
            "SELECT * FROM needles WHERE id = ?",
            (needle_id,)
        ).fetchone()

        if needle is None:
            return "Data jarum tidak ditemukan.", 404

        compatible_machines = conn.execute("""
            SELECT
                m.id AS machine_id,
                m.model,
                b.name AS brand_name,
                nc.compatibility_status,
                nc.source_url,
                nc.notes
            FROM needle_machine_compatibility nc
            JOIN machines m ON m.id = nc.machine_id
            JOIN brands b ON b.id = m.brand_id
            WHERE nc.needle_id = ?
            ORDER BY b.name, m.model
        """, (needle_id,)).fetchall()

    finally:
        conn.close()

    return render_template(
        "needle_detail.html",
        needle=needle,
        compatible_machines=compatible_machines
    )


@app.route("/admin/needle/add", methods=["GET", "POST"])
@admin_required
def add_needle():
    conn = get_db()

    try:
        if request.method == "POST":
            fields = (
                "brand",
                "needle_system",
                "size_nm",
                "point_code",
                "point_description",
                "material_application",
                "product_code",
                "description",
                "source_url",
                "verification_status",
            )

            values = {
                field: request.form.get(field, "").strip()
                for field in fields
            }

            nm_text = request.form.get("size_nm_value", "").strip()
            manufacturer_size = request.form.get(
                "manufacturer_size", ""
            ).strip()

            nm_value = None
            if nm_text:
                try:
                    nm_value = float(nm_text.replace(",", "."))
                except ValueError:
                    return "Ukuran NM harus berupa angka.", 400

                if not 1 <= nm_value <= 500:
                    return "Periksa kembali ukuran NM.", 400

            if not any((
                values["brand"],
                values["needle_system"],
                nm_text,
                manufacturer_size,
                values["product_code"],
            )):
                return (
                    "Isi setidaknya merek, sistem jarum, NM, "
                    "nomor produsen, atau kode produk.",
                    400,
                )

            # Tetap isi kolom lama agar kompatibel dengan data sebelumnya.
            legacy_size = values["size_nm"]
            if nm_value is not None or manufacturer_size:
                pieces = []
                if nm_value is not None:
                    pieces.append(f"NM {nm_text}")
                if manufacturer_size:
                    pieces.append(manufacturer_size)
                legacy_size = " (" .join(pieces[:1])
                if len(pieces) > 1:
                    legacy_size += f" ({pieces[1]})"

            status_options = {
                "Belum diverifikasi",
                "Terverifikasi",
            }
            if values["verification_status"] not in status_options:
                values["verification_status"] = "Belum diverifikasi"

            verification_notes = request.form.get(
                "verification_notes", ""
            ).strip()

            if values["verification_status"] == "Terverifikasi" and (
                not values["source_url"] or not verification_notes
            ):
                return (
                    "Untuk memverifikasi data, URL sumber dan catatan bukti "
                    "verifikasi wajib diisi.",
                    400,
                )

            verified_at = None
            if values["verification_status"] == "Terverifikasi":
                verified_at = __import__("datetime").datetime.now().astimezone().isoformat(
                    timespec="seconds"
                )

            cursor = conn.execute("""
                INSERT INTO needles (
                    brand, needle_system, size_nm, point_code,
                    point_description, material_application,
                    product_code, description, source_url,
                    verification_status, size_nm_value,
                    manufacturer_size, verification_notes, verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                values["brand"],
                values["needle_system"],
                legacy_size,
                values["point_code"],
                values["point_description"],
                values["material_application"],
                values["product_code"],
                values["description"],
                values["source_url"],
                values["verification_status"],
                nm_value,
                manufacturer_size or None,
                verification_notes or None,
                verified_at,
            ))

            needle_id = cursor.lastrowid

            # Hanya hubungkan mesin yang dipilih secara eksplisit.
            selected_ids = set()
            for raw_id in request.form.getlist("machine_ids"):
                try:
                    selected_ids.add(int(raw_id))
                except (ValueError, TypeError):
                    continue

            if selected_ids:
                placeholders = ",".join("?" for _ in selected_ids)
                valid_ids = conn.execute(
                    f"SELECT id FROM machines WHERE id IN ({placeholders})",
                    tuple(selected_ids)
                ).fetchall()

                compatibility_source = request.form.get(
                    "compatibility_source_url", ""
                ).strip()
                compatibility_notes = request.form.get(
                    "compatibility_notes", ""
                ).strip()

                for machine in valid_ids:
                    conn.execute("""
                        INSERT OR IGNORE INTO needle_machine_compatibility (
                            needle_id, machine_id, compatibility_status,
                            source_url, notes
                        )
                        VALUES (?, ?, 'Belum diverifikasi', ?, ?)
                    """, (
                        needle_id,
                        machine["id"],
                        compatibility_source or None,
                        compatibility_notes or None,
                    ))

            conn.commit()
            return redirect("/needle-catalog")

        machines = conn.execute("""
            SELECT m.id, m.model, b.name AS brand_name
            FROM machines m
            JOIN brands b ON b.id = m.brand_id
            ORDER BY b.name, m.model
        """).fetchall()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return render_template("needle_add.html", machines=machines)



@app.route("/admin/needle/<int:needle_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_needle(needle_id):
    conn = get_db()
    try:
        needle = conn.execute(
            "SELECT * FROM needles WHERE id = ?", (needle_id,)
        ).fetchone()

        if needle is None:
            return "Data jarum tidak ditemukan.", 404

        if request.method == "POST":
            fields = (
                "brand", "needle_system", "size_nm", "point_code",
                "point_description", "material_application", "product_code",
                "description", "source_url", "verification_status",
            )
            values = {
                field: request.form.get(field, "").strip()
                for field in fields
            }
            notes = request.form.get("verification_notes", "").strip()
            status = values["verification_status"]

            if status not in ("Belum diverifikasi", "Terverifikasi"):
                return "Status verifikasi tidak valid.", 400

            if status == "Terverifikasi" and (
                not values["source_url"] or not notes
            ):
                return (
                    "Untuk memverifikasi data, URL sumber dan catatan bukti "
                    "verifikasi wajib diisi.",
                    400,
                )

            nm_text = request.form.get("size_nm_value", "").strip()
            manufacturer_size = request.form.get(
                "manufacturer_size", ""
            ).strip()
            nm_value = None
            if nm_text:
                try:
                    nm_value = float(nm_text.replace(",", "."))
                except ValueError:
                    return "Ukuran NM harus berupa angka.", 400
                if not 1 <= nm_value <= 500:
                    return "Periksa kembali ukuran NM.", 400

            old_status = needle["verification_status"]
            verified_at = needle["verified_at"]

            if status == "Terverifikasi":
                if old_status != "Terverifikasi" or not verified_at:
                    verified_at = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
            else:
                verified_at = None

            conn.execute("""
                UPDATE needles SET
                    brand = ?, needle_system = ?, size_nm = ?,
                    point_code = ?, point_description = ?,
                    material_application = ?, product_code = ?,
                    description = ?, source_url = ?,
                    verification_status = ?, size_nm_value = ?,
                    manufacturer_size = ?, verification_notes = ?,
                    verified_at = ?
                WHERE id = ?
            """, (
                values["brand"] or None,
                values["needle_system"] or None,
                values["size_nm"] or None,
                values["point_code"] or None,
                values["point_description"] or None,
                values["material_application"] or None,
                values["product_code"] or None,
                values["description"] or None,
                values["source_url"] or None,
                status,
                nm_value,
                manufacturer_size or None,
                notes or None,
                verified_at,
                needle_id,
            ))
            conn.commit()
            return redirect(f"/needle/{needle_id}")

        return render_template("needle_edit.html", needle=needle)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



@app.route("/admin/needle-systems/add", methods=["GET", "POST"])
@admin_required
def add_needle_system():
    from datetime import datetime, timezone

    fields = (
        "system_code",
        "alternative_names",
        "manufacturer",
        "stitch_type",
        "machine_category",
        "description",
        "reference_url",
        "verification_notes",
    )

    values = {
        field: request.form.get(field, "").strip()
        for field in fields
    }
    error = None

    if request.method == "POST":
        code = values["system_code"]

        if not code:
            error = "Kode sistem jarum wajib diisi."
        elif len(code) > 100:
            error = "Kode sistem terlalu panjang."
        elif values["reference_url"] and not (
            values["reference_url"].startswith("https://")
            or values["reference_url"].startswith("http://")
        ):
            error = "Referensi harus berupa URL http:// atau https://."
        else:
            conn = get_db()
            try:
                duplicate = conn.execute("""
                    SELECT id FROM needle_systems
                    WHERE LOWER(TRIM(system_code)) = LOWER(TRIM(?))
                      AND COALESCE(LOWER(TRIM(manufacturer)), '') =
                          COALESCE(LOWER(TRIM(?)), '')
                    LIMIT 1
                """, (code, values["manufacturer"])).fetchone()

                if duplicate:
                    error = (
                        "Kode sistem tersebut sudah ada. "
                        "Periksa katalog sebelum menambahkan data."
                    )
                else:
                    now = datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    )
                    note = values["verification_notes"] or (
                        "Data baru ditambahkan melalui formulir admin. "
                        "Belum diverifikasi; periksa katalog resmi dan "
                        "manual mesin sebelum menyimpulkan kompatibilitas."
                    )
                    reference = values["reference_url"] or None

                    conn.execute("""
                        INSERT INTO needle_systems (
                            system_code,
                            alternative_names,
                            stitch_type,
                            machine_category,
                            description,
                            source_url,
                            verification_status,
                            verification_notes,
                            created_at,
                            verified_at,
                            manufacturer,
                            reference_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    """, (
                        code,
                        values["alternative_names"] or None,
                        values["stitch_type"] or None,
                        values["machine_category"] or None,
                        values["description"] or None,
                        reference,
                        "Belum diverifikasi",
                        note,
                        now,
                        values["manufacturer"] or None,
                        reference,
                    ))
                    conn.commit()
                    return redirect("/needle-systems?added=1")
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    return render_template(
        "needle_system_add.html",
        values=values,
        error=error,
    )



@app.route("/admin/needle-systems/<int:system_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_needle_system(system_id):
    fields = (
        "system_code", "alternative_names", "manufacturer",
        "stitch_type", "machine_category", "description",
        "source_url", "reference_url", "verification_notes",
    )

    conn = get_db()
    try:
        item = conn.execute(
            "SELECT * FROM needle_systems WHERE id = ?",
            (system_id,),
        ).fetchone()

        if item is None:
            return "Data sistem jarum tidak ditemukan.", 404

        values = {
            field: (
                request.form.get(field, item[field] or "").strip()
                if request.method == "POST"
                else (item[field] or "")
            )
            for field in fields
        }

        allowed_statuses = (
            "Belum diverifikasi",
            "Kode ditemukan di referensi resmi",
            "Terverifikasi - sistem dan jenis jahitan",
        )
        values["verification_status"] = (
            request.form.get(
                "verification_status",
                item["verification_status"] or "Belum diverifikasi",
            ).strip()
            if request.method == "POST"
            else (item["verification_status"] or "Belum diverifikasi")
        )

        error = None

        if request.method == "POST":
            code = values["system_code"]

            if values["verification_status"] not in allowed_statuses:
                error = "Status verifikasi tidak valid."
            elif not code:
                error = "Kode sistem jarum wajib diisi."
            elif len(code) > 100:
                error = "Kode sistem terlalu panjang."
            elif any(
                values[field] and not values[field].startswith(("https://", "http://"))
                for field in ("source_url", "reference_url")
            ):
                error = "URL harus diawali http:// atau https://."
            else:
                duplicate = conn.execute("""
                    SELECT id FROM needle_systems
                    WHERE LOWER(TRIM(system_code)) = LOWER(TRIM(?))
                      AND COALESCE(LOWER(TRIM(manufacturer)), '') =
                          COALESCE(LOWER(TRIM(?)), '')
                      AND id != ?
                    LIMIT 1
                """, (code, values["manufacturer"], system_id)).fetchone()

                if duplicate:
                    error = "Kode sistem tersebut sudah digunakan."
                else:
                    notes = values["verification_notes"] or (
                        "Belum diverifikasi; periksa katalog resmi dan "
                        "manual mesin sebelum menyimpulkan kompatibilitas."
                    )

                    conn.execute("""
                        UPDATE needle_systems SET
                            system_code = ?,
                            alternative_names = ?,
                            manufacturer = ?,
                            stitch_type = ?,
                            machine_category = ?,
                            description = ?,
                            source_url = ?,
                            reference_url = ?,
                            verification_notes = ?,
                            verification_status = ?
                        WHERE id = ?
                    """, (
                        code,
                        values["alternative_names"] or None,
                        values["manufacturer"] or None,
                        values["stitch_type"] or None,
                        values["machine_category"] or None,
                        values["description"] or None,
                        values["source_url"] or None,
                        values["reference_url"] or None,
                        notes,
                        values["verification_status"],
                        system_id,
                    ))
                    conn.commit()
                    return redirect("/needle-systems?edited=1")

        return render_template(
            "needle_system_edit.html",
            item=item,
            values=values,
            error=error,
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



@app.route("/admin/needle-systems/<int:system_id>/delete", methods=["POST"])
@admin_required
def delete_needle_system(system_id):
    conn = get_db()
    try:
        item = conn.execute(
            "SELECT id FROM needle_systems WHERE id = ?",
            (system_id,),
        ).fetchone()

        if item is None:
            return "Data sistem jarum tidak ditemukan.", 404

        conn.execute(
            "DELETE FROM needle_systems WHERE id = ?",
            (system_id,),
        )
        conn.commit()
        return redirect("/needle-systems?deleted=1")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.route("/admin/needle-series", methods=["GET", "POST"])
@admin_required
def manage_needle_series():
    fields = (
        "series_code",
        "series_name",
        "description",
        "verification_notes",
    )

    values = {
        field: request.form.get(field, "").strip()
        for field in fields
    }
    error = None

    if request.method == "POST":
        code = values["series_code"]
        name = values["series_name"]

        if not code:
            error = "Kode seri wajib diisi."
        elif len(code) > 50:
            error = "Kode seri maksimal 50 karakter."
        elif not name:
            error = "Nama seri wajib diisi."
        elif len(name) > 120:
            error = "Nama seri maksimal 120 karakter."
        else:
            conn = get_db()
            try:
                duplicate = conn.execute("""
                    SELECT id FROM needle_series
                    WHERE LOWER(TRIM(series_code)) =
                          LOWER(TRIM(?))
                    LIMIT 1
                """, (code,)).fetchone()

                if duplicate:
                    error = "Kode seri tersebut sudah terdaftar."
                else:
                    conn.execute("""
                        INSERT INTO needle_series (
                            series_code,
                            series_name,
                            description,
                            verification_status,
                            verification_notes
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        code,
                        name,
                        values["description"] or None,
                        "Perlu diverifikasi",
                        values["verification_notes"] or (
                            "Seri baru ditambahkan melalui admin. "
                            "Periksa referensi resmi sebelum "
                            "menetapkan status verifikasi."
                        ),
                    ))
                    conn.commit()
                    return redirect("/admin/needle-series?added=1")
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    conn = get_db()
    try:
        series = conn.execute("""
            SELECT
                s.id,
                s.series_code,
                s.series_name,
                s.description,
                s.verification_status,
                s.verification_notes,
                COUNT(ns.id) AS system_count
            FROM needle_series s
            LEFT JOIN needle_systems ns
                ON ns.series_id = s.id
            GROUP BY s.id
            ORDER BY s.series_code
        """).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_series_admin.html",
        series=series,
        values=values,
        error=error,
        added=request.args.get("added") == "1",
    )




@app.route(
    "/admin/needle-series/<int:series_id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_needle_series(series_id):
    fields = (
        "series_code",
        "series_name",
        "description",
        "verification_notes",
        "verification_status",
    )

    conn = get_db()
    try:
        item = conn.execute(
            "SELECT * FROM needle_series WHERE id = ?",
            (series_id,),
        ).fetchone()

        if item is None:
            return "Seri jarum tidak ditemukan.", 404

        values = {
            field: (
                request.form.get(field, "").strip()
                if request.method == "POST"
                else (item[field] or "")
            )
            for field in fields
        }
        error = None

        if request.method == "POST":
            code = values["series_code"]
            name = values["series_name"]

            allowed_statuses = {
                "Perlu diverifikasi",
                "Terverifikasi",
                "Perlu koreksi",
            }

            if values["verification_status"] not in allowed_statuses:
                error = "Status verifikasi tidak valid."
            elif not code:
                error = "Kode seri wajib diisi."
            elif len(code) > 50:
                error = "Kode seri maksimal 50 karakter."
            elif not name:
                error = "Nama seri wajib diisi."
            elif len(name) > 120:
                error = "Nama seri maksimal 120 karakter."
            else:
                duplicate = conn.execute("""
                    SELECT id FROM needle_series
                    WHERE LOWER(TRIM(series_code)) =
                          LOWER(TRIM(?))
                      AND id != ?
                    LIMIT 1
                """, (code, series_id)).fetchone()

                if duplicate:
                    error = "Kode seri tersebut sudah terdaftar."
                else:
                    conn.execute("""
                        UPDATE needle_series
                        SET series_code = ?,
                            series_name = ?,
                            description = ?,
                            verification_notes = ?,
                            verification_status = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        code,
                        name,
                        values["description"] or None,
                        values["verification_notes"] or None,
                        values["verification_status"],
                        series_id,
                    ))
                    conn.commit()
                    return redirect(
                        "/admin/needle-series?edited=1"
                    )

        return render_template(
            "needle_series_edit.html",
            item=item,
            values=values,
            error=error,
        )

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.route("/needle-systems")
def needle_systems_catalog():
    conn = get_db()
    try:
        systems = conn.execute("""
            SELECT ns.*,
                   s.series_code AS master_series_code,
                   s.series_name AS master_series_name
            FROM needle_systems AS ns
            LEFT JOIN needle_series AS s
                ON ns.series_id = s.id
            ORDER BY ns.manufacturer, ns.system_code
        """).fetchall()

        series = conn.execute("""
            SELECT series_code, series_name
            FROM needle_series
            ORDER BY series_code COLLATE NOCASE
        """).fetchall()
    finally:
        conn.close()

    return render_template(
        "needle_systems.html",
        systems=systems,
        series=series
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

