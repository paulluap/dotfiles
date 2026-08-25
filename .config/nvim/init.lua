-- reuse vim plugin
vim.cmd([[
  set runtimepath^=~/.vim runtimepath+=~/.vim/after
  let &packpath = &runtimepath
  source ~/.vimrc
]])

-- LSP
---- https://github.com/nvim-java/nvim-java
vim.pack.add({
  {
    src = 'https://github.com/JavaHello/spring-boot.nvim',
    version = '218c0c26c14d99feca778e4d13f5ec3e8b1b60f0',
  },
  'https://github.com/MunifTanjim/nui.nvim',
  'https://github.com/mfussenegger/nvim-dap',

  'https://github.com/nvim-java/nvim-java',
})

require('java').setup()
vim.lsp.enable('jdtls')

vim.lsp.config('jdtls', {
  settings = {
    java = {
      configuration = {
        runtimes = {
          {
            name = "JavaSE-21",
            path = "/home/kingstar/.sdkman/candidates/java/current",
            default = true,
          }
        }
      }
    }
  }
})

vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostic location list' })

-- LSP outline 
vim.pack.add({
    { src = 'https://github.com/simrat39/symbols-outline.nvim' }
})
require("symbols-outline").setup()
