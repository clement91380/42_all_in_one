" Norminette Auto-Formatter — Vim/Neovim configuration
" Add to your .vimrc or init.vim

" Option 1: Native LSP (Neovim 0.5+)
" Add to your lua config (init.lua or after/plugin/lsp.lua):
"
" lua << EOF
" local lspconfig = require('lspconfig')
" local configs = require('lspconfig.configs')
"
" if not configs.norminette_formatter then
"   configs.norminette_formatter = {
"     default_config = {
"       cmd = { 'naf', 'server' },
"       filetypes = { 'c' },
"       root_dir = lspconfig.util.root_pattern('.git', 'Makefile'),
"       settings = {},
"     },
"   }
" end
"
" lspconfig.norminette_formatter.setup{}
" EOF

" Option 2: CoC (works in both Vim and Neovim)
" Add to coc-settings.json:
" {
"   "languageserver": {
"     "norminette": {
"       "command": "naf",
"       "args": ["server"],
"       "filetypes": ["c"],
"       "rootPatterns": [".git", "Makefile"]
"     }
"   }
" }

" Option 3: ALE integration (Vim/Neovim)
" let g:ale_linters = { 'c': ['norminette_formatter'] }
" let g:ale_fixers = { 'c': ['norminette_formatter'] }

" Manual commands (work without LSP)
command! NafCheck !naf check %
command! NafFix !naf fix %

" Format on save (optional)
augroup NorminetteAutoFix
  autocmd!
  " Uncomment to enable auto-fix on save:
  " autocmd BufWritePre *.c :silent !naf fix %
augroup END
