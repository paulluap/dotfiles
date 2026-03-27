
## The Bare Repository Method

**Init**

This method treats your entire home directory as a potential workspace without Git "tracking" everything by default.

Step-by-Step Setup

1. Initialize the bare repo:

    `git init --bare $HOME/.cfg`

2. Create an alias: (Add this to your .zshrc or .bashrc)

    `alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'


3. Hide untracked files: (Crucial, so config status doesn't show your whole Downloads folder)

    `config config --local status.showUntrackedFiles no`

4. Add and push:

    ```
    config add .vimrc
    config commit -m "Add vimrc"
    config push
    ```

**clone**

```
# Create the repo as a bare clone in a hidden folder
git clone --bare git@github.com:paulluap/dotfiles.git $HOME/.cfg

# Alias git to target your home directory
alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'

# Configure git to not show untracked files in the home directory
config config --local status.showUntrackedFiles no

# Checkout your files
config checkout
```

**Updating Submodules**

This repository includes a `.tmux` submodule. To update it to the latest version:

```
config submodule update --remote .tmux  #need --init option for fresh clone 
config add .tmux
config commit -m "Update .tmux submodule"
```

