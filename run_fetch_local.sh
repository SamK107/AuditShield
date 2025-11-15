#!/usr/bin/env bash
# Robust run_fetch_local.sh (Windows Git Bash / WSL2 friendly)
set -euo pipefail

# 1) Aller au dossier du script (peu importe d’où on le lance)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2) Choix Python (priorité au binaire venv Windows ; fallback Linux ; sinon 'python')
if [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python"
fi

# 3) Logs (dans logs/)
mkdir -p logs
LOGFILE="logs/fetch_receipts.log"

# 4) Settings
export DJANGO_SETTINGS_MODULE=config.settings.dev

# 5) Run
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOGFILE"
$PY manage.py fetch_receipts -v 3 >> "$LOGFILE" 2>&1
echo "" >> "$LOGFILE"
