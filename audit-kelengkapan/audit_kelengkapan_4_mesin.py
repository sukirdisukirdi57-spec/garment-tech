from pathlib import Path
import sqlite3
import sys
from datetime import date

DB = Path("database/garment.db")
OUT = Path("audit-kelengkapan/laporan_audit_kelengkapan_4_mesin.md")
TARGETS = {
    16: "JUKI DDL-8000C",
    17: "JUKI DDL-9000CS",
    226: "LYGOLD LGA105E-BUT",
    227: "BROTHER BAS-311HN-03S",
}
FIELDS = [
    "problem", "symptoms", "possible_cause",
    "solution", "safety_notes", "source"
]

if OUT.exists():
    sys.exit(f"File sudah ada; tidak ditimpa: {OUT}")
if not DB.is_file():
    sys.exit(f"Database tidak ditemukan: {DB}")

con = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
con.execute("PRAGMA query_only=ON")

try:
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
    machine_total = con.execute("SELECT COUNT(*) FROM machines").fetchone()[0]
    troubleshooting_total = con.execute(
        "SELECT COUNT(*) FROM troubleshooting"
    ).fetchone()[0]

    columns = {
        r["name"] for r in
        con.execute("PRAGMA table_info(troubleshooting)").fetchall()
    }
    required = {"id", "machine_id", "code", *FIELDS}
    missing_columns = required - columns
    if missing_columns:
        sys.exit("Kolom wajib tidak ditemukan: " + ", ".join(sorted(missing_columns)))

    results = {}
    for mid, label in TARGETS.items():
        machine = con.execute(
            "SELECT id, model, function FROM machines WHERE id=?",
            (mid,)
        ).fetchone()
        if machine is None:
            sys.exit(f"Mesin ID {mid} tidak ditemukan.")

        rows = con.execute("""
            SELECT id, code, problem, symptoms, possible_cause,
                   solution, safety_notes, source
            FROM troubleshooting
            WHERE machine_id=?
            ORDER BY id
        """, (mid,)).fetchall()

        blanks = {}
        for field in FIELDS:
            blanks[field] = sum(
                1 for r in rows
                if r[field] is None or not str(r[field]).strip()
            )

        blank_codes = sum(
            1 for r in rows
            if r["code"] is None or not str(r["code"]).strip()
        )

        coded = {}
        for r in rows:
            code = r["code"]
            if code is not None and str(code).strip():
                key = str(code).strip().upper()
                coded.setdefault(key, []).append(r["id"])
        duplicates = {k: v for k, v in coded.items() if len(v) > 1}

        draft_count = sum(
            1 for r in rows
            if r["source"] and "DRAF_PERLU_VERIFIKASI_TEKNIS" in r["source"]
        )
        blank_source = blanks["source"]

        results[mid] = {
            "label": label,
            "model": machine["model"],
            "function": machine["function"],
            "rows": rows,
            "count": len(rows),
            "blanks": blanks,
            "blank_codes": blank_codes,
            "duplicates": duplicates,
            "drafts": draft_count,
            "blank_source": blank_source,
            "unique_codes": len(coded),
        }

    orphan_count = con.execute("""
        SELECT COUNT(*)
        FROM troubleshooting t
        LEFT JOIN machines m ON m.id=t.machine_id
        WHERE m.id IS NULL
    """).fetchone()[0]

    all_target_ids = tuple(TARGETS)
    placeholders = ",".join("?" for _ in all_target_ids)
    target_total = con.execute(
        f"SELECT COUNT(*) FROM troubleshooting WHERE machine_id IN ({placeholders})",
        all_target_ids
    ).fetchone()[0]

finally:
    con.close()

