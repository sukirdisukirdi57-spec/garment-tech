import sqlite3
from pathlib import Path
from collections import Counter
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DB = Path("database/garment.db").resolve()
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

print("=" * 68)
print("AUDIT READ-ONLY BRAND PEGASUS")
print("=" * 68)

print("\n[A] IDENTITAS DAN JUMLAH DATA PER MODEL")
rows = cur.execute("""
SELECT m.id, m.model,
       (SELECT COUNT(*) FROM specifications s
        WHERE s.machine_id=m.id) AS specs,
       (SELECT COUNT(*) FROM documents d
        WHERE d.machine_id=m.id) AS docs,
       (SELECT COUNT(*) FROM components c
        WHERE c.machine_id=m.id) AS components,
       (SELECT COUNT(*) FROM troubleshooting t
        WHERE t.machine_id=m.id) AS troubleshooting,
       (SELECT COUNT(*) FROM technician_notes n
        WHERE n.machine_id=m.id) AS notes
FROM machines m
JOIN brands b ON b.id=m.brand_id
WHERE UPPER(b.name)='PEGASUS'
ORDER BY m.model
""").fetchall()

print("Jumlah model:", len(rows))
for r in rows:
    print(
        f"ID={r['id']:>3} | {r['model']:<18} | "
        f"spec={r['specs']:>3} docs={r['docs']:>2} "
        f"components={r['components']:>3} "
        f"troubleshooting={r['troubleshooting']:>2} "
        f"notes={r['notes']}"
    )

print("\n[B] RINGKASAN KEKOSONGAN DATA")
for field in ("specs", "docs", "components", "troubleshooting", "notes"):
    counts = Counter(r[field] for r in rows)
    print(field, dict(sorted(counts.items())))

print("\n[C] AUDIT DOKUMEN: URL, JUDUL, FILE LOKAL")
docs = cur.execute("""
SELECT d.id, d.machine_id, m.model, d.document_type,
       d.title, d.source_url, d.local_file
FROM documents d
JOIN machines m ON m.id=d.machine_id
JOIN brands b ON b.id=m.brand_id
WHERE UPPER(b.name)='PEGASUS'
ORDER BY m.model, d.document_type, d.id
""").fetchall()

print("Jumlah record dokumen:", len(docs))
url_counts = Counter((d["source_url"] or "").strip() for d in docs)
print("URL berbeda:", len(url_counts))
print("URL kosong:", sum(not (d["source_url"] or "").strip() for d in docs))
print("File lokal terisi:", sum(bool((d["local_file"] or "").strip()) for d in docs))

print("\nURL yang digunakan oleh banyak record:")
for url, count in url_counts.most_common():
    if count > 1:
        print(f"{count:>2} record | {url}")

print("\nDetail dokumen tanpa file lokal:")
for d in docs:
    if not (d["local_file"] or "").strip():
        print(
            f"doc={d['id']} machine={d['machine_id']} "
            f"model={d['model']} type={d['document_type']}\n"
            f"  title={d['title']}\n"
            f"  url={d['source_url']}"
        )

print("\n[D] CONTOH TROUBLESHOOTING")
ts = cur.execute("""
SELECT t.id, t.machine_id, m.model, t.problem, t.symptoms,
       t.possible_cause, t.solution, t.safety_notes, t.source
FROM troubleshooting t
JOIN machines m ON m.id=t.machine_id
JOIN brands b ON b.id=m.brand_id
WHERE UPPER(b.name)='PEGASUS'
ORDER BY m.model, t.id
LIMIT 12
""").fetchall()

for t in ts:
    print("-" * 60)
    print(f"ID={t['id']} | {t['model']} | machine_id={t['machine_id']}")
    for key in ("problem", "symptoms", "possible_cause",
                "solution", "safety_notes", "source"):
        value = t[key]
        print(f"{key}: {(value or '')[:350]}")

print("\n[E] PEMERIKSAAN URL RESMI (GET RINGKAS)")
urls = sorted({
    (d["source_url"] or "").strip()
    for d in docs
    if (d["source_url"] or "").strip().startswith("https://")
})
for url in urls:
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; read-only audit)"}
        )
        with urlopen(req, timeout=12) as response:
            print(
                f"HTTP {response.status} | "
                f"type={response.headers.get('Content-Type', '?')} | {url}"
            )
    except HTTPError as e:
        print(f"HTTP {e.code} | {url}")
    except (URLError, TimeoutError, OSError) as e:
        print(f"GAGAL DICEK | {type(e).__name__}: {e} | {url}")

print("\n[F] INTEGRITAS DATABASE")
print("integrity_check:", cur.execute("PRAGMA integrity_check").fetchone()[0])
con.close()
print("\nSELESAI — DATABASE TIDAK DIUBAH")
