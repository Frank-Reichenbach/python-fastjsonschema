# PR #2 / Issue #1: Resolve local refs inside a subschema with a urn: $id

Branch `origin/fix/urn-id-local-refs` (commit `77b3985`), parent `fix/data-keyword-values` (`a467003`). The review covers only `git diff a467003..77b3985`: `CHANGELOG.txt`, `fastjsonschema/ref_resolver.py` (+19/-4) and `tests/test_integration.py` (+147).

## Verdict

**Approve with nits.** The fix is small and correct, and it goes no further than the bug. `join_uri` takes the new path only for a `#...` ref against a base whose scheme is not in `uses_relative`. Everything else still goes through `urljoin`, so output for `http`/`https`/`file`/no-id schemas is unchanged. I checked this by comparing generated function names and the full official-suite outcomes, which are identical per case.

I ran 58 adversarial cases in both `fast_fail` modes (the 2 handler cases with `fast_fail` on only), 114 runs in total (about 20 schemes including `urn:`, `urn:uuid:`, `tag:`, `mailto:`, `data:`, `s3://`, custom `myapp:` and `myapp://`, an uppercase `URN:`, query, empty fragment and quotes/braces in the id; nested urn-in-urn; plain names; boolean targets; `$defs`; escaped pointers; handlers). On the branch every run agrees with `jsonschema` except 4 (2 cases × 2 modes), and in those both libraries reject the schema. On the parent, 58 runs disagree.

