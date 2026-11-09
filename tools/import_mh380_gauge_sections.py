import re
from pathlib import Path

SOURCE = Path("assets/documents/juki/mh380-parts.txt")

GAUGES = {
    "B": "1/8", "C": "5/32", "D": "3/16", "E": "7/32",
    "F": "1/4", "H": "5/16", "K": "3/8", "L": "1/2",
}

# REF yang merupakan gauge MH-380; REF MH-382 sengaja tidak dipetakan.
MAPS = {
    25: {
        **{i: c for i, c in enumerate("BCDE FHKL".replace(" ", ""), 1)},
        **{i: c for i, c in enumerate("BCDE FHKL".replace(" ", ""), 10)},
        **{i: c for i, c in enumerate("BCDE FHKL".replace(" ", ""), 19)},
        28: "B", 29: "E", 30: "F", 31: "H", 32: "K", 33: "L",
        35: "C", 36: "E", 37: "H", 38: "L",
        40: "E", 41: "E",
    },
    27: {
        1: "E", 2: "E", 3: "E", 4: "L",
        5: "D", 6: "H", 7: "L",
        8: "B", 9: "C", 10: "D", 11: "E", 12: "F", 13: "H",
    },
}

def extract(page_no):
    pages = SOURCE.read_text(errors="replace").split("\f")
    rows = []
    for line in pages[page_no - 1].splitlines():
        m = re.match(
            r'\s*(\d{1,2})\s+(\S{8,})\s+(.+?)\s+(\(?\d+(?:\.\d+)?\)?)\s*$',
            line
        )
        if m:
            rows.append({
                "ref": int(m.group(1)),
                "pn": m.group(2),
                "name": m.group(3).strip(),
                "qty": m.group(4),
                "line": line.strip(),
            })
    return rows

all_rows = {}
for page, expected in ((25, 42), (27, 17)):
    rows = extract(page)
    refs = [r["ref"] for r in rows]
    assert len(rows) == expected, (page, len(rows), expected)
    assert refs == list(range(1, expected + 1)), (page, refs)
    assert len({r["ref"] for r in rows}) == expected
    all_rows[page] = rows

for page, rows in all_rows.items():
    mapping = MAPS[page]
    assert set(mapping).issubset({r["ref"] for r in rows})
    print(f"\nPAGE {page}: {len(rows)} occurrences; {len(mapping)} gauge maps")
    for r in rows:
        code = mapping.get(r["ref"])
        print(
            f"REF {r['ref']:02} | {r['pn']} | {r['name']} | "
            f"GAUGE {code or 'MH-382 / tanpa map'}"
        )

print("\nTOTAL OCCURRENCES:", sum(map(len, all_rows.values())))
print("TOTAL GAUGE MAPS:", sum(map(len, MAPS.values())))
print("TANPA MAP:", sum(
    len(all_rows[p]) - len(MAPS[p]) for p in all_rows
))
print("KODE GAUGE:", sorted(set(c for m in MAPS.values() for c in m.values())))
print("\nDRY-RUN OK — database belum diubah.")
