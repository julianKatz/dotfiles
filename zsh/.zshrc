# zmodload zsh/zprof

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# configure zsh-vi-mode
function zvm_config() {
  # start zsh-vi-mode in insert mode
  ZVM_LINE_INIT_MODE=$ZVM_MODE_INSERT
}


# Fix make target completion
autoload -U compinit && compinit

###########################
#####     PLUGINS     #####
###########################

source ~/.zplug/init.zsh

zplug 'romkatv/powerlevel10k', as:theme, depth:1

# zplug mafredri/zsh-async, from:github

# oh-my-zsh specific
zplug "plugins/git",       from:oh-my-zsh
zplug "plugins/gitfast",   from:oh-my-zsh
zplug "plugins/fzf",       from:oh-my-zsh
zplug "plugins/kubectl",   from:oh-my-zsh # for some reason this won't source the autocomplete, even though it runs the script
zplug "lib/history",       from:oh-my-zsh
zplug "lib/directories",   from:oh-my-zsh
zplug "lib/completion",    from:oh-my-zsh
# zplug "lib/clipboard",     from:oh-my-zsh  -- maybe this will help at some point

zplug "zsh-users/zsh-syntax-highlighting"
zplug "zsh-users/zsh-completions"

zplug "djui/alias-tips"
zplug "romkatv/zsh-defer", from:github
# Waiting on the solve to this bug as of 1/27/22: https://github.com/jeffreytse/zsh-vi-mode/issues/124
zplug "jeffreytse/zsh-vi-mode"

zplug "Aloxaf/fzf-tab", from:github
  # disable sort when completing `git checkout`
  zstyle ':completion:*:git-checkout:*' sort false
  # disable sort when completing options of any command
  zstyle ':completion:complete:*:options' sort false
  # set descriptions format to enable group support
  zstyle ':completion:*:descriptions' format '[%d]'
  # set list-colors to enable filename colorizing
  zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
  # limit users to root and myself
  zstyle ':completion:*' users root $USER
  # preview directory's content with exa when completing cd
  zstyle ':fzf-tab:complete:cd:*' fzf-preview 'exa -1 --color=always $realpath'
  # stole this from https://tlvince.com/slow-zsh-completion
  zstyle ':completion:*' hosts off

# has to be the last plugin, b/c says in README
zplug "zsh-users/zsh-syntax-highlighting", defer:2

zplug load

zstyle ':fzf-tab:complete:*:*' fzf-preview 'less ${(Q)realpath}'
export LESSOPEN='|lessfilter %s | head -200'

__git_files () { 
    _wanted files expl 'local files' _files     
}

#####################################
#####    SHELL CONFIGURATION    #####
#####################################

# Make filesystem navigation more like oh-my-zsh
setopt autocd autopushd

# I've had pasting problems in the past.  This has fixed before
## fix slow pasting with fast-syntax-highlight
#zstyle ':bracketed-paste-magic' active-widgets '.self-*'
#printf "\e[?2004l" # can fix bracketed paste something?

# improve responsiveness
# KEYTIMEOUT=1

# Make nvim the default EDITOR
export EDITOR='nvim'

# Add bin for tldr
export PATH="$HOME/bin:$PATH"

# Configure delta's use of `less` to always open the pager and clear after
# exiting (https://stackoverflow.com/a/12352224)
export DELTA_PAGER="less -+cFX"

# Fix weird non unicode characters
export LC_ALL="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LANGUAGE="en_US.UTF-8"

zstyle ':completion:*:*:make:*' tag-order 'targets'


export PATH="$PATH:${HOME}/.cargo/bin"

export BAT_THEME="Monokai Extended Origin"

#############################
######     ALIASES     ######
#############################

