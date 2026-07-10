# 42 All-in-One — Auto-installer for Windows (PowerShell)
# Usage: iwr -useb https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$INSTALL_DIR = "$env:USERPROFILE\.42aio"
$VENV_DIR = "$INSTALL_DIR\venv"
$BIN_DIR = "$INSTALL_DIR\bin"
$REPO_URL = "https://github.com/clement91380/42_all_in_one.git"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") `
              + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

Write-Host ""
Write-Host "  +-----------------------------------------+" -ForegroundColor Blue
Write-Host "  |         42 All-in-One Installer          |" -ForegroundColor Blue
Write-Host "  |    Norminette + Compiler + Exams +       |" -ForegroundColor Blue
Write-Host "  |    Grade Predictor + Repo Checker        |" -ForegroundColor Blue
Write-Host "  +-----------------------------------------+" -ForegroundColor Blue
Write-Host ""

# ============================================================
# STEP 1: Ask what to install
# ============================================================
Write-Host "What do you want to install?" -ForegroundColor Yellow
Write-Host "  1) Full 42 All-in-One (GUI + CLI + formatter + all tools)"
Write-Host "  2) Norminette formatter only (CLI + LSP server)"
Write-Host ""
$INSTALL_MODE = Read-Host "Choice [1/2] (default: 1)"
if (-not $INSTALL_MODE) { $INSTALL_MODE = "1" }

Write-Host ""
Write-Host "Editor configuration:" -ForegroundColor Yellow
Write-Host "  1) Auto-configure ALL detected editors"
Write-Host "  2) Choose ONE editor to configure"
Write-Host "  3) Skip editor configuration"
Write-Host ""
$EDITOR_MODE = Read-Host "Choice [1/2/3] (default: 1)"
if (-not $EDITOR_MODE) { $EDITOR_MODE = "1" }

$CHOSEN_EDITOR = ""
if ($EDITOR_MODE -eq "2") {
    Write-Host ""
    Write-Host "  a) VSCode / VSCodium"
    Write-Host "  b) Vim / Neovim"
    Write-Host "  c) Sublime Text"
    Write-Host ""
    $CHOSEN_EDITOR = Read-Host "Which editor? [a/b/c]"
}

# ============================================================
# STEP 2: Install system dependencies
# ============================================================
Write-Info "Checking system dependencies..."

$hasWinget = Get-Command winget -ErrorAction SilentlyContinue
$hasChoco  = Get-Command choco  -ErrorAction SilentlyContinue

function Install-Dep($name, $wingetId, $chocoName, $url) {
    Write-Info "Installing $name..."
    if ($hasWinget) {
        winget install --id $wingetId --accept-package-agreements --accept-source-agreements --silent
        Refresh-Path
    } elseif ($hasChoco) {
        choco install $chocoName -y
        Refresh-Path
    } elseif ($url) {
        Write-Warn "Install $name manually: $url"
    } else {
        Write-Warn "$name not found. Install it manually."
    }
}

# Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Install-Dep "Python 3" "Python.Python.3.12" "python" "https://www.python.org/downloads/"
}
$pyVersion = python --version 2>&1
Write-Ok "Python: $pyVersion"

# Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Install-Dep "Git" "Git.Git" "git" "https://git-scm.com/downloads"
}
Write-Ok "Git ready"

# GCC via MinGW
if (-not (Get-Command gcc -ErrorAction SilentlyContinue)) {
    Install-Dep "GCC (MinGW)" "MinGW.MinGW" "mingw" "https://www.mingw-w64.org/downloads/"
}

# GitHub CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Install-Dep "GitHub CLI" "GitHub.cli" "gh" "https://cli.github.com"
}

# ============================================================
# STEP 3: GitHub authentication
# ============================================================
Write-Host ""
Write-Info "Checking GitHub connection..."

if (Get-Command gh -ErrorAction SilentlyContinue) {
    $ghStatus = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "GitHub login required for git automation." -ForegroundColor Yellow
        $doAuth = Read-Host "Connect to GitHub now? [Y/n]"
        if (-not $doAuth -or $doAuth -match '^[Yy]') {
            gh auth login --web -h github.com
        }
    } else {
        $ghUser = gh api user --jq '.login' 2>$null
        Write-Ok "GitHub connected as: $ghUser"
    }
}

# ============================================================
# STEP 4: Clone and install
# ============================================================
Write-Info "Installing to $INSTALL_DIR..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

