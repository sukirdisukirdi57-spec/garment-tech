import csv
from pathlib import Path

out = Path("tools/pegasus_safety_doc_staging.csv")
url = (
    "https://www.pegasus.co.jp/webcatalog/file.php"
    "?docflg=8&itemcd=9B9020000009&pageseq=1&rev=00"
)

rows = [
    {
        "model": "E22L",
        "machine_id": 216,
        "document_type": "Safety Precautions",
        "title": "PEGASUS E22L/E32L/E52L/E256 Safety Precautions",
        "source_url": url,
        "action": "PROPOSE_ADD_SUPPORTING_DOCUMENT",
        "evidence": (
            "Dokumen resmi mencantumkan E22L dan E256; "
            "dokumen keselamatan, bukan manual troubleshooting lengkap."
        ),
        "approval_status": "PENDING_REVIEW",
    },
    {
        "model": "E256",
        "machine_id": 213,
        "document_type": "Safety Precautions",
        "title": "PEGASUS E22L/E32L/E52L/E256 Safety Precautions",
        "source_url": url,
        "action": "PROPOSE_ADD_SUPPORTING_DOCUMENT",
        "evidence": (
            "Dokumen resmi mencantumkan E22L dan E256; "
            "dokumen keselamatan, bukan manual troubleshooting lengkap."
        ),
        "approval_status": "PENDING_REVIEW",
    },
]

fields = [
    "model", "machine_id", "document_type", "title",
    "source_url", "action", "evidence", "approval_status"
]

with out.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("=== STAGING DOKUMEN KESELAMATAN PEGASUS ===")
print("Usulan dokumen:", len(rows))
print("Model:", ", ".join(r["model"] for r in rows))
print("File:", out)
print("Database diubah: TIDAK")
