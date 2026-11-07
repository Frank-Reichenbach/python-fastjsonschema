# Brief: rewrite one fastjsonschema issue in shorter form

Context: repository /Users/frankreichenbach/Development/private/python-fastjsonschema (fastjsonschema, which generates Python validators from JSON Schema). Read its CLAUDE.md. Issues and PRs live on the fork Frank-Reichenbach/python-fastjsonschema. A chain of 8 resolver PRs is being replaced by a simpler set. Each issue is rewritten **shorter, with the same information**, and filed as a new issue. You write ONE issue body to a file. You do NOT create anything on GitHub and do not modify any repository or worktree.

Inputs:
- Old issue (title + body): `SCRATCH/gh/issue-<OLD>.md`
- The fix that will reference this issue: branch `<BRANCH>`, worktree `SCRATCH/impl/ro-<SUFFIX>` (read-only, detached). Read its commit: `git -C SCRATCH/impl/ro-<SUFFIX> show HEAD` (code, CHANGELOG lines, tests).
- Current master (fastjsonschema 2.22.3 + one later fix): worktree `SCRATCH/impl/master-ro`. Run Python against it with `PYTHONPATH=SCRATCH/impl/master-ro SCRATCH/venv/bin/python your_script.py`, and against the fix with `PYTHONPATH=SCRATCH/impl/ro-<SUFFIX> …`. Put scripts in `SCRATCH/impl/issue-<OLD>/` only. `jsonschema` 4.26 is installed in the venv (use it as reference only where the old issue does).
- SCRATCH = /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad

Rules for the new body (Markdown):
1. Keep the old issue's section order and headings (Summary, Reproduction, Actual result, Expected behavior and why, Cause, Workaround, Environment), but:
   - **Drop the "Possible fix" section entirely**: the PR proposes the fix. Don't mention PR numbers.
   - **Replace the `<details>` "Further cases" script + output** with a compact Markdown table: case | actual on master | expected. Keep every case that the old issue listed, unless the PR moved that case out of scope (see notes below).
   - Keep the minimal reproduction script, but re-run it on current master and paste the **real current output**. Label versions correctly: master is 2.22.3 plus one unrelated fix; say "2.22.3 and master" where both behave the same (check `git -C SCRATCH/impl/wt-v2.22.3 log -1` exists for 2.22.3 at SCRATCH/impl/wt-v2.22.3; 2.22.2 at SCRATCH/impl/wt-v2.22.2). Remove claims about versions you didn't check, or check them.
   - Keep spec citations and the cause analysis with line links, but trim wording. Line links may keep pointing to release 2.22.2 (`b88fa37`) as the old issue does; if you keep them, verify the lines still say what you claim (the code at those lines in 2.22.2).
   - Environment: one line (fastjsonschema versions checked, CPython 3.14 on macOS).
   - Last line: `Found and analyzed with AI assistance (Claude Code and Codex).` (the old issues have it; keep it).
2. Target length: at most ~55% of the old body's characters, never longer. Plain, precise English; no marketing; no "Note that".
3. Every claim must be true for the current code. If the old issue says something that is no longer accurate (stale design notes, "Limitation" paragraphs about designs that changed, version labels), fix or drop it.
4. Use the notes for your issue below; they reflect decisions already made.

Output: write `SCRATCH/impl/new-issues/issue-from-<OLD>.md` with the first line `TITLE: <title>` (keep the old title unless it is now inaccurate), then a blank line, then the body. Then reply with: title, old length → new length (characters), and any claim you dropped or corrected and why (max 10 lines).
