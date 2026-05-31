## Init

This repo is already initialized, if you are interested in how it is done:

<details> <summary> init steps</summary>
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

</details>

## Clone and Update

```bash
# Create the repo as a bare clone in a hidden folder
git clone --bare git@github.com:paulluap/dotfiles.git $HOME/.cfg

# Alias git to target your home directory
alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'

# Configure git to not show untracked files in the home directory
config config --local status.showUntrackedFiles no

# Checkout your files
config checkout
```

### Post Clone 

#### vim plug

https://github.com/junegunn/vim-plug

```bash
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
```


#### tmux config

https://github.com/gpakosz/.tmux
> Oh my tmux! My self-contained, pretty & versatile tmux configuration made with 💛🩷💙🖤❤️🤍


first time init 

```bash
config submodule --init
```

To update it to the latest version:

```
config submodule update --remote .tmux  
config add .tmux
config commit -m "Update .tmux submodule"
```


#### User-level systemd services

Custom service files live in `~/.config/systemd/user/`. These run under the user instance of systemd (no `sudo` needed).


**Enable a service** (start now + start on login):

```bash
systemctl --user enable --now <service>
```

**Disable a service**:

```bash
systemctl --user disable --now <service>
```

**Check status**:

```bash
systemctl --user status <service>
```

**View logs**:

```bash
journalctl --user -u <service> -f
```

**After adding a new .service file**, reload the daemon first:

```bash
systemctl --user daemon-reload
```






## Dev Setup

### Programming Languages

| programming language | dev sdk | script install |
|----------------------|---------|-----------------------------------------|
| java                 | [sdkman](https://sdkman.io/) | `curl -s "https://get.sdkman.io" \| bash` |
| python               | [uv](https://docs.astral.sh/uv/getting-started/installation) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| golang               | [go](https://go.dev/learn/)                                  |  |
| javascript           | [nvm](https://github.com/nvm-sh/nvm)                         | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh \| bash` |


### Tools (terminal)

| name     | website                                         | script install                                                                                                 | 
| ------   | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| docker   | https://docs.docker.com/engine/install/ubuntu/  | `curl -fsSL https://get.docker.com -o get-docker.sh`                                                           |
| jq       |                                                 | `apt install jq`                                                                                               |
| lazygit  |                                                 | `apt install lazygit`                                                                                          |
| fzf      |                                                 | `apt install fzf`                                                                                              |
| tmux     |                                                 | `apt install tmux`                                                                                             |
| yazi     | https://yazi-rs.github.io/docs/installation/    | `snap install yazi --classic`                                                                                  |
| autossh  |                                                 | `apt install autossh`                                                                                          |
| coursier | https://get-coursier.io/docs/cli-installation   | `curl -fL "https://github.com/coursier/launchers/raw/master/cs-x86_64-pc-linux.gz" \| gzip -d > cs; ./cs setup` |
| starship | https://github.com/starship/starship, https://starship.rs/presets/ | `curl -sS https://starship.rs/install.sh \| sh`                                             |
| eza      | https://github.com/eza-community/eza/blob/main/INSTALL.md |                                                                                                      |
| claude   | https://www.volcengine.com/docs/82379/1928261?lang=zh | `npm install -g @anthropic-ai/claude-code`                                                               |
| bun      | curl -fsSL https://bun.com/install | bash