The approach matches what `referencing` (jsonschema's resolver) does: it treats a ref starting with `#` as base plus fragment and uses `urljoin` for everything else. The new `JsonSchemaDefinitionException` is required by the spec, is documented in the CHANGELOG, and fails loudly instead of validating wrongly. Its message, though, is confusing for exactly the users it will hit (Finding 1). The remaining findings are about test coverage and follow-ups.

## Issue review

The issue is accurate. Everything I checked was reproduced:

- **Main repro** (master 2.22.3 and parent): `{'p': {'all': [{'eq': [1, 2, 3]}]}} -> valid`. On the branch it gives `data.p.all[0].eq must contain less than or equal to 2 items`, as the issue expects.
- **"Further cases" script**: master's output matches the issue's listed output byte for byte (`diff` is empty). On the branch every row has the expected value, including both orders of case 4.
- **Root `additionalProperties: false` variant**: master rejects the valid value with `data.p.all[0] must not contain {'eq'} properties`, as claimed.
- **Generated code on master**: it calls `validate(data__all_item, ...)` inside `validate_urn_example_node`, as quoted.
- **`urljoin` behaviour**: `urljoin("urn:example:node", "#") == '#'` and `urljoin("urn:example:node", "#/definitions/x") == '#/definitions/x'` on both 3.9.6 and 3.14.10. On 3.14 `urljoin("http://example.com/node.json", "#")` gives `'http://example.com/node.json#'` (on 3.9 the `#` is dropped).
- **Line references**: the four line numbers at `b88fa37` (v2.22.2) are correct (121, 133, 153, 194).
- **Official suite**: draft6/7 URN tests put the `urn:` `$id` on the root and are XPASS. The draft2019 "URN ref with nested pointer ref" case is XFAIL on both parent and branch. `ref.json` is file-level ignored in draft6, draft7 and draft2019.
- **Spec citations**: the RFC 3986 §5.2.2 reading is correct. For a fragment-only reference, path and query are kept and only the fragment is replaced, which is what `base.partition('#')[0] + ref` does (for example `urn:example:node?=q` + `#x` gives `urn:example:node?=q#x`).

Not verified: the 2.21.2 behaviour (no old release installed), and the claim that `python/cpython#63028` is still open (no network fetch).

## Findings

### 1. Minor: the new compile error doesn't say which ref failed or against what base
**Areas:** 16 Usability, 18 Observability, 12 Compatibility. **Location:** `fastjsonschema/ref_resolver.py:51` (message in `resolve_path`, pre-existing), reached newly through `ref_resolver.py:185` and `:89`.

Schemas that compiled before (a `#/definitions/x` inside a `urn:` subschema that only the root defines) now fail with:

```
$ python workaround.py      # parent vs branch
## wt-data-keyword-values
ref to root-only def compiles
## wt-urn-id-local-refs
ref to root-only def -> JsonSchemaDefinitionException: 'Unresolvable ref: definitions'
```

The user's root does contain `definitions`, so the message points them the wrong way. It names neither the ref (`#/definitions/x`) nor the base it was resolved against (`urn:ex:item`).

The change itself is justified. `jsonschema` also refuses this schema (`_WrappedReferencingError` / Unresolvable), and it is the same result as with an `http` `$id`.

If the root has no `$id`, a `urn:`-ided subschema can no longer reach the root's definitions at all. The only way, which I verified, is to give the root an `$id` and write the ref as absolute: `'$id': 'urn:ex:root'` on the root plus `'$ref': 'urn:ex:root#/definitions/x'` validates correctly on the branch.

**Suggested fix (cheap):**
- Mention this workaround in the CHANGELOG "Changed ..." line (or in the PR's breaking-changes text).
- Optionally, in `resolving`, catch the `JsonSchemaDefinitionException` from `resolve_path` and re-raise it with the resolved URI, e.g. `Unresolvable ref: urn:ex:item#/definitions/x`. Note that this rewords an existing message, so it may be better as a separate follow-up.

### 2. Nit: some covered behaviours have no regression test
**Areas:** 11 Test coverage, 10 Testability. **Location:** `tests/test_integration.py:335-475`.

The 27 new test cases (22 fail on the parent, and the 5 "passes on master" cases behave as described) cover the main shapes well. Behaviours I verified by hand that are not pinned by any test:

- **Nested `urn:` inside `urn:`**: `#` in the inner subschema must hit the inner one, and `#` in the outer must hit the outer.
- **`#` inside a plain-name (`#foo`) subschema** that lives in a `urn:` document. It must resolve to the `urn:` document; the parent resolves it to the root instead.
- **A direct unit test of `join_uri`**. Pure string cases would pin the cross-version contract on every CI Python cheaply, e.g. `('urn:a#frag', '#b') -> 'urn:a#b'`, `('URN:a', '#') -> 'URN:a#'`, `('urn:a?', '#x') -> 'urn:a?#x'`, `('http://e/a', '#x') -> urljoin result`, `('', '#x') -> '#x'`, `('urn:a', 'b') -> 'b'`.

Repro output (branch; parent shows `valid` for the two invalid rows):

```
ff=True  nested urn: inner self x='a'          fjs=invalid  js=invalid
ff=True  nested urn: outer self x=1            fjs=invalid  js=invalid
ff=True  plain-name then # back to urn doc: k='a'  fjs=invalid  js=invalid
```

**Suggested fix:** add these two parametrized cases and a small `join_uri` table test.

### 3. Nit / follow-up (opinion): relative refs that don't start with `#` are still unresolved under hierarchical custom schemes
**Areas:** 2 Completeness, 4 Robustness. **Location:** `fastjsonschema/ref_resolver.py:90`.

The PR deliberately scopes this out, with a sound rationale for `urn:` (RFC resolution would turn `b.json` into `urn:b.json`). For schemes that have an authority, though, such as `s3://bucket/a.json`, `gs://` or `myapp://host/...` (typical with `handlers`), `$ref: "b.json"` is unambiguous per RFC 3986. It still comes out of `urljoin` as `b.json` and then fails with a raw `ValueError`:

```
ff=True  relative 'b.json' under s3:// (s3://bucket/b.json exists)  fjs=COMPILE-ValueError: unknown url type: 'b.json'
```

The parent gives the same result, so this PR doesn't make it worse. `jsonschema` fails here too, because it also uses `urljoin`. The issue lists `s3:` as an affected scheme, so a reader might expect this case to be fixed as well.

**Suggestion:** a separate issue, or one sentence in the PR body's "Decisions" saying that relative non-fragment refs under such schemes stay as they were.

No other findings. Pre-existing and unchanged by this PR: a root with `$id` ending in an empty fragment (`urn:ex:root#`, and equally `http://ex.com/root#`) next to a root-level `$ref: '#/definitions/x'` fails on parent and branch alike. It raises `URLError` (an attempted remote fetch) because the root isn't stored when it has a `$ref` and `'urn:ex:root' != base_uri 'urn:ex:root#'`. That belongs to the `$ref`-sibling work (#13 / PR #14), not here.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | All 114 adversarial runs agree with `jsonschema` on the branch except 4 (2 cases × 2 modes) where both reject the schema (`adv.py`). The issue's script gives the expected value in every row. Partitioning on the first `#` matches RFC 3986 §5.2.2. |
| 2 | Completeness | Finding 3 | All four `urljoin` call sites are converted, and `generator.generate_ref`'s `in_scope($ref)` goes through `join_uri` too. There are no other `urljoin` uses in the package. Relative non-`#` refs are scoped out. |
| 3 | Consistency | OK | Under a `urn:` id, behaviour and generated names now mirror `http:` ids (same `validate_<id>__definitions_i` pattern). It matches `referencing`'s `startswith("#")` rule. |
| 4 | Robustness | OK | Hostile id `urn:x:'"\\\n{0}{__import__}"""; raise SystemExit(7) #` compiles and runs (both modes, `compile_to_code` exec'd). `urlsplit` raises `ValueError` on bad bases exactly where `urljoin` did. A Windows-path id like `C:\x` now takes the new path (scheme `c`), which is harmless. |
| 5 | Reliability | OK | Results don't depend on the Python version: `partition` instead of `urldefrag`. Verified that `urldefrag('urn:a?#x')` is `'urn:a'` on 3.9 but `'urn:a?'` on 3.14, as the PR says. `uses_relative` is identical on 3.9 and 3.14 except `rtsps` (3.14). For `rtsps` both branches give the same `#` result, so the conditional is version-safe. A library that mutates `uses_relative` only changes normalization, not the target. |
| 6 | Security | OK | New URIs reach function names only via `get_scope_name` (sanitized) and schema values via repr. `tests/test_security.py` passes. |
| 7 | Performance | OK | Compile with 200 local refs: no-id 18.0 vs 18.5 ms, http 21.5 vs 21.1, urn 19.7 vs 20.3 (noise). Validation code is unchanged apart from function names. |
| 8 | Maintainability | OK | A single 6-line helper, with comments explaining both non-obvious choices (scheme gate, no `urldefrag`). |
| 9 | Readability | OK | The docstring is accurate. |
| 10 | Testability | Finding 2 | `join_uri` is a pure function but has no direct unit test. |
| 11 | Test coverage | Finding 2 | 22 of the 27 new cases fail on the parent. The "fails without #9" and "fails without #8" claims are verified by applying the patch onto `#8` and onto master: 2 and 4 failures. |
| 12 | Compatibility | Finding 1 | Two documented compile-time changes. Function names in `compile_to_code()` change only for root `urn:`-style ids (`validate__foo`/`validate___definitions_i`/duplicate `validate` become `validate_urn_example_root_foo`/`..._definitions_i`, with no duplicate). The name `compile()` returns is unchanged. |
| 13 | Architecture | OK | The fix sits in the resolver, not in a global `uses_relative` patch. That is the right layer. |
| 14 | Integration | OK | Depends on #8/#9 as stated; verified by test failures when the patch is applied to master or to #8 alone. The next PR (#16) adapts the http test to its non-mutating API. |
| 15 | Data integrity | OK | `{"$ref": "#"}` inside `const`/`default` under a `urn:` id stays unchanged (the test passes). |
| 16 | Usability | Finding 1 | The error message is unhelpful for the newly failing case. |
| 17 | Accessibility | N/A | Library. See 16/18 for message clarity. |
| 18 | Observability | Finding 1 | Same as 16. |
| 19 | Documentation | OK | The three CHANGELOG lines are accurate. The second "Changed" line could carry the workaround (Finding 1). No user docs mention `urn:`. The PR body's claims (suite unchanged, CI doesn't run the suite: `actions/checkout@v2` without submodules) are verified. |
| 20 | Regression | OK | Full suite passes; the official suite has identical per-case outcomes on parent and branch (5293 lines, `diff` empty); pylint output is identical (9.91/10, same messages). No xfail entries were removed, and none needed to be: `ref.json` is ignored at file level and no case changed outcome. |

## Verification log

Worktrees: `wt-data-keyword-values` (parent, `a467003`), `wt-urn-id-local-refs` (`77b3985`), `wt-master`, `wt-unique-validation-function-names`. Scripts are in `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-2/`. Python 3.14.10 (venv) and 3.9.6 (`/usr/bin/python3`, for `urllib` comparisons only); no 3.10–3.13 interpreter was available.

- **Full suite:**
  - Branch: `4841 passed, 12 skipped, 411 xfailed, 954 xpassed`.
  - Parent: `4814 passed, 12 skipped, 411 xfailed, 954 xpassed` (+27 = the new tests).
- **Lint:** `pylint fastjsonschema` gives 9.91/10 on parent and branch, with an identical message list.
- **New tests against other code** (the branch's `tests/test_integration.py` copied into `pr-2/tests/`):
  - Parent code: 22 failed / 59 passed. The 5 new tests that pass are `..._http_id_is_rewritten_by_urljoin`, `..._data_keyword_under_urn_id_is_data[x2]` and `..._next_to_similar_urn[x2]`, as described.
  - The `ref_resolver.py` hunk patched onto master: 4 failures (`data_keyword_under_urn_id[x2]`, `next_to_similar_urn[x2]`). This confirms "needs #8" and "needs #9".
  - The hunk patched onto #8: 2 failures (`data_keyword_under_urn_id[x2]`). This confirms "needs #9".
  - The hunk on the parent: 27/27 pass.
- **Official suite per case:** `pytest tests/json_schema -rA`, then `diff` of the sorted outcome lines, parent vs branch: identical (5293 lines). URN cases are XPASS in draft6/7/2019, except draft2019 "URN ref with nested pointer ref" and "URN base URI with URN and anchor ref", which are XFAIL on both.
- **`issue_repro.py` / `issue_further.py`** (extracted from the issue): master's output equals the issue's listing; the branch gives the expected value in every row.
- **`adv.py`** (fastjsonschema vs `jsonschema` 4.x/referencing, both `fast_fail` modes, 114 runs): branch 4 differences (relative `b.json` under `s3://`, Finding 3, and the root-only-definition case, Finding 1; both libraries reject the schema in all 4); parent 58 differences.
- **`adv2.py`**:
  - Refs inside `allOf` arrays: urn and http behave identically on parent and branch. The pre-existing #4 behaviour is unchanged.
  - Handler-loaded doc fetched as `urn:ex:alias` with `$id: urn:ex:real` and inner `#/definitions/i`: parent `['invalid','valid','valid']` (wrong), branch `['valid','invalid','invalid']`, which matches the http control.
- **`nocache.py`**: `RefResolver(cache=False)` with a urn handler. The parent fails to compile (`Unresolvable ref: definitions`). The branch is correct, calls the handler 2 times and doesn't loop.
- **`names.py`**: `compile_to_code()` function names for root `urn:` id, root `http:` id and no id. Only the urn case changes; the standalone exec of the generated module gives the same results.
- **`plain.py`**: plain names under `urn:ex:root`, `urn:ex:root#`, draft-04 `id`, and in a handler document next to a root `#foo`. The branch is correct in all; the parent is wrong in the handler case.
- **`rootref.py`**: root `$id` with an empty fragment plus a root `$ref`. Pre-existing `URLError`, identical on parent and branch for urn, tag and http.
- **`sec.py`**: hostile `urn:` id. Compiles and validates in both modes; no code injection.
- **`perf.py`**: compile timings, listed in checklist item 7.
- **`pyver.py`**: `join_uri` vs `urljoin` on 3.9.6 and 3.14.10 over 16 base/ref pairs. The `join_uri` results are identical across versions for every non-`uses_relative` base. For `uses_relative` bases they differ only where `urljoin` itself differs: an empty fragment or query is dropped on 3.9 and kept on 3.14, and `normalize` evens this out.
- Not verified (no interpreter): the PR's claim that taking the new path for `file:schemas/node.json` would loop forever on 3.10/3.11. It doesn't matter, because that path isn't taken for `file:`.
