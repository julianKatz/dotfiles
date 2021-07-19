" ---------------------------------------- GENERAL SETTINGS ---------------------------------------
filetype plugin indent on

let VIM_CONFIG_DIR=expand("$HOME/.config/nvim/vim-config")

execute "source" VIM_CONFIG_DIR . "/basic-settings.vim"

" WIP Settings
set nowrapscan  " Searches do not wrap, they are top to bottom
set splitbelow  " horizontal splits will open the new file on bottom
set splitright  " vertical splits open on the right, and splitting a file now makes the cursor end up on the right pane

execute "source" VIM_CONFIG_DIR . "/mappings.vim"

" WIP Mappings

" Create movements for 'in/at next parens' and 'in/at last parens'
onoremap in( :<c-u>normal! f(vi(<cr>
onoremap an( :<c-u>normal! f(va(<cr>
onoremap il( :<c-u>normal! F)vi(<cr>
onoremap al( :<c-u>normal! F)va(<cr>

" Do the same for curly braces... we need searching for this!  Will come in
" Chapter 30
" onoremap in{ :<c-u>normal! /{<cr>vi{<cr>
" onoremap an{ :<c-u>normal! /{<cr>va{<cr>
" onoremap il{ :<c-u>normal! ?}<cr>vi{<cr>
" onoremap al{ :<c-u>normal! ?}<cr>va{<cr>

" Underline the current text with [-]
nnoremap <leader>ul VypVr-<esc>o<esc>

" MISC

" Make help pages open as a vertical split
" Stolen From: https://vi.stackexchange.com/a/4464
augroup vimrc_help
  autocmd!
  autocmd BufEnter *.txt if &buftype == 'help' | wincmd L | endif
augroup END

" Turn on spellchecking for .txt, markdown files
augroup filetype_based_spelling
  autocmd!
  autocmd FileType text,markdown :setlocal spell spelllang=en_us
augroup END

" ----------------------------------------
" PLUGINS
" ----------------------------------------

" BEGIN PLUGIN DECLARATIONS
call plug#begin('~/.config/nvim/plugged')

Plug 'flwyd/vim-conjoin'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-repeat'
Plug 'tomtom/tcomment_vim'
Plug 'elzr/vim-json'
Plug 'christoomey/vim-tmux-navigator'
Plug 'nhooyr/neoman.vim'
Plug 'djoshea/vim-autoread'
Plug 'google/vim-searchindex' " This is broken by incsearch
Plug 'psliwka/vim-smoothie'
Plug 'honza/vim-snippets'
Plug 'easymotion/vim-easymotion'
if has('nvim-0.5')
Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}
Plug 'romgrk/nvim-treesitter-context'
endif

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'airblade/vim-gitgutter'

  let g:gitgutter_sign_allow_clobber=0

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'ojroques/vim-oscyank'

  augroup OSCYank
    autocmd!
    autocmd TextYankPost *
      \ if v:event.operator is 'y' && v:event.regname is '' | call YankOSC52(getreg('+')) | endif
  augroup END

  command! F f<bar> OSCYankReg%

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'haya14busa/incsearch-easymotion.vim'

  " Basic Usage
  map z/ <Plug>(incsearch-easymotion-/)
  map z? <Plug>(incsearch-easymotion-?)
  map zg/ <Plug>(incsearch-easymotion-stay)

  " Julian Usage
  map <space><space>/ <Plug>(incsearch-easymotion-/)
  map <space><space>? <Plug>(incsearch-easymotion-?)

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'joshdick/onedark.vim'

  set notermguicolors

  let g:onedark_terminal_italics=1

  augroup colorextend
    autocmd!

    " Make the main text lighter
    autocmd ColorScheme * call onedark#extend_highlight("Normal", { "fg": { "cterm": "253" } })

    " Remove search result background
    autocmd ColorScheme * call onedark#extend_highlight("Search", { "bg": { "cterm": "NONE" }})

    " Make search results underlined
    let s:yellow = { "gui": "#ffaf00", "cterm": "214", "cterm16": "3" }
    autocmd ColorScheme * call onedark#set_highlight("Search", { "fg": s:yellow, "gui": "underline", "cterm": "underline" })
  augroup END

  syntax enable

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'jiangmiao/auto-pairs'

  let g:AutoPairsFlyMode=0

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'scrooloose/nerdtree'
Plug 'jistr/vim-nerdtree-tabs'

  function! OpenFind()
    silent NERDTreeFind
    silent NERDTreeSteppedOpen
  endfunction

  let NERDTreeIgnore=['\.DS_Store$']

  nnoremap <silent><leader>n :call OpenFind()<cr>
  nnoremap <silent><leader>a :NERDTreeTabsToggle<cr>

  let g:nerdtree_tabs_focus_on_files=1
  let g:NERDTreeWinSize=60
  let NERDTreeShowHidden=1

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'dyng/ctrlsf.vim'

  nnoremap <Leader>f :CtrlSF<space>-R<space>
  vmap ?? <Plug>CtrlSFVwordExec

  let g:ctrlsf_auto_focus = {
      \ "at": "start"
      \ }

  let g:ctrlsf_ackprg = 'rg'

  " Try to make these as similar to fzf bindings as possible
  " vsplit is notably different because Ctrl-v is a visual editing command
  let g:ctrlsf_mapping = {
      \ "vsplit"   : "<C-O>",
      \ "split"    : "",
      \ "tab"      : "<C-T>",
      \ }

  " This makes the preview window show up in the search window.  Just trying
  " this out
  let g:ctrlsf_preview_position = 'inside'

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'

  nnoremap <c-p> :Files<CR>

  " Make ripgrep the default command
  command! -bang -nargs=* Rg
    \ call fzf#vim#grep(
    \   'rg --no-ignore --column --line-number --no-heading --color=always --smart-case '.shellescape(<q-args>), 1,
    \   <bang>0 ? fzf#vim#with_preview('up:60%')
    \           : fzf#vim#with_preview('right:50%:hidden', '?'),
    \   <bang>0)

  " Have to declare all actions to override some actions
  let g:fzf_action = {
      \ 'ctrl-t': 'tab split',
      \ 'ctrl-i': 'split',
      \ 'ctrl-v': 'vsplit'
      \ }

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'ryanoasis/vim-devicons'

  let g:webdevicons_enable=1
  let g:webdevicons_enable_nerdtree = 1
  let g:webdevicons_enable_airline_statusline = 1
  set encoding=utf8

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'itchyny/lightline.vim'

  let g:lightline = {
    \ 'colorscheme': 'wombat',
    \ 'active': {
    \   'left': [ [ 'mode', 'paste' ],
    \             [ 'cocstatus', 'readonly', 'relativepath', 'modified' ] ]
    \ },
    \ 'component_function': {
    \   'cocstatus': 'coc#status'
    \ },
  \ }
  set noshowmode    " Remove the normal status line

  " Use auocmd to force lightline update.
  augroup lightline-coc
    autocmd!
    autocmd User CocStatusChange,CocDiagnosticChange call lightline#update()
  augroup END

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" JAVASCRIPT
Plug 'pangloss/vim-javascript'

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'mxw/vim-jsx'

  let g:jsx_ext_required = 0

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" TYPESCRIPT
Plug 'leafgarland/typescript-vim'

" RUBY
Plug 'tpope/vim-endwise'

" PYTHON
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'hdima/python-syntax'

  let g:python_highlight_all = 1
  let g:python_version_2 = 1

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" MARKDOWN
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Plug 'suan/vim-instant-markdown'

  let g:vim_markdown_follow_anchor = 1

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" REGO
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'tsandall/vim-rego'

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Plug 'neoclide/coc.nvim', {'branch': 'release' }

  execute "source" VIM_CONFIG_DIR . "/cocnvim.vim"

Plug 'liuchengxu/vista.vim'

  let g:vista_default_executive = 'coc'
  " let g:vista_sidebar_width = '50'
  let g:vista_sidebar_open_cmd = '50vsplit' "Opens vista in the tab that's focused when I open it
  let g:vista_fzf_preview = ['right:50%']
  " let g:vista_echo_cursor_strategy = 'floating_win' Can't figure out what this does
  let g:vista_close_on_jump = 1
  let g:vista_close_on_fzf_select = 1
  let g:vista_update_on_text_changed = 1

  nmap <silent> <leader>o  :<C-u>Vista!!<cr>


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" YAML
Plug 'chase/vim-ansible-yaml'

" GOLANG
Plug 'sebdah/vim-delve'
" One higher than git-gutter's default of 10
let g:delve_sign_priority=11

" Only set delve test mapping for golang files
" How-to link: https://vi.stackexchange.com/a/10666
autocmd FileType go nnoremap <buffer> <silent> <leader>t  :DlvTest<cr>

" END PLUGIN DECLARATIONS
call plug#end()

colorscheme onedark

if has('nvim-0.5')

lua <<EOF
require'nvim-treesitter.configs'.setup {
  ensure_installed = "maintained",
  highlight = {
    enable = true,
  },
}
EOF

  set foldmethod=expr
  set foldexpr=nvim_treesitter#foldexpr()

endif

" https://sunaku.github.io/vim-256color-bce.html
if &term =~ '256color'
  " disable Background Color Erase (BCE) so that color schemes
  " render properly when inside 256-color tmux and GNU screen.
  " see also http://snk.tuxfamily.org/log/vim-256color-bce.html
  set t_ut=
endif


" ----------- GOOGLE CONFIG -----------
if filereadable("/usr/local/google/home/juliankatz/.config/nvim/google-specific.vim")
  source /usr/local/google/home/juliankatz/.config/nvim/google-specific.vim
endif

" Vimscript exercises
if filereadable("/Users/juliankatz/dev/vimscript-the-hard-way/exercises.vim")
  source /Users/juliankatz/dev/vimscript-the-hard-way/exercises.vim
endif

" A fix for nerdtree devicons having brackets after vimrc source
if exists("g:loaded_webdevicons")
  call webdevicons#refresh()
endif
