from pathlib import Path

path = Path("app.py")
content = path.read_text()

start = content.find('@app.route("/troubleshooting")')
end = content.find('@app.route("/add-troubleshooting"', start)

if start == -1 or end == -1:
    raise SystemExit("Batas fungsi tidak ditemukan. app.py tidak diubah.")

new_function = '''@app.route("/troubleshooting")
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


'''

path.write_text(content[:start] + new_function + content[end:])
print("Fungsi troubleshooting berhasil diperbarui.")