alias cb="git rev-parse --abbrev-ref HEAD"
alias vim="nvim"
alias v="vim"
alias c="clear"
alias dk="docker"
alias dkk="dk kill"
alias dkps="dk ps"
alias cat-basic="/usr/bin/cat"
alias cat="bat"
alias l="exa -l"
alias ll="exa -la"
alias ls="ls --color=tty"
alias fd="fdfind"
alias vimrc="cd ~/dotfiles/nvim/.config/nvim; vim init.vim"
alias zshrc="cd ~/dotfiles/zsh/; vim .zshrc"
alias dotfiles="cd ~/dotfiles"
alias gld="gcloud"
alias szsh="source ~/.zshrc"
alias m="make"
alias x="exit"
alias :q="exit"
alias pd="popd"
alias mt="make test"

alias dev="cd ${HOME}/dev"

# Improved git log graph alias
alias glog="git log --graph --abbrev-commit --decorate --date=relative --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)'"

alias gpmr="git pull origin master --rebase"
alias glmr="git pull origin master --rebase"
alias glum="git pull upstream master"
alias glumr="git pull upstream master --rebase"
alias gdno="git --no-pager diff --name-only"
alias gdm="git diff master"
alias gdum="git diff upstream/master"
alias gcho="git branch | fzf | xargs -I {} git checkout {}"
alias gchod="git branch | fzf | xargs -I {} git branch -D {}"
alias gdcho="git diff --name-only | fzf | xargs -I {} git diff {}"
alias gdmcho="git diff master --name-only | fzf | xargs -I {} git diff master -- {}"
alias gcocho="git diff --name-only | fzf | xargs -I {} git checkout {}"
alias gcfd="git clean -fd"
alias gft="git fetch --tags"
alias gl="git log"
ggpf () {
  git push origin $(git_current_branch) --force-with-lease
}
# overwrite the verbose part of this alias
alias gc!="git commit --amend"
alias gsh="git stash"
alias gpgt="git push origin HEAD:refs/for/master"

# variables for faster kubectl
alias kls="kubectl config get-contexts"
alias kaf="kubectl apply -f"
alias kdf="kubeclt delete -f"
alias wk="watch kubectl"

# tmux
alias tm="tmux"
alias tma="tmux attach -t"
alias tmd="tmux detach"
alias tmls="tmux ls"
alias tmn="tmux new -s"
alias tmks="tmux kill-session -t"
alias tms="tmux switch -t"
alias tmkw="tmux kill-window"

##################################
#####     AUTOCOMPLETION     #####
##################################

### KUBECTL ###
if command -v kubectl &> /dev/null
then
  source <(command kubectl completion zsh)
fi
# kubectl () {
#     command kubectl $*
#     if [[ -z $KUBECTL_COMPLETE ]]
#     then
#         source <(command kubectl completion zsh)
#         KUBECTL_COMPLETE=1
#     fi
# }

### GCLOUD ###
gcloud () {
    command gcloud $*
    if [[ -z $GCLOUD_COMPLETE ]]
    then
        source /usr/share/google-cloud-sdk/completion.zsh.inc
        GCLOUD_COMPLETE=1
    fi
}

### GCLOUD ###
aws () {
    command aws $*
    if [[ -z $AWS_CLI_COMPLETE ]]
    then
        source ${HOME}/.local/bin/aws_zsh_completer.sh
        AWS_CLI_COMPLETE=1
    fi
}

#######################
#####     FZF     #####
#######################

# The plugin will auto execute this zvm_after_init function
function zvm_after_init() {
  # b/c fzf has key bindings that overlap with zvm, we have to wrap our fzf
  # source in this function.  There is some flexibility in how this works, so I
  # can refactor this in the future based on these example:
  # https://github.com/jeffreytse/zsh-vi-mode#execute-extra-commands
  [ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
}

# only store unique commands in the history... improves fzf Ctrl-R
setopt HIST_IGNORE_ALL_DUPS

# export FZF_COMPLETION_OPTS="--preview 'bat_or_tree {}'"
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow 2> /dev/null'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
# export FZF_DEFAULT_OPTS="--layout=reverse"
# export FZF_ALT_C_OPTS="--preview 'tree -C {} | head -200'"

############################
#####     SOURCING     #####
############################

# Google workstation config
if [[ -e $HOME/.zshrc-google ]]; then
  source $HOME/.zshrc-google
else
  source $HOME/.zshrc-personal
fi

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# zprof
