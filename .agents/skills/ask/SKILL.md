---
name: ask
version: 1.0.0
description: "Short answer mode: Answer questions briefly in short form, do not perform any side effect actions (read actions are always permitted)."
---

# Short Answer Mode (v1)

## Core Rules (MUST follow strictly when this skill is invoked):
1. **Answer format**: Always provide concise, short-form answers (direct to the point, no extra elaboration unless explicitly requested by user).
2. **Action restrictions**: NEVER perform side effect actions: No file edits/writes, no bash commands that modify the system/files, no API calls that change state, no commit/PR operations, no creation of new resources.
3. **Permitted actions**: Read actions are always allowed: You can read files, query documentation, check git status, and fetch any read-only information needed to answer the user's question.
