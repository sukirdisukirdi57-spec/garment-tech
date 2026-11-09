import csv
from pathlib import Path

out = Path("tools/tml326_catalog_staging.csv")

rows = [{
    "model": "TML326",
    "machine_id": 215,
    "document_type": "Product Catalog",
    "title": "PEGASUS TML Series Catalog",
    "source_url": (
        "https://www.pegasus.co.jp/en/imgs/machine/series/pdf/e_TML_leaf.pdf"
    ),
    "action": "PROPOSE_ADD_SUPPORTING_CATALOG",
    "evidence": (
        "Katalog seri resmi PEGASUS; referensi identitas dan seri mesin, "
        "bukan manual troubleshooting lengkap."
    ),
    "approval_status": "PENDING_REVIEW",
}]

with out.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("=== STAGING KATALOG TML326 ===")
print("Usulan:", len(rows))
print("Model: TML326 | Machine ID: 215")
print("File:", out)
print("Database diubah: TIDAK")
