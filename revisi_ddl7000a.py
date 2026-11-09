import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime

DB = Path("database/garment.db")
MODEL_ID = 4
EXPECTED_IDS = list(range(5, 13))
OFFICIAL = "https://juki.com/ddl-7000a-series"

# Format: symptoms, possible_cause, solution, safety_notes, source
REVISI = {
    5: (
        "Motor tidak berputar atau mesin tidak merespons saat pedal diinjak.",
        "Kemungkinan gangguan sumber listrik, kabel atau konektor eksternal, "
        "pengaturan penggerak, atau sistem kontrol. Penyebab perlu diperiksa.",
        "Pastikan sakelar dan sumber listrik eksternal tersedia. Periksa kabel "
        "dan konektor dari luar tanpa membongkar mesin. Cocokkan tegangan dan "
        "jenis catu daya dengan pelat spesifikasi mesin. Jika tetap tidak "
        "merespons, minta teknisi memeriksa sistem penggerak.",
        "Matikan mesin dan lepaskan sumber listrik sebelum memeriksa kabel "
        "atau konektor. Jangan membuka control box atau menangani kabel "
        "bertegangan.",
        "Panduan pemeriksaan umum; spesifikasi dan varian: " + OFFICIAL
    ),
    6: (
        "Benang jarum putus berulang saat proses menjahit.",
        "Kemungkinan pemasangan jarum atau jalur benang tidak tepat, jarum "
        "rusak, atau tegangan benang tidak sesuai.",
        "Periksa kondisi dan pemasangan jarum, jalur benang sesuai panduan "
        "mesin, serta tegangan benang. Gunakan tipe dan ukuran jarum sesuai "
        "varian mesin: AS-7 menggunakan DB×1; AH-7 menggunakan DP×5. "
        "Sesuaikan ukuran dengan material dan spesifikasi yang berlaku.",
        "Matikan mesin sebelum mengganti jarum atau menyentuh area jarum.",
        "Panduan pemeriksaan umum; tipe jarum menurut varian: " + OFFICIAL
    ),
    7: (
        "Jahitan tidak terbentuk secara konsisten atau terdapat bagian "
        "jahitan yang terlewat.",
        "Kemungkinan jarum bengkok atau tumpul, pemasangan jarum tidak tepat, "
        "atau hubungan jarum dengan hook memerlukan pemeriksaan.",
        "Periksa dan bila perlu ganti jarum dengan tipe yang sesuai varian "
        "mesin. Pastikan pemasangannya benar. Jika jahitan tetap loncat, "
        "minta teknisi memeriksa hubungan jarum dengan hook dan timing "
        "berdasarkan manual varian.",
        "Matikan mesin dan lepaskan sumber listrik sebelum memeriksa jarum. "
        "Jangan menyetel timing hook tanpa prosedur dan keahlian yang sesuai.",
        "Panduan pemeriksaan umum; spesifikasi varian: " + OFFICIAL
    ),
    8: (
        "Benang bawah putus, tersangkut, atau hasil jahitan bagian bawah "
        "tidak stabil.",
        "Kemungkinan pemasangan bobbin atau jalur benang bawah tidak tepat, "
        "bobbin case kotor atau rusak, atau tegangan benang tidak sesuai.",
        "Dengan mesin mati, periksa pemasangan bobbin, jalur benang bawah, "
        "serta kebersihan dan kondisi bobbin case. Ikuti panduan mesin "
        "sebelum mengubah tegangan. Jika masalah berlanjut, minta teknisi "
        "memeriksa mekanisme hook.",
        "Matikan mesin dan lepaskan sumber listrik sebelum melepas bobbin "
        "case atau membersihkan area hook.",
        "Panduan pemeriksaan umum; spesifikasi mesin: " + OFFICIAL
    ),
    9: (
        "Presser foot sulit terangkat atau tinggi angkatnya tidak sesuai.",
        "Kemungkinan mekanisme pengangkat terhambat, aus, atau memerlukan "
        "penyetelan.",
        "Periksa gerakan mekanisme pengangkat dari luar dan pastikan tidak "
        "ada hambatan yang terlihat. Spesifikasi seri mencantumkan tinggi "
        "angkat 5,5 mm dengan tangan dan 13 mm menggunakan knee lifter. "
        "Jika tinggi berbeda atau mekanisme macet, cocokkan varian dan "
        "prosedur pada manual sebelum penyetelan.",
        "Matikan mesin sebelum memeriksa mekanisme. Serahkan penyetelan "
        "mekanis yang tidak dipahami kepada teknisi.",
        "Spesifikasi seri JUKI; cocokkan varian dan manual: " + OFFICIAL
    ),
    10: (
        "Mesin terdengar kasar, terasa panas tidak biasa, atau gerakan "
        "mekanis tidak lancar.",
        "Kemungkinan masalah pelumasan, kotoran, keausan, atau gangguan "
        "mekanis lainnya. Gejala ini saja tidak memastikan penyebabnya.",
        "Matikan mesin. Periksa level oli menurut tanda dan prosedur manual "
        "untuk varian yang teridentifikasi. Untuk AS-7, katalog JUKI "
        "mencantumkan JUKI Machine Oil 7 yang setara ISO VG7. Jangan "
        "menambahkan oli atau membongkar sistem sebelum memastikan jenis "
        "sistem pelumasan mesin. Jika suara atau panas tidak normal "
        "berlanjut, minta teknisi memeriksa mesin.",
        "Matikan mesin dan lepaskan sumber listrik sebelum pemeriksaan. "
        "Jangan menyentuh bagian bergerak atau membongkar mekanisme saat "
        "mesin terhubung ke listrik.",
        "Spesifikasi oli untuk AS-7 dan pemeriksaan umum; verifikasi varian: "
        + OFFICIAL
    ),
    11: (
        "Panjang jahitan aktual berbeda dari pengaturan atau hasil jahitan "
        "tidak konsisten.",
        "Kemungkinan pengaturan panjang jahitan tidak tepat, mekanisme "
        "feeding terganggu, atau kain tidak terumpan secara stabil.",
        "Periksa pengaturan panjang jahitan dan pergerakan kain. Jika perlu "
        "memeriksa feed dog atau mekanisme feeding, matikan mesin terlebih "
        "dahulu. Panjang jahitan standar seri yang tercantum adalah 5 mm; "
        "periksa apakah mesin memakai kit opsional atau konfigurasi khusus "
        "sebelum menetapkan batas maksimum.",
        "Matikan mesin dan lepaskan sumber listrik sebelum memeriksa "
        "mekanisme feeding.",
        "Spesifikasi panjang jahitan seri; periksa konfigurasi mesin: "
        + OFFICIAL
    ),
    12: (
        "Suara motor tidak normal, putaran tidak stabil, atau respons pedal "
        "terganggu.",
        "Kemungkinan gangguan pada penggerak, koneksi, sistem kontrol, "
        "atau hambatan mekanis. Penyebab belum dapat dipastikan dari gejala.",
        "Periksa kabel dan konektor eksternal saat mesin mati. Pastikan tidak "
        "ada hambatan yang terlihat dari luar. Jika masalah berlanjut, "
        "minta teknisi memeriksa sistem direct-drive, motor, dan kontrol "
        "sesuai manual varian.",
        "Matikan mesin dan lepaskan sumber listrik sebelum pemeriksaan "
        "eksternal. Jangan membuka control box, motor, atau mekanisme "
        "penggerak sendiri.",
        "Spesifikasi sistem penggerak dan pemeriksaan umum; verifikasi "
        "manual varian: " + OFFICIAL
    ),
}

