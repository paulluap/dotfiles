---
description: "global rule"
alwaysApply: true
---

## General Guidelines

* Do not perform git commits automatically; leave commit operations to the user.
* When making technical decisions, do not give much weight to development cost. 
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability. (since you are an AI with no time boundry).
* When writing tests, real implementation should be preferred over a test double. (Book: Software Engineering at Google)

## Dev tool guide

* Python: Always use `uv` to manage Python environments and run Python commands
* Java: SDKMAN is pre-installed; use it to get the correct jdk version
* cousier: more effecient than maven, use this to quickly find maven denpendencies, show dependency trees or run tools in maven repository 
    * `cs resolve -t com.google.guava:guava:33.6.0-jre`: show the dependency tree for the guava 33 library
* tmux: when the user refers to a tmux pane x, 
    * Prefer tmux operations to accomplish the work
        * `tmux capture-pane -t x` : capture what's in pane x, (use the `-S -n` option to capture last n lines of scrolled-out content
        * `tmux send-keys -t x "..." Enter`: execute the cmd in pane x
    * In this case, we are already in the tmux session, so `-t x` is enough to refer to pane x
    * When to apply: when the user explicitly refers to a tmux pane (otherwise never touch any tmux session)
* Herdr: when the user refers to a Herdr pane x,
    * Prefer Herdr operations to accomplish the work
        * `herdr pane read x --source recent-unwrapped --lines 120`: capture recent output from pane x
        * `herdr pane run x "..."`: execute a command in pane x
        * `herdr pane send-keys "..."`: send key presses to a pane 
    * Identify the current pane with `herdr pane current --current` or `$HERDR_PANE_ID`; list panes with `herdr pane list --workspace "$HERDR_WORKSPACE_ID"`
    * When to apply: only when the user explicitly refers to a Herdr pane (otherwise never inspect or control any Herdr session)

## Search guide

* use context7 to search for dev related doc
* you may want to use github.com to explore the sourcefile as the source of truth
* if access to some web content is resitricuted (github, google), try proxychains
    * example: `proxychains -q  curl -L https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/README.md` 
