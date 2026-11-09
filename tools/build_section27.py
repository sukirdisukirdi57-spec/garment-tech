from pathlib import Path
import sys

src = Path("tools/import_ams224_section26.py")
dst = Path("tools/import_ams224_section27.py")

if not src.is_file():
    sys.exit("GAGAL: Script Section 26 tidak ditemukan")

if dst.exists():
    sys.exit("GAGAL: Script Section 27 sudah ada. Tidak ditimpa.")

s = src.read_text(encoding="utf-8")


def replace_once(old, new, label=None):
    count = s.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label or old!r}: ditemukan {count} kali, harus tepat 1"
        )
    return s.replace(old, new, 1)


# ------------------------------------------------------------
# KONFIGURASI SECTION 27
# ------------------------------------------------------------

changes = [
    (
        'tmp/ams224en6030-section26/page50.txt',
        'tmp/ams224en6030-section27/page51.txt',
        'TXT',
    ),
    (
        'tmp/ams224en6030-section26/page-50.png',
        'tmp/ams224en6030-section27/page-51.png',
        'IMAGE_SRC',
    ),
    (
        'ams224en6030_type_g_exclusive_parts_page50.png',
        'ams224en6030_separate_stroke_type_exclusive_parts_page51.png',
        'IMAGE_NAME',
    ),
    (
        'TYPE G EXCLUSIVE PARTS',
        'SEPARATE STROKE TYPE EXCLUSIVE PARTS',
        'COMPONENT_NAME',
    ),
    ('DIAGRAM_PAGE = 50', 'DIAGRAM_PAGE = 51', 'DIAGRAM_PAGE'),
    ('BASELINE = (1079, 21, 1079)',
     'BASELINE = (1107, 22, 1107)', 'BASELINE'),
    ('TARGET = (1107, 22, 1107)',
     'TARGET = (1132, 23, 1132)', 'TARGET'),
    ('EXPECTED_REFS = list(range(1, 29))',
     'EXPECTED_REFS = list(range(1, 26))', 'EXPECTED_REFS'),
    ('EXPECTED_DUPLICATES = {}',
     '''EXPECTED_DUPLICATES = {
    "BT-0400251-EB": 2,
    "PJ-3080400-02": 2,
    "EA-9500B01-00": 2,
}''', 'EXPECTED_DUPLICATES'),
    ('if len(records) != 28:',
     'if len(records) != 25:', 'jumlah REF'),
    ('if len(number_counts) != 28:',
     'if len(number_counts) != 22:', 'jumlah nomor unik'),
    ('if len(before) != 21:',
     'if len(before) != 22:', 'jumlah komponen lama'),
    ("OR catalog_ref = '26'",
     "OR catalog_ref = '27'", 'catalog_ref'),
    ('"database/garment-before-section26-"',
     '"database/garment-before-section27-"', 'nama backup'),
    ('                28,\n            )',
     '                25,\n            )', 'snapshot relasi'),
]

for old, new, label in changes:
    s = replace_once(old, new, label)


# ------------------------------------------------------------
# DATA RESMI SECTION 27
# REF: PART NUMBER, DESCRIPTION, QTY RAW, MARKER
# ------------------------------------------------------------

start = s.index("EXPECTED_VALUES = {")
end_marker = "\n\n\n# ============================================================\n# PARSING"
end = s.index(end_marker, start)

expected_values = '''EXPECTED_VALUES = {
    1: ("400-76736", "SOLENOID_INSTALLING_PLATE_A_ASM.", "1", None),
    2: ("400-76738", "SOLENOID_INSTALLING_PLATE", "(1)", None),
    3: ("PV-1352070-00", "3-PORT ELECTROMAGNETIC VALVE", "(1)", None),
    4: ("PJ-3040652-01", "ELBOW UNION 6XPT1/4", "(1)", None),
    5: ("PJ-3050652-04", "DOUBLE-ENDED T UNION", "(1)", None),
    6: ("PV-1551130-00", "5-PORT SOLENOID VALVE", "(1)", None),
    7: ("PJ-3050651-07", "DOUBLE-ENDED T UNION", "(1)", None),
    8: ("PJ-3080600-05", "DIFFERENT DIAMETER UNION Y", "(1)", None),
    9: ("PC-0124060-00", "SPEED CONTROLLER", "(2)", None),
    10: ("PJ-3080400-02", "QUICK COUPLING", "(4)", None),
    11: ("SL-4031691-SC", "SCREW M3 L=16", "(4)", None),
    12: ("SL-4032591-SC", "SCREW M3X25", "(4)", None),
    13: ("EA-9500B01-00", "CABLE BAND", "(3)", None),
    14: ("BT-0400251-EB", "URETHANE HOSE BLACK", "(0.6)", None),
    15: ("BT-0600401-EB", "TUBE", "(1.1)", None),
    16: ("SL-6051292-TN", "BOLT", "2", None),
    17: ("PX-9500010-00", "PLUG", "1", None),
    18: ("GPK-470010AB", "3-PEDAL ASM.", "1", None),
    19: ("BT-0400251-EB", "URETHANE HOSE BLACK", "1.7", None),
    20: ("PJ-3080400-02", "QUICK COUPLING", "4", None),
    21: ("EA-9500B01-00", "CABLE BAND", "3", None),
    22: ("400-74127", "AIR EXTENSION CODE ASM.", "1", None),
    23: ("400-33875", "PK47 RELAY CABLE ASM", "1", None),
    24: ("HX-0015000-0E", "CORD PRESSER 3-POLE (220/240V)", "1", None),
    25: ("SL-4040891-SC", "SCREW M4 L=8", "2", None),
}'''

