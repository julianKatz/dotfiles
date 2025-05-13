-- lua/plugins/init.lua

require("lazy").setup({
  -- Appearance
  { "folke/tokyonight.nvim", lazy = false, priority = 1000 },

  -- Editing
  { "echasnovski/mini.surround", version = false },
  { "tpope/vim-repeat" },
  { "christoomey/vim-tmux-navigator" },
  { "easymotion/vim-easymotion" },
  { "karb94/neoscroll.nvim" },

  -- Git
  { "lewis6991/gitsigns.nvim" },

  -- LSP and autocomplete
  { "neovim/nvim-lspconfig" },
  { "williamboman/mason.nvim" },
  { "williamboman/mason-lspconfig.nvim" },
  { "hrsh7th/nvim-cmp" },
  { "hrsh7th/cmp-nvim-lsp" },
  { "L3MON4D3/LuaSnip" },
  { "saadparwaiz1/cmp_luasnip" },

  -- Syntax highlighting
  { "nvim-treesitter/nvim-treesitter", build = ":TSUpdate" },

  -- Comments and autopairs
  { "numToStr/Comment.nvim", opts = {} },
  { "windwp/nvim-autopairs", opts = {} },
})