if (Test-Path "$INSTALL_DIR\src\.git") {
    Write-Info "Updating existing installation..."
    Push-Location "$INSTALL_DIR\src"; git pull --quiet; Pop-Location
} else {
    if (Test-Path "$INSTALL_DIR\src") { Remove-Item -Recurse -Force "$INSTALL_DIR\src" }
    git clone --depth=1 $REPO_URL "$INSTALL_DIR\src"
}

# venv
Write-Info "Creating virtual environment..."
$VENV_OK = $false
try { python -m venv $VENV_DIR; $VENV_OK = $true } catch {}

if (-not $VENV_OK) {
    try { pip install --user virtualenv; python -m virtualenv $VENV_DIR; $VENV_OK = $true } catch {}
}

if ($VENV_OK) {
    & "$VENV_DIR\Scripts\Activate.ps1"
} else {
    Write-Warn "No venv, installing system-wide..."
}

function Install-PyPkg {
    param([string[]]$Packages)
    $pkgStr = $Packages -join " "
    $tried = @(
        { pip install --quiet $Packages },
        { pip install --quiet --break-system-packages $Packages },
        { python -m pip install --quiet $Packages }
    )
    foreach ($t in $tried) {
        try { & $t; return } catch {}
    }
    Write-Warn "Could not install: $pkgStr"
}

Push-Location "$INSTALL_DIR\src"
Install-PyPkg "--upgrade","pip","setuptools","wheel"
Install-PyPkg "-e","."
Install-PyPkg "norminette"
Pop-Location

Write-Ok "Packages installed"

# ============================================================
# STEP 5: Launchers
# ============================================================
Write-Info "Creating launchers..."

if ($VENV_OK) {
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
} else {
    @"
@echo off
python -m forty_two_aio.main %*
"@ | Set-Content "$BIN_DIR\42aio.bat" -Encoding ASCII

    @"
@echo off
python -m norminette_formatter.cli.main %*
"@ | Set-Content "$BIN_DIR\naf.bat" -Encoding ASCII
}

@"
function 42aio { & "$VENV_DIR\Scripts\python.exe" -m forty_two_aio.main @args }
function naf   { & "$VENV_DIR\Scripts\python.exe" -m norminette_formatter.cli.main @args }
"@ | Set-Content "$BIN_DIR\42aio-profile.ps1" -Encoding UTF8

# PATH
$curPath = [Environment]::GetEnvironmentVariable("Path","User")
if ($curPath -notlike "*$BIN_DIR*") {
    [Environment]::SetEnvironmentVariable("Path","$BIN_DIR;$curPath","User")
    $env:Path = "$BIN_DIR;$env:Path"
}

# PowerShell profile
if (-not (Test-Path $PROFILE)) { New-Item -Force $PROFILE | Out-Null }
$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($profileContent -notlike "*42aio-profile*") {
    Add-Content $PROFILE "`n# 42 All-in-One`n. `"$BIN_DIR\42aio-profile.ps1`""
}

# ============================================================
# STEP 6: Configure editors
# ============================================================
function Configure-VSCode {
    Write-Info "Configuring VSCode..."
    $dirs = @(
        "$env:APPDATA\Code\User",
        "$env:APPDATA\VSCodium\User"
    )
    foreach ($d in $dirs) {
        if (Test-Path $d) {
            $settings = "$d\settings.json"
            if (-not (Test-Path $settings)) { '{}' | Set-Content $settings }
            $json = Get-Content $settings -Raw | ConvertFrom-Json
            if (-not $json.'norminetteFormatter.serverPath') {
                Add-Member -InputObject $json -NotePropertyName 'norminetteFormatter.serverPath' -NotePropertyValue 'naf' -Force
                $json | ConvertTo-Json -Depth 10 | Set-Content $settings
                Write-Ok "VSCode settings.json updated"
            }
            # Copy extension
            $extDir = "$d\..\extensions\norminette-formatter-0.1.0"
            New-Item -ItemType Directory -Force -Path $extDir | Out-Null
            Copy-Item "$INSTALL_DIR\src\editors\vscode\*" $extDir -Force
            Write-Ok "VSCode extension copied"
        }
    }
}

function Configure-Vim {
    Write-Info "Configuring Vim/Neovim..."
    # Neovim
    $nvimDir = "$env:LOCALAPPDATA\nvim"
    if ((Get-Command nvim -ErrorAction SilentlyContinue) -or (Test-Path $nvimDir)) {
        New-Item -ItemType Directory -Force -Path "$nvimDir\lua" | Out-Null
        Copy-Item "$INSTALL_DIR\src\editors\vim\lua\norminette-formatter.lua" "$nvimDir\lua\" -Force
        $initLua = "$nvimDir\init.lua"
        if (-not (Test-Path $initLua)) { "" | Set-Content $initLua }
        $content = Get-Content $initLua -Raw -ErrorAction SilentlyContinue
        if ($content -notlike "*norminette-formatter*") {
            Add-Content $initLua "`n-- 42 Norminette Formatter`npcall(function() require('norminette-formatter').setup{} end)"
            Write-Ok "Neovim configured"
        }
    }
    # Vim
    $vimrc = "$env:USERPROFILE\_vimrc"
    if (Get-Command vim -ErrorAction SilentlyContinue) {
        if (-not (Test-Path $vimrc)) { "" | Set-Content $vimrc }
        $content = Get-Content $vimrc -Raw -ErrorAction SilentlyContinue
        if ($content -notlike "*NafCheck*") {
            Add-Content $vimrc "`n\" 42 Norminette`ncommand! NafCheck !naf check %`ncommand! NafFix !naf fix %"
            Write-Ok "Vim configured"
        }
    }
}

