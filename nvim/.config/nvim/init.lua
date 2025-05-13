-- init.lua

-- Bootstrap lazy.nvim plugin manager
require("plugins.lazy-bootstrap")

-- Load user config
require("plugins")
require("config.options")
require("config.keymaps")
require("config.lsp")
require("config.theme")

