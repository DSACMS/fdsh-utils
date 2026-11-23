# Checks each cert's expiry and warns if it's within a configurable threshold (default 30 days). Exits non-zero if anything is expired or expiring soon.

# ./certs/check_expiry.sh
# warn if expiring within 30 days

# ./certs/check_expiry.sh 7
# warn if expiring within 7 days

#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WARN_DAYS="${1:-30}"
STATUS=0

check_cert() {
    local file="$1"
    local label="$2"

    if [[ ! -f "$file" ]]; then
        echo "  [MISSING] $label ($file not found)"
        STATUS=1
        return
    fi

    local end_date epoch_end epoch_now days_left
    end_date=$(openssl x509 -enddate -noout -in "$file" | cut -d= -f2)
    epoch_end=$(date -d "$end_date" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$end_date" +%s)
    epoch_now=$(date +%s)
    days_left=$(( (epoch_end - epoch_now) / 86400 ))

    if (( days_left < 0 )); then
        echo "  [EXPIRED]  $label — expired $(( -days_left )) day(s) ago ($end_date)"
        STATUS=1
    elif (( days_left <= WARN_DAYS )); then
        echo "  [WARNING]  $label — expires in $days_left day(s) ($end_date)"
        STATUS=1
    else
        echo "  [OK]       $label — expires in $days_left day(s) ($end_date)"
    fi
}

echo "==> Checking certificate expiry (warn threshold: ${WARN_DAYS} days)"
check_cert "$CERT_DIR/ca.crt"     "CA cert"
check_cert "$CERT_DIR/server.crt" "Server cert"
check_cert "$CERT_DIR/client.crt" "Client cert"

if [[ "$STATUS" -ne 0 ]]; then
    echo ""
    echo "One or more certs are expired or expiring soon. Run ./certs/generate.sh to regenerate."
fi

exit "$STATUS"