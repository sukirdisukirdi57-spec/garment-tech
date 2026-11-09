import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

ROOT = Path.home() / "garment-tech"
OUT = ROOT / "garment-tech-pythonanywhere.zip"
FILES = [
    "app.py", "juki_importer.py", "requirements.txt",
    "database/garment.db",
]
DIRS = ["templates", "static", "assets"]

def ignored(name):
    n = name.lower()
    return (
        n in {".env", ".git", "__pycache__", ".ds_store"}
        or n.endswith((".pyc", ".pyo", ".tmp", "~"))
        or ".backup" in n or ".bak" in n
    )

def copy_filtered(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.iterdir():
        if ignored(p.name):
            continue
        target = dst / p.name
        if p.is_dir():
            copy_filtered(p, target)
        elif p.is_file():
            shutil.copy2(p, target)

def verify_db(path):
    with sqlite3.connect(path) as con:
        result = con.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Database tidak sehat: {result}")
        return con.execute("SELECT COUNT(*) FROM machines").fetchone()[0]

for f in FILES:
    if not (ROOT / f).is_file():
        raise SystemExit(f"File wajib tidak ada: {f}")
for d in DIRS:
    if not (ROOT / d).is_dir():
        raise SystemExit(f"Direktori wajib tidak ada: {d}")

machine_count = verify_db(ROOT / "database/garment.db")
print("Database sumber OK; jumlah mesin:", machine_count)

with tempfile.TemporaryDirectory(prefix="gt-release-") as td:
    stage = Path(td) / "release"
    stage.mkdir()

    for f in FILES:
        dst = stage / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, dst)

    for d in DIRS:
        copy_filtered(ROOT / d, stage / d)

    for f in ["app.py", "juki_importer.py"]:
        compile((stage / f).read_text(), f, "exec")

    temp_zip = Path(td) / "release.zip"
    with zipfile.ZipFile(
        temp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6
    ) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage).as_posix())

    with zipfile.ZipFile(temp_zip) as z:
        names = z.namelist()
        required = FILES + [
            "templates/index.html",
            "templates/component_detail.html",
            "templates/components.html",
            "static/style.css",
        ]
        missing = [f for f in required if f not in names]
        if missing:
            raise RuntimeError("File wajib hilang: " + repr(missing))

        bad = [
            n for n in names
            if Path(n).name == ".env"
            or "__pycache__" in n
            or n.endswith((".pyc", ".pyo", ".tmp"))
            or ".backup" in n.lower()
            or ".bak" in n.lower()
        ]
        if bad:
            raise RuntimeError("File terlarang: " + repr(bad))

        verify_path = Path(td) / "verify.db"
        verify_path.write_bytes(z.read("database/garment.db"))
        if verify_db(verify_path) != machine_count:
            raise RuntimeError("Database ZIP tidak cocok!")

    shutil.copy2(temp_zip, OUT)

with zipfile.ZipFile(OUT) as z:
    print("Jumlah file ZIP:", len(z.namelist()))
    print("Database paket: OK")
    print("File backup/rahasia terlarang: tidak ditemukan")

print("PAKET BERHASIL:", OUT)
print("Ukuran ZIP:", f"{OUT.stat().st_size:,}", "bytes")
print("Kompilasi Python: OK")
