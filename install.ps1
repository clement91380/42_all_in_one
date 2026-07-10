# 42 All-in-One — Installation script for Windows (PowerShell)
# Usage: iwr -useb https://raw.githubusercontent.com/YOUR_USER/42_all_in_one/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$INSTALL_DIR = "$env:USERPROFILE\.42aio"
$VENV_DIR = "$INSTALL_DIR\venv"
$BIN_DIR = "$INSTALL_DIR\bin"
$REPO_URL = "https://github.com/clement91380/42_all_in_one.git"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  +-----------------------------------------+" -ForegroundColor Blue
Write-Host "  |         42 All-in-One Installer          |" -ForegroundColor Blue
Write-Host "  |    Norminette + Compiler + Exams +       |" -ForegroundColor Blue
Write-Host "  |    Grade Predictor + Repo Checker        |" -ForegroundColor Blue
Write-Host "  +-----------------------------------------+" -ForegroundColor Blue
Write-Host ""

# Check Python
Write-Info "Checking Python..."
try {
    $pyVersion = python --version 2>&1
    Write-Info "Found: $pyVersion"
} catch {
    Write-Err "Python is required. Download from https://www.python.org/downloads/"
}

# Check Git
Write-Info "Checking Git..."
try {
    git --version | Out-Null
} catch {
    Write-Err "Git is required. Download from https://git-scm.com/downloads"
}

# Create directories
Write-Info "Installing to $INSTALL_DIR..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

# Clone repository
if (Test-Path "$INSTALL_DIR\src") {
    Write-Info "Updating existing installation..."
    Push-Location "$INSTALL_DIR\src"
    git pull --quiet
    Pop-Location
} else {
    Write-Info "Cloning repository..."
    try {
        git clone --depth=1 $REPO_URL "$INSTALL_DIR\src"
    } catch {
        # Fallback to local copy
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        if (Test-Path "$scriptDir\forty_two_aio") {
            Copy-Item -Recurse -Force $scriptDir "$INSTALL_DIR\src"
            Write-Ok "Installed from local files"
        } else {
            Write-Err "Could not find source files"
        }
    }
}

# Create virtual environment
Write-Info "Creating virtual environment..."
python -m venv $VENV_DIR
& "$VENV_DIR\Scripts\Activate.ps1"

# Install
Write-Info "Installing 42 All-in-One..."
Push-Location "$INSTALL_DIR\src"
pip install --quiet --upgrade pip
pip install --quiet -e .
pip install --quiet norminette

Pop-Location

# Create batch launchers
Write-Info "Creating launchers..."

@"
@echo off
call "$VENV_DIR\Scripts\activate.bat"
python -m forty_two_aio.main %*
"@ | Set-Content "$BIN_DIR\42aio.bat"

@"
@echo off
call "$VENV_DIR\Scripts\activate.bat"
python -m norminette_formatter.cli.main %*
"@ | Set-Content "$BIN_DIR\naf.bat"

# PowerShell aliases
@"
function 42aio { & "$VENV_DIR\Scripts\python.exe" -m forty_two_aio.main @args }
function naf { & "$VENV_DIR\Scripts\python.exe" -m norminette_formatter.cli.main @args }
"@ | Set-Content "$BIN_DIR\42aio-aliases.ps1"

# Add to PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$BIN_DIR*") {
    Write-Info "Adding to PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$BIN_DIR;$currentPath", "User")
    $env:Path = "$BIN_DIR;$env:Path"
}

Write-Host ""
Write-Ok "Installation complete!"
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  42aio              Launch GUI"
Write-Host "  42aio check *.c    Check norm + compilation"
Write-Host "  42aio fix *.c      Auto-fix norm errors"
Write-Host "  42aio repo URL     Check a GitHub repo"
Write-Host "  42aio exam         Browse exam exercises"
Write-Host "  42aio predict .    Predict project grade"
Write-Host "  naf check *.c      Norminette check only"
Write-Host "  naf server         Start LSP server"
Write-Host ""
Write-Host "To load aliases in PowerShell:" -ForegroundColor Cyan
Write-Host "  . $BIN_DIR\42aio-aliases.ps1"
Write-Host ""
Write-Host "Add to your PowerShell profile for persistence:" -ForegroundColor Cyan
Write-Host "  Add-Content `$PROFILE '. $BIN_DIR\42aio-aliases.ps1'"
Write-Host ""
