
""" settings
"let g:solarized_termcolors=256
"colorscheme desert

syntax on               " syntax highlighting

" Show line numbers
set number
set relativenumber

set nobackup            " do not keep backup files, it's 70's style cluttering
set nowb
set noswapfile

" Search improvements
set hlsearch
set incsearch
set ignorecase

" Better splitting
set splitbelow
set splitright

" Better netrw
let g:netrw_liststyle = 3  " tree
let g:netrw_banner = 0
let g:netrw_winsize = -30
let g:netrw_browse_split = 4 "1. new horizontal, 2. new vertical, 3. new tab, 4. prev window

set expandtab           " expand tabs to spaces by default
set shiftwidth=4        " number of spaces to use for autoindenting
set tabstop=4           " a tab is four space

"set cursorline          " hightlight curent line

set t_Co=256            " iTerm2 supports 256 color mode.
set history=100         " keep 100 lines of history
if !has('nvim')
  set fillchars=vert:\    " remove vertical dashed bar
endif
 
set autoindent          " always set autoindenting on
set copyindent          " copy the previous indentation on autoindenting


set viminfo='20,\"80            " read/write a .viminfo file, don't store more
                                "    than 80 lines of registers

set visualbell                  " don't beep
set noerrorbells                " don't beep

set wildmenu                    " make tab completion for files/buffers act like bash
set wildignore=*.swp,*.bak,*.pyc,*.class

if !has('nvim')
  set re=0                " without this, open ts is slow in Vim
endif

set shortmess-=F       "required by https://github.com/scalameta/nvim-metals

autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab
autocmd FileType typescript setl sw=2 sts=2 et
autocmd FileType javascript setl sw=2 sts=2 et
autocmd FileType xml setl sw=2 sts=2 et
autocmd FileType html setl sw=2 sts=2 et

""" custom functions
function! IsGitRepo()
  let result = system('git rev-parse --is-inside-work-tree 2>/dev/null')
  return v:shell_error == 0
endfunction
let s:is_git_repo = IsGitRepo()

""" basic shortcuts
nnoremap <c-h> :bprevious<cr>
nnoremap <c-l> :bnext<cr>

" Alt-w 作为 Ctrl-w 的别名，用于分屏操作等
nnoremap <A-w> <C-w>

""" vim plug
call plug#begin()

if exists('$ENABLE_COC') && $ENABLE_COC != '0'
  " config doc: https://github.com/neoclide/coc.nvim/blob/master/data/schema.json
  Plug 'neoclide/coc.nvim', {'branch': 'release'}
  source ~/.vim/coc.vim
endif

Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
Plug 'junegunn/fzf.vim'
  let g:fzf_layout = { 'down': '40%' }
  if s:is_git_repo
    noremap <silent><nowait> <C-p>f :<C-u>GFiles<cr>
  else 
    noremap <silent><nowait> <C-p>f :<C-u>Files<cr>
  endif


Plug 'tpope/vim-surround'
Plug 'tpope/vim-repeat'
Plug 'preservim/nerdtree'
Plug 'wellle/context.vim'

call plug#end()

