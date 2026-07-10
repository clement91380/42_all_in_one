#!/usr/bin/env bash
# 42 All-in-One — Auto-installer for Linux/macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.sh | bash
#    or: wget -qO- https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.sh | bash

# No set -e — we handle errors manually so partial failures don't abort the whole install

# ── When piped via curl|bash, stdin is the script itself so read() gets nothing.
# Reopen stdin from the terminal so interactive prompts work correctly. ──────
if [ ! -t 0 ] && [ -e /dev/tty ]; then
    exec 0</dev/tty
fi

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

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()     { echo -e "${RED}[ERR]${NC}  $1"; }
sep()     { echo ""; echo -e "${BOLD}--------------------------------------------${NC}"; echo ""; }

echo -e "${BOLD}"
echo "  +-----------------------------------------+"
echo "  |         42 All-in-One Installer          |"
echo "  |  Norminette + Compiler + Exams + Git +   |"
echo "  |     Grade Predictor + Repo Checker       |"
echo "  +-----------------------------------------+"
echo -e "${NC}"

# ============================================================
# STEP 1 — Choose action
# ============================================================
sep
echo -e "${BOLD}Action:${NC}"
echo "  1) Install / Update   (safe, keeps existing config)"
echo "  2) Reinstall          (clean: removes old venv + source)"
echo "  3) Uninstall          (removes everything)"
echo ""
read -rp "Choice [1/2/3] (default: 1): " ACTION
ACTION="${ACTION:-1}"

if [ "$ACTION" = "3" ]; then
    echo ""
    warn "This will remove $INSTALL_DIR and all launchers in $BIN_DIR."
    read -rp "Are you sure? [y/N]: " CONFIRM
    if [[ "$CONFIRM" =~ ^[Yy] ]]; then
        rm -rf "$INSTALL_DIR"
        rm -f "$BIN_DIR/42aio" "$BIN_DIR/naf" "$BIN_DIR/gh"
        for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
            [ -f "$rc" ] && sed -i '/# 42 All-in-One/d' "$rc" 2>/dev/null || true
            [ -f "$rc" ] && sed -i '/\.42aio/d'         "$rc" 2>/dev/null || true
        done
        success "42 All-in-One uninstalled."
    else
        info "Cancelled."
    fi
    exit 0
fi

if [ "$ACTION" = "2" ]; then
    info "Removing old source and venv for clean install..."
    rm -rf "$INSTALL_DIR/src" "$INSTALL_DIR/venv"
fi

# ============================================================
# STEP 2 — What to install
# ============================================================
sep
echo -e "${BOLD}What to install:${NC}"
echo "  1) Full 42 All-in-One  (GUI + CLI + all tools)"
echo "  2) Formatter only      (CLI + LSP server for editors)"
echo ""
read -rp "Choice [1/2] (default: 1): " INSTALL_MODE
INSTALL_MODE="${INSTALL_MODE:-1}"

# ============================================================
# STEP 3 — Editor configuration
# ============================================================
sep
echo -e "${BOLD}Editor setup:${NC}"
echo "  1) Auto-configure ALL detected editors"
echo "  2) Choose one editor"
echo "  3) Skip"
echo ""
read -rp "Choice [1/2/3] (default: 1): " EDITOR_MODE
EDITOR_MODE="${EDITOR_MODE:-1}"

CHOSEN_EDITOR=""
if [ "$EDITOR_MODE" = "2" ]; then
    echo ""
    echo "  a) VSCode / VSCodium"
    echo "  b) Vim / Neovim"
    echo "  c) Emacs"
    echo "  d) Sublime Text"
    echo ""
    read -rp "Editor [a/b/c/d]: " CHOSEN_EDITOR
fi

# ============================================================
# STEP 4 — Detect OS + package manager
# ============================================================
OS="$(uname -s)"
PKG=""
INSTALL_CMD=""
HAS_SUDO=false

if [ "$(id -u)" -eq 0 ]; then
    HAS_SUDO=true
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    HAS_SUDO=true
fi

