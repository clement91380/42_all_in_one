#!/usr/bin/env bash
# 42 All-in-One — Auto-installer for Linux/macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.sh | bash
#    or: wget -qO- https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.sh | bash

set -e

REPO_AIO="https://github.com/clement91380/42_all_in_one.git"
INSTALL_DIR="$HOME/.42aio"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${BOLD}"
echo "  +-----------------------------------------+"
echo "  |         42 All-in-One Installer          |"
echo "  |    Norminette + Compiler + Exams +       |"
echo "  |    Grade Predictor + Repo Checker        |"
echo "  +-----------------------------------------+"
echo -e "${NC}"

# ============================================================
# STEP 1: Action — install / reinstall / uninstall
# ============================================================
echo -e "${BOLD}What do you want to do?${NC}"
echo ""
echo "  1) Install / Update"
echo "  2) Reinstall (clean install)"
echo "  3) Uninstall (remove everything)"
echo ""
read -p "Action [1/2/3] (default: 1): " ACTION
ACTION="${ACTION:-1}"

if [ "$ACTION" = "3" ]; then
    echo ""
    warn "This will remove $INSTALL_DIR and all launchers."
    read -p "Are you sure? [y/N]: " CONFIRM_REMOVE
    if [[ "$CONFIRM_REMOVE" =~ ^[Yy] ]]; then
        rm -rf "$INSTALL_DIR"
        rm -f "$BIN_DIR/42aio" "$BIN_DIR/naf"
        for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
            [ -f "$rc" ] && sed -i '/# 42 All-in-One/d; /\.42aio/d; /\.local\/bin.*PATH/d' "$rc" 2>/dev/null || true
        done
        success "42 All-in-One uninstalled."
    else
        info "Uninstall cancelled."
    fi
    exit 0
fi

if [ "$ACTION" = "2" ]; then
    info "Cleaning previous installation..."
    rm -rf "$INSTALL_DIR/src" "$INSTALL_DIR/venv"
fi

echo ""
echo -e "${BOLD}What do you want to install?${NC}"
echo ""
echo "  1) Full 42 All-in-One (GUI + CLI + formatter + all tools)"
echo "  2) Norminette formatter only (CLI + LSP server)"
echo ""
read -p "Choice [1/2] (default: 1): " INSTALL_MODE
INSTALL_MODE="${INSTALL_MODE:-1}"

echo ""
echo -e "${BOLD}Editor configuration:${NC}"
echo ""
echo "  1) Auto-configure ALL detected editors"
echo "  2) Choose ONE editor to configure"
echo "  3) Skip editor configuration"
echo ""
read -p "Choice [1/2/3] (default: 1): " EDITOR_MODE
EDITOR_MODE="${EDITOR_MODE:-1}"

CHOSEN_EDITOR=""
if [ "$EDITOR_MODE" = "2" ]; then
    echo ""
    echo "  a) VSCode / VSCodium"
    echo "  b) Vim / Neovim"
    echo "  c) Emacs"
    echo "  d) Sublime Text"
    echo ""
    read -p "Which editor? [a/b/c/d]: " CHOSEN_EDITOR
fi

# ============================================================
# STEP 2: Detect OS, package manager, sudo availability
# ============================================================
OS="$(uname -s)"
PKG=""
INSTALL_CMD=""
HAS_SUDO=false

# Only use sudo if it exists AND works without a password (non-interactive safe)
if [ "$(id -u)" -eq 0 ]; then
    HAS_SUDO=true
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    HAS_SUDO=true
fi

if [ "$OS" = "Linux" ]; then
    if command -v apt-get >/dev/null 2>&1; then
        PKG="apt"
        if $HAS_SUDO; then
            INSTALL_CMD="sudo apt-get install -y"
            sudo apt-get update -qq 2>/dev/null || true
        fi
    elif command -v dnf >/dev/null 2>&1; then
        PKG="dnf"
        $HAS_SUDO && INSTALL_CMD="sudo dnf install -y"
    elif command -v pacman >/dev/null 2>&1; then
        PKG="pacman"
        $HAS_SUDO && INSTALL_CMD="sudo pacman -S --noconfirm"
    elif command -v zypper >/dev/null 2>&1; then
        PKG="zypper"
        $HAS_SUDO && INSTALL_CMD="sudo zypper install -y"
    fi
