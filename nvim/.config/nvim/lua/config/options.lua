-- lua/config/options.lua

local opt = vim.opt

-- Editor UI
opt.number = true
opt.relativenumber = true
opt.cursorline = true
opt.signcolumn = "yes"
opt.termguicolors = true
opt.colorcolumn = "100"

-- Indentation
opt.expandtab = true
opt.shiftwidth = 2
opt.tabstop = 2
opt.smartindent = true

-- Search
opt.ignorecase = true
opt.smartcase = true
opt.hlsearch = true
opt.incsearch = true

-- File handling
opt.swapfile = false
opt.backup = false
opt.undofile = true
opt.autoread = true

-- Behavior
opt.scrolloff = 5
opt.updatetime = 300
opt.timeoutlen = 400
opt.clipboard = "unnamedplus"
opt.mouse = "a"