if [ "$OS" = "Linux" ]; then
    if   command -v apt-get >/dev/null 2>&1; then PKG="apt"
    elif command -v dnf     >/dev/null 2>&1; then PKG="dnf"
    elif command -v pacman  >/dev/null 2>&1; then PKG="pacman"
    elif command -v zypper  >/dev/null 2>&1; then PKG="zypper"
    fi
    if $HAS_SUDO && [ -n "$PKG" ]; then
        case "$PKG" in
            apt)    INSTALL_CMD="sudo apt-get install -y"; sudo apt-get update -qq 2>/dev/null || true ;;
            dnf)    INSTALL_CMD="sudo dnf install -y" ;;
            pacman) INSTALL_CMD="sudo pacman -S --noconfirm" ;;
            zypper) INSTALL_CMD="sudo zypper install -y" ;;
        esac
    fi
elif [ "$OS" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
        PKG="brew"; INSTALL_CMD="brew install"
    else
        info "Installing Homebrew (no sudo needed)..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || true
        command -v brew >/dev/null 2>&1 && { PKG="brew"; INSTALL_CMD="brew install"; }
    fi
fi

sys_install() {
    # $1=apt $2=dnf $3=pacman $4=brew $5=zypper
    [ -z "$INSTALL_CMD" ] && { warn "No package manager available — skipping $1"; return 1; }
    case "$PKG" in
        apt)    $INSTALL_CMD "$1" 2>/dev/null ;;
        dnf)    $INSTALL_CMD "$2" 2>/dev/null ;;
        pacman) $INSTALL_CMD "$3" 2>/dev/null ;;
        brew)   $INSTALL_CMD "$4" 2>/dev/null ;;
        zypper) $INSTALL_CMD "$5" 2>/dev/null ;;
    esac
    return $?
}

# ============================================================
# STEP 5 — Install system dependencies (all optional/silent)
# ============================================================
sep
info "Checking dependencies..."

# python3
if ! command -v python3 >/dev/null 2>&1; then
    info "Installing Python3..."
    sys_install python3 python3 python python@3 python3 || warn "python3 not found — install manually"
fi
command -v python3 >/dev/null 2>&1 || { err "python3 required."; exit 1; }

# python3-venv
if ! python3 -m venv --help >/dev/null 2>&1; then
    sys_install python3-venv python3-libs python python@3 python3-base 2>/dev/null || true
fi

# git
if ! command -v git >/dev/null 2>&1; then
    info "Installing git..."
    sys_install git git git git git || true
fi
command -v git >/dev/null 2>&1 || { err "git required."; exit 1; }

# gcc (optional — compilation checks warn if missing)
if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1; then
    sys_install gcc gcc gcc gcc gcc 2>/dev/null || warn "gcc not found — compilation checks disabled"
fi

# tkinter (only needed for GUI mode)
if [ "$INSTALL_MODE" = "1" ] && ! python3 -c "import tkinter" 2>/dev/null; then
    info "Installing tkinter..."
    sys_install python3-tk python3-tkinter tk python-tk python3-tk 2>/dev/null || \
        warn "tkinter not available — GUI disabled, CLI still works"
fi

# gh CLI — try system then download binary (never requires sudo for binary path)
if ! command -v gh >/dev/null 2>&1; then
    info "Installing GitHub CLI..."
    GH_DONE=false

    if [ -n "$INSTALL_CMD" ]; then
        case "$PKG" in
            apt)
                { type -p wget >/dev/null || sys_install wget wget wget wget wget; } && \
                sudo mkdir -p -m 755 /etc/apt/keyrings 2>/dev/null && \
                wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
                    | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null 2>&1 && \
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
                    | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null 2>&1 && \
                sudo apt-get update -qq 2>/dev/null && sudo apt-get install -y gh 2>/dev/null && GH_DONE=true
                ;;
            dnf)    sudo dnf install -y gh 2>/dev/null && GH_DONE=true ;;
            pacman) sudo pacman -S --noconfirm github-cli 2>/dev/null && GH_DONE=true ;;
            brew)   brew install gh 2>/dev/null && GH_DONE=true ;;
        esac
    fi

    # Binary fallback — no sudo at all
    if ! $GH_DONE && ! command -v gh >/dev/null 2>&1; then
        info "Downloading gh binary to $BIN_DIR (no sudo)..."
        GH_VER="2.47.0"
        case "$(uname -m)" in
            x86_64)  GH_ARCH="amd64" ;;
            aarch64) GH_ARCH="arm64" ;;
            *)       GH_ARCH="amd64" ;;
        esac
        GH_URL="https://github.com/cli/cli/releases/download/v${GH_VER}/gh_${GH_VER}_linux_${GH_ARCH}.tar.gz"
        [ "$OS" = "Darwin" ] && GH_URL="https://github.com/cli/cli/releases/download/v${GH_VER}/gh_${GH_VER}_macOS_${GH_ARCH}.zip"

        mkdir -p "$BIN_DIR"
        TMPD="$(mktemp -d)"
        if curl -fsSL "$GH_URL" -o "$TMPD/gh.tar.gz" 2>/dev/null; then
            tar -xzf "$TMPD/gh.tar.gz" -C "$TMPD" 2>/dev/null && \
            find "$TMPD" -name "gh" -type f | head -1 | xargs -I{} cp {} "$BIN_DIR/gh" && \
            chmod +x "$BIN_DIR/gh" && success "gh installed to $BIN_DIR/gh"
        else
            warn "Could not download gh — GitHub features will still work via git directly"
        fi
        rm -rf "$TMPD"
    fi
