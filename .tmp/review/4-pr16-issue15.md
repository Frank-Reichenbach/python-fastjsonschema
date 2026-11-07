# PR #16 Leave the $ref values of the schema unchanged (fixes issue #15)

Step 4 of 8. Branch `fix/keep-schema-unchanged`, head `c4840e2`, base #2's branch. Added in the rework. Status: ready for review.

## Issue #15

Real, reproduced on master `4999d6b` and on 2.21.2. `RefResolver.walk` writes the resolved URI of every `$ref` back into the caller's schema, and the generator reads it from there. So an object shared by two schemas with different `$id`s keeps the base URI of the first, a schema compiled again after its `$id` changed loads the old URI through a handler or the network, and a ref under a relative base is resolved again on every compile (`schemas/schemas/…`). This in-place rewrite was the root cause of the most serious findings of the first review: #11 F1 (High), #10 F1 (Medium), #12 F4.

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | Shared objects, recompiling after an `$id` change, `compile_to_code` all leave the schema unchanged and resolve correctly. |
| 2 | Completeness | ⚠️ Minor | Documented: one object used twice inside one schema under two `$id`s still resolves against the first (as on master; needs the generator to track `$id` scopes). |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | The table holds the objects, so `id()` keys can't be reused while the resolver exists. |
| 5 | Reliability | ✅ | `compile()` no longer depends on earlier compiles of the same objects. |
| 6 | Security | ✅ | No unexpected downloads of URIs left over from an earlier compile. |
| 7 | Performance | ✅ | One dict lookup per ref. |
| 8 | Maintainability | ✅ | |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | `get_ref()` makes resolved refs inspectable. |
| 11 | Test coverage | ✅ | Unchanged schema (`compile`, `compile_to_code`), shared object, recompiling; both modes. |
| 12 | Compatibility | ⚠️ Minor | Documented: nested `$ref`s in `JsonSchemaValueException.definition` show the value as written; code relying on the rewritten schema sees the original. |
| 13 | Architecture | ✅ | #10, #12 and #11 build on the table instead of extending the rewrite. |
| 14 | Integration | ✅ | |
| 15 | Data integrity | ✅ | The point of the change. |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | |
| 20 | Regression | ✅ | Suite outcomes unchanged; generated code differs from #2 only in `definition=` values, in 12 of 1204 suite schemas. |

## Findings and outcome

| Finding | Outcome |
|---|---|
| Codex: one object at two places of one schema under two `$id`s | Pre-existing (identical on master and 2.21.2); documented under Limitations. |

## Remaining

- The limitation in row 2.
