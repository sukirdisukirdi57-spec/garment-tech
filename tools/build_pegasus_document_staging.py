import csv
from pathlib import Path

OUT = Path("tools/pegasus_document_staging.csv")

manual_catalog = "https://www.pegasus.co.jp/webcatalog/?filter=manual&lang=en"
parts_catalog = "https://www.pegasus.co.jp/webcatalog/?filter=parts&lang=en"
ex5400_manual = (
    "https://www.pegasus.co.jp/webcatalog/file.php"
    "?docflg=1&itemcd=9B2057000009&pageseq=1&rev=00"
)

docs = [
    {
        "document_id": 532, "model": "E22L",
        "type": "Manual",
        "current_url": manual_catalog,
        "proposed_url": manual_catalog,
        "action": "KEEP_CATALOG_VERIFY_DIRECT",
        "evidence": "E22L/E32L/E52L tercantum pada katalog manual resmi.",
    },
    {
        "document_id": 533, "model": "E22L",
        "type": "Parts List",
        "current_url": parts_catalog,
        "proposed_url": parts_catalog,
        "action": "KEEP_CATALOG_VERIFY_MODEL",
        "evidence": "Katalog parts resmi mencantumkan kelompok E22L/E32L/E52L.",
    },
    {
        "document_id": 526, "model": "E256",
        "type": "Manual",
        "current_url": manual_catalog,
        "proposed_url": manual_catalog,
        "action": "KEEP_CATALOG_VERIFY_DIRECT",
        "evidence": "E256 tercantum pada katalog manual resmi; PDF langsung belum diverifikasi.",
    },
    {
        "document_id": 527, "model": "E256",
        "type": "Parts List",
        "current_url": parts_catalog,
        "proposed_url": parts_catalog,
        "action": "KEEP_CATALOG_VERIFY_MODEL",
        "evidence": "E256 tercantum pada katalog parts resmi.",
    },
    {
        "document_id": 528, "model": "EX5400",
        "type": "Manual",
        "current_url": manual_catalog,
        "proposed_url": ex5400_manual,
        "action": "PROPOSE_DIRECT_MANUAL",
        "evidence": "Manual EX5400 resmi; Cat. No. 9B2057000009, September 2019. Belum diterapkan.",
    },
    {
        "document_id": 529, "model": "EX5400",
        "type": "Parts List",
        "current_url": parts_catalog,
        "proposed_url": parts_catalog,
        "action": "KEEP_CATALOG_VERIFY_MODEL",
        "evidence": "EX5400 tercantum pada katalog parts resmi; halaman langsung belum diverifikasi.",
    },
    {
        "document_id": 530, "model": "TML326",
        "type": "Manual",
        "current_url": manual_catalog,
        "proposed_url": manual_catalog,
        "action": "HOLD_VERIFY_MODEL",
        "evidence": "Manual khusus TML326 belum terverifikasi; jangan menganggap halaman katalog sebagai manual.",
    },
    {
        "document_id": 531, "model": "TML326",
        "type": "Parts List",
        "current_url": parts_catalog,
        "proposed_url": parts_catalog,
        "action": "HOLD_VERIFY_MODEL",
        "evidence": "Parts catalog khusus TML326 belum terverifikasi.",
    },
]

fields = [
    "document_id", "model", "type", "current_url",
    "proposed_url", "action", "evidence", "approval_status"
]

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for d in docs:
        d["approval_status"] = "PENDING_REVIEW"
        writer.writerow(d)

print("=== PEGASUS DOCUMENT STAGING ===")
print("Jumlah dokumen:", len(docs))
print("Usulan URL langsung:", sum(
    d["action"] == "PROPOSE_DIRECT_MANUAL" for d in docs
))
print("Ditahan untuk verifikasi:", sum(
    d["action"] == "HOLD_VERIFY_MODEL" for d in docs
))
print("File:", OUT)
print("Database diubah: TIDAK")
