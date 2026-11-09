import sqlite3
import csv
from pathlib import Path
from collections import Counter

ROOT = Path.cwd()
DB = ROOT / "database/garment.db"
OUT = ROOT / "audit-kelengkapan"

con = sqlite3.connect(
    f"file:{DB.resolve()}?mode=ro", uri=True
)
con.row_factory = sqlite3.Row

def cols(table):
    return {
        r["name"] for r in con.execute(
            f'PRAGMA table_info("{table}")'
        )
    }

tables = {
    r["name"] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
}

required = {
    "machines", "documents", "specifications", "troubleshooting"
}
if not required.issubset(tables):
    raise SystemExit("Ada tabel wajib yang tidak ditemukan.")

machine_cols = cols("machines")
brand_table = next(
    (t for t in ("brands", "brand") if t in tables), None
)

select_brand = (
    "b.name AS brand"
    if brand_table and "name" in cols(brand_table)
    else "CAST(m.brand_id AS TEXT) AS brand"
)
brand_join = (
    f'LEFT JOIN "{brand_table}" b ON b.id=m.brand_id'
    if brand_table and "id" in cols(brand_table)
    else ""
)

type_table = next(
    (t for t in ("machine_types", "machine_type")
     if t in tables), None
)
select_type = (
    "mt.name AS machine_type"
    if type_table and "name" in cols(type_table)
    else "CAST(m.machine_type_id AS TEXT) AS machine_type"
)
type_join = (
    f'LEFT JOIN "{type_table}" mt ON mt.id=m.machine_type_id'
    if type_table and "id" in cols(type_table)
    else ""
)

machines = con.execute(f"""
    SELECT m.id, m.model, m.brand_id, m.machine_type_id,
           {select_brand}, {select_type}
    FROM machines m
    {brand_join}
    {type_join}
    ORDER BY brand, m.model
""").fetchall()

def rows(table):
    return [dict(r) for r in con.execute(
        f'SELECT * FROM "{table}"'
    ).fetchall()]

docs = rows("documents")
specs = rows("specifications")
troubles = rows("troubleshooting")

def blank(v):
    return v is None or not str(v).strip()

def write_csv(name, data):
    path = OUT / name
    if not data:
        path.write_text("Tidak ada temuan.\n", encoding="utf-8")
        print(f"{name}: 0 temuan")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)
    print(f"{name}: {len(data)} baris -> {path}")

def by_machine(data):
    result = Counter()
    for r in data:
        result[r.get("machine_id")] += 1
    return result

doc_count = by_machine(docs)
spec_count = by_machine(specs)
trouble_count = by_machine(troubles)

# 1. Ringkasan kelengkapan per mesin
summary = []
for m in machines:
    mid = m["id"]
    nd, ns, nt = (
        doc_count[mid], spec_count[mid], trouble_count[mid]
    )
    issues = []
    if nd == 0: issues.append("TANPA DOKUMEN")
    if ns == 0: issues.append("TANPA SPESIFIKASI")
    if nt == 0: issues.append("TANPA TROUBLESHOOTING")
    summary.append({
        "machine_id": mid,
        "brand": m["brand"],
        "model": m["model"],
        "machine_type": m["machine_type"],
        "documents": nd,
        "specifications": ns,
        "troubleshooting": nt,
        "audit_awal": "; ".join(issues) or "Perlu cek isi",
    })

write_csv("01_ringkasan_per_mesin.csv", summary)

# 2. Dokumen kosong / file lokal tidak ada
doc_issues = []
doc_types = Counter()
for d in docs:
    issues = []
    for field in ("title", "document_type"):
        if blank(d.get(field)):
            issues.append(f"{field.upper()} KOSONG")

    if blank(d.get("source_url")) and blank(d.get("local_file")):
        issues.append("TANPA URL DAN FILE LOKAL")

    local = d.get("local_file")
    if not blank(local):
        p = Path(str(local))
        candidates = [p] if p.is_absolute() else [
            ROOT / p, ROOT / "static" / p
        ]
        if not any(x.is_file() for x in candidates):
            issues.append("FILE LOKAL TIDAK DITEMUKAN")

    doc_types[str(d.get("document_type") or "(KOSONG)")] += 1
    if issues:
        doc_issues.append({
            "document_id": d.get("id"),
            "machine_id": d.get("machine_id"),
            "title": d.get("title"),
            "document_type": d.get("document_type"),
            "source_url": d.get("source_url"),
            "local_file": local,
            "temuan": "; ".join(issues),
        })

