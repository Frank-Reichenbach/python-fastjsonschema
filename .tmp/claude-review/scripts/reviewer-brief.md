# Review brief (shared by all per-PR reviewers)

Repo: /Users/frankreichenbach/Development/private/python-fastjsonschema (fastjsonschema: generates Python source for JSON Schema validators). Read its CLAUDE.md first (architecture, test conventions, CHANGELOG rule, security rule about escaping schema values in generated code).

Fork: Frank-Reichenbach/python-fastjsonschema. Eight stacked resolver-fix PRs, merged in order #8 -> #9 -> #2 -> #16 -> #10 -> #12 -> #11 -> #14. Each PR branch = parent branch + exactly ONE commit; review only that commit (`git show <branch>` / `git diff <parent>..<branch>`), but judge it in the context of the parent (code that already exists below it is not this PR's finding unless this PR makes it worse or relies on it wrongly).

  PR  issue  branch (origin/fix/...)            parent
  #8   #3    unique-validation-function-names   master
  #9   #6    data-keyword-values                fix/unique-validation-function-names
  #2   #1    urn-id-local-refs                  fix/data-keyword-values
  #16  #15   keep-schema-unchanged              fix/urn-id-local-refs
  #10  #4    walk-schema-arrays                 fix/keep-schema-unchanged
  #12  #7    relative-id-resolved-once          fix/walk-schema-arrays
  #11  #5    handler-schema-nested-id           fix/relative-id-resolved-once
  #14  #13   ref-sibling-definitions            fix/handler-schema-nested-id

Already downloaded (read these, don't re-fetch): /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/gh/issue-<N>.md, /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/gh/pr-<N>.md (body, commits, comments), /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/gh/pr-<N>.diff (diff vs. its base branch).
Prepared worktrees (detached, JSON-Schema-Test-Suite symlinked in): /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/wt-<branch-suffix> for every branch, plus /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/wt-master. DO NOT modify the main checkout or other worktrees' HEADs; you may create throwaway scripts in /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/<your-pr>/ only. Don't push, comment on GitHub, or edit PRs.
Shared venv (no package installed; use PYTHONPATH): run tests with
  cd /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/wt-<branch> && PYTHONPATH=$PWD /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/venv/bin/python -m pytest -q -W default --benchmark-skip -p no:cacheprovider [path] [-k ...]
Lint: PYTHONPATH=$PWD /private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/venv/bin/python -m pylint fastjsonschema
Baseline already verified: full suite passes on master and on the stack tip.

What to do:
1. Understand the issue: are its claims, repro and spec citations correct? Reproduce on the parent branch (and master) and confirm the fix on the PR branch.
2. Review the PR's own commit against the 20-item checklist below. Actively try to break it: write adversarial schemas (nested $id, relative/urn/http ids, $ref siblings, boolean schemas, arrays, fast_fail=False, compile_to_code output, cache=False, handlers, recursion, weird URIs, keys with braces/quotes) and compare against the parent branch and, where useful, against `jsonschema` (installed in the venv) as an oracle. Check that tests fail on the parent and pass on the branch (claimed "fails on master" tests). Check xfail-list removals in tests/json_schema/ match newly passing suite cases and that no newly passing case was left xfailed (XPASS) when the PR claims to fix it. Check performance claims if any (quick timing is fine). Check the CHANGELOG line and docs/docstrings accuracy. Check claims in the PR body (e.g. "same code as master for N schemas") at least by spot check.
3. Only report findings you verified (give the repro script/output) or clearly mark as "unverified/opinion". Severity: blocker / major / minor / nit. No padding: if a checklist item is fine, say "OK" with one-line evidence; "N/A" where not applicable (e.g. Accessibility is mostly N/A for a library — note error-message clarity instead if relevant).

Checklist: 1 Correctness, 2 Completeness, 3 Consistency, 4 Robustness, 5 Reliability, 6 Security, 7 Performance, 8 Maintainability, 9 Readability, 10 Testability, 11 Test coverage, 12 Compatibility, 13 Architecture, 14 Integration, 15 Data integrity, 16 Usability, 17 Accessibility, 18 Observability, 19 Documentation, 20 Regression.

Output: write your report as Markdown to
  /Users/frankreichenbach/Development/private/python-fastjsonschema/.tmp/claude-review/pr-<PR>-issue-<ISSUE>.md
Structure:
  # PR #<n> / Issue #<m>: <title>
  ## Verdict  (approve / approve with nits / request changes, one paragraph)
  ## Issue review  (accuracy of the issue report)
  ## Findings  (numbered, each: severity, checklist area(s), file:line, description, repro + observed output, suggested fix)
  ## Checklist  (table: # | Area | Result (OK/Finding n/N/A) | Note)
  ## Verification log  (commands run and key results: tests on parent vs branch, lint)
Then reply with a 5-10 line summary (verdict + findings titles with severity). Keep the reply short; details belong in the file.
