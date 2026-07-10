-- Norminette Auto-Formatter — Neovim LSP setup
-- Add this to your init.lua or source it from init.vim

local M = {}

function M.setup(opts)
    opts = opts or {}
    local cmd = opts.cmd or { "naf", "server" }

    local lspconfig_ok, lspconfig = pcall(require, "lspconfig")
    local configs_ok, configs = pcall(require, "lspconfig.configs")

    if not lspconfig_ok or not configs_ok then
        vim.notify("norminette-formatter: lspconfig required", vim.log.levels.ERROR)
        return
    end

    if not configs.norminette_formatter then
        configs.norminette_formatter = {
            default_config = {
                cmd = cmd,
                filetypes = { "c" },
                root_dir = lspconfig.util.root_pattern(".git", "Makefile"),
                settings = {},
            },
        }
    end

    lspconfig.norminette_formatter.setup({
        on_attach = opts.on_attach,
        capabilities = opts.capabilities,
    })
end

return M
