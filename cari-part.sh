#!/data/data/com.termux/files/usr/bin/bash

DB="$HOME/garment-tech/ps800-database.tsv"

if [ ! -f "$DB" ]; then
    echo "Database tidak ditemukan: $DB"
    exit 1
fi

cari_part() {
    clear
    echo "========================================"
    echo "       HASIL PENCARIAN JUKI PS-800"
    echo "========================================"
    echo "Kata kunci : $1"
    echo

    awk -F'|' -v q="$1" '
    BEGIN {
        IGNORECASE=1
        printf "%-18s %-38s %-5s %-6s %-5s\n", "PART NO", "DESCRIPTION", "QTY", "PAGE", "REF"
        print "------------------------------------------------------------------------------------------"
    }
    index($1,q) || index($2,q) {
        printf "%-18s %-38s %-5s %-6s %-5s\n", $1, $2, $3, $4, $5
        count++
    }
    END {
        print "------------------------------------------------------------------------------------------"
        printf "Jumlah hasil : %d\n", count
    }
    ' "$DB"

    echo "========================================"
    echo
    read -p "Tekan ENTER untuk kembali ke menu..."
}

while true; do
    clear
    echo "========================================"
    echo "       DATABASE PART JUKI PS-800"
    echo "========================================"
    echo
    echo "1. Cari nomor / nama part"
    echo "2. Tampilkan semua data"
    echo "3. Statistik database"
    echo "4. Keluar"
    echo
    read -p "Pilih menu [1-4]: " pilihan

    case "$pilihan" in
        1)
            read -p "Masukkan nomor/nama part: " kata
            if [ -n "$kata" ]; then
                cari_part "$kata"
            fi
            ;;
        2)
            clear
            echo "========================================"
            echo "          SEMUA DATA PART"
            echo "========================================"
            printf "%-18s %-38s %-5s %-6s %-5s\n" "PART NO" "DESCRIPTION" "QTY" "PAGE" "REF"
            echo "------------------------------------------------------------------------------------------"
            awk -F'|' '{
                printf "%-18s %-38s %-5s %-6s %-5s\n", $1, $2, $3, $4, $5
            }' "$DB"
            echo "------------------------------------------------------------------------------------------"
            echo
            read -p "Tekan ENTER untuk kembali ke menu..."
            ;;
        3)
            clear
            echo "========================================"
            echo "        STATISTIK DATABASE"
            echo "========================================"
            echo
            echo "Total record : $(wc -l < "$DB")"
            echo "Part unik    : $(cut -d'|' -f1 "$DB" | sort -u | wc -l)"
            echo
            read -p "Tekan ENTER untuk kembali ke menu..."
            ;;
        4)
            clear
            echo "Keluar dari database PS-800."
            exit 0
            ;;
        *)
            echo
            echo "Pilihan tidak valid."
            sleep 1
            ;;
    esac
done
