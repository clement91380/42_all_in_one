# 42 All-in-One — Auto-installer for Windows (PowerShell)
# Usage: iwr -useb https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.ps1 | iex

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

# --- Install dependencies automatically ---

# Check for winget (Windows 11 / Windows 10 with App Installer)
$hasWinget = Get-Command winget -ErrorAction SilentlyContinue
$hasChoco = Get-Command choco -ErrorAction SilentlyContinue

function Install-Dep($name, $wingetId, $chocoName) {
    Write-Info "Installing $name..."
    if ($hasWinget) {
        winget install --id $wingetId --accept-package-agreements --accept-source-agreements --silent 2>$null
    } elseif ($hasChoco) {
        choco install $chocoName -y 2>$null
    } else {
        Write-Err "$name is required. Install winget or chocolatey first, or install $name manually."
    }
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Python
Write-Info "Checking Python..."
$hasPython = Get-Command python -ErrorAction SilentlyContinue
if (-not $hasPython) {
    Install-Dep "Python" "Python.Python.3.12" "python"
}
$pyVersion = python --version 2>&1
Write-Ok "Found: $pyVersion"

# Git
Write-Info "Checking Git..."
$hasGit = Get-Command git -ErrorAction SilentlyContinue
if (-not $hasGit) {
    Install-Dep "Git" "Git.Git" "git"
}
Write-Ok "Git ready"

# GCC (via MinGW)
Write-Info "Checking C compiler..."
$hasGcc = Get-Command gcc -ErrorAction SilentlyContinue
if (-not $hasGcc) {
    $hasCc = Get-Command cc -ErrorAction SilentlyContinue
    if (-not $hasCc) {
        Install-Dep "MinGW (gcc)" "MinGW.MinGW" "mingw"
    }
}
Write-Ok "C compiler ready"

# --- Create directories ---
Write-Info "Installing to $INSTALL_DIR..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

# --- Clone repository ---
if (Test-Path "$INSTALL_DIR\src\.git") {
    Write-Info "Updating existing installation..."
    Push-Location "$INSTALL_DIR\src"
    git pull --quiet
    Pop-Location
} else {
    Write-Info "Cloning repository..."
    if (Test-Path "$INSTALL_DIR\src") { Remove-Item -Recurse -Force "$INSTALL_DIR\src" }
    try {
        git clone --depth=1 $REPO_URL "$INSTALL_DIR\src"
    } catch {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        if (Test-Path "$scriptDir\forty_two_aio") {
            Copy-Item -Recurse -Force "$scriptDir\*" "$INSTALL_DIR\src\"
            Write-Ok "Installed from local files"
        } else {
            Write-Err "Could not find source files"
        }
    }
}

# --- Create virtual environment ---
Write-Info "Creating virtual environment..."
python -m venv $VENV_DIR
& "$VENV_DIR\Scripts\Activate.ps1"

# --- Install packages ---
Write-Info "Installing 42 All-in-One..."
Push-Location "$INSTALL_DIR\src"
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -e .
pip install --quiet norminette
Pop-Location

# --- Create launchers ---
Write-Info "Creating launchers..."

@"
@echo off
call "$VENV_DIR\Scripts\activate.bat"
python -m forty_two_aio.main %*
"@ | Set-Content "$BIN_DIR\42aio.bat" -Encoding ASCII

@"
@echo off
call "$VENV_DIR\Scripts\activate.bat"
python -m norminette_formatter.cli.main %*
"@ | Set-Content "$BIN_DIR\naf.bat" -Encoding ASCII

# PowerShell functions
@"
function 42aio { & "$VENV_DIR\Scripts\python.exe" -m forty_two_aio.main `@args }
function naf { & "$VENV_DIR\Scripts\python.exe" -m norminette_formatter.cli.main `@args }
"@ | Set-Content "$BIN_DIR\42aio-profile.ps1" -Encoding UTF8

# --- Add to PATH ---
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$BIN_DIR*") {
    Write-Info "Adding to PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$BIN_DIR;$currentPath", "User")
    $env:Path = "$BIN_DIR;$env:Path"
}

# --- Add to PowerShell profile ---
$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Force -Path $profileDir | Out-Null }
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }

$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($profileContent -notlike "*42aio-profile*") {
    Add-Content $PROFILE "`n# 42 All-in-One`n. `"$BIN_DIR\42aio-profile.ps1`""
    Write-Info "Added to PowerShell profile"
}

# --- Verify ---
Write-Info "Verifying installation..."
& "$VENV_DIR\Scripts\python.exe" -c "from forty_two_aio.gui.app import App; print('  GUI: OK')" 2>$null
& "$VENV_DIR\Scripts\python.exe" -c "from norminette_formatter.core import NorminetteFormatter; print('  Formatter: OK')" 2>$null
& "$VENV_DIR\Scripts\python.exe" -c "from forty_two_aio.modules.exams.database import EXAM_DATABASE; print('  Exams: ' + str(len(EXAM_DATABASE)) + ' exercises')" 2>$null

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
Write-Host "Restart your terminal to use the commands." -ForegroundColor Cyan
Write-Host ""
