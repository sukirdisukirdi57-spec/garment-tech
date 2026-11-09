from pathlib import Path
import re
import shutil

app_path = Path("app.py")
paths = [
    app_path,
    Path("templates/admin_login.html"),
    Path("templates/needle_system_add.html"),
    Path("templates/needle_system_edit.html"),
    Path("templates/needle_systems.html"),
]

for p in paths:
    if not p.is_file():
        raise SystemExit(f"File tidak ditemukan: {p}")

app = app_path.read_text()
contents = {p: p.read_text() for p in paths[1:]}

if "def validate_admin_csrf" in app:
    raise SystemExit("CSRF tampaknya sudah dipasang. Tidak ada perubahan.")

if 'app.secret_key = os.getenv("SECRET_KEY")' not in app:
    raise SystemExit("Konfigurasi SECRET_KEY tidak ditemukan.")

checks = [
    (paths[1], '<form method="POST">'),
    (paths[2], '<form method="post">'),
    (paths[3], '<form method="post">'),
]
for p, marker in checks:
    if contents[p].count(marker) != 1:
        raise SystemExit(f"Formulir tidak cocok: {p}")

delete_pattern = re.compile(
    r'<form method="post"\s+'
    r'action="/admin/needle-systems/\{\{ item\[\'id\'\] \}\}/delete"'
    r'[^>]*>'
)
p = paths[4]
if len(delete_pattern.findall(contents[p])) != 1:
    raise SystemExit("Formulir hapus tidak cocok; tidak ada perubahan.")

for module in ("hmac", "re", "secrets"):
    if not re.search(r"^import " + module + r"\s*$", app, re.M):
        app = app.replace("import sqlite3", f"import {module}\nimport sqlite3", 1)

csrf_code = '''

def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = generate_csrf_token


@app.before_request
def validate_admin_csrf():
    if request.method != "POST":
        return None

    path = request.path
    protected = (
        path == "/admin/login"
        or path == "/admin/needle-systems/add"
        or re.fullmatch(
            r"/admin/needle-systems/\\d+/(?:edit|delete)",
            path,
        )
    )

    if not protected:
        return None

    expected = session.get("_csrf_token")
    supplied = request.form.get("_csrf_token", "")

    if (
        not isinstance(expected, str)
        or not supplied
        or not hmac.compare_digest(expected, supplied)
    ):
        return (
            "Permintaan ditolak: token CSRF tidak valid. "
            "Muat ulang halaman dan coba lagi.",
            400,
        )
'''

app = app.replace(
    'app.secret_key = os.getenv("SECRET_KEY")',
    'app.secret_key = os.getenv("SECRET_KEY")' + csrf_code,
    1,
)

contents[paths[1]] = contents[paths[1]].replace(
    '<form method="POST">',
    '<form method="POST">\n'
    '        <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">',
    1,
)
contents[paths[2]] = contents[paths[2]].replace(
    '<form method="post">',
    '<form method="post">\n'
    '        <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">',
    1,
)
contents[paths[3]] = contents[paths[3]].replace(
    '<form method="post">',
    '<form method="post">\n'
    '<input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">',
    1,
)
contents[paths[4]] = delete_pattern.sub(
    lambda m: m.group(0)
    + '\n                    <input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">',
    contents[paths[4]],
    count=1,
)

if any('name="_csrf_token"' not in contents[p] for p in paths[1:]):
    raise SystemExit("Token belum masuk ke semua formulir; tidak ada perubahan.")

backups = [Path(str(p) + ".backup-before-csrf") for p in paths]
if any(b.exists() for b in backups):
    raise SystemExit(
        "Cadangan CSRF sudah ada. Skrip dihentikan untuk mencegah penimpaan."
    )

for original, backup in zip(paths, backups):
    shutil.copy2(original, backup)

try:
    app_path.write_text(app)
    for p, content in contents.items():
        p.write_text(content)
except Exception:
    for original, backup in zip(paths, backups):
        shutil.copy2(backup, original)
    raise

print("Berhasil memasang CSRF pada login, tambah, edit, dan hapus.")
print("Cadangan lima file telah dibuat.")
