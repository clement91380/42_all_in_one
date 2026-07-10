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
BOLD='\033[1m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${RED}[WARN]${NC} $1"; }

echo -e "${BOLD}"
echo "  +-----------------------------------------+"
echo "  |         42 All-in-One Installer          |"
echo "  |    Norminette + Compiler + Exams +       |"
echo "  |    Grade Predictor + Repo Checker        |"
echo "  +-----------------------------------------+"
echo -e "${NC}"

# --- Detect OS and package manager ---
OS="$(uname -s)"
PKG=""
INSTALL_CMD=""
SUDO=""

if [ "$(id -u)" -ne 0 ]; then
    SUDO="sudo"
fi

if [ "$OS" = "Linux" ]; then
    if command -v apt-get >/dev/null 2>&1; then
        PKG="apt"
        INSTALL_CMD="$SUDO apt-get install -y"
        $SUDO apt-get update -qq 2>/dev/null
    elif command -v dnf >/dev/null 2>&1; then
        PKG="dnf"
        INSTALL_CMD="$SUDO dnf install -y"
    elif command -v pacman >/dev/null 2>&1; then
        PKG="pacman"
        INSTALL_CMD="$SUDO pacman -S --noconfirm"
    elif command -v zypper >/dev/null 2>&1; then
        PKG="zypper"
        INSTALL_CMD="$SUDO zypper install -y"
    fi
elif [ "$OS" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
        PKG="brew"
        INSTALL_CMD="brew install"
    else
        info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        PKG="brew"
        INSTALL_CMD="brew install"
    fi
fi

install_pkg() {
    local pkg_apt="$1"
    local pkg_dnf="$2"
    local pkg_pacman="$3"
    local pkg_brew="$4"
    local pkg_zypper="$5"

    case "$PKG" in
        apt)     $INSTALL_CMD "$pkg_apt" ;;
        dnf)     $INSTALL_CMD "$pkg_dnf" ;;
        pacman)  $INSTALL_CMD "$pkg_pacman" ;;
        brew)    $INSTALL_CMD "$pkg_brew" ;;
        zypper)  $INSTALL_CMD "$pkg_zypper" ;;
        *)       warn "Unknown package manager, install '$pkg_apt' manually" ;;
    esac
}

# --- Install all dependencies ---
info "Installing dependencies..."

# Python
if ! command -v python3 >/dev/null 2>&1; then
    info "Installing Python..."
    install_pkg "python3" "python3" "python" "python@3" "python3"
fi

# pip / venv
if ! python3 -m venv --help >/dev/null 2>&1; then
    info "Installing python3-venv..."
    install_pkg "python3-venv" "python3-libs" "python" "python@3" "python3-base"
fi

# git
if ! command -v git >/dev/null 2>&1; then
    info "Installing git..."
    install_pkg "git" "git" "git" "git" "git"
fi

# gcc / cc (for compilation checks)
if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1; then
    info "Installing gcc..."
    install_pkg "gcc" "gcc" "gcc" "gcc" "gcc"
fi

# tkinter (required for GUI)
if ! python3 -c "import tkinter" 2>/dev/null; then
    info "Installing tkinter..."
    install_pkg "python3-tk" "python3-tkinter" "tk" "python-tk" "python3-tk"
fi

# make (useful but not strictly required)
if ! command -v make >/dev/null 2>&1; then
    info "Installing make..."
    install_pkg "make" "make" "make" "make" "make"
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
success "Python $PYTHON_VERSION ready"

# --- Create install directory ---
info "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# --- Clone or update repository ---
if [ -d "$INSTALL_DIR/src/.git" ]; then
    info "Updating existing installation..."
    cd "$INSTALL_DIR/src"
    git pull --quiet
else
    info "Cloning repository..."
    rm -rf "$INSTALL_DIR/src"
    git clone --depth=1 "$REPO_AIO" "$INSTALL_DIR/src" 2>&1 || {
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -d "$SCRIPT_DIR/forty_two_aio" ]; then
            cp -r "$SCRIPT_DIR/." "$INSTALL_DIR/src/"
            success "Installed from local files"
        else
            warn "Could not clone repo, trying local install..."
            exit 1
        fi
    }
fi

# --- Create virtual environment ---
info "Creating virtual environment..."
VENV_OK=false

