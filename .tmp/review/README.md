# Review of the `$ref`/`$id` resolver fix stack

State of 2026-11-03, after the review and the rework. Fork: `Frank-Reichenbach/python-fastjsonschema`. Base: upstream master `4999d6b` (2.22.3).

Every PR was reviewed against the 20-point checklist (correctness, completeness, consistency, robustness, reliability, security, performance, maintainability, readability, testability, test coverage, compatibility, architecture, integration, data integrity, usability, accessibility, observability, documentation, regression). The per-PR files hold the current checklist, the findings with their outcome, and what remains open. The reviews of the first versions and their evidence for since-fixed findings were removed; the outcomes are kept.

## Stack

Merge in this order, with merge commits (see `../merge-order.md`):

| Step | PR | Fixes | Branch | Head | File |
|---|---|---|---|---|---|
| 1 | #8 Use one validation function name per URI | #3 | fix/unique-validation-function-names | 2ee7fbb | `1-pr8-issue3.md` |
| 2 | #9 Treat the values of const, enum, default and examples as data | #6 | fix/data-keyword-values | a467003 | `2-pr9-issue6.md` |
| 3 | #2 Resolve local refs inside a subschema with a urn: $id | #1 | fix/urn-id-local-refs | 77b3985 | `3-pr2-issue1.md` |
| 4 | #16 Leave the $ref values of the schema unchanged | #15 | fix/keep-schema-unchanged | c4840e2 | `4-pr16-issue15.md` |
| 5 | #10 Resolve refs inside allOf, anyOf, oneOf and items arrays against their $id | #4 | fix/walk-schema-arrays | 35ae4a3 | `5-pr10-issue4.md` |
| 6 | #12 Resolve each URI once under a relative $id with a directory | #7 | fix/relative-id-resolved-once | a1e7dc3 | `6-pr12-issue7.md` |
| 7 | #11 Walk schemas loaded through handlers like the main schema | #5 | fix/handler-schema-nested-id | 5fd4ad5 | `7-pr11-issue5.md` |
| 8 | #14 Register $id and resolve refs in definitions next to a $ref | #13 | fix/ref-sibling-definitions | 2375eb3 | `8-pr14-issue13.md` |

Each PR is one commit and targets the branch of the PR before it. #16 and its issue #15 were added in the rework: the root cause of the most serious findings in #10, #11 and #12 was that `compile()` rewrote the `$ref` values of the caller's schema, a bug that master and 2.21.2 have as well.

## Status

All seven original issues reproduce on master `4999d6b`, and the stack fixes them. All findings of the review are fixed or documented as a decision or limitation in the PR descriptions; each PR description has a "Changes after review" section. Two Codex reviews (GPT-6.1 Terra, high effort) of the reworked stack followed; their findings were fixed or, for one pre-existing case, documented. No further Codex pass ran after those fixes.

## Verification

- Full suite, including the official JSON-Schema-Test-Suite, on every commit (macOS, Python 3.14.10, bytecode caching off):

  | | master | #8 | #9 | #2 | #16 | #10 | #12 | #11 | #14 |
  |---|---|---|---|---|---|---|---|---|---|
  | passed | 4758 | 4776 | 4814 | 4841 | 4847 | 5024 | 5042 | 5062 | 5123 |
  | xfailed | 415 | 415 | 411 | 411 | 411 | 393 | 393 | 393 | 382 |
  | xpassed | 970 | 970 | 954 | 954 | 954 | 824 | 824 | 824 | 835 |

  No official-suite outcome gets worse at any step.
- CI: one run of the `tests` workflow on `fix/ref-sibling-definitions` (all eight commits), Python 3.10 to 3.14 on Linux, macOS and Windows: all 15 jobs passed ([run 41617614937](https://github.com/Frank-Reichenbach/python-fastjsonschema/actions/runs/41617614937)). CI on the fork is off by the owner's decision; this single manual run was made without knowing that. CI doesn't check out the official suite.
- pylint: no message that master doesn't have, on every commit.
- Benchmarks (`tests/benchmarks`): no `min` regression above 5% against master. Compile time of 8000 definitions: 0.64 s (master 0.61 s).
- `compile_to_code()` for all 1204 official-suite schemas, stack vs. master: 51 differ, all in `ref.json`, `refRemote.json`, `optional/id.json`, `anchor.json` and the two `unevaluated*` files. They are the cases the stack fixes, plus `definition=` values of errors that now show `$ref`s as written (#16).

## Open points

- **Upstream PR horejsek/python-fastjsonschema#224** (another contributor) fixes the same function-name collision as #8, in `get_scope_name()`. Whichever is merged second has to be adapted. #8's description mentions it.
- **Pre-existing, outside the stack:**
  - One Python object used at two places of one schema under two different `$id`s resolves against the first in both places (#16 Limitations). A fix needs the code generator to track `$id` scopes.
  - `?#…` refs inside `anyOf`, `not` and similar raise a raw `ValueError` at compile time (`_expand_refs`).
  - A used `$ref` that isn't a valid URI raises a raw `ValueError` instead of `JsonSchemaDefinitionException`.
  - `walk` honours `id` in every draft, also in draft-06 and later where it is an unknown keyword (#10 Limitations).
- **Not covered:** the official suite on Python 3.10 to 3.13 and on Linux/Windows (CI ran the other tests only).