function Configure-Sublime {
    Write-Info "Configuring Sublime Text..."
    $sublimeDirs = @(
        "$env:APPDATA\Sublime Text\Packages\User",
        "$env:APPDATA\Sublime Text 3\Packages\User"
    )
    foreach ($d in $sublimeDirs) {
        if (Test-Path $d) {
            $lsp = "$d\LSP.sublime-settings"
            if (-not (Test-Path $lsp)) {
                @'
{
    "clients": {
        "norminette-formatter": {
            "enabled": true,
            "command": ["naf", "server"],
            "selector": "source.c"
        }
    }
}
'@ | Set-Content $lsp
            }
            Copy-Item "$INSTALL_DIR\src\editors\sublime\*" $d -Force
            Write-Ok "Sublime Text configured"
        }
    }
}

switch ($EDITOR_MODE) {
    "1" { Configure-VSCode; Configure-Vim; Configure-Sublime }
    "2" {
        switch ($CHOSEN_EDITOR) {
            "a" { Configure-VSCode }
            "b" { Configure-Vim }
            "c" { Configure-Sublime }
        }
    }
    "3" { Write-Info "Skipping editor configuration" }
}

# ============================================================
# STEP 7: Verify
# ============================================================
Write-Host ""
Write-Info "Verifying installation..."
Write-Host ""

python -c "from norminette_formatter.core import NorminetteFormatter; print('  Formatter : OK')" 2>$null
if ($INSTALL_MODE -eq "1") {
    python -c "from forty_two_aio.gui.app import App; print('  GUI       : OK')" 2>$null
    python -c "from forty_two_aio.modules.exams.database import EXAM_DATABASE; print('  Exams     : ' + str(len(EXAM_DATABASE)) + ' exercises')" 2>$null
}
if (Get-Command norminette -ErrorAction SilentlyContinue) { Write-Host "  Norminette: OK" }
if (Get-Command gcc        -ErrorAction SilentlyContinue) { Write-Host "  Compiler  : OK" }
if (Get-Command gh         -ErrorAction SilentlyContinue) { Write-Host "  GitHub CLI: OK" }

Write-Host ""
Write-Host "+------------------------------------------+" -ForegroundColor Green
Write-Host "|        Installation complete!            |" -ForegroundColor Green
Write-Host "+------------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
if ($INSTALL_MODE -eq "1") {
    Write-Host "  42aio              Launch GUI"
    Write-Host "  42aio check *.c    Check norm + compilation"
    Write-Host "  42aio fix *.c      Auto-fix norm errors"
    Write-Host "  42aio repo URL     Check GitHub repo"
    Write-Host "  42aio exam         Browse exam exercises"
    Write-Host "  42aio predict .    Predict project grade"
    Write-Host ""
}
Write-Host "  naf check *.c      Norminette check"
Write-Host "  naf fix *.c        Auto-fix norm errors"
Write-Host "  naf server         Start LSP server"
Write-Host ""
Write-Host "Restart your terminal to use the commands." -ForegroundColor Cyan
Write-Host ""