# Attempt 1: standard venv
if python3 -m venv "$VENV_DIR" 2>/dev/null; then
    VENV_OK=true
    success "venv created"
fi

# Attempt 2: install python3-venv package and retry
if [ "$VENV_OK" = false ]; then
    info "venv failed, installing python3-venv..."
    install_pkg "python3-venv" "python3-libs" "python" "python@3" "python3-base"
    if python3 -m venv "$VENV_DIR" 2>/dev/null; then
        VENV_OK=true
        success "venv created (after installing python3-venv)"
    fi
fi

# Attempt 3: use virtualenv as fallback
if [ "$VENV_OK" = false ]; then
    info "venv still failing, trying virtualenv..."
    pip3 install --user virtualenv 2>/dev/null || python3 -m pip install --user virtualenv 2>/dev/null
    if python3 -m virtualenv "$VENV_DIR" 2>/dev/null; then
        VENV_OK=true
        success "virtualenv created as fallback"
    fi
fi

# Attempt 4: no isolation (last resort)
if [ "$VENV_OK" = false ]; then
    warn "Could not create virtual environment. Installing without isolation..."
    VENV_DIR=""
fi

# Activate if venv exists
if [ -n "$VENV_DIR" ] && [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

# --- Install the package ---
info "Installing 42 All-in-One..."
cd "$INSTALL_DIR/src"

install_python_pkg() {
    # Attempt 1: normal pip install
    if pip install --quiet "$@" 2>/dev/null; then
        return 0
    fi
    # Attempt 2: --break-system-packages (PEP 668 bypass)
    if pip install --quiet --break-system-packages "$@" 2>/dev/null; then
        return 0
    fi
    # Attempt 3: pip3 with --user
    if pip3 install --quiet --user "$@" 2>/dev/null; then
        return 0
    fi
    # Attempt 4: python3 -m pip
    if python3 -m pip install --quiet "$@" 2>/dev/null; then
        return 0
    fi
    # Attempt 5: python3 -m pip --break-system-packages
    if python3 -m pip install --quiet --break-system-packages "$@" 2>/dev/null; then
        return 0
    fi
    warn "Failed to install: $*"
    return 1
}

install_python_pkg --upgrade pip setuptools wheel
install_python_pkg -e .

# --- Install norminette ---
info "Installing norminette..."
install_python_pkg norminette

# --- Create launcher scripts ---
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

chmod +x "$BIN_DIR/42aio"
chmod +x "$BIN_DIR/naf"

# --- Add to PATH ---
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    info "Adding $BIN_DIR to PATH..."

    for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
        if [ -f "$rc" ]; then
            if ! grep -q "# 42 All-in-One" "$rc" 2>/dev/null; then
                echo "" >> "$rc"
                echo "# 42 All-in-One" >> "$rc"
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$rc"
            fi
        fi
    done

    export PATH="$BIN_DIR:$PATH"
fi

# --- Verify installation ---
info "Verifying installation..."
python -c "from forty_two_aio.gui.app import App; print('  GUI: OK')" 2>/dev/null && true
python -c "from norminette_formatter.core import NorminetteFormatter; print('  Formatter: OK')" 2>/dev/null && true
python -c "from forty_two_aio.modules.exams.database import EXAM_DATABASE; print(f'  Exams: {len(EXAM_DATABASE)} exercises')" 2>/dev/null && true
command -v norminette >/dev/null 2>&1 && echo "  Norminette: OK"
command -v cc >/dev/null 2>&1 && echo "  Compiler: OK"

echo ""
success "Installation complete!"
echo ""
echo -e "${BOLD}Usage:${NC}"
echo "  42aio              Launch GUI"
echo "  42aio check *.c    Check norm + compilation"
echo "  42aio fix *.c      Auto-fix norm errors"
echo "  42aio repo URL     Check a GitHub repo"
echo "  42aio exam         Browse exam exercises"
echo "  42aio predict .    Predict project grade"
echo "  naf check *.c      Norminette check only"
echo "  naf fix *.c        Norminette fix only"
echo "  naf server         Start LSP server (for editors)"
echo ""
echo -e "${BLUE}Restart your shell or run:${NC} source ~/.bashrc"
echo ""
