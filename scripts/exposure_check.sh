#!/usr/bin/env bash
# ==============================================================================
# Jimcan Security Build - Web-Root Exposure Verification Script
# Conforms to docs/security/prompts/02-phase1-foundation.md Task 7.
#
# Usage:
#   ./scripts/exposure_check.sh <BASE_URL>
#
# Examples:
#   ./scripts/exposure_check.sh https://staging.jimcanconstruction.site
#   ./scripts/exposure_check.sh http://127.0.0.1:8000
# ==============================================================================

set -u

BASE_URL="${1:-}"

if [ -z "$BASE_URL" ]; then
  echo "Usage: $0 <BASE_URL>"
  echo "Example: $0 https://staging.jimcanconstruction.site"
  exit 1
fi

# Strip trailing slash from BASE_URL if present
BASE_URL="${BASE_URL%/}"

echo "=============================================================================="
echo " Running Web-Root Exposure Check against: $BASE_URL"
echo "=============================================================================="

PATHS_TO_CHECK=(
  "/.git/config"
  "/.env"
  "/db.sqlite3"
  "/manage.py"
  "/requirements.txt"
  "/media/"
  "/static/../settings.py"
  "/admin/"
  "/robots.txt"
)

EXPOSED_COUNT=0
SAFE_COUNT=0

for path in "${PATHS_TO_CHECK[@]}"; do
  TARGET_URL="${BASE_URL}${path}"
  
  # Perform read-only GET request without credentials, capturing HTTP status code
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET_URL")

  if [ "$HTTP_CODE" = "000" ]; then
    echo "  [ERROR] Connection failed to $TARGET_URL (HTTP 000)"
    echo "  Aborting: Server at $BASE_URL is unreachable or connection was refused."
    exit 2
  fi
  
  if [ "$path" = "/robots.txt" ]; then
    # robots.txt is normally public (200) or missing (404)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
      echo "  [OK]   $path -> HTTP $HTTP_CODE (Public file)"
      SAFE_COUNT=$((SAFE_COUNT + 1))
    else
      echo "  [WARN] $path -> HTTP $HTTP_CODE"
      SAFE_COUNT=$((SAFE_COUNT + 1))
    fi
  else
    # Sensitive targets must return 403 (Forbidden) or 404 (Not Found)
    if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "404" ]; then
      echo "  [SAFE] $path -> HTTP $HTTP_CODE"
      SAFE_COUNT=$((SAFE_COUNT + 1))
    else
      echo "  [FAIL] $path -> HTTP $HTTP_CODE (POTENTIAL EXPOSURE!)"
      EXPOSED_COUNT=$((EXPOSED_COUNT + 1))
    fi
  fi
done

echo "=============================================================================="
if [ "$EXPOSED_COUNT" -gt 0 ]; then
  echo " [FAIL] Exposure check detected $EXPOSED_COUNT potentially accessible sensitive path(s)."
  exit 1
else
  echo " [PASS] All sensitive paths returned 403 or 404. ($SAFE_COUNT safe endpoints checked)."
  exit 0
fi
