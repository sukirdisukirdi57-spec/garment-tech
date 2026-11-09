import urllib.request
import re
import html

base = "https://industrialsewingmachine.global.brother"
pages = [
("KE-430DP", base + "/en-ap/support/catalog?category=Bar+Tacking+Machine"),
("BE-438DP", base + "/en-ap/support/catalog?category=Button+Attaching+Machine"),
("BAS-HX", base + "/en-ap/support/catalog?category=Programmable+Electronic+Pattern+Sewing+Machine"),
("MANUAL", base + "/en-ap/support/manual"),
("PARTS BOOK", base + "/en-ap/support/partbook"),
]
terms = ["KE-430DP", "BE-438DP", "BAS-311HX", "BAS-326HX",
"S-7180A", "S-7200A", "S-7220B"]

def main():
for label, url in pages:
print("\n" + "=" * 50)
print(label, url)
try:
req = urllib.request.Request(
url, headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=20) as response:
source = response.read().decode("utf-8", "ignore")
print("HTTP:", response.status)
print("Final:", response.geturl())
except Exception as exc:
print("GAGAL:", exc)
continue

    source = html.unescape(source)
    found = 0
    for term in terms:
        matches = list(re.finditer(re.escape(term), source, re.I))
        for match in matches[:2]:
            start = max(0, match.start() - 200)
            end = min(len(source), match.end() + 500)
            snippet = re.sub(r"\s+", " ", source[start:end])
            print("\nMODEL:", term)
            print(snippet[:700])
            found += 1
            if found >= 10:
                break
        if found >= 10:
            break
    if not found:
        print("Nama model tidak ditemukan di HTML.")

print("\nSelesai. Database tidak diubah.")

if name == "main":
main()