fi

success "Dependencies checked"

# ============================================================
# STEP 6 — GitHub authentication (optional, non-blocking)
# ============================================================
sep
info "GitHub connection..."
export PATH="$BIN_DIR:$PATH"   # ensure our local gh is in PATH

if command -v gh >/dev/null 2>&1; then
    # Check auth without blocking on keyring issues
    GH_OK=false
    GH_USER=""
    if gh auth status --hostname github.com 2>&1 | grep -q "Logged in"; then
        GH_OK=true
        GH_USER="$(gh api user --jq '.login' 2>/dev/null || echo "")"
    fi

    if $GH_OK && [ -n "$GH_USER" ]; then
        success "GitHub: connected as $GH_USER"
    else
        echo ""
        echo -e "${BOLD}Connect GitHub for git automation (push, clone, create repos)?${NC}"
        echo "  A browser tab will open — log in with your GitHub account."
        echo "  You can skip this and connect later with: gh auth login"
        echo ""
        read -rp "Connect now? [Y/n]: " DO_AUTH
        DO_AUTH="${DO_AUTH:-Y}"
        if [[ "$DO_AUTH" =~ ^[Yy] ]]; then
            gh auth login --web -h github.com 2>/dev/null || warn "Auth failed — run 'gh auth login' manually later"
        else
            info "Skipping GitHub auth"
        fi
    fi
else
    warn "gh not available — git push will still work via git directly"
fi

# ============================================================
# STEP 7 — Clone / update source
# ============================================================
sep
info "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if [ -d "$INSTALL_DIR/src/.git" ]; then
    info "Updating existing source..."
    git -C "$INSTALL_DIR/src" pull --ff-only --quiet 2>/dev/null || \
        warn "Could not git pull — using existing version"
else
    rm -rf "$INSTALL_DIR/src"
    if git clone --depth=1 "$REPO_AIO" "$INSTALL_DIR/src" 2>/dev/null; then
        success "Source cloned"
    else
        # Fallback: use the script's own directory if running locally
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || SCRIPT_DIR="."
        if [ -d "$SCRIPT_DIR/forty_two_aio" ] || [ -d "$SCRIPT_DIR/norminette_formatter" ]; then
            cp -r "$SCRIPT_DIR/." "$INSTALL_DIR/src/"
            success "Installed from local files"
        else
            err "Could not clone repo and no local source found."
            err "Check your internet connection or run from the source directory."
            exit 1
        fi
    fi
fi

# ============================================================
# STEP 8 — Python venv
# ============================================================
VENV_OK=false

if [ -d "$VENV_DIR/bin/python" ]; then
    VENV_OK=true
    info "Using existing venv"
elif python3 -m venv "$VENV_DIR" 2>/dev/null; then
    VENV_OK=true
    success "venv created"
else
    sys_install python3-venv python3-libs python python@3 python3-base 2>/dev/null || true
    if python3 -m venv "$VENV_DIR" 2>/dev/null; then
        VENV_OK=true
        success "venv created (after installing python3-venv)"
    else
        pip3 install --user virtualenv 2>/dev/null || true
        python3 -m virtualenv "$VENV_DIR" 2>/dev/null && VENV_OK=true || \
            warn "No venv available — installing into user site-packages"
        VENV_DIR=""
    fi
fi

PYTHON="python3"
PIP="pip3"
if [ -n "$VENV_DIR" ] && [ -d "$VENV_DIR/bin" ]; then
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate" 2>/dev/null || true
    PYTHON="$VENV_DIR/bin/python"
    PIP="$VENV_DIR/bin/pip"
fi

