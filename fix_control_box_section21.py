import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
SECTION = "AMS-210EN catalog staging; section 21"
BACKUP_DIR = Path("backups")

# REF, NOTE, PART NO, DESCRIPTION, QTY RAW
data = [
(1,"#01","400-81561","MC-587 BOX A","1"),
(2,"#02","400-81562","MC-587 BOX B","1"),
(3,"#03","400-81563","MC-587 BOX C","1"),
(4,"","400-55355","CONTROL BOX","(1)"),
(5,"","400-55366","CONTROL BOX FRONT COVER","(1)"),
(6,"","400-55357","CONTROL BOX REAR COVER","(1)"),
(7,"","SL-4040891-SC","SCREW M4 L=8","(6)"),
(8,"","SL-4040891-SC","SCREW M4 L=8","(4)"),
(9,"","M3801-476-000","TRANSMISSION BOX FITTING PLATE","(1)"),
(10,"","SL-6083092-TN","SCREW","(4)"),
(11,"","HX-0032600-0K","GROMMET","(1)"),
(12,"","SL-4040891-SC","SCREW M4 L=8","(4)"),
(13,"","NM-6080001-SC","NUT M8X1.25","(8)"),
(14,"","M4206-461-000","WASHER","(4)"),
(15,"","402-68712","MAIN PCB A ASSY","(1)"),
(16,"#05","SL-4040881-SC","SCREW M4 L=8","(6)"),
(17,"","400-82758","SDC PCB A ASSY","(1)"),
(18,"","SL-4040881-SC","SCREW M4 L=8","(10)"),
(19,"#01","400-00056","FLT-T PCB A ASS'Y","(1)"),
(20,"#05","SL-4040881-SC","SCREW M4 L=8","(6)"),
(21,"","HX-0033900-00","STUD","(6)"),
(22,"","NM-3040520-SC","NUT M4","(6)"),
(23,"","400-05401","FAN MOTOR ASS'Y","(1)"),
(24,"","KM-0000004-80","FAN MOTOR","(1)"),
(25,"","SL-4043591-SC","SCREW","(4)"),
(26,"","NM-3040520-SC","NUT M4","(4)"),
(27,"","400-05706","MAIN PCB HOLDER PLATE","(1)"),
(28,"","SL-4040881-SC","SCREW M4 L=8","(5)"),
(29,"","HX-0040700-00","BUSH","(1)"),
(30,"","178-45009","CORD FITTING PLATE","(1)"),
(31,"","SL-4041091-SC","SCREW M4 L=10","(2)"),
(32,"#01","400-86465","POWER CORD 3P ASSY","(1)"),
(33,"","HX-0041000-0A","STRAIN RELIEF BUSHING","(1)"),
(34,"#05","400-05393","FLT-SDC CORD P ASS'Y","(1)"),
(35,"","400-05394","FLT-SDC CORD S ASS'Y","(1)"),
(36,"","400-05726","SDC-MAIN CORD P ASS'Y","(1)"),
(37,"","400-05727","SDC-MAIN CORD S ASS'Y","(1)"),
(38,"","HX-0051100-00","WIRE SADDLE","(3)"),
(39,"","E9607-603-000","STICKER (SMALL)","(1)"),
(40,"","E9567-319-000","EARTH MARK","(1)"),
(41,"","400-03458","MASK SEAL","(15)"),
(42,"","WP-0841601-SC","WASHER 8.4X17.4X1.6","(4)"),
(43,"#02","401-62838","FLT-CE PCB A ASSY","(1)"),
(44,"#03","400-86466","POWER CORD JE ASSY","(1)"),
(45,"#04","400-86467","POWER CORD 1P ASSY","(1)"),
(46,"#03","CM-2001000-01","PE MARK LABEL","(1)"),
(47,"","KX-0000002-10","SADDLE TYPE TIE MOUNT","(1)"),
(48,"","KX-0000002-30","RELEASIBLE CABLE TIE","(1)"),
(49,"","SL-4040881-SC","SCREW M4 L=8","(1)"),
(50,"#03","HN-0024600-00","CORES","(1)"),
(51,"#03","HN-0028400-00","CORES","(1)"),
(52,"","HN-0014900-00","CLAMP FILTER(L)","(1)"),
(53,"","400-73659","SW RELAY CORD ASM","(1)"),
(54,"","EA-9500B01-00","CABLE BAND","(1)"),
(55,"","M9029-580-0A0","FDD EARTH CORD ASM.","(1)"),
(56,"#03","SL-4041081-SC","SCREW M4 L=10","(1)"),
(57,"#03","CM-6001001-01","WEEE MARK LABEL S","(1)"),
(58,"#05","400-51640","ELECTRICAL_RATING_LABEL_UNIVERSAL","(1)"),
(59,"#03","400-57278","ELECTRICAL_RATING_LABEL_CE_UNIVERSAL","(1)"),
(60,"#03","HX-0033900-0M","SPACER","(5)"),
(61,"#03","SL-4040881-SC","SCREW M4 L=8","(1)"),
(62,"#03","SL-4041091-SC","SCREW M4 L=10","(5)"),
(63,"#03","SL-4040881-SC","SCREW M4 L=8","(5)"),
(64,"#03","SL-4041081-SC","SCREW M4 L=10","(1)"),
(65,"#03","401-63025","REACTOR CORD ASSY","(1)"),
(66,"#03","SL-4040891-SC","SCREW M4 L=8","(2)"),
]

def parse_qty(raw):
    s = raw.strip().strip("()")
    try:
        n = float(s)
        return int(n) if n.is_integer() else None
    except ValueError:
        return None

if not DB.exists():
    raise SystemExit(f"Database tidak ditemukan: {DB}")

if [r[0] for r in data] != list(range(1, 67)):
    raise SystemExit("REF harus lengkap 1–66. Tidak ada perubahan dilakukan.")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / (
    "garment-before-fix-control-box-section21-"
    + datetime.now().strftime("%Y%m%d-%H%M%S") + ".db"
)
shutil.copy2(DB, backup)
print("BACKUP:", backup)

con = sqlite3.connect(DB)
try:
    con.execute("BEGIN IMMEDIATE")
    count = con.execute(
        "SELECT COUNT(*) FROM parts WHERE machine_id=44 AND notes=?",
        (SECTION,)
    ).fetchone()[0]

    if count:
        raise RuntimeError(
            f"Section 21 sudah berisi {count} baris; transaksi dibatalkan."
        )

    for ref, note, part_no, name, qty_raw in data:
        con.execute("""
            INSERT INTO parts (
                machine_id, part_number, part_name, quantity,
                catalog_ref, note, notes, quantity_raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            44, part_no, name, parse_qty(qty_raw), ref,
            note or "COMMON", SECTION, qty_raw
        ))

    con.commit()
except Exception:
    con.rollback()
    raise
finally:
    con.close()

con = sqlite3.connect(DB)
rows = con.execute("""
    SELECT catalog_ref, part_number, part_name, quantity,
           quantity_raw, note
    FROM parts
    WHERE machine_id=44 AND notes=?
    ORDER BY catalog_ref
""", (SECTION,)).fetchall()

refs = [r[0] for r in rows]
print("\n=== AUDIT SECTION 21 ===")
print("Jumlah baris:", len(rows))
print("REF lengkap 1–66:", refs == list(range(1, 67)))
print("REF duplikat:", len(refs) - len(set(refs)))
print("REF 1, 16, 19, 32, 43–46, 54, 57–66:")
for r in rows:
    if r[0] in {1,16,19,32,43,44,45,46,54,57,58,59,60,61,62,63,64,65,66}:
        print(r)
con.close()