FIELDS = (
    "symptoms",
    "possible_cause",
    "solution",
    "safety_notes",
    "source",
)

def main():
    if not DB.is_file():
        raise SystemExit(f"Database tidak ditemukan: {DB}")

    apply = "--apply" in sys.argv

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    try:
        machine = con.execute(
            "SELECT id, model FROM machines WHERE id = ?",
            (MODEL_ID,),
        ).fetchone()

        if not machine or machine["model"] != "DDL-7000A":
            raise SystemExit(
                "DIBATALKAN: identitas machine ID 4 bukan DDL-7000A."
            )

        rows = con.execute(
            "SELECT * FROM troubleshooting "
            "WHERE machine_id = ? ORDER BY id",
            (MODEL_ID,),
        ).fetchall()

        ids = [r["id"] for r in rows]
        if ids != EXPECTED_IDS:
            raise SystemExit(
                "DIBATALKAN: daftar ID berubah. "
                f"ID yang ditemukan: {ids}"
            )

        print("MODE:", "TERAPKAN" if apply else "PRATINJAU")
        print("Mesin:", machine["model"], "| ID:", MODEL_ID)
        print("Jumlah entri:", len(rows))

        changes = []
        for row in rows:
            for field in FIELDS:
                old = row[field] or ""
                new = REVISI[row["id"]][FIELDS.index(field)]
                if old != new:
                    changes.append((row["id"], field, old, new))

        if not changes:
            print("Tidak ada perubahan yang diperlukan.")
            return

        print(f"\nJumlah perubahan kolom: {len(changes)}")
        for rid, field, old, new in changes:
            print(f"\n--- ID {rid} | {field} ---")
            print("LAMA :", old)
            print("BARU :", new)

        if not apply:
            print(
                "\nPRATINJAU SAJA: database belum diubah.\n"
                "Periksa isi perubahan di atas terlebih dahulu."
            )
            return

        # Backup tambahan dibuat tepat sebelum perubahan.
        backup = DB.with_name(
            "garment_before_ddl7000a_apply_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".db"
        )
        con.close()
        shutil.copy2(DB, backup)

        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        con.execute("BEGIN IMMEDIATE")

        check = con.execute(
            "SELECT model FROM machines WHERE id = ?",
            (MODEL_ID,),
        ).fetchone()
        if not check or check["model"] != "DDL-7000A":
            raise RuntimeError("Identitas mesin berubah; batalkan.")

        current_ids = [
            r[0] for r in con.execute(
                "SELECT id FROM troubleshooting "
                "WHERE machine_id = ? ORDER BY id",
                (MODEL_ID,),
            )
        ]
        if current_ids != EXPECTED_IDS:
            raise RuntimeError("Daftar ID berubah; batalkan.")

        for rid in EXPECTED_IDS:
            values = REVISI[rid]
            assignments = ", ".join(f"{field} = ?" for field in FIELDS)
            con.execute(
                f"UPDATE troubleshooting SET {assignments} "
                "WHERE id = ? AND machine_id = ?",
                (*values, rid, MODEL_ID),
            )
            if con.execute("SELECT changes()").fetchone()[0] != 1:
                raise RuntimeError(f"ID {rid} tidak diperbarui tepat satu baris.")

        con.commit()
        print("\nPERUBAHAN BERHASIL DISIMPAN.")
        print("Cadangan sebelum perubahan:", backup)

    except Exception as exc:
        if con:
            try:
                con.rollback()
            except Exception:
                pass
        raise SystemExit(f"DIBATALKAN / GAGAL: {exc}")
    finally:
        try:
            con.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
