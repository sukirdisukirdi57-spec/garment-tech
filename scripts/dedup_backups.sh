#!/usr/bin/env bash
# Deduplicate garment.db backups: keep newest file per hash group, delete the rest.
# Usage: ./scripts/dedup_backups.sh           # dry-run
#        ./scripts/dedup_backups.sh --commit  # actually delete
set -euo pipefail

DB_DIR="${DB_DIR:-database}"
COMMIT=0
[[ "${1:-}" == "--commit" ]] && COMMIT=1

echo "Scanning $DB_DIR for backups..."
TMP_HASHES="$(mktemp)"
find "$DB_DIR" -maxdepth 1 \( -name 'garment.db.backup-*' -o -name 'garment.db.bak-*' \) \
    -exec sha256sum {} + | sort > "$TMP_HASHES"

# For each hash group with >1 file, keep the newest by mtime, mark the rest for deletion
awk '{print $1}' "$TMP_HASHES" | sort | uniq -c | awk '$1>1 {print $2}' > "${TMP_HASHES}.groups"

TO_DELETE=()
while read -r h; do
    mapfile -t files < <(grep "^$h" "$TMP_HASHES" | awk '{print $2}')
    # sort by mtime (oldest first), keep last
    mapfile -t sorted < <(for f in "${files[@]}"; do stat -c '%Y %n' "$f"; done | sort -n | awk '{print $2}')
    keep="${sorted[-1]}"
    echo "Group $h:"
    echo "  KEEP : $keep"
    for f in "${sorted[@]}"; do
        [[ "$f" == "$keep" ]] && continue
        echo "  DEL  : $f"
        TO_DELETE+=("$f")
    done
done < "${TMP_HASHES}.groups"

echo
echo "=== Summary ==="
echo "Files to delete: ${#TO_DELETE[@]}"
if (( ${#TO_DELETE[@]} > 0 )); then
    total=$(du -ch "${TO_DELETE[@]}" | tail -1 | awk '{print $1}')
    echo "Space to free  : $total"
fi

if (( COMMIT == 0 )); then
    echo
    echo "[DRY-RUN] No files deleted. Re-run with --commit to delete."
    rm -f "$TMP_HASHES" "${TMP_HASHES}.groups"
    exit 0
fi

echo
read -r -p "Delete ${#TO_DELETE[@]} files? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; rm -f "$TMP_HASHES" "${TMP_HASHES}.groups"; exit 0; }

for f in "${TO_DELETE[@]}"; do rm -v "$f"; done
rm -f "$TMP_HASHES" "${TMP_HASHES}.groups"
echo "[DONE] Deleted ${#TO_DELETE[@]} files."
