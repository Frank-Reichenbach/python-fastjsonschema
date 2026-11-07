# PR #14 Register $id and resolve refs in definitions next to a $ref (fixes issue #13)

Step 8 of 8. Branch `fix/ref-sibling-definitions`, head `2375eb3`, base #11's branch. Status: ready for review.

## Issue #13

Real, and the analysis is correct for draft-04 to draft-07. On master `4999d6b`, `walk` doesn't descend into an object with a `$ref`, so schemas in `definitions`/`$defs` next to it lose their `$id`: refs inside them resolve against the outer base, and a `$ref` to that `$id` goes to a handler. "All other properties in a $ref object MUST be ignored" (Draft-07 Core §8.3) concerns validation; it doesn't hide schemas reachable by JSON pointer. In 2019-09, an `$id` next to a `$ref` is also the base URI of that `$ref` and of the definitions next to it; the PR handles that per draft (below).

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | Draft-04 to 07 walk the definitions in the outer scope; 2019-09 uses the sibling `$id` (only `$id`, not draft-04 `id`). |
| 2 | Completeness | ✅ | |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | |
| 5 | Reliability | ✅ | |
| 6 | Security | ✅ | Only `definitions`/`$defs` are walked next to a `$ref`, so data in other keywords can't register `$id`s. |
| 7 | Performance | ✅ | |
| 8 | Maintainability | ✅ | |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Drafts, `$id` forms, 2019-09 "order of evaluation" shape, JSON pointer into such definitions, draft detection agreeing with `_get_code_generator_class`. |
| 12 | Compatibility | ⚠️ Minor | Documented: schemas without `$schema` (2019-09) now honour an `$id` next to a `$ref`. |
| 13 | Architecture | ⚠️ Minor | The resolver repeats the draft rule of `_get_code_generator_class`; a test keeps the two in step. |
| 14 | Integration | ✅ | Needs #11, #10 and #9. |
| 15 | Data integrity | ✅ | |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | CHANGELOG lines for the fix, the 2019-09 change and the depth limit. |
| 20 | Regression | ⚠️ Minor | Documented: unused definitions next to a `$ref` nested about 500 levels deep now hit the depth limit. 11 official 2019-09 outcomes go from expected failure to pass, none the other way. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 2019-09: relative `$id` next to a `$ref` with its own `$id` registered at the wrong URI | Fixed: the resolver reads the draft. |
| F2 Limitations omitted the 2019-09 sibling `$id` | Superseded: 2019-09 now applies it; PR description rewritten. |
| F3 `[not]` test pinned 2019-09-wrong behaviour | Fixed: the test pins draft-07. |
| F4 test gaps | Fixed. |
| F5 no CHANGELOG line for the depth limit | Fixed. |
| Codex: JSON pointer into definitions next to a `$ref` with `$id` (draft-07) | Fixed by the draft-aware rule; test. |
| Codex: draft-04 `id` next to `$ref` changed the base in 2019-09 | Fixed: only `$id`; test. |
| Codex: CHANGELOG overstated draft-04 to 07 behaviour for the root | Fixed: the root `$id` is the base in every draft, as before. |

## Remaining

- In 2019-09, keywords next to a `$ref` other than the definitions (such as `if`) aren't walked; the suite cases "ref to if/then/else" stay expected failures.
- A handler-loaded document with its own `$schema` is treated with the root's draft, as the code generator treats it.
