#!/usr/bin/env bash
set -euo pipefail

: "${CINETPAY_WEBHOOK_SECRET:?Veuillez definir CINETPAY_WEBHOOK_SECRET avant d'executer.}"

ORDER="ORD-SIMU-001"
echo "== Envoi OK (PAID, signature valide) =="
python manage.py cinetpay_simulate_webhook --order "$ORDER" --status PAID --signature ok

echo

"== Idempotence (2e appel, même order) =="
python manage.py cinetpay_simulate_webhook --order "$ORDER" --status PAID --signature ok --repeat 2 --delay 2

echo

echo "== Signature invalide (doit 400) =="
python manage.py cinetpay_simulate_webhook --order "ORD-SIMU-BADSIGN" --status PAID --signature bad

# Pour tester d'autres formats de signature :
# python manage.py cinetpay_simulate_webhook --order "$ORDER" --status PAID --signature ok --algo hex
# python manage.py cinetpay_simulate_webhook --order "$ORDER" --status PAID --signature ok --algo b64
# python manage.py cinetpay_simulate_webhook --order "$ORDER" --status PAID --signature ok --algo hexpref
