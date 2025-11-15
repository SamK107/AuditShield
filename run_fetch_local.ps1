# Script : run_fetch_local.ps1
# Objet : lancer automatiquement la commande fetch_receipts toutes les 10 min

$ErrorActionPreference = "Stop"

# Get the directory where the script is located
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Write-Host "Script directory: $SCRIPT_DIR"
Write-Host "Project root: $PROJECT_ROOT"

# Go to project root to activate virtual environment
Set-Location $PROJECT_ROOT

# Activate virtual environment from project root
$venvPath = $null
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating .venv from project root..."
    $venvPath = ".venv\Scripts\Activate.ps1"
} else {
    Write-Error "Virtual environment not found in project root. Looking for $PROJECT_ROOT\.venv\Scripts\Activate.ps1"
    exit 1
}

# Activate the virtual environment
& $venvPath

# Go back to auditshield directory
Set-Location $SCRIPT_DIR

# Verify Django is available
try {
    python -c "import django" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Django import failed"
    }
    Write-Host "Virtual environment activated successfully. Python: $(Get-Command python | Select-Object -ExpandProperty Source)"
} catch {
    Write-Error "Django is not available after activating virtual environment."
    Write-Error "Python path: $(Get-Command python | Select-Object -ExpandProperty Source)"
    python -c "import django"
    exit 1
}

# Set Django settings
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"

# Log file path
$LOG_FILE = Join-Path $SCRIPT_DIR "..\fetch_receipts.log"

# Ensure log file directory exists
$LOG_DIR = Split-Path -Parent $LOG_FILE
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

# Log timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"=== $timestamp ===" | Out-File -FilePath $LOG_FILE -Append -Encoding utf8

# Run fetch_receipts command
Write-Host "Running fetch_receipts command..."
python manage.py fetch_receipts -v 3 2>&1 | Out-File -FilePath $LOG_FILE -Append -Encoding utf8

if ($LASTEXITCODE -ne 0) {
    Write-Error "fetch_receipts command failed. Check log: $LOG_FILE"
    exit 1
}

"" | Out-File -FilePath $LOG_FILE -Append -Encoding utf8
Write-Host "fetch_receipts completed successfully. Log: $LOG_FILE"

