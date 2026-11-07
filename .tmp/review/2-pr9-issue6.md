# PR #9 Treat the values of const, enum, default and examples as data (fixes issue #6)

Step 2 of 8. Branch `fix/data-keyword-values`, head `a467003`, base #8's branch. Status: ready for review.

## Issue #6

Real, and the analysis is correct. On master `4999d6b`, `walk()` descends into the values of `const` and `default` and `_expand_refs()` into those of `const`, `enum` and `examples`, so a `$ref` or `$id` there is treated as schema: `compile()` fails with `Unresolvable ref` or `ValueError`, equal data is rejected, `use_default` inserts a rewritten value, and an `$id` inside such a value replaces the real subschema. The draft-07 Validation references (§6.1.2, §6.1.3, §10.2, §10.4) hold, and the official suite's `optional/id.json` covers the `$id`-in-`const` case.

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | All issue cases, draft-04 to 2019-09, both modes, cache on/off, `compile_to_code`, handler-loaded schemas. |
| 2 | Completeness | ✅ | Both traversals (`walk`, `_expand_refs`) follow the same rules. |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | Depth limit still raises before Python's recursion limit. |
| 5 | Reliability | ✅ | |
| 6 | Security | ✅ | Data values are no longer interpreted. |
| 7 | Performance | ✅ | |
| 8 | Maintainability | ✅ | `_expand_refs` mirrors `subschemas()` in a commented loop. |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Data keywords, properties named like them, error `definition` via `_expand_refs`. |
| 12 | Compatibility | ✅ | |
| 13 | Architecture | ✅ | |
| 14 | Integration | ✅ | #2, #10, #11 and #14 build on `subschemas()`. |
| 15 | Data integrity | ✅ | `const`/`default` values stay unchanged. |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | The wrong `const` error message is gone. |
| 19 | Documentation | ✅ | |
| 20 | Regression | ⚠️ Minor | Documented: in a custom keyword map such as `x-defs`, an entry named `const`, `default`, `enum` or `examples` is now skipped as data, so an `$id` in it isn't registered. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 custom-map entries named like data keywords are skipped | Documented under Decisions: telling a custom map from a schema would need every keyword of every draft. |
| F2 `_expand_refs` map handling untested | Fixed: test (fails against a naive variant). |
| F3 `Assisted-by` mismatch | Fixed. |
| F4 dense comprehension in `_expand_refs` | Fixed: explicit loop. |

## Remaining

- The custom-map edge case (row 20).
