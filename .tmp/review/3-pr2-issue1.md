# PR #2 Resolve local refs inside a subschema with a urn: $id (fixes issue #1)

Step 3 of 8. Branch `fix/urn-id-local-refs`, head `77b3985`, base #9's branch. Status: ready for review.

## Issue #1

Real, and the analysis is correct. On master `4999d6b`, a `#…` ref inside a subschema whose `$id` has a scheme outside `urllib.parse.uses_relative` (`urn:`, `tag:` and others) resolves against the root schema, because `urljoin` returns a fragment-only reference unchanged for such a base. Draft-07 Core §8.2/§8.3.2 and RFC 3986 §5.2.2 resolve it against the subschema's base URI for every scheme. Schemas without `$id` and with `http:` `$id`s are unaffected.

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | urn:, tag:, s3:, uppercase scheme, `$id` with fragment, draft-04 `id`, plain names, handler-loaded documents. |
| 2 | Completeness | ✅ | All four `urljoin` call sites use `join_uri`. |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | |
| 5 | Reliability | ✅ | `base.partition('#')` gives the same result on every Python version. |
| 6 | Security | ✅ | |
| 7 | Performance | ✅ | |
| 8 | Maintainability | ✅ | |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Several schemes and `$id` forms, both modes; generated function names pinned. |
| 12 | Compatibility | ⚠️ Minor | Documented breaking changes: a `#…` ref whose target exists only in the root now raises `JsonSchemaDefinitionException`; function names for `#` refs under a root urn `$id` change. |
| 13 | Architecture | ✅ | Fix in fastjsonschema, not in the global `uses_relative`. |
| 14 | Integration | ✅ | Needs #8 and #9 (guard tests prove it). |
| 15 | Data integrity | ✅ | |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | |
| 20 | Regression | ✅ | `http:`, `file:` and schemas without `$id` unchanged; suite outcomes unchanged. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 `urldefrag` output depends on Python version and base | Fixed: `base.partition('#')`. |
| F2 test gaps (other schemes, uppercase, fragment, draft-04, function names) | Fixed: tests, all failing on master. |
| F3 `Assisted-by` mismatch | Fixed. |

## Remaining

- Python 3.10 to 3.13 ran in CI without the official suite only.
