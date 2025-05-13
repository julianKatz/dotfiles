-- lua/config/lsp.lua

-- Safely require dependencies
local mason_ok, mason = pcall(require, "mason")
local mason_lspconfig_ok, mason_lspconfig = pcall(require, "mason-lspconfig")
local lspconfig_ok, lspconfig = pcall(require, "lspconfig")

if not (mason_ok and mason_lspconfig_ok and lspconfig_ok) then
  vim.notify("LSP setup skipped: mason or lspconfig not loaded", vim.log.levels.WARN)
  return
end

-- Setup mason
mason.setup()

-- Setup mason-lspconfig and auto-install servers
mason_lspconfig.setup({
  ensure_installed = {
    "gopls",
    "pyright",
    "jsonls",
    "yamlls",
    "bashls",
  },
  automatic_installation = true,
})

-- LSP mappings
local on_attach = function(_, bufnr)
  local map = function(mode, lhs, rhs)
    vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, silent = true })
  end
  map("n", "gd", vim.lsp.buf.definition)
  map("n", "K", vim.lsp.buf.hover)
  map("n", "<leader>rn", vim.lsp.buf.rename)
  map("n", "<leader>ca", vim.lsp.buf.code_action)
  map("n", "gr", vim.lsp.buf.references)
end

-- Manually register servers to avoid setup_handlers timing issues
local servers = { "gopls", "pyright", "jsonls", "yamlls", "bashls" }

for _, server in ipairs(servers) do
  lspconfig[server].setup({
    on_attach = on_attach,
    capabilities = require("cmp_nvim_lsp").default_capabilities(),
  })
end

-- Autocomplete
local cmp = require("cmp")
cmp.setup({
  snippet = {
    expand = function(args)
      require("luasnip").lsp_expand(args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ["<C-Space>"] = cmp.mapping.complete(),
    ["<CR>"] = cmp.mapping.confirm({ select = true }),
  }),
  sources = {
    { name = "nvim_lsp" },
    { name = "luasnip" },
  },
})

