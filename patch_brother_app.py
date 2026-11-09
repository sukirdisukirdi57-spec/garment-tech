from pathlib import Path

path = Path("app.py")
source = path.read_text()

old = '''    conn.close()

    return render_template(
        "component_detail.html",
        component=component,
        sub_parts=sub_parts,
        clamp_d1_parts=clamp_d1_parts,
        clamp_d2_parts=clamp_d2_parts,
        juki_parts=juki_parts
    )
'''

new = '''    # Daftar part katalog Brother berdasarkan halaman diagram.
    brother_parts = []
    if (
        component["machine_id"] == 227
        and component["diagram_page"] is not None
    ):
        brother_parts = conn.execute(
            """
            SELECT *
            FROM parts
            WHERE machine_id = ?
              AND diagram_page = ?
            ORDER BY
                catalog_ref IS NULL,
                CAST(catalog_ref AS INTEGER),
                id
            """,
            (component["machine_id"], component["diagram_page"])
        ).fetchall()

    conn.close()

    return render_template(
        "component_detail.html",
        component=component,
        sub_parts=sub_parts,
        clamp_d1_parts=clamp_d1_parts,
        clamp_d2_parts=clamp_d2_parts,
        juki_parts=juki_parts,
        brother_parts=brother_parts
    )
'''

if old not in source:
    raise SystemExit(
        "GAGAL: blok kode tidak cocok. app.py tidak diubah."
    )

path.write_text(source.replace(old, new, 1))
print("OK: query Brother ditambahkan ke app.py")
