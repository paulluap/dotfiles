---
description: "global rule"
globs: **/*
alwaysApply: true
---

## Behavior guide

* Do not perform git commits automatically; leave commit operations to the user

## Dev tool guide

* Python: Always use `uv` to manage Python environments and run Python commands
* Java: SDKMAN is pre-installed; use it to get the correct jdk version
* cousier: this more effecient than maven, use this to quickly find maven denpendencies, show dependency trees or run tools in maven repository 
    * `cs resolve -t com.google.guava:guava:33.6.0-jre`: show the dependency tree for the guava 33 library
* tmux: when asked to see tmux pane x, you are in a tmux session, some useful commands:
    * `tmux capture-pane -t x` : capture what's in pane x, (use the `-S -n` option to capture last n lines of scrolled-out content
    * `tmux send-keys -t x "..." Enter`: execute the cmd in pane x

## Search guide

* use context7 to search for dev related doc
* you may want to use github.com to explore the sourcefile as the source of truth
* if access to some web content is resitricuted (github, google), try proxychains
    * example: `proxychains -q  curl -L https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/README.md` 