write_csv("02_masalah_dokumen.csv", doc_issues)

with (OUT / "02_ringkasan_jenis_dokumen.csv").open(
    "w", newline="", encoding="utf-8-sig"
) as f:
    w = csv.writer(f)
    w.writerow(["document_type", "jumlah"])
    w.writerows(sorted(doc_types.items()))

# 3. Spesifikasi dengan field penting kosong
spec_issues = []
for s in specs:
    issues = []
    for field in ("specification", "value"):
        if blank(s.get(field)):
            issues.append(f"{field.upper()} KOSONG")
    if issues:
        spec_issues.append({
            "specification_id": s.get("id"),
            "machine_id": s.get("machine_id"),
            "specification": s.get("specification"),
            "value": s.get("value"),
            "notes": s.get("notes"),
            "description": s.get("description"),
            "temuan": "; ".join(issues),
        })
write_csv("03_spesifikasi_kosong.csv", spec_issues)

# 4. Troubleshooting tidak lengkap
trouble_issues = []
for t in troubles:
    issues = []
    for field in ("problem", "symptoms", "possible_cause", "solution"):
        if blank(t.get(field)):
            issues.append(f"{field.upper()} KOSONG")
    if issues:
        trouble_issues.append({
            "troubleshooting_id": t.get("id"),
            "machine_id": t.get("machine_id"),
            "problem": t.get("problem"),
            "symptoms": t.get("symptoms"),
            "possible_cause": t.get("possible_cause"),
            "solution": t.get("solution"),
            "safety_notes": t.get("safety_notes"),
            "source": t.get("source"),
            "temuan": "; ".join(issues),
        })
write_csv("04_troubleshooting_tidak_lengkap.csv", trouble_issues)

# 5. Duplikat persis berdasarkan field isi, bukan ID
for table, fields, filename in [
    ("specifications", ("machine_id", "specification", "value"),
     "05_duplikat_spesifikasi.csv"),
    ("troubleshooting",
     ("machine_id", "problem", "symptoms", "possible_cause", "solution"),
     "06_duplikat_troubleshooting.csv"),
    ("documents", ("machine_id", "document_type", "title", "source_url", "local_file"),
     "07_duplikat_dokumen.csv"),
]:
    data = rows(table)
    groups = {}
    for r in data:
        key = tuple(
            str(r.get(field) or "").strip().casefold()
            for field in fields
        )
        if not any(key):
            continue
        groups.setdefault(key, []).append(r)

    duplicate_report = []
    for key, group in groups.items():
        if len(group) > 1:
            duplicate_report.append({
                "jumlah": len(group),
                "record_ids": ", ".join(
                    str(r.get("id")) for r in group
                ),
                **{field: group[0].get(field) for field in fields},
            })
    write_csv(filename, duplicate_report)

# 6. Referensi machine_id yang tidak ada
valid_ids = {m["id"] for m in machines}
for table, data, filename in [
    ("documents", docs, "08_dokumen_orphan.csv"),
    ("specifications", specs, "09_spesifikasi_orphan.csv"),
    ("troubleshooting", troubles, "10_troubleshooting_orphan.csv"),
]:
    orphan = [
        {k: r.get(k) for k in ("id", "machine_id")}
        for r in data
        if r.get("machine_id") not in valid_ids
    ]
    write_csv(filename, orphan)

print("\n===== RINGKASAN AUDIT =====")
print("Mesin:", len(machines))
print("Dokumen:", len(docs))
print("Spesifikasi:", len(specs))
print("Troubleshooting:", len(troubles))
print("Mesin tanpa dokumen:",
      sum(doc_count[m["id"]] == 0 for m in machines))
print("Mesin tanpa spesifikasi:",
      sum(spec_count[m["id"]] == 0 for m in machines))
print("Mesin tanpa troubleshooting:",
      sum(trouble_count[m["id"]] == 0 for m in machines))
print("\nLaporan tersimpan di:", OUT.resolve())
print("Database tidak diubah.")
con.close()
