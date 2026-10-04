#!/data/data/com.termux/files/usr/bin/bash

if [ -z "$1" ]; then
    echo "Penggunaan:"
    echo "  ./part.sh 402-28015"
    echo "  ./part.sh 402-28010"
    exit 1
fi

echo "========================================"
echo "PENCARIAN PART PS-800"
echo "PART: $1"
echo "========================================"

grep -nE "$1" ps800-parts.txt

echo "========================================"
