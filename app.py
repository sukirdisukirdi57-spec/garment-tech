from juki_importer import ambil_spesifikasi_ddl8700
from flask import Response, Flask, render_template, request, redirect, send_file, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import csv
import os
import sqlite3

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

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
    search = request.args.get("search", "").strip()

    conn = get_db()

    brands = conn.execute(
        "SELECT * FROM brands ORDER BY name"
    ).fetchall()

    machine_types = conn.execute(
        "SELECT * FROM machine_types ORDER BY name"
    ).fetchall()

    statistics = {
        "brands": conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0],
        "machines": conn.execute("SELECT COUNT(*) FROM machines").fetchone()[0],
        "documents": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
        "components": conn.execute("SELECT COUNT(*) FROM components").fetchone()[0],
        "parts": conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
    }


    if search:
        words = search.split()

        searchable_columns = [
            "brands.name",
            "machine_types.name",
            "machines.model",
            "machines.function",
            "machines.description",
            "machines.notes",
            "troubleshooting.problem",
            "troubleshooting.symptoms",
            "troubleshooting.possible_cause",
            "troubleshooting.solution",
            "specifications.specification",
            "specifications.value",
            "specifications.notes",
            "components.component_name",
            "components.part_number",
            "components.location",
            "components.function",
            "components.notes",
            "technician_notes.problem",
            "technician_notes.diagnosis",
            "technician_notes.action_taken",
            "technician_notes.result",
            "technician_notes.technician"
        ]

        conditions = []
        params = []

        for word in words:
            word_conditions = []

            for column in searchable_columns:
                word_conditions.append(
                    f"LOWER(COALESCE({column}, '')) LIKE LOWER(?)"
                )
                params.append(f"%{word}%")

            conditions.append(
                "(" + " OR ".join(word_conditions) + ")"
            )

        where_clause = " AND ".join(conditions)

        machines = conn.execute(
            f"""
            SELECT DISTINCT
                machines.*,
                brands.name AS brand_name,
                machine_types.name AS type_name,
                (SELECT COUNT(*) FROM specifications WHERE machine_id = machines.id) AS specifications_count,
                (SELECT COUNT(*) FROM components WHERE machine_id = machines.id) AS components_count,
                (SELECT COUNT(*) FROM parts WHERE machine_id = machines.id) AS parts_count,
                (SELECT COUNT(*) FROM troubleshooting WHERE machine_id = machines.id) AS troubleshooting_count,
                (SELECT COUNT(*) FROM documents WHERE machine_id = machines.id) AS documents_count
            FROM machines
            LEFT JOIN brands
                ON machines.brand_id = brands.id
            LEFT JOIN machine_types
                ON machines.machine_type_id = machine_types.id
            LEFT JOIN troubleshooting
                ON troubleshooting.machine_id = machines.id
            LEFT JOIN specifications
                ON specifications.machine_id = machines.id
            LEFT JOIN components
                ON components.machine_id = machines.id
            LEFT JOIN technician_notes
                ON technician_notes.machine_id = machines.id
            WHERE {where_clause}
            ORDER BY brands.name, machines.model
            """,
            params
        ).fetchall()

    else:
        machines = conn.execute(
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
            ORDER BY brands.name, machines.model
            """
        ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        brands=brands,
        machine_types=machine_types,
        machines=machines,
        search=search,
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

        conn.execute(
            """
            INSERT INTO machines
            (brand_id, machine_type_id, model, function, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                brand_id,
                machine_type_id,
                model,
                function,
                description
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
    machine_id = request.args.get("machine_id", "").strip()

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

    query = """
        SELECT
            troubleshooting.*,
            machines.model AS machine_model,
            brands.name AS brand_name
        FROM troubleshooting
        LEFT JOIN machines
            ON troubleshooting.machine_id = machines.id
        LEFT JOIN brands
            ON machines.brand_id = brands.id
    """

    params = []

    if search:
        words = search.split()

        conditions = []

        for word in words:
            pattern = f"%{word}%"

            conditions.append(
                "(" 
                "troubleshooting.problem LIKE ? OR "
                "troubleshooting.symptoms LIKE ? OR "
                "troubleshooting.possible_cause LIKE ? OR "
                "troubleshooting.solution LIKE ? OR "
                "troubleshooting.safety_notes LIKE ? OR "
                "troubleshooting.source LIKE ? OR "
                "machines.model LIKE ? OR "
                "brands.name LIKE ?"
                ")"
            )

            params.extend([pattern] * 8)

        if " WHERE " in query:
            query += " AND " + " AND ".join(conditions)
        else:
            query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY troubleshooting.id DESC"

    troubleshooting_data = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "troubleshooting.html",
        troubleshooting_data=troubleshooting_data,
        search=search,
        machine_id=machine_id,
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

    query = """
        SELECT
            components.*,
            machines.model AS machine_model,
            brands.name AS brand_name
        FROM components
        LEFT JOIN machines
            ON components.machine_id = machines.id
        LEFT JOIN brands
            ON machines.brand_id = brands.id
    """

    params = []

    if search:
        words = search.split()
        conditions = []

        for word in words:
            pattern = f"%{word}%"

            conditions.append(
                "("
                "components.component_name LIKE ? OR "
                "components.part_number LIKE ? OR "
                "components.location LIKE ? OR "
                "components.function LIKE ? OR "
                "components.notes LIKE ? OR "
                "machines.model LIKE ? OR "
                "brands.name LIKE ?"
                ")"
            )

            params.extend([pattern] * 7)

        query += " WHERE " + " AND ".join(conditions)

    query += """
        ORDER BY
            brands.name,
            machines.model,
            components.component_name
    """

    components_data = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "components.html",
        components_data=components_data,
        search=search
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
        technician_notes=technician_notes
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
        ORDER BY parts.id
        """,
        (component_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "component_detail.html",
        component=component,
        sub_parts=sub_parts
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

    for specification, value in specs:

        existing = conn.execute(
            """
            SELECT id
            FROM specifications
            WHERE machine_id = ?
              AND specification = ?
            """,
            (machine_id, specification)
        ).fetchone()

        if existing:
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

    # Semua halaman mesin dari database
    cur.execute("SELECT id FROM machines ORDER BY id")
    machines = cur.fetchall()

    for machine in machines:
        urls.append(f"/machine/{machine['id']}")

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

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

