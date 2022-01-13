" COC EXTENSIONS
let g:coc_global_extensions = [
  \ 'coc-markdownlint',
  \ 'coc-go',
  \ 'coc-diagnostic',
  \ 'coc-yank',
  \ 'coc-css',
  \ 'coc-tsserver',
  \ 'coc-json',
  \ 'coc-highlight',
  \ 'coc-docker',
  \]


" Switch to the test file
autocmd FileType go nmap <leader>tt :CocCommand go.test.toggle<cr>

Plug 'antoinemadec/coc-fzf', {'branch': 'release'}

" Make coc nvim 
let g:coc_fzf_preview_fullscreen=1

Plug 'neoclide/coc-yank', {'do': 'yarn install --frozen-lockfile'}
  " Key mapping for special yank list to go with this extension
nnoremap <silent> <space>y  :CocFzfList yank<cr>

" Better display for messages
set cmdheight=2

" don't give |ins-completion-menu| messages.
set shortmess+=c

set signcolumn=yes

function! s:check_back_space() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

" Autocomplete mappings:
" - TAB will trigger autocompletion options when in 

" Julian's original version
inoremap <silent><expr> <c-J>
      \ pumvisible() ? "\<C-n>" :
      \ <SID>check_back_space() ? "\<TAB>" :
      \ coc#refresh()
inoremap <silent><expr> <TAB>
      \ pumvisible() ? "\<C-n>" :
      \ <SID>check_back_space() ? "\<TAB>" :
      \ coc#refresh()
imap <expr><c-K> pumvisible() ? "\<C-p>" : "\<C-h>"

" I've tried different options for a better key for selecting a completion
" option.  But it turns out that they're all broken or slow.  The best
" option seems to be the built in C-y.

" Somehow <CR> is still working to select autocomplete at some weird times.
" Lets completely disable it

" inoremap <expr> <cr> pumvisible() ? "\<C-g>u\<CR>" : "\<C-g>u\<CR>"

" Still can't get the highlighting to work ???
Plug 'antoinemadec/FixCursorHold.nvim'
let g:cursorhold_updatetime=100

" Highlight the symbol and its references when holding the cursor.
autocmd CursorHold * silent call CocActionAsync('highlight')

" Use <c-space> to trigger completion.
inoremap <silent><expr> <c-space> coc#refresh()

" Use `[d` and `]d` to navigate diagnostics
nmap <silent> [d <Plug>(coc-diagnostic-prev)
nmap <silent> ]d <Plug>(coc-diagnostic-next)
nmap <silent> <leader>i  <Plug>(coc-diagnostic-info)

" Remap keys for gotos
nmap <silent> gd <Plug>(coc-definition)
nmap <silent> gv :vsplit<CR><Plug>(coc-definition)
nmap <silent> gnt :tab sp<CR><Plug>(coc-definition)
nmap <silent> gy <Plug>(coc-type-definition)
nmap <silent> gi <Plug>(coc-implementation)
" I switched this out for (coc-references) because this one doesn't include
" the function declaration, which is always noise for me
nmap <silent> gr <Plug>(coc-references-used)

" Remap for rename current word
nmap <leader>rn <Plug>(coc-rename)

nmap <leader>rf <Plug>(coc-refactor)

" Remap for format selected region
nmap <leader>cf  <Plug>(coc-format)
" " Show all diagnostics
nmap <silent> <leader>d  :<C-u>CocFzfList diagnostics<cr>
nmap <silent> <leader>cl  :CocFzfList<cr>
nmap <silent> <leader>cc  :CocCommand<cr>
" requires the `pynvim` to be installed on the system

nmap <silent> <leader>cs  :CocFzfList symbols<cr>

nmap <silent> [s :CocCommand document.jumpToPrevSymbol<cr>
nmap <silent> ]s :CocCommand document.jumpToNextSymbol<cr>

" Manage extensions
" nmap <silent> <leader>e  :<C-u>CocList extensions<cr>
" Show commands
" nmap <silent> <leader>c  :<C-u>CocList commands<cr>
" " Find symbol of current document

" Original cocfzflist version
" nmap <silent> <leader>col  :<C-u>CocFzfList outline<cr>
" Newer version, based on vista
nmap <silent> <leader>col  :<C-u>Vista finder fzf<cr>

" " Search workspace symbols
" nmap <silent> <leader>s  :<C-u>CocList -I symbols<cr>
" " Do default action for next item.
" nmap <silent> <leader>j  :<C-u>CocNext<CR>
" " Do default action for previous item.
" nmap <silent> <leader>k  :<C-u>CocPrev<CR>
" " Resume latest coc list
nmap <silent> <leader>cr  :<C-u>CocFzfListResume<CR>

" Applying codeAction to the selected region.
" Example: `<leader>aap` for current paragraph
" xmap <leader>a  <Plug>(coc-codeaction-selected)
" nmap <leader>a  <Plug>(coc-codeaction-selected)

" Remap keys for applying codeAction to the current buffer.
" nmap <leader>ac  <Plug>(coc-codeaction)
" Apply AutoFix to problem on the current line.
nmap <leader>qf  <Plug>(coc-fix-current)

" Use CTRL-S for selections ranges.
" Requires 'textDocument/selectionRange' support of language server.
nmap <silent> <C-s> <Plug>(coc-range-select)
xmap <silent> <C-s> <Plug>(coc-range-select)

" Map function and class text objects
" NOTE: Requires 'textDocument.documentSymbol' support from the language server.
xmap if <Plug>(coc-funcobj-i)
omap if <Plug>(coc-funcobj-i)
xmap af <Plug>(coc-funcobj-a)
omap af <Plug>(coc-funcobj-a)
xmap ic <Plug>(coc-classobj-i)
omap ic <Plug>(coc-classobj-i)
xmap ac <Plug>(coc-classobj-a)
omap ac <Plug>(coc-classobj-a)

" Set K to show documentation
" Use U to show documentation in preview window
nnoremap <silent> U :call <SID>show_documentation()<CR>
function! s:show_documentation()
  if (index(['vim','help'], &filetype) >= 0)
    execute 'h '.expand('<cword>')
  elseif (coc#rpc#ready())
    call CocActionAsync('doHover')
  else
    execute '!' . &keywordprg . " " . expand('<cword>')
  endif
endfunction

" Disable coc during easymotion jumps.  Meant to surpress the diagnostic
" output.
autocmd User EasyMotionPromptBegin silent! CocDisable
autocmd User EasyMotionPromptEnd silent! CocEnable

" Support showing signature help in insert mode by hitting Ctrl-U
autocmd User CocJumpPlaceholder call CocActionAsync('showSignatureHelp')
inoremap <silent><C-U> <esc>:call CocActionAsync('showSignatureHelp')<cr> i

" organize imports on save
autocmd BufWritePre *.go :silent call CocAction('runCommand', 'editor.action.organizeImport')
