-- lua/config/keymaps.lua

local map = vim.keymap.set
local opts = { noremap = true, silent = true }

-- Leader key
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- Clear search highlight
map("n", "<leader>l", ":nohlsearch<CR>", opts)

-- Fast saving
map("n", "<leader>w", ":w<CR>", opts)

-- Toggle line numbers
map("n", "<leader>n", ":set relativenumber!<CR>", opts)

-- Window navigation (redundant with tmux-navigator but handy in splits)
map("n", "<C-h>", "<C-w>h", opts)
map("n", "<C-j>", "<C-w>j", opts)
map("n", "<C-k>", "<C-w>k", opts)
map("n", "<C-l>", "<C-w>l", opts)

-- Quick source and edit config
map("n", "<leader>sv", ":source $MYVIMRC<CR>", opts)
map("n", "<leader>ev", ":edit $MYVIMRC<CR>", opts)

-- Easymotion bindings (must use noremap = false to resolve <Plug> mappings)
vim.keymap.set("n", "<leader><leader>f", "<Plug>(easymotion-bd-f)", { noremap = false })
vim.keymap.set("n", "<leader><leader>w", "<Plug>(easymotion-bd-w)", { noremap = false })
vim.keymap.set("n", "<leader><leader>l", "<Plug>(easymotion-bd-jk)", { noremap = false })