elif [ "$OS" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
        PKG="brew"
        INSTALL_CMD="brew install"   # brew never needs sudo
    else
        info "Installing Homebrew (no sudo needed)..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        PKG="brew"
        INSTALL_CMD="brew install"
    fi
fi

# install_pkg: runs system package install only if we have rights — otherwise warns and continues
install_pkg() {
    local pkg_apt="$1" pkg_dnf="$2" pkg_pacman="$3" pkg_brew="$4" pkg_zypper="$5"
    if [ -z "$INSTALL_CMD" ]; then
        warn "No root/sudo — skipping system install of '$pkg_apt' (install manually if needed)"
        return 1
    fi
    case "$PKG" in
        apt)     $INSTALL_CMD "$pkg_apt" 2>/dev/null || warn "Could not install $pkg_apt" ;;
        dnf)     $INSTALL_CMD "$pkg_dnf" 2>/dev/null || warn "Could not install $pkg_dnf" ;;
        pacman)  $INSTALL_CMD "$pkg_pacman" 2>/dev/null || warn "Could not install $pkg_pacman" ;;
        brew)    $INSTALL_CMD "$pkg_brew" 2>/dev/null || warn "Could not install $pkg_brew" ;;
        zypper)  $INSTALL_CMD "$pkg_zypper" 2>/dev/null || warn "Could not install $pkg_zypper" ;;
        *)       warn "Unknown package manager — install '$pkg_apt' manually" ;;
    esac
    return 0
}

# ============================================================
# STEP 3: Install system dependencies
# ============================================================
info "Installing dependencies..."

if ! command -v python3 >/dev/null 2>&1; then
    info "Installing Python..."
    install_pkg "python3" "python3" "python" "python@3" "python3"
fi

# python3-venv: try system install, fall back silently (some distros bundle it)
if ! python3 -m venv --help >/dev/null 2>&1; then
    install_pkg "python3-venv" "python3-libs" "python" "python@3" "python3-base" || true
fi

# git: try system install, warn if missing
if ! command -v git >/dev/null 2>&1; then
    info "Installing git..."
    install_pkg "git" "git" "git" "git" "git" || warn "git not found. Install it manually."
fi
command -v git >/dev/null 2>&1 || { err "git is required."; exit 1; }

# gcc: try system install, warn but continue (compilation checks will just fail)
if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1; then
    info "Trying to install gcc..."
    install_pkg "gcc" "gcc" "gcc" "gcc" "gcc" || warn "gcc not found — compilation checks will be skipped."
fi

# tkinter: try system install; if unavailable, GUI will not start but CLI still works
if [ "$INSTALL_MODE" = "1" ]; then
    if ! python3 -c "import tkinter" 2>/dev/null; then
        info "Installing tkinter (required for GUI)..."
        install_pkg "python3-tk" "python3-tkinter" "tk" "python-tk" "python3-tk" || \
            warn "tkinter not available — GUI disabled, CLI still works. Install python3-tk manually."
    fi
fi