lines = [
    "# Laporan Audit Kelengkapan Data — Empat Mesin",
    "",
    f"Tanggal audit: {date.today().isoformat()}",
    "Mode: baca-saja; database tidak diubah.",
    "",
    "## 1. Ringkasan database",
    "",
    f"- Total mesin: {machine_total}",
    f"- Total troubleshooting: {troubleshooting_total}",
    f"- Total baris empat mesin target: {target_total}",
    f"- Baris troubleshooting tanpa mesin terkait: {orphan_count}",
    f"- Integritas SQLite: {integrity}",
    f"- Foreign key errors: {len(fk_errors)}",
    "",
    "## 2. Ringkasan per mesin",
    "",
    "| Mesin | Baris | Kode kosong | Kode unik | Kode duplikat | Sumber kosong | Baris berstatus draf |",
    "|---|---:|---:|---:|---:|---:|---:|",
]

for mid, r in results.items():
    lines.append(
        f"| {r['label']} (ID {mid}) | {r['count']} | "
        f"{r['blank_codes']} | {r['unique_codes']} | "
        f"{len(r['duplicates'])} | {r['blank_source']} | {r['drafts']} |"
    )

lines += [
    "",
    "## 3. Kelengkapan enam kolom",
    "",
    "Angka menunjukkan jumlah baris yang kolomnya kosong atau hanya berisi spasi.",
    "",
    "| Mesin | Problem | Symptoms | Possible cause | Solution | Safety notes | Source |",
    "|---|---:|---:|---:|---:|---:|---:|",
]

for mid, r in results.items():
    b = r["blanks"]
    lines.append(
        f"| {r['label']} (ID {mid}) | " +
        " | ".join(str(b[x]) for x in FIELDS) + " |"
    )

lines += ["", "## 4. Rincian masalah yang ditemukan", ""]

for mid, r in results.items():
    lines += [f"### {r['label']} (ID {mid})", ""]

    if r["count"] == 0:
        lines.append("- Belum ada baris troubleshooting.")
    else:
        issues = []
        for field, count in r["blanks"].items():
            if count:
                issues.append(f"- Kolom `{field}` kosong pada {count} baris.")
        if r["blank_codes"]:
            issues.append(f"- Kode kosong pada {r['blank_codes']} baris.")
        if r["duplicates"]:
            for code, ids in sorted(r["duplicates"].items()):
                issues.append(
                    f"- Kode `{code}` duplikat pada ID baris: "
                    + ", ".join(map(str, ids)) + "."
                )
        if r["drafts"] < r["count"]:
            issues.append(
                f"- {r['count'] - r['drafts']} baris tidak memiliki penanda "
                "`DRAF_PERLU_VERIFIKASI_TEKNIS` pada kolom source."
            )
        if not issues:
            issues.append(
                "- Tidak ditemukan kolom kosong, kode kosong, atau kode duplikat "
                "dalam pemeriksaan dasar."
            )
        lines.extend(issues)

    lines += [
        "- Kelengkapan isi tidak otomatis membuktikan akurasi teknis.",
        ""
    ]

lines += [
    "## 5. Batasan interpretasi",
    "",
    "- Kode kosong dapat wajar untuk troubleshooting umum yang bukan kode alarm.",
    "- Kode duplikat dihitung per mesin setelah spasi dibuang dan huruf diubah menjadi kapital; "
    "duplikat belum tentu salah jika memang memiliki makna berbeda.",
    "- Penanda draf diperiksa dari kolom `source` karena tabel belum memiliki kolom status terpisah.",
    "- Pemeriksaan ini mengukur kelengkapan struktural, bukan kebenaran diagnosis atau keamanan solusi.",
    "- Semua perubahan data harus melalui persetujuan eksplisit dan pencadangan terlebih dahulu.",
    "",
    "## 6. Kesimpulan",
    "",
    "Gunakan hasil per mesin dan per kolom untuk menentukan prioritas perbaikan dokumentasi. "
    "Jangan mengubah data hanya berdasarkan jumlah kosong; tinjau konteks setiap baris terlebih dahulu.",
    "",
    "Database tidak diubah dalam audit ini.",
    ""
]

with OUT.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("BERHASIL:", OUT)
print("Total mesin:", machine_total)
print("Total troubleshooting:", troubleshooting_total)
print("Baris empat mesin:", target_total)
print("Orphan:", orphan_count)
print("Integritas:", integrity)
print("Foreign key errors:", len(fk_errors))
print("Database tidak diubah.")
