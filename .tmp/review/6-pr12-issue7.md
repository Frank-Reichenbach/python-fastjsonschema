# PR #12 Resolve each URI once under a relative $id with a directory (fixes issue #7)

Step 6 of 8. Branch `fix/relative-id-resolved-once`, head `a1e7dc3`, base #10's branch. Status: ready for review.

## Issue #7

Real, and the analysis is correct. On master `4999d6b`, a relative `$id` with a directory, such as `schemas/item.json`, is applied more than once, so refs below it resolve to `schemas/schemas/item.json`; a subschema with such an `$id` that refers to itself makes `compile()` hang (also by file name, `"$ref": "node.json"`). Each of the four double-resolution points named in the issue was confirmed by mutation testing. Draft-07 Core §8.2 allows a relative `$id`.

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | All issue cases, including both hangs and `file:` ids. |
| 2 | Completeness | ✅ | A second `compile()` of the same schema works too (needs #16). |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | No more non-terminating compiles. |
| 5 | Reliability | ✅ | |
| 6 | Security | ✅ | |
| 7 | Performance | ✅ | |
| 8 | Maintainability | ✅ | |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Every change is caught by a test, including entering the document URI with `resolved=True`. |
| 12 | Compatibility | ✅ | `RefResolver` gains keyword-only `base_uri_is_id`; `walk` gains keyword-only `id_applied`, so positional calls keep their meaning. |
| 13 | Architecture | ✅ | Uses #16's table to know which refs `walk` resolved. |
| 14 | Integration | ✅ | |
| 15 | Data integrity | ✅ | |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | |
| 20 | Regression | ✅ | Documented behaviour change: a nested `$id` is no longer registered a second time under a wrong URI. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 `in_scope(document_uri, resolved=True)` untested | Fixed: test (fails on the mutant). |
| F2 test wrote into the shared default `store` | Fixed. |
| F3 test gaps (both modes, self-reference by file name) | Fixed. |
| F4 second compile under a relative `$id` fails | Fixed by #16; test. |
| `walk()` third positional parameter (from #11's review) | Fixed: `id_applied` keyword-only. |

## Remaining

- Nothing specific.
