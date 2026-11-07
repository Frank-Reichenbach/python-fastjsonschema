# PR #11 Walk schemas loaded through handlers like the main schema (fixes issue #5)

Step 7 of 8. Branch `fix/handler-schema-nested-id`, head `5fd4ad5`, base #12's branch. Status: ready for review.

## Issue #5

Real, a regression released in 2.22.3: `c9a311e` (upstream #219, the fix for #218) stopped `walk` from resolving the refs of handler-loaded schemas, so a `$ref` there ignores the `$id` of its subschema and a relative root `$id` of the loaded schema. 2.22.0 to 2.22.2 resolve it correctly; 2.21.2, 2.22.3 and master `4999d6b` don't. The issue's title and text were updated to say "released in 2.22.3". Draft-07 Core §8.2 makes no distinction between embedded and retrieved schemas.

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | The regression is fixed; objects shared between loaded documents resolve per document. |
| 2 | Completeness | ✅ | Handler results and `store` values stay unchanged (#16). |
| 3 | Consistency | ✅ | Loaded schemas are walked like the main schema. |
| 4 | Robustness | ✅ | Compiling twice with the same handler data works (upstream's #218 test pattern). |
| 5 | Reliability | ✅ | `compile()` doesn't depend on what was compiled before. |
| 6 | Security | ✅ | No downloads of URIs left over from an earlier compile. |
| 7 | Performance | ⚠️ Minor | Documented: with `cache=False`, every `$ref` into a remote document loads, copies and walks it again. |
| 8 | Maintainability | ✅ | The special case for loaded schemas is gone. |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Regression cases; compiling twice; compiling a loaded dict directly; shared objects (fail without the copy). |
| 12 | Compatibility | ⚠️ Minor | `walk` loses `rewrite_refs` (positional callers now fail loudly); handler results are deep-copied. |
| 13 | Architecture | ✅ | |
| 14 | Integration | ✅ | Needs #16, #12 and #9. |
| 15 | Data integrity | ✅ | Handler results and `store` values aren't modified. |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | CHANGELOG line for the main fix; texts say "released in 2.22.3". |
| 20 | Regression | ✅ | `c9a311e`'s own test still passes, also when run twice. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 (High) handler results rewritten in place; #218 pattern fails on the second compile | Fixed by #16; tests. |
| F2 object reachable under two document URIs | Fixed: handler results are deep-copied; tests fail without the copy. |
| F3 "isn't released yet"; no CHANGELOG line for the main fix | Fixed in PR, commit message, issue #5, CHANGELOG. |
| F4 `ValueError` CHANGELOG wording | Fixed. |
| F5 `cache=False` cost | Documented in the `RefResolver` docstring. |
| F6 `walk()` third positional parameter | Fixed in #12 (keyword-only `id_applied`). |

## Remaining

- The `cache=False` cost (row 7).
