#!/usr/bin/env python3
"""Parse MAICA UAM-03 (dual-format: pos-first dan qty-first)."""
import pymupdf, re, csv
from pathlib import Path

PDF = "tmp/pdf-baru/UAM03_parts_book.pdf"
OUT = Path("data/maica/UAM03-parts-generated.csv")

CODE_PATTERN = re.compile(r"^(?:MC\d{8}|PFUAM\d{5}|UAM\d{2}-[A-Z0-9\-]+|PUAM\d?[A-Z]\d{3}|[A-Z]{2,3}\d{3,8}(?:-[A-Z0-9]+)?)$")
MAT_PATTERN = re.compile(r"^(?:Ottone|Alluminio|Acciaio|INOX|S235JR|AVP|Bronzo|Nylon|Policarbonato|Silicone|Generico|Commercio|90MnCrV8|18NiCrMo4)")

def try_parse(lines, idx):
    code = lines[idx]
    
    # Format A: CODE / POS / RM, look back for QTY MAT DESC [OLD]
    if idx + 1 < len(lines) and re.match(r'^\d+$', lines[idx+1]):
        pos = int(lines[idx+1])
        for back in range(1, 6):
            if idx - back < 0: break
            if MAT_PATTERN.match(lines[idx - back]):
                mat = lines[idx - back]
                desc_idx = idx - back - 1
                desc = lines[desc_idx] if desc_idx >= 0 else ""
                qty_idx = idx - back - 2
                ql = lines[qty_idx] if qty_idx >= 0 else ""
                if re.match(r'^\d+$', ql):
                    return {"pos": pos, "old": "", "desc": desc, "mat": mat, "qty": int(ql), "fmt": "A"}
                return {"pos": pos, "old": "", "desc": desc, "mat": mat, "qty": 1, "fmt": "A1"}
    
    # Format B: POS / CODE / [OLD] / DESC / MAT / QTY
    if idx >= 1 and re.match(r'^\d+$', lines[idx-1]):
        pos = int(lines[idx-1])
        j = idx + 1
        old = ""
        if j < len(lines) and re.match(r'^UAM\d{2}-', lines[j]):
            old = lines[j]
            j += 1
        if j < len(lines) and not MAT_PATTERN.match(lines[j]) and not re.match(r'^\d+$', lines[j]):
            desc = lines[j]
            j += 1
            if j < len(lines) and MAT_PATTERN.match(lines[j]):
                mat = lines[j]
                j += 1
                if j < len(lines) and re.match(r'^\d+$', lines[j]):
                    return {"pos": pos, "old": old, "desc": desc, "mat": mat, "qty": int(lines[j]), "fmt": "B"}
    
    return None

doc = pymupdf.open(PDF)
rows = []

for page_idx in range(doc.page_count):
    text = doc[page_idx].get_text()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Deteksi section name
    sec_name = ""
    for l in lines[:30]:
        if "ASSIEME" in l.upper():
            sec_name = l.strip()
            break
    
    part_count = sum(1 for l in lines if CODE_PATTERN.match(l))
    if part_count < 3:
        continue
    
    page_rows = 0
    for idx in range(len(lines)):
        if not CODE_PATTERN.match(lines[idx]):
            continue
        parsed = try_parse(lines, idx)
        if not parsed:
            continue
        rows.append({
            "page": page_idx + 1,
            "section": sec_name,
            "item": parsed["pos"],
            "part_no": lines[idx],
            "old_code": parsed["old"],
            "description": parsed["desc"],
            "material": parsed["mat"],
            "quantity": parsed["qty"],
        })
        page_rows += 1
    print(f"[hal {page_idx+1:>2}] {page_rows:>3}/{part_count:>3} — {sec_name[:50]}")

doc.close()

# Dedupe
seen = set()
unique = []
for r in rows:
    k = (r['page'], r['item'], r['part_no'])
    if k in seen: continue
    seen.add(k)
    unique.append(r)

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["page","section","item","part_no","old_code","description","material","quantity"])
    w.writeheader()
    w.writerows(unique)

print(f"\n[TOTAL] {len(unique)} parts dari 19 halaman tabel")
print(f"[CSV] {OUT}")
