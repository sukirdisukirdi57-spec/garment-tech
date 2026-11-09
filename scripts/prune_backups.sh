#!/usr/bin/env bash
# Tiered retention for garment.db backups.
# Policy:
#   - Today            : keep ALL
#   - Yesterday        : keep 1 per hour (newest in each hour)
#   - Older (<= yesterday) : keep 1 per day (newest in each day)
#
# Usage:
#   ./scripts/prune_backups.sh           # dry-run (safe)
#   ./scripts/prune_backups.sh --commit  # actually delete (asks y/N)
set -euo pipefail

DB_DIR="${DB_DIR:-database}"
COMMIT=0
[[ "${1:-}" == "--commit" ]] && COMMIT=1

TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d '1 day ago' +%Y-%m-%d 2>/dev/null \
    || date -d "@$(($(date +%s) - 86400))" +%Y-%m-%d)

echo "Retention policy:"
echo "  Today      ($TODAY)     : keep ALL"
echo "  Yesterday  ($YESTERDAY) : keep 1 per hour (newest)"
echo "  Older      (<=$YESTERDAY): keep 1 per day (newest)"
echo

TMP=".prune_scan.txt"
find "$DB_DIR" -maxdepth 1 \
    \( -name 'garment.db.backup-*' -o -name 'garment.db.bak-*' \) \
    -printf '%TY-%Tm-%Td\t%TH\t%T@\t%p\n' | sort -k3,3n > "$TMP"

declare -A KEEPERS
while IFS=$'\t' read -r day hour _epoch path; do
    if   [[ "$day" == "$TODAY"     ]]; then KEEPERS["path:$path"]=1
    elif [[ "$day" == "$YESTERDAY" ]]; then KEEPERS["hour:$day:$hour"]="$path"
    else                                    KEEPERS["day:$day"]="$path"
    fi
done < "$TMP"

declare -A KEEP
for k in "${!KEEPERS[@]}"; do
    if [[ "$k" == path:* ]]; then KEEP["${k#path:}"]=1
    else                          KEEP["${KEEPERS[$k]}"]=1
    fi
done

DELETE=()
while IFS=$'\t' read -r _ _ _ path; do
    [[ -z "${KEEP[$path]:-}" ]] && DELETE+=("$path")
done < "$TMP"

TOTAL=$(wc -l < "$TMP")
echo "=== Summary ==="
echo "Total backups     : $TOTAL"
echo "Keep              : ${#KEEP[@]}"
echo "Delete            : ${#DELETE[@]}"
if (( ${#DELETE[@]} > 0 )); then
    freed=$(du -ch "${DELETE[@]}" 2>/dev/null | tail -1 | awk '{print $1}')
    echo "Space to free     : $freed"
fi
echo

echo "=== Files to KEEP ==="
printf '%s\n' "${!KEEP[@]}" | sort
echo

echo "=== Files to DELETE (first 25) ==="
for ((i=0; i<${#DELETE[@]} && i<25; i++)); do echo "  ${DELETE[$i]}"; done
(( ${#DELETE[@]} > 25 )) && echo "  ... and $(( ${#DELETE[@]} - 25 )) more"
echo

if (( COMMIT == 0 )); then
    echo "[DRY-RUN] No files deleted. Re-run with --commit to delete."
    rm -f "$TMP"
    exit 0
fi

read -r -p "Delete ${#DELETE[@]} files? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; rm -f "$TMP"; exit 0; }

for f in "${DELETE[@]}"; do rm -v "$f"; done
rm -f "$TMP"
echo "[DONE] Deleted ${#DELETE[@]} files."
