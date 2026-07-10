```
     _  _  ____       _    _ _       _             ___
    | || ||___ \     / \  | | |     (_)_ __       / _ \ _ __   ___
    | || |_ __) |   / _ \ | | |___  | | '_ \    | | | | '_ \ / _ \
    |__   _/ __/   / ___ \| | |___| | | | | |   | |_| | | | |  __/
       |_||_____| /_/   \_\_|_|     |_|_| |_|    \___/|_| |_|\___|

```

# 42 All-in-One

Everything you need to accelerate your 42 cursus in a single tool.

---

## Features

- **Norminette Auto-Formatter** -- check and auto-fix norm errors (CLI + LSP + GUI)
- **Compilation Checker** -- verifies your code compiles with -Wall -Wextra -Werror
- **main() Detection** -- catches commented-out or missing main functions
- **GitHub Repo Verifier** -- clones your repo and runs all checks automatically
- **Exam Database** -- 43 exercises from ranks 02 to 06 with subjects and hints
- **Grade Predictor** -- estimates your project score before the evaluation
- **Modern GUI** -- dark-mode interface, everything accessible in one window
- **LSP Server** -- real-time diagnostics in VSCode, Vim, Neovim, Emacs, Sublime Text

---

## Install

### Linux / macOS

```sh
curl -fsSL https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.sh | bash
```

or

```sh
wget -qO- https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/clement91380/42_all_in_one/main/install.ps1 | iex
```

### Manual

```sh
git clone https://github.com/clement91380/42_all_in_one.git
cd 42_all_in_one
make dev
```

---

## Usage

### GUI (default)

```sh
42aio
```

Opens the full graphical interface with all tools.

### CLI

```sh
42aio check *.c          # norm + compilation check
42aio fix *.c            # auto-fix norm errors
42aio repo <URL>         # clone and verify a GitHub repo
42aio exam               # list all exam exercises
42aio exam --rank 3      # filter by rank
42aio exam --search split
42aio predict ./my_project
```

### Norminette Formatter (standalone)

```sh
naf check *.c            # check norm errors
naf fix *.c              # auto-fix
naf server               # start LSP server
```

---

## Editor Setup (LSP)

All editors use the same core via `naf server`.

### VSCode

Install the extension from `editors/vscode/` or configure:

```json
{
  "norminetteFormatter.serverPath": "naf"
}
```

### Neovim (lspconfig)

```lua
require('norminette-formatter').setup{}
```

Or manually:

```lua
local lspconfig = require('lspconfig')
local configs = require('lspconfig.configs')

configs.norminette_formatter = {
  default_config = {
    cmd = { 'naf', 'server' },
    filetypes = { 'c' },
    root_dir = lspconfig.util.root_pattern('.git', 'Makefile'),
  },
}
lspconfig.norminette_formatter.setup{}
```

### Vim (CoC)

Add to `coc-settings.json`:

```json
{
  "languageserver": {
    "norminette": {
      "command": "naf",
      "args": ["server"],
      "filetypes": ["c"]
    }
  }
}
```

### Emacs (eglot, built-in since Emacs 29)

```elisp
(add-to-list 'eglot-server-programs '(c-mode . ("naf" "server")))
(add-hook 'c-mode-hook 'eglot-ensure)
```

### Sublime Text (LSP package)

Add to LSP settings:

```json
{
  "norminette-formatter": {
    "enabled": true,
    "command": ["naf", "server"],
    "selector": "source.c"
  }
}
```

---

## Exam Database

43 exercises covering ranks 02-06:

```
Rank 02: ft_strcpy, ft_strlen, fizzbuzz, inter, print_bits...
Rank 03: ft_split, ft_atoi_base, add_prime_sum, pgcd...
Rank 04: flood_fill, ft_itoa, sort_list, rev_wstr...
Rank 05: ft_printf, get_next_line
Rank 06: mini_serv
```

### Grade Predictor supports

```
libft, ft_printf, get_next_line, push_swap, pipex,
so_long, philosophers, minishell, + generic
```

---

## Project Structure

```
.
+-- forty_two_aio/          42 All-in-One application
|   +-- gui/                GUI (CustomTkinter)
|   +-- modules/
|       +-- norm/           Norminette integration
|       +-- compiler/       Compilation checker
|       +-- github/         Repo verifier
|       +-- exams/          Exam database
|       +-- predictor/      Grade predictor
+-- norminette_formatter/   Standalone formatter + LSP
|   +-- core/               Rules, diagnostics, fixer
|   +-- cli/                CLI interface
|   +-- server/             LSP server
+-- editors/                Editor configurations
|   +-- vscode/
|   +-- vim/
|   +-- emacs/
|   +-- sublime/
+-- tests/
+-- install.sh              Linux/macOS installer
+-- install.ps1             Windows installer
```

---

## Requirements

- Python 3.9+
- norminette (pip install norminette)
- gcc/cc (for compilation checks)
- git (for repo checker)
- tkinter (for GUI, usually pre-installed)

---

## License

MIT