# GitHub CLI — try system install first, then download binary to ~/.local/bin (no sudo needed)
if ! command -v gh >/dev/null 2>&1; then
    info "Installing GitHub CLI..."
    GH_INSTALLED=false

    # System package (requires sudo)
    if [ -n "$INSTALL_CMD" ]; then
        case "$PKG" in
            apt)
                (type -p wget >/dev/null || sudo apt-get install wget -y 2>/dev/null) && \
                sudo mkdir -p -m 755 /etc/apt/keyrings && \
                wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
                    | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && \
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
                    | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
                sudo apt-get update -qq && sudo apt-get install gh -y && GH_INSTALLED=true || true
                ;;
            dnf)    sudo dnf install -y gh 2>/dev/null && GH_INSTALLED=true || true ;;
            pacman) sudo pacman -S --noconfirm github-cli 2>/dev/null && GH_INSTALLED=true || true ;;
            brew)   brew install gh && GH_INSTALLED=true || true ;;
        esac
    fi

    # Fallback: download pre-built binary to ~/.local/bin (no sudo required)
    if ! $GH_INSTALLED && ! command -v gh >/dev/null 2>&1; then
        info "Downloading GitHub CLI binary (no sudo needed)..."
        GH_VERSION="2.47.0"
        ARCH="$(uname -m)"
        case "$ARCH" in
            x86_64)  GH_ARCH="amd64" ;;
            aarch64) GH_ARCH="arm64" ;;
            armv6l)  GH_ARCH="armv6" ;;
            *)       GH_ARCH="amd64" ;;
        esac

        if [ "$OS" = "Linux" ]; then
            GH_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${GH_ARCH}.tar.gz"
        elif [ "$OS" = "Darwin" ]; then
            GH_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_macOS_${GH_ARCH}.zip"
        fi

        mkdir -p "$BIN_DIR"
        TMP_GH="$(mktemp -d)"

        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$GH_URL" -o "$TMP_GH/gh.tar.gz" 2>/dev/null && \
                tar -xzf "$TMP_GH/gh.tar.gz" -C "$TMP_GH" 2>/dev/null && \
                find "$TMP_GH" -name "gh" -type f -exec cp {} "$BIN_DIR/gh" \; && \
                chmod +x "$BIN_DIR/gh" && GH_INSTALLED=true || true
        elif command -v wget >/dev/null 2>&1; then
            wget -qO "$TMP_GH/gh.tar.gz" "$GH_URL" 2>/dev/null && \
                tar -xzf "$TMP_GH/gh.tar.gz" -C "$TMP_GH" 2>/dev/null && \
                find "$TMP_GH" -name "gh" -type f -exec cp {} "$BIN_DIR/gh" \; && \
                chmod +x "$BIN_DIR/gh" && GH_INSTALLED=true || true
        fi
        rm -rf "$TMP_GH"

        $GH_INSTALLED && success "GitHub CLI installed to ~/.local/bin/gh" || \
            warn "Could not install GitHub CLI. Git push will still work without it."
    fi
fi

success "Dependencies ready"

# ============================================================
# STEP 4: GitHub authentication
# ============================================================
echo ""
info "Checking GitHub connection..."

if command -v gh >/dev/null 2>&1; then
    if ! gh auth status >/dev/null 2>&1; then
        echo ""
        echo -e "${BOLD}GitHub login required for git automation (push, clone, etc.)${NC}"
        echo "A browser will open for authentication."
        echo ""
        read -p "Connect to GitHub now? [Y/n]: " GH_AUTH
        GH_AUTH="${GH_AUTH:-Y}"
        if [[ "$GH_AUTH" =~ ^[Yy] ]]; then
            gh auth login --web -h github.com || warn "GitHub auth failed, you can retry later with: gh auth login"
        fi
    else
        GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
        success "GitHub connected as: $GH_USER"
    fi
fi

# ============================================================
# STEP 5: Clone and install
# ============================================================
info "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

if [ -d "$INSTALL_DIR/src/.git" ]; then
    info "Updating existing installation..."
    cd "$INSTALL_DIR/src"
    git pull --quiet
else
    rm -rf "$INSTALL_DIR/src"
    git clone --depth=1 "$REPO_AIO" "$INSTALL_DIR/src" 2>&1 || {
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -d "$SCRIPT_DIR/forty_two_aio" ] || [ -d "$SCRIPT_DIR/norminette_formatter" ]; then
            cp -r "$SCRIPT_DIR/." "$INSTALL_DIR/src/"
            success "Installed from local files"
        else
            err "Could not find source. Check your internet connection."
            exit 1
        fi
    }
fi

