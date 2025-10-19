local wezterm = require("wezterm")

-- Define a version of Tokyo Night with a pure black background and brighter text
local tokyo_night_black = {
  foreground = "#DDEEFF", -- Brighter foreground color (e.g., a lighter blue-white)
  background = "#000000", -- Keep pure black background
  cursor_bg = "#DDEEFF",   -- Cursor background often matches foreground
  cursor_fg = "#1a1b26",
  cursor_border = "#DDEEFF",
  selection_fg = "#1a1b26",
  selection_bg = "#DDEEFF",
  ansi = {
    "#15161e", "#f7768e", "#9ece6a", "#e0af68",
    "#7aa2f7", "#bb9af7", "#7dcfff", "#a9b1d6"
  },
  brights = {
    "#5e6481", -- Slightly brighter version of a muted grey/blue
    "#ff88a0", -- Brighter red
    "#b2f080", -- Brighter green
    "#ffc87e", -- Brighter yellow/orange
    "#8cc0ff", -- Brighter blue
    "#d0adff", -- Brighter magenta/purple
    "#94e6ff", -- Brighter cyan
    "#FFFFFF"  -- Pure white for the brightest text (was #c0caf5)
  },
}

return {
  color_scheme = "Tokyo Night Black",
  color_schemes = {
    ["Tokyo Night Black"] = tokyo_night_black,
  },

  font = wezterm.font_with_fallback({
    "MesloLGS Nerd Font",
    "FiraCode Nerd Font",
    "CaskaydiaCove Nerd Font",
    "JetBrainsMono Nerd Font",
    "Menlo",
  }),
  font_size = 11.0,
  line_height = 1,
  freetype_render_target = "HorizontalLcd",  -- better LCD-style smoothing
  freetype_load_target = "Normal",

  enable_tab_bar = false,
  use_fancy_tab_bar = false,
  window_background_opacity = 0.96,
  term = "wezterm",

  window_padding = {
    left = 8,
    right = 8,
    top = 4,
    bottom = 4,
  },
}

