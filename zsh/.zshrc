# NEW VERSION
# Starting fresh.  Things have gotten very slow and I made this before LLMs.  Let's let the LLM help decide the best way to do things.

### --- PATH & ENV --------------------------------------------------------

export PATH="$PATH:$HOME/bin:/opt/homebrew/bin"
export EDITOR="nvim"
export TERM="xterm-256color"

### --- Zinit Plugin Manager ----------------------------------------------

# Install zinit only if it doesn't exist
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
[ ! -d $ZINIT_HOME ] && mkdir -p "$(dirname $ZINIT_HOME)"
[ ! -d $ZINIT_HOME/.git ] && git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
source "${ZINIT_HOME}/zinit.zsh"

### --- Completion Init ---------------------------------------------------
# Per fzf-tab docs, this needs tohappen before fzf-tab

autoload -Uz compinit
# Use cache for faster startup (optional)
zstyle ':completion::complete:*' use-cache on
zstyle ':completion::complete:*' cache-path ~/.zcompcache

compinit

### --- Plugins -----------------------------------------------------------

#### --- fzf + ripgrep -----------------------------------------------------

# Use ripgrep for fzf file search
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_DEFAULT_OPTS='--height=40% --layout=reverse --border'

# Optional: fuzzy search through history
# bindkey '^R' fzf-history-widget

zinit light Aloxaf/fzf-tab
# Syntax highlighting for commands as you type
zinit light zdharma-continuum/fast-syntax-highlighting

# General completions
zinit light zsh-users/zsh-completions

# Git plugin
git_current_branch() {
  git symbolic-ref --quiet --short HEAD 2>/dev/null || \
  git rev-parse --short HEAD 2>/dev/null
}
zinit snippet OMZ::plugins/git/git.plugin.zsh

# Custom make target completion
_make-targets() {
  local targets
  targets=(
    $(awk -F':' '/^[a-zA-Z0-9][^$#\/\t=]*:/ {
      sub(/:.*/, "", $1);
      if (!seen[$1]++) print $1
    }' Makefile 2>/dev/null)
  )
  compadd -- $targets
}
compdef _make-targets make

# Vim mode with prompt indicator and visual mode
function zvm_config() {
  ZVM_LINE_INIT_MODE=$ZVM_MODE_INSERT
}
zinit light jeffreytse/zsh-vi-mode

# ZVM will break fzf without this
zvm_after_init_commands+=('source <(fzf --zsh)')

### --- Aliases -----------------------------------------------------------

alias ..='cd ..'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias gl='git log'
alias x='exit'

### --- Starship Prompt ---------------------------------------------------

eval "$(starship init zsh)"

