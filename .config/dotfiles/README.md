
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
git clone --separate-git-dir=$HOME/.cfg [https://github.com/YOUR_USERNAME/dotfiles.git](https://github.com/YOUR_USERNAME/dotfiles.git) $HOME/cfg-tmp
cp -rv $HOME/cfg-tmp/. $HOME/
rm -rf $HOME/cfg-tmp
```

**Updating Submodules**

This repository includes a `.tmux` submodule. To update it to the latest version:

```
config submodule update --remote .tmux
config add .tmux
config commit -m "Update .tmux submodule"
```

Or if working directly in the dotfiles directory:

```
git submodule update --remote .tmux
git add .tmux
git commit -m "Update .tmux submodule"
```

