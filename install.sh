#!/usr/bin/env bash
# 42 All-in-One — Installation script for Linux/macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/YOUR_USER/42_all_in_one/main/install.sh | bash
#    or: wget -qO- https://raw.githubusercontent.com/YOUR_USER/42_all_in_one/main/install.sh | bash

set -e

REPO_AIO="https://github.com/clement91380/42_all_in_one.git"
REPO_NAF="https://github.com/clement91380/norminette-auto-formatter.git"
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
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${BOLD}"
echo "  ┌─────────────────────────────────────┐"
echo "  │        42 All-in-One Installer       │"
echo "  │   Norminette + Compiler + Exams +    │"
echo "  │   Grade Predictor + Repo Checker     │"
echo "  └─────────────────────────────────────┘"
echo -e "${NC}"

# Check dependencies
info "Checking dependencies..."

command -v python3 >/dev/null 2>&1 || error "python3 is required. Install it with: sudo apt install python3"
command -v pip3 >/dev/null 2>&1 || command -v python3 -m pip >/dev/null 2>&1 || error "pip is required. Install it with: sudo apt install python3-pip"
command -v git >/dev/null 2>&1 || error "git is required. Install it with: sudo apt install git"

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python version: $PYTHON_VERSION"

# Check for tkinter
python3 -c "import tkinter" 2>/dev/null || {
    info "tkinter not found, installing..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt install -y python3-tk 2>/dev/null || info "Could not install tkinter automatically. Run: sudo apt install python3-tk"
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm tk 2>/dev/null || info "Run: sudo pacman -S tk"
    elif command -v brew >/dev/null 2>&1; then
        brew install python-tk 2>/dev/null || info "Run: brew install python-tk"
    fi
}

# Create install directory
info "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Clone or update repository
if [ -d "$INSTALL_DIR/src" ]; then
    info "Updating existing installation..."
    cd "$INSTALL_DIR/src"
    git pull --quiet
else
    info "Cloning repository..."
    git clone --depth=1 "$REPO_AIO" "$INSTALL_DIR/src" 2>/dev/null || {
        # Fallback: if repo doesn't exist yet, copy from local
        info "Repo not available, checking local files..."
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -d "$SCRIPT_DIR/forty_two_aio" ]; then
            cp -r "$SCRIPT_DIR" "$INSTALL_DIR/src"
            success "Installed from local files"
        else
            error "Could not find source files"
        fi
    }
fi

# Create virtual environment
info "Creating virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install the package
info "Installing 42 All-in-One..."
cd "$INSTALL_DIR/src"
pip install --quiet --upgrade pip
pip install --quiet -e .

# Install norminette if not present
if ! command -v norminette >/dev/null 2>&1; then
    info "Installing norminette..."
    pip install --quiet norminette
fi

# Create launcher scripts
info "Creating launchers..."

cat > "$BIN_DIR/42aio" << 'LAUNCHER'
#!/usr/bin/env bash
source "$HOME/.42aio/venv/bin/activate"
python -m forty_two_aio.main "$@"
LAUNCHER
chmod +x "$BIN_DIR/42aio"

cat > "$BIN_DIR/naf" << 'LAUNCHER'
#!/usr/bin/env bash
source "$HOME/.42aio/venv/bin/activate"
python -m norminette_formatter.cli.main "$@"
LAUNCHER
chmod +x "$BIN_DIR/naf"

# Add to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    info "Adding $BIN_DIR to PATH..."
    SHELL_RC=""
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    fi

    if [ -n "$SHELL_RC" ]; then
        echo "" >> "$SHELL_RC"
        echo "# 42 All-in-One" >> "$SHELL_RC"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
        info "Added to $SHELL_RC — restart your shell or run: source $SHELL_RC"
    fi
fi

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
echo -e "${BLUE}LSP for editors:${NC} naf server"
echo "  VSCode: install extension from editors/vscode/"
echo "  Vim/Neovim: see editors/vim/"
echo "  Emacs: see editors/emacs/"
echo "  Sublime: see editors/sublime/"
echo ""