# ============================================================
# STEP 9 — Pip install
# ============================================================
pip_install() {
    "$PIP" install --quiet "$@" 2>/dev/null && return 0
    "$PIP" install --quiet --break-system-packages "$@" 2>/dev/null && return 0
    "$PYTHON" -m pip install --quiet "$@" 2>/dev/null && return 0
    "$PYTHON" -m pip install --quiet --break-system-packages "$@" 2>/dev/null && return 0
    warn "pip: could not install $*"
    return 1
}

info "Installing packages..."
pip_install --upgrade pip setuptools wheel
cd "$INSTALL_DIR/src" && pip_install -e . && success "42 All-in-One installed"
pip_install norminette && success "norminette installed"

# ============================================================
# STEP 10 — Launchers
# ============================================================
info "Creating launchers..."

if [ -n "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
    cat > "$BIN_DIR/42aio" <<LAUNCHER
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate" 2>/dev/null
python -m forty_two_aio.main "\$@"
LAUNCHER

    cat > "$BIN_DIR/naf" <<LAUNCHER
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate" 2>/dev/null
python -m norminette_formatter.cli.main "\$@"
LAUNCHER
else
    printf '#!/usr/bin/env bash\npython3 -m forty_two_aio.main "$@"\n' > "$BIN_DIR/42aio"
    printf '#!/usr/bin/env bash\npython3 -m norminette_formatter.cli.main "$@"\n' > "$BIN_DIR/naf"
fi

chmod +x "$BIN_DIR/42aio" "$BIN_DIR/naf"

# PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
        [ -f "$rc" ] || continue
        grep -q "# 42 All-in-One" "$rc" 2>/dev/null && continue
        { echo ""; echo "# 42 All-in-One"; echo "export PATH=\"\$HOME/.local/bin:\$PATH\""; } >> "$rc"
    done
    export PATH="$BIN_DIR:$PATH"
fi

# ============================================================
# STEP 11 — Configure editors
# ============================================================
configure_vscode() {
    for settings_dir in \
        "$HOME/.config/Code/User" \
        "$HOME/.config/Code - OSS/User" \
        "$HOME/.config/VSCodium/User" \
        "$HOME/Library/Application Support/Code/User"; do
        [ -d "$settings_dir" ] || continue
        SETTINGS="$settings_dir/settings.json"
        [ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
        grep -q "norminetteFormatter" "$SETTINGS" 2>/dev/null && continue
        python3 -c "
import json
try:
    with open('$SETTINGS') as f: d = json.load(f)
except: d = {}
d['norminetteFormatter.serverPath'] = 'naf'
d['norminetteFormatter.autoFixOnSave'] = False
with open('$SETTINGS','w') as f: json.dump(d, f, indent=2)
" 2>/dev/null && success "VSCode: settings.json updated ($settings_dir)"

        for ext_dir in \
            "$HOME/.vscode/extensions" \
            "$HOME/.vscode-oss/extensions" \
            "$HOME/.vscode-server/extensions"; do
            [ -d "$ext_dir" ] || continue
            mkdir -p "$ext_dir/norminette-formatter-0.1.0"
            cp "$INSTALL_DIR/src/editors/vscode/"* "$ext_dir/norminette-formatter-0.1.0/" 2>/dev/null && \
                success "VSCode: extension installed"
        done
    done
}

configure_vim() {
    # Neovim
    NVIM_DIR="$HOME/.config/nvim"
    if command -v nvim >/dev/null 2>&1 || [ -d "$NVIM_DIR" ]; then
        mkdir -p "$NVIM_DIR/lua"
        cp "$INSTALL_DIR/src/editors/vim/lua/norminette-formatter.lua" "$NVIM_DIR/lua/" 2>/dev/null
        INIT="$NVIM_DIR/init.lua"
        [ -f "$INIT" ] || touch "$INIT"
        grep -q "norminette-formatter" "$INIT" 2>/dev/null || \
            printf '\n-- 42 Norminette\npcall(function() require("norminette-formatter").setup{} end)\n' >> "$INIT"
        success "Neovim: init.lua configured"
    fi
    # Vim
    if command -v vim >/dev/null 2>&1; then
        VIMRC="$HOME/.vimrc"
        [ -f "$VIMRC" ] || touch "$VIMRC"
        grep -q "NafCheck" "$VIMRC" 2>/dev/null || \
            printf '\n\" 42 Norminette\ncommand! NafCheck !naf check %%\ncommand! NafFix !naf fix %%\n' >> "$VIMRC"
        success "Vim: .vimrc configured"
    fi
}

configure_emacs() {
    if command -v emacs >/dev/null 2>&1 || [ -d "$HOME/.emacs.d" ]; then
        mkdir -p "$HOME/.emacs.d/lisp"
        cp "$INSTALL_DIR/src/editors/emacs/norminette-formatter.el" "$HOME/.emacs.d/lisp/" 2>/dev/null
        INIT="$HOME/.emacs.d/init.el"
        [ -f "$INIT" ] || touch "$INIT"
        grep -q "norminette-formatter" "$INIT" 2>/dev/null || cat >> "$INIT" <<'ELISP'

;; 42 Norminette Formatter
(add-to-list 'load-path (expand-file-name "lisp" user-emacs-directory))
(require 'norminette-formatter nil t)
ELISP
        success "Emacs: init.el configured"
    fi
}

configure_sublime() {
    for d in \
        "$HOME/.config/sublime-text/Packages/User" \
        "$HOME/.config/sublime-text-3/Packages/User" \
        "$HOME/Library/Application Support/Sublime Text/Packages/User"; do
        [ -d "$d" ] || continue
        LSP="$d/LSP.sublime-settings"
        if [ ! -f "$LSP" ]; then
            cat > "$LSP" <<'JSON'
{
    "clients": {
        "norminette-formatter": {
            "enabled": true,
            "command": ["naf", "server"],
            "selector": "source.c"
        }
    }
}
JSON
        elif ! grep -q "norminette-formatter" "$LSP" 2>/dev/null; then
            python3 -c "
import json
with open('$LSP') as f: d = json.load(f)
d.setdefault('clients',{})['norminette-formatter']={'enabled':True,'command':['naf','server'],'selector':'source.c'}
with open('$LSP','w') as f: json.dump(d, f, indent=4)
" 2>/dev/null
        fi
        cp "$INSTALL_DIR/src/editors/sublime/"* "$d/" 2>/dev/null
        success "Sublime Text: LSP configured"
    done
}

case "$EDITOR_MODE" in
    1) configure_vscode; configure_vim; configure_emacs; configure_sublime ;;
    2)
        case "$CHOSEN_EDITOR" in
            a) configure_vscode ;;
            b) configure_vim ;;
            c) configure_emacs ;;
            d) configure_sublime ;;
        esac
        ;;