# --- venv ---
info "Creating virtual environment..."
VENV_OK=false
if python3 -m venv "$VENV_DIR" 2>/dev/null; then
    VENV_OK=true
elif install_pkg "python3-venv" "python3-libs" "python" "python@3" "python3-base" && python3 -m venv "$VENV_DIR" 2>/dev/null; then
    VENV_OK=true
fi

if [ "$VENV_OK" = false ]; then
    pip3 install --user virtualenv 2>/dev/null || true
    python3 -m virtualenv "$VENV_DIR" 2>/dev/null && VENV_OK=true
fi

if [ "$VENV_OK" = false ]; then
    warn "No venv available, installing system-wide..."
    VENV_DIR=""
fi

if [ -n "$VENV_DIR" ] && [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

# --- pip install ---
cd "$INSTALL_DIR/src"

install_python_pkg() {
    pip install --quiet "$@" 2>/dev/null && return 0
    pip install --quiet --break-system-packages "$@" 2>/dev/null && return 0
    pip3 install --quiet --user "$@" 2>/dev/null && return 0
    python3 -m pip install --quiet "$@" 2>/dev/null && return 0
    python3 -m pip install --quiet --break-system-packages "$@" 2>/dev/null && return 0
    warn "Failed to install: $*"
    return 1
}

install_python_pkg --upgrade pip setuptools wheel
install_python_pkg -e .
install_python_pkg norminette

success "42 All-in-One installed"

# ============================================================
# STEP 6: Create launchers
# ============================================================
info "Creating launchers..."

if [ -n "$VENV_DIR" ] && [ -d "$VENV_DIR" ]; then
    cat > "$BIN_DIR/42aio" << LAUNCHER
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
python -m forty_two_aio.main "\$@"
LAUNCHER

    cat > "$BIN_DIR/naf" << LAUNCHER
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
python -m norminette_formatter.cli.main "\$@"
LAUNCHER
else
    cat > "$BIN_DIR/42aio" << 'LAUNCHER'
#!/usr/bin/env bash
python3 -m forty_two_aio.main "$@"
LAUNCHER

    cat > "$BIN_DIR/naf" << 'LAUNCHER'
#!/usr/bin/env bash
python3 -m norminette_formatter.cli.main "$@"
LAUNCHER
fi

chmod +x "$BIN_DIR/42aio" "$BIN_DIR/naf"

# ============================================================
# STEP 7: Configure editors
# ============================================================
configure_vscode() {
    info "Configuring VSCode/VSCodium..."
    local VSCODE_DIR=""
    for d in "$HOME/.vscode/extensions" "$HOME/.vscode-oss/extensions" "$HOME/.vscode-server/extensions"; do
        [ -d "$(dirname "$d")" ] && VSCODE_DIR="$(dirname "$d")"
    done

    # settings.json
    for settings_dir in \
        "$HOME/.config/Code/User" \
        "$HOME/.config/Code - OSS/User" \
        "$HOME/.config/VSCodium/User" \
        "$HOME/Library/Application Support/Code/User"; do
        if [ -d "$settings_dir" ]; then
            local SETTINGS="$settings_dir/settings.json"
            if [ ! -f "$SETTINGS" ]; then
                echo '{}' > "$SETTINGS"
            fi
            if ! grep -q "norminetteFormatter" "$SETTINGS" 2>/dev/null; then
                python3 -c "
import json, sys
try:
    with open('$SETTINGS') as f: data = json.load(f)
except: data = {}
data['norminetteFormatter.serverPath'] = 'naf'
data['norminetteFormatter.autoFixOnSave'] = False
data.setdefault('[c]', {})['editor.defaultFormatter'] = 'norminette-formatter'
with open('$SETTINGS', 'w') as f: json.dump(data, f, indent=2)
" 2>/dev/null && success "VSCode settings configured"
            fi
        fi
    done

    # Copy extension files
    if [ -n "$VSCODE_DIR" ]; then
        local EXT_DIR="$VSCODE_DIR/extensions/norminette-formatter-0.1.0"
        mkdir -p "$EXT_DIR"
        cp "$INSTALL_DIR/src/editors/vscode/package.json" "$EXT_DIR/" 2>/dev/null
        cp "$INSTALL_DIR/src/editors/vscode/extension.js" "$EXT_DIR/" 2>/dev/null
        success "VSCode extension installed"
    fi
}

configure_vim() {
    info "Configuring Vim/Neovim..."

    # Neovim lua config
    local NVIM_DIR="$HOME/.config/nvim"
    if [ -d "$NVIM_DIR" ] || command -v nvim >/dev/null 2>&1; then
        mkdir -p "$NVIM_DIR/lua"
        cp "$INSTALL_DIR/src/editors/vim/lua/norminette-formatter.lua" "$NVIM_DIR/lua/" 2>/dev/null

        # Add to init.lua if it exists
        if [ -f "$NVIM_DIR/init.lua" ]; then
            if ! grep -q "norminette-formatter" "$NVIM_DIR/init.lua" 2>/dev/null; then
                echo "" >> "$NVIM_DIR/init.lua"
                echo "-- 42 Norminette Formatter LSP" >> "$NVIM_DIR/init.lua"
                echo "pcall(function() require('norminette-formatter').setup{} end)" >> "$NVIM_DIR/init.lua"
                success "Neovim init.lua configured"
            fi
        else
            # Create minimal init.lua
            cat > "$NVIM_DIR/init.lua" << 'LUA'
-- 42 Norminette Formatter LSP
pcall(function() require('norminette-formatter').setup{} end)
LUA
            success "Neovim init.lua created"
        fi
    fi

    # Vim vimrc
    local VIMRC="$HOME/.vimrc"
    if command -v vim >/dev/null 2>&1; then
        if [ ! -f "$VIMRC" ] || ! grep -q "NafCheck" "$VIMRC" 2>/dev/null; then
            cat >> "$VIMRC" << 'VIM'

" 42 Norminette Formatter
command! NafCheck !naf check %
command! NafFix !naf fix %
VIM
            success "Vim configured (commands :NafCheck :NafFix)"
        fi
    fi
}

configure_emacs() {
    info "Configuring Emacs..."

    local EMACS_DIR="$HOME/.emacs.d"
    local INIT_EL="$EMACS_DIR/init.el"

    if command -v emacs >/dev/null 2>&1 || [ -d "$EMACS_DIR" ]; then
        mkdir -p "$EMACS_DIR/lisp"
        cp "$INSTALL_DIR/src/editors/emacs/norminette-formatter.el" "$EMACS_DIR/lisp/" 2>/dev/null

        if [ ! -f "$INIT_EL" ]; then
            touch "$INIT_EL"
        fi

        if ! grep -q "norminette-formatter" "$INIT_EL" 2>/dev/null; then
            cat >> "$INIT_EL" << 'ELISP'

;; 42 Norminette Formatter
(add-to-list 'load-path (expand-file-name "lisp" user-emacs-directory))
(require 'norminette-formatter nil t)
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs '(c-mode . ("naf" "server"))))
ELISP
            success "Emacs configured"
        fi
    fi
}

configure_sublime() {
    info "Configuring Sublime Text..."

    local SUBLIME_DIR=""
    for d in \
        "$HOME/.config/sublime-text/Packages/User" \
        "$HOME/.config/sublime-text-3/Packages/User" \
        "$HOME/Library/Application Support/Sublime Text/Packages/User"; do
        if [ -d "$d" ]; then
            SUBLIME_DIR="$d"
            break
        fi
    done

    if [ -n "$SUBLIME_DIR" ]; then
        # LSP settings
        local LSP_SETTINGS="$SUBLIME_DIR/LSP.sublime-settings"
        if [ ! -f "$LSP_SETTINGS" ]; then
            cat > "$LSP_SETTINGS" << 'JSON'
{
    "clients": {
        "norminette-formatter": {
            "enabled": true,
            "command": ["naf", "server"],
            "selector": "source.c",
            "schemes": ["file"]
        }
    }
}
JSON
            success "Sublime Text LSP configured"
        elif ! grep -q "norminette-formatter" "$LSP_SETTINGS" 2>/dev/null; then
            python3 -c "
import json
with open('$LSP_SETTINGS') as f: data = json.load(f)
data.setdefault('clients', {})['norminette-formatter'] = {
    'enabled': True, 'command': ['naf', 'server'],
    'selector': 'source.c', 'schemes': ['file']
}
with open('$LSP_SETTINGS', 'w') as f: json.dump(data, f, indent=4)
" 2>/dev/null && success "Sublime Text LSP configured"
        fi

        # Commands
        cp "$INSTALL_DIR/src/editors/sublime/NorminetteFormatter.sublime-commands" "$SUBLIME_DIR/" 2>/dev/null
    else
        if command -v subl >/dev/null 2>&1; then
            warn "Sublime Text found but Packages/User not detected"
        fi
    fi
}

# Apply editor configuration
case "$EDITOR_MODE" in
    1)
        configure_vscode
        configure_vim
        configure_emacs
        configure_sublime
        ;;
    2)
        case "$CHOSEN_EDITOR" in
            a) configure_vscode ;;
            b) configure_vim ;;
            c) configure_emacs ;;
            d) configure_sublime ;;
            *) warn "Invalid choice, skipping editor config" ;;
        esac
        ;;
    3)
        info "Skipping editor configuration"
        ;;
