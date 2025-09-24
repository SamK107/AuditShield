if (-not $env:CINETPAY_WEBHOOK_SECRET) {
  Write-Error "Veuillez définir CINETPAY_WEBHOOK_SECRET avant d'exécuter ce script."
  exit 1
}

$ORDER = "ORD-SIMU-001"
Write-Host "== Envoi OK (PAID, signature valide) ==" -ForegroundColor Green
python manage.py cinetpay_simulate_webhook --order $ORDER --status PAID --signature ok

# Pour tester d'autres formats de signature :
# python manage.py cinetpay_simulate_webhook --order $ORDER --status PAID --signature ok --algo hex
# python manage.py cinetpay_simulate_webhook --order $ORDER --status PAID --signature ok --algo b64
# python manage.py cinetpay_simulate_webhook --order $ORDER --status PAID --signature ok --algo hexpref

Write-Host "`n== Idempotence (2e appel, même order) ==" -ForegroundColor Yellow
python manage.py cinetpay_simulate_webhook --order $ORDER --status PAID --signature ok --repeat 2 --delay 2

Write-Host "`n== Signature invalide (doit 400) ==" -ForegroundColor Red
python manage.py cinetpay_simulate_webhook --order "ORD-SIMU-BADSIGN" --status PAID --signature bad
