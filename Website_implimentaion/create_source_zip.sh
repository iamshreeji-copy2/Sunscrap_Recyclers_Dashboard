#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

OUTPUT_ZIP="/home/linux/Documents/Darshan_SCADA_Software_October_2026/Sunscrap_Solar_SCADA_Source.zip"

echo "Creating clean reproducible source ZIP archive..."
rm -f "$OUTPUT_ZIP"

zip -r "$OUTPUT_ZIP" . \
  -x "data/db.sqlite3*" \
  -x "data/captured_emails/*" \
  -x "data/exports/*" \
  -x "*.pyc" \
  -x "*__pycache__*" \
  -x ".git*" \
  -x "venv/*" \
  -x ".env"

echo "Archive successfully generated at: $OUTPUT_ZIP"
ls -lh "$OUTPUT_ZIP"
