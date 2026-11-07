# PR #10 Resolve refs inside allOf, anyOf, oneOf and items arrays against their $id (fixes issue #4)

Step 5 of 8. Branch `fix/walk-schema-arrays`, head `35ae4a3`, base #16's branch. Status: ready for review.

## Issue #4

Real, and the analysis is correct. On master `4999d6b`, `walk` descends only into object values, so a `$ref` inside `allOf`, `anyOf`, `oneOf` or an array-form `items` ignores the `$id` of its subschema, and an `$id` there isn't registered. Draft-07 Core §8.2 and draft-04 `id` apply to subschemas inside arrays too. The issue's warning that a keyword check alone would also descend into arrays inside `const`/`default` is right; #9's `subschemas()` handles it.

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | All issue cases; 18 official-suite cases now pass, all of draft6/draft7 `ref.json`. |
| 2 | Completeness | ✅ | |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | Booleans and non-objects in arrays are skipped. |
| 5 | Reliability | ✅ | Thanks to #16, a shared array behaves the same on every compile. |
| 6 | Security | ✅ | |
| 7 | Performance | ✅ | |
| 8 | Maintainability | ✅ | |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Five array shapes × two drafts × both modes; booleans; shared array; array under unknown keyword; `items` in `default`. |
| 12 | Compatibility | ✅ | |
| 13 | Architecture | ✅ | |
| 14 | Integration | ✅ | Needs #9 and #16. |
| 15 | Data integrity | ✅ | Arrays in data keywords stay untouched; the schema stays unchanged (#16). |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | |
| 20 | Regression | ⚠️ Minor | Documented: in draft-06 and later, an `id` annotation inside an array item now changes the base URI below it, as it already does at object positions on master. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 shared array fragment broken on a second compile (Medium) | Fixed by #16 before this PR; test fails on this PR as first written. |
| F2 `id` treated as identifier in draft-06+ arrays | Documented under Limitations (pre-existing behaviour reaching further). |
| F3 test gaps | Fixed. |
| F4 `SCHEMA_ARRAYS` comment | Fixed. |

## Remaining

- The `id` limitation (row 20); a draft-aware `id`/`$id` rule would be a separate change.
