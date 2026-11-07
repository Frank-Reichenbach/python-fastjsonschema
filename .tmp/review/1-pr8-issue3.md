# PR #8 Use one validation function name per URI (fixes issue #3)

Step 1 of 8. Branch `fix/unique-validation-function-names`, head `2ee7fbb`, base `master`. Status: ready for review.

## Issue #3

Real, and the analysis is correct. On master `4999d6b`, two refs whose targets differ only in case or punctuation (`#/definitions/user-id`, `#/definitions/user_id`) call the same generated function, and two spellings of one URI (`?#/definitions/ab`, `#/definitions/ab`) get two names, which raises `NameError` during validation. Cause: `get_scope_name()` maps different URIs to one name, and `generate_ref` keyed functions by the normalized URI but named them from the unnormalized one. The issue misses one consequence of the same cause: a referenced schema can take the root's name, and `compile()` then returns the validator of the referenced schema instead of the whole schema (reproduced on master with `#/-`, and with a root `$id` `http://x/a-b.json` next to a handler-loaded `http://x/a_b.json`).

## Checklist

| # | Area | Verdict | Notes |
|---|---|---|---|
| 1 | Correctness | ✅ | All issue cases fixed in both `fast_fail` modes, also the root collision. |
| 2 | Completeness | ✅ | Both call sites use the new name map. |
| 3 | Consistency | ✅ | |
| 4 | Robustness | ✅ | Names are always valid identifiers. |
| 5 | Reliability | ✅ | Names are deterministic across runs and hash seeds. |
| 6 | Security | ✅ | Names are sanitized as before. |
| 7 | Performance | ✅ | Taken names in a set: 8000 definitions compile in 0.66 s (master 0.61 s). |
| 8 | Maintainability | ✅ | `compile()` finds the root through "the root is named first"; a test guards it. |
| 9 | Readability | ✅ | |
| 10 | Testability | ✅ | |
| 11 | Test coverage | ✅ | Collisions by case, `-`/`_`, `/`, non-ASCII, trailing `_`; `$id`s; normalization; root collision; both modes. |
| 12 | Compatibility | ✅ | Function names change only for colliding URIs; official-suite code unchanged. |
| 13 | Architecture | ✅ | The generator owns the names of the functions it defines. |
| 14 | Integration | ⚠️ Minor | Upstream PR horejsek#224 fixes the same collision in `get_scope_name()`; whichever merges second must be adapted. |
| 15 | Data integrity | ✅ | |
| 16 | Usability | ✅ | |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | ✅ | |
| 19 | Documentation | ✅ | CHANGELOG mentions the root case; comment and commit message explain the trailing `_` correctly. |
| 20 | Regression | ✅ | |

## Findings and outcome

| Finding | Outcome |
|---|---|
| F1 naming quadratic (1.30 s for 8000 definitions) | Fixed: set of taken names. |
| F2 root replacement fixed but untested | Fixed: test (local and handler case, both modes); CHANGELOG. |
| F3 `$id` and normalization tests only with `fast_fail=True` | Fixed. |
| F4 reason for the trailing `_` imprecise | Fixed in comment, commit message and PR description. |
| F5 accessor for the root function name | Not done: the new root test guards the invariant. |
| `Assisted-by` mismatch (Sol vs. Terra) | Fixed. |

## Remaining

- Coordination with upstream #224 (see row 14).