esac

# ============================================================
# STEP 12 — Verify
# ============================================================
sep
info "Verifying..."
echo ""

"$PYTHON" -c "from norminette_formatter.core import NorminetteFormatter; print('  formatter : OK')" 2>/dev/null || echo "  formatter : FAILED"
[ "$INSTALL_MODE" = "1" ] && {
    "$PYTHON" -c "from forty_two_aio.gui.app import App; print('  GUI       : OK')" 2>/dev/null \
        || echo "  GUI       : FAILED (tkinter missing? run: sudo apt install python3-tk)"
    "$PYTHON" -c "from forty_two_aio.modules.exams.database import EXAM_DATABASE; print('  exams     : ' + str(len(EXAM_DATABASE)) + ' exercises')" 2>/dev/null || true
}
command -v norminette >/dev/null 2>&1 && echo "  norminette: OK" || echo "  norminette: not found"
command -v cc         >/dev/null 2>&1 && echo "  compiler  : OK" || echo "  compiler  : not found (optional)"
command -v gh         >/dev/null 2>&1 && echo "  gh CLI    : OK" || echo "  gh CLI    : not found (optional)"

echo ""
echo -e "${GREEN}+------------------------------------------+${NC}"
echo -e "${GREEN}|        Installation complete!            |${NC}"
echo -e "${GREEN}+------------------------------------------+${NC}"
echo ""
echo -e "${BOLD}Commands:${NC}"
[ "$INSTALL_MODE" = "1" ] && echo "  42aio              Launch GUI (all tools)"
echo "  42aio check *.c    Check norm + compilation"
echo "  42aio fix *.c      Auto-fix norm errors"
echo "  42aio repo URL     Check a GitHub repo"
echo "  naf check *.c      Norminette check only"
echo "  naf fix *.c        Auto-fix only"
echo "  naf server         Start LSP server for editors"
echo ""
echo -e "${BLUE}Restart your shell or run:${NC}  source ~/.bashrc"
echo ""