esac

# ============================================================
# STEP 8: Add to PATH
# ============================================================
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
        if [ -f "$rc" ] && ! grep -q "# 42 All-in-One" "$rc" 2>/dev/null; then
            echo "" >> "$rc"
            echo "# 42 All-in-One" >> "$rc"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$rc"
        fi
    done
    export PATH="$BIN_DIR:$PATH"
fi

# ============================================================
# STEP 9: Verify and finish
# ============================================================
echo ""
info "Verifying installation..."
echo ""

python3 -c "from norminette_formatter.core import NorminetteFormatter; print('  Formatter: OK')" 2>/dev/null || echo "  Formatter: FAILED"

if [ "$INSTALL_MODE" = "1" ]; then
    python3 -c "from forty_two_aio.gui.app import App; print('  GUI: OK')" 2>/dev/null || echo "  GUI: FAILED (tkinter missing?)"
    python3 -c "from forty_two_aio.modules.exams.database import EXAM_DATABASE; print(f'  Exams: {len(EXAM_DATABASE)} exercises')" 2>/dev/null || true
fi

command -v norminette >/dev/null 2>&1 && echo "  Norminette: OK" || echo "  Norminette: FAILED"
command -v cc >/dev/null 2>&1 && echo "  Compiler: OK" || echo "  Compiler: not found"
command -v gh >/dev/null 2>&1 && echo "  GitHub CLI: OK" || echo "  GitHub CLI: not found"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "?")
    echo "  GitHub user: $GH_USER"
fi

echo ""
echo -e "${GREEN}+------------------------------------------+${NC}"
echo -e "${GREEN}|        Installation complete!            |${NC}"
echo -e "${GREEN}+------------------------------------------+${NC}"
echo ""

if [ "$INSTALL_MODE" = "1" ]; then
    echo -e "${BOLD}Commands:${NC}"
    echo "  42aio              Launch GUI (all tools)"
    echo "  42aio check *.c    Check norm + compilation"
    echo "  42aio fix *.c      Auto-fix norm errors"
    echo "  42aio repo URL     Check + clone GitHub repo"
    echo "  42aio exam         Browse exam exercises"
    echo "  42aio predict .    Predict project grade"
    echo ""
fi

echo -e "${BOLD}Formatter:${NC}"
echo "  naf check *.c      Check norminette"
echo "  naf fix *.c        Auto-fix norm errors"
echo "  naf server         Start LSP (editors connect here)"
echo ""
echo -e "${BLUE}Restart your shell or run:${NC} source ~/.bashrc"
echo ""
