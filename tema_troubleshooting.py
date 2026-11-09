from pathlib import Path
import shutil

template = Path("templates/troubleshooting.html")
css = Path("static/style.css")

html = template.read_text(encoding="utf-8")
styles = css.read_text(encoding="utf-8")

# Pastikan perubahan hanya diterapkan satu kali.
if '<body id="troubleshooting">' not in html:
    if "<body>" not in html:
        raise SystemExit("Tag <body> tidak ditemukan. Tidak ada perubahan.")
    shutil.copy2(template, "templates/troubleshooting.html.sebelum-tema")
    html = html.replace(
        "<body>",
        '<body id="troubleshooting">',
        1
    )
    template.write_text(html, encoding="utf-8")

marker = "/* TEMA KHUSUS TROUBLESHOOTING - GARMENT MACHINE TECH */"

theme = """
/* TEMA KHUSUS TROUBLESHOOTING - GARMENT MACHINE TECH */
#troubleshooting {
    background: #f2f4f7;
    color: #222;
}

#troubleshooting header {
    background: linear-gradient(135deg, #17202a, #273746);
    color: #fff;
    border-bottom: 4px solid #1f618d;
}

#troubleshooting main {
    max-width: 1000px;
}

#troubleshooting .welcome {
    background: #fff;
    border: 1px solid #dce3e9;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(23, 32, 42, 0.08);
}

#troubleshooting .welcome h2 {
    color: #17202a;
}

#troubleshooting .welcome form {
    padding: 16px;
    background: #f8fafb;
    border: 1px solid #dce3e9;
    border-radius: 12px;
}

#troubleshooting .welcome form label {
    display: block;
    margin-bottom: 8px;
    color: #273746;
}

#troubleshooting .welcome form select,
#troubleshooting .welcome form input[type="text"] {
    display: block;
    min-height: 44px;
    border: 1px solid #bdc9d3;
    border-radius: 8px;
    background: #fff;
    color: #222;
    font: inherit;
}

#troubleshooting .welcome form select:focus,
#troubleshooting .welcome form input[type="text"]:focus {
    outline: 2px solid #1f618d;
    outline-offset: 1px;
    border-color: #1f618d;
}

#troubleshooting .welcome form select:disabled {
    background: #e9eef2;
    color: #687782;
    cursor: not-allowed;
}

#troubleshooting .add-button {
    background: #17202a;
    color: #fff;
    border: 1px solid #17202a;
    border-radius: 8px;
    cursor: pointer;
}

#troubleshooting .add-button:hover {
    background: #273746;
}

#troubleshooting .back-button {
    display: inline-block;
    margin: 8px 0 0 8px;
    padding: 10px 14px;
    border-radius: 8px;
    color: #1f4e6b;
    border: 1px solid #bdc9d3;
    text-decoration: none;
}

#troubleshooting .back-button:hover {
    background: #eaf1f6;
}

#troubleshooting .machine-card {
    border: 1px solid #dce3e9;
    border-left: 5px solid #1f618d;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(23, 32, 42, 0.06);
}

#troubleshooting .machine-card h3 {
    color: #1f4e6b;
}

@media (max-width: 600px) {
    #troubleshooting .welcome {
        padding: 14px;
    }

    #troubleshooting .welcome form {
        padding: 12px;
    }

    #troubleshooting .back-button {
        margin-left: 0;
    }
}
"""

if marker not in styles:
    shutil.copy2(css, "static/style.css.sebelum-tema-troubleshooting")
    css.write_text(styles.rstrip() + "\n\n" + theme, encoding="utf-8")
    print("Tema warna berhasil ditambahkan.")
else:
    print("Tema khusus sudah tersedia; CSS tidak ditambahkan ulang.")

print("Template dan CSS selesai diperiksa.")
