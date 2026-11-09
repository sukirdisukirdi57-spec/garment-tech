import sqlite3

DB = "database/garment.db"
APPLY = True

revisions = {
    359: (
        "Kancing mudah lepas atau jahitan tidak cukup kuat.",
        "Ketegangan benang, posisi jarum, jumlah jahitan, atau "
        "penahanan bahan tidak sesuai.",
        "Periksa pemasangan benang, kondisi jarum, posisi kancing, "
        "dan jumlah jahitan. Uji kekuatan pemasangan pada bahan "
        "percobaan. Jika masalah berlanjut, periksa mekanisme "
        "sesuai manual mesin.",
        "Matikan mesin dan putuskan sumber daya sebelum memeriksa "
        "jarum atau mekanisme."
    ),
    360: (
        "Kancing bergeser dari posisi yang ditentukan.",
        "Posisi bahan atau kancing tidak tepat, attachment tidak "
        "sesuai, atau mekanisme penahan tidak stabil.",
        "Periksa posisi bahan, kancing, dan attachment. Pastikan "
        "bahan tertahan stabil lalu lakukan uji posisi.",
        "Jauhkan tangan dari jarum saat mesin beroperasi. Matikan "
        "mesin sebelum menyetel attachment."
    ),
    361: (
        "Jumlah tusukan berbeda dari pilihan 8, 16, atau 32 jahitan.",
        "Pilihan jumlah jahitan tidak tepat atau mekanisme "
        "pengatur siklus mengalami gangguan.",
        "Periksa pilihan dan posisi tuas sesuai manual. Lakukan "
        "uji jahit dan hitung jumlah tusukan. Jika tetap tidak "
        "sesuai, minta teknisi memeriksa mekanisme pengatur.",
        "Matikan mesin sebelum memeriksa mekanisme pengatur."
    ),
    362: (
        "Pola tusukan berbeda dari bentuk jahitan yang dipilih.",
        "Posisi tuas pemilih tidak tepat atau mekanisme pemilih "
        "pola mengalami gangguan.",
        "Periksa posisi tuas pemilih sesuai manual. Uji pola "
        "pada bahan percobaan. Jika masalah berlanjut, minta "
        "teknisi memeriksa mekanisme pemilih.",
        "Matikan mesin sebelum memeriksa atau menyetel pemilih pola."
    ),
    363: (
        "Kancing tidak tertahan stabil sebelum atau selama siklus jahit.",
        "Attachment tidak terpasang benar, tidak sesuai dengan "
        "kancing, atau mekanisme penahan tidak stabil.",
        "Periksa pemasangan dan kesesuaian attachment. Pastikan "
        "kancing tertahan stabil sebelum menjahit. Uji pada bahan "
        "percobaan dan periksa mekanisme jika masalah berlanjut.",
        "Matikan mesin sebelum memeriksa atau menyetel attachment."
    ),
    364: (
        "Benang putus selama proses pemasangan kancing.",
        "Pemasangan benang tidak benar, jarum tidak sesuai atau "
        "rusak, ketegangan berlebihan, jalur benang kasar, atau "
        "timing mekanisme tidak sesuai.",
        "Periksa jalur dan pemasangan benang, kondisi serta ukuran "
        "jarum, ketegangan benang, dan kemungkinan gesekan. Uji "
        "jahit. Jika benang tetap putus, minta teknisi memeriksa "
        "mekanisme sesuai manual servis.",
        "Matikan mesin dan putuskan sumber daya sebelum mengganti "
        "jarum atau memeriksa jalur benang."
    )
}

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

try:
    db.execute("BEGIN IMMEDIATE")

    rows = db.execute("""
        SELECT id, problem
        FROM troubleshooting
        WHERE machine_id = 41
          AND id BETWEEN 359 AND 364
        ORDER BY id
    """).fetchall()

    if [r["id"] for r in rows] != list(revisions):
        raise RuntimeError(
            "ID atau machine_id tidak cocok. Revisi dibatalkan."
        )

    for row_id, values in revisions.items():
        db.execute("""
            UPDATE troubleshooting
            SET symptoms = ?,
                possible_cause = ?,
                solution = ?,
                safety_notes = ?
            WHERE id = ? AND machine_id = 41
        """, (*values, row_id))

    print("=== HASIL REVISI ===")
    for r in db.execute("""
        SELECT id, problem, symptoms, possible_cause,
               solution, safety_notes, code
        FROM troubleshooting
        WHERE machine_id = 41
          AND id BETWEEN 359 AND 364
        ORDER BY id
    """):
        print(f"\nID {r['id']}: {r['problem']}")
        print("Gejala :", r["symptoms"])
        print("Penyebab:", r["possible_cause"])
        print("Solusi :", r["solution"])
        print("Safety :", r["safety_notes"])
        print("Code   :", r["code"])

    if APPLY:
        db.commit()
        print("\nPERUBAHAN DISIMPAN.")
    else:
        db.rollback()
        print("\nPRATINJAU SAJA — perubahan dibatalkan.")
        print("Periksa hasil sebelum mengaktifkan APPLY = True.")

except Exception:
    db.rollback()
    raise
finally:
    db.close()