s = s[:start] + expected_values + s[end:]


# ------------------------------------------------------------
# DRY RUN DINAMIS: TANPA MARKER SECTION 26
# ------------------------------------------------------------

begin = s.index('        if "--apply" not in sys.argv:')
finish = s.index(
    '        # ----------------------------------------------------\n'
    '        # BACKUP',
    begin,
)

dry_run = '''        if "--apply" not in sys.argv:
            qty_counts = Counter(r["qty_raw"] for r in records)
            print("\\\\n=== DRY RUN BERHASIL ===")
            print("Database belum diubah.")
            print("Target parts    :", TARGET[0])
            print("Target komponen :", TARGET[1])
            print("Target relasi   :", TARGET[2])
            print("REF baru        :", len(records))
            print("Nomor part unik :", len({r["number"] for r in records}))
            print("Duplikasi       :", actual_duplicates)
            print("Quantity raw    :", dict(qty_counts))
            print("Diagram page    :", DIAGRAM_PAGE)
            print("\\\\nJalankan --apply hanya setelah dry-run valid.")
            return

'''

s = s[:begin] + dry_run + s[finish:]


# ------------------------------------------------------------
# LABEL SECTION 26 MENJADI SECTION 27
# ------------------------------------------------------------

if "Section 26" not in s:
    raise RuntimeError("Label Section 26 tidak ditemukan")

s = s.replace("Section 26", "Section 27")


# ------------------------------------------------------------
# VALIDASI OUTPUT SEBELUM MENULIS FILE
# ------------------------------------------------------------

required = [
    'COMPONENT_NAME = "SEPARATE STROKE TYPE EXCLUSIVE PARTS"',
    'DIAGRAM_PAGE = 51',
    'BASELINE = (1107, 22, 1107)',
    'TARGET = (1132, 23, 1132)',
    'EXPECTED_REFS = list(range(1, 26))',
    'if len(records) != 25:',
    'if len(number_counts) != 22:',
    "OR catalog_ref = '27'",
    '                25,',
    'EXPECTED_VALUES = {',
]

for item in required:
    if item not in s:
        raise RuntimeError(f"Validasi output gagal: {item}")

if s.count('("BT-0400251-EB", "URETHANE HOSE BLACK"') != 2:
    raise RuntimeError("Validasi occurrence BT-0400251-EB gagal")

if s.count('("PJ-3080400-02", "QUICK COUPLING"') != 2:
    raise RuntimeError("Validasi occurrence PJ-3080400-02 gagal")

if s.count('("EA-9500B01-00", "CABLE BAND"') != 2:
    raise RuntimeError("Validasi occurrence EA-9500B01-00 gagal")

s = s.replace(
    'print("Marker #01 sampai #06: VALID")',
    'print("Marker katalog: VALID")'
)

s = s.replace(
    'print("Marker #01 sampai #06 valid:", True)',
    'print("Marker katalog valid:", True)'
)

s = s.replace(
    'print("Marker #01 sampai #06: VALID")',
    'print("Marker katalog: VALID")'
)

if "Marker #01 sampai #06" in s:
    raise RuntimeError("Label marker lama masih tertinggal")

dst.write_text(s, encoding="utf-8")

print("BERHASIL membuat:", dst)
print("Jumlah baris:", len(s.splitlines()))
print("REF:", 25)
print("Nomor part unik:", 22)
print("Kelompok duplikasi:", 3)
print("Baseline:", "(1107, 22, 1107)")
print("Target:", "(1132, 23, 1132)")
