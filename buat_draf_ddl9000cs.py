from pathlib import Path
import csv

folder = Path("audit-kelengkapan")
folder.mkdir(parents=True, exist_ok=True)

output = folder / "draf_ddl9000cs_revisi_manual.csv"

kolom = [
    "target_machine_id", "target_model",
    "reference_machine_id", "reference_model",
    "code", "problem", "symptoms",
    "possible_cause", "solution", "safety_notes",
    "source", "review_status"
]

# Daftar kode error dari halaman 52-54 manual
# E000 dicantumkan tetapi bukan error menurut manual.
kode_error = [
    "E000", "E007", "E009", "E011", "E012", "E013",
    "E014", "E015", "E016", "E032", "E071", "E072",
    "E081", "E204", "E220", "E221", "E302", "E303",
    "E704", "E730", "E731", "E733", "E811", "E813",
    "E815", "E903", "E904", "E910", "E912", "E915",
    "E922", "E924", "E946", "E955", "E961", "E962",
    "E971", "E972", "E973", "E974", "E975", "E976",
    "E985"
]

sumber = (
    "Manual resmi JUKI DDL-9000C-S, bagian 4-6 List of errors, "
    "halaman cetak 52-54; "
    "https://www.juki.co.jp/industrial_j/download_j/manual_j/"
    "ddl9000cs/menu/ddl9000cs/pdf/instruction_eg.pdf"
)

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=kolom)
    writer.writeheader()

    for kode in kode_error:
        if kode == "E000":
            problem = "E000 - bukan error menurut manual"
            gejala = "Kode status; konfirmasi konteks tampilannya."
        else:
            problem = f"{kode} - rincian pesan perlu dicocokkan dengan manual"
            gejala = "Isi gejala belum dilengkapi dari kutipan manual."

        writer.writerow({
            "target_machine_id": 17,
            "target_model": "DDL-9000CS",
            "reference_machine_id": "",
            "reference_model": "DDL-9000C-S",
            "code": kode,
            "problem": problem,
            "symptoms": gejala,
            "possible_cause": "Perlu verifikasi terhadap teks lengkap manual.",
            "solution": "Jangan menetapkan prosedur perbaikan sebelum diverifikasi.",
            "safety_notes": (
                "Pemeriksaan listrik, PCB, motor, encoder, dan konektor "
                "internal harus dilakukan teknisi kompeten. Matikan daya "
                "sebelum pemeriksaan yang mensyaratkannya."
            ),
            "source": sumber,
            "review_status": "DRAF_PERLU_VERIFIKASI_TEKNIS"
        })

print("CSV draf berhasil dibuat:", output)
print("Jumlah baris:", len(kode_error))
print("Jumlah kode unik:", len(set(kode_error)))
print("Database tidak dibuka atau diubah.")
