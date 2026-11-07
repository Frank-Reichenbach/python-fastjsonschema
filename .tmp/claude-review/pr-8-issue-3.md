# PR #8 / Issue #3: Use one validation function name per URI

## Verdict

**Approve with nits.** The fix does what it says. There is one name per normalized URI, different URIs always get different names, and the root keeps its unsuffixed name. Every case in the issue is fixed in both `fast_fail` modes. All 18 new tests fail on master and pass on the branch. The rest of the suite is unchanged: same xfail and XPASS lists, and the same pylint messages. `compile_to_code()` gives byte-identical output to master for all 1204 suite schemas I checked. A 3000-schema fuzzer finds no duplicate `def`s, wrong-target refs or replaced roots on the branch (master: 4297 failures on the same seed). Names are deterministic across `PYTHONHASHSEED`s.

Nothing here blocks the merge:
- naming is quadratic when many URIs share one base name;
- the `?#/definitions/ab` example given in the CHANGELOG still crashes `compile()` in most schema shapes, through a separate bug that predates this PR;
- two test and maintainability nits.

## Issue review

The issue is accurate. Checked:

- **Repro and outputs.** The main repro and all 19 rows of "Further cases" reproduce on master (2.22.3) exactly as reported. That includes both `NameError` messages (`validate____definitions_ab`, `validate___definitions_a_b`). On the branch every row is `valid`.
- **Cause and line links.** Checked with `git show b88fa37:...`: `get_scope_name` is at ref_resolver.py L172–179, `normalize` at L49–50, `get_uri` at L169–170, and generator.py L76 and L227–231 match the description. Commit `95df60d` (2018-06-14) is the RefResolver introduction.
- **Spec citations.** RFC 6901 §4 (byte-by-byte member names) and RFC 3986 §6.2.2.1 (case sensitivity) are quoted correctly.
  - Caveat for the empty-query case: RFC 3986 §6.2.3 says `http://example.com/?` "cannot be assumed to be equivalent" to the URI without `?`, and `jsonschema` reports `Unresolvable: ?#/definitions/ab`. The issue frames the expectation as consistency with fastjsonschema's own normalization ("fastjsonschema itself treats both `$ref`s as the same URI"). That holds, but it is a library choice, not a spec requirement.
- **Not verified:** the claim that 2.21.2 and 2.22.2 behave the same (I didn't install old releases).

## Findings

### 1. Minor: naming is quadratic in the number of URIs that share a base name (Performance, Robustness)

`fastjsonschema/generator.py:228-230`: the `while name in self._taken_validation_function_names` loop starts at `index = 2` for every new URI. The k-th URI with the same base therefore probes k−1 names, so k colliding URIs cost O(k²). The PR body says "naming stays linear in the number of URIs". That is only true when names don't collide.

Repro (`scratchpad/pr-8/perf.py`): 8000 definitions `a?b?b?b?b?b` with separators from `-_. +*,;` all map to `validate___definitions_a_b_b_b_b_b`. Best of 3 `compile()` runs:

```
wt-master:                           distinct 8000 0.891   same 2000 0.218   same 8000 0.893
wt-unique-validation-function-names: distinct 8000 0.883   same 2000 0.565   same 8000 6.575
```

The "distinct" row confirms there is no regression for normal schemas, consistent with the PR's 0.61 s vs 0.66 s claim. The pathological case is about 7x slower than master and grows quadratically. Real schemas almost never have thousands of names that differ only in punctuation or case, so this is minor.

Suggested fix: keep a per-base next index, `self._next_name_index = {}`, and use it as below. The loop can stay as a guard.

```python
index = self._next_name_index.get(base, 2)
while name in self._taken_validation_function_names:
    name = '{}_{}_'.format(base, index)
    index += 1
self._next_name_index[base] = index
```

Results with this fix monkeypatched in (`perf_fix.py`, `fuzz_fix.py`): `same 8000` takes 0.913 s, and the fuzzer (seed 2) gives the same result as the branch (163 failures, all the existing `?#` `ValueError`, see Finding 2). Uniqueness still holds:
- Unsuffixed names never end in `_`.
- A suffix contains no `_` apart from its delimiters, so `base_N_` determines both `base` and `N`.

### 2. Minor: the `?#/definitions/ab` example in the CHANGELOG still fails `compile()` in most schema shapes (Completeness, Documentation)

This bug predates the PR, but the CHANGELOG names `?#/definitions/ab` as fixed. The `NameError` is gone. However, any keyword in an enclosing schema that emits an error message calls `_expand_refs` (`fastjsonschema/generator.py:354`), and `_expand_refs` resolves the **raw** `$ref`. With an empty base, `?` is then loaded as a remote URI:

```python
{'definitions': {'ab': {'type': 'integer'}}, 'type': 'object',
 'properties': {'x': {'$ref': '?#/definitions/ab'}}}
# master, branch and stack tip (wt-ref-sibling-definitions): ValueError: unknown url type: '?'
```

The traceback goes `generate_type` → `exc` → `_expand_refs` → `resolving`. The same happens with `required` at the root, or with a `$ref: '?#'`. The new test `test_ref_changed_by_normalization_and_its_normalized_form_use_one_function` passes only because its root schema has no keyword that emits an error.

Suggested fix: not required for this PR. Either word the CHANGELOG line more narrowly, or note it as a follow-up. If the second, `_expand_refs` should resolve the same normalized URI that `generate_ref` uses, or catch the error. Whatever is done should also take into account that, per RFC 3986 §6.2.3, the empty query isn't strictly equivalent (see Issue review).

### 3. Nit: no test pins the trailing-`_` decision or the `compile_to_code()` root name (Test coverage)

The trailing `_` in the suffix is the PR's key design choice ("Decisions"): a URI whose base name doesn't collide keeps its master name, whichever URI comes first. No test asserts that. Changing the suffix to `_2` would break that property, and every test would still pass, because the names would still be unique.

Verified behaviour (`scratchpad/pr-8/det.py`): with keys `a`, `A`, `a-2`, `a_2`, …, the key `a_2` keeps `..._definitions_a_2`, the `a` family gets `_a_2_`, `_a_2_2_`, and so on.

Suggested test: compile `{'definitions': {'a': ..., 'A': ..., 'a_2': ...}}` with `compile_to_code()`. Assert that `def validate___definitions_a_2(` is present and that the module-level root is still `validate`. The root test currently covers only `compile()`.

### 4. Nit: `compile()` finds the root function by recomputing its name (Maintainability, Integration)

`fastjsonschema/__init__.py:295` still uses `global_state[resolver.get_scope_name()]`. This works only because the root is named first and so never gets a suffix (generator.py:80). The invariant is documented in the PR body and the commit message, but not at the call site. Reading the root name from the generator would remove the coupling, for example with a `code_generator.root_function_name` attribute set at line 80.

This also matters for upstream horejsek#224, which makes `get_scope_name()` itself stateful (see Integration in the Checklist). This is the only remaining direct caller of `get_scope_name()` outside `_validation_function_name`, as `grep` confirms.

### 5. Nit (opinion): suffixed names depend on generation order (Usability, Compatibility)

Names are deterministic across runs and hash seeds: the same sha1 for `PYTHONHASHSEED` 0, 1, 2, 3 and random. But the suffix goes to whichever URI is reached first, in the generator's LIFO `popitem()` order. Adding a colliding definition can therefore rename an existing `_2_` function in `compile_to_code()` output. Names such as `..._a_2_` (base `a`, suffix 2) next to `..._a_2` (base `a_2`) are also easy to confuse when reading the generated code.

Only users who import non-root functions from generated modules are affected, and only in schemas that were already broken on master. No change requested.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | All issue rows fixed. Fuzzer (3000 schemas, seeds 1 and 2): 0 duplicate `def`s, wrong-target refs or replaced roots (master: 4297 failures) |
| 2 | Completeness | Finding 2 | Both call sites use the new helper. `?#…` still crashes through `_expand_refs` (predates this PR) |
| 3 | Consistency | OK | One key (`get_uri()`) for the name, `_needed_validation_functions` and `_validation_functions_done` |
| 4 | Robustness | Finding 1 | Quadratic only in the pathological same-base case |
| 5 | Reliability | OK | Deterministic across hash seeds (sha1 identical for 5 seeds) |
| 6 | Security | OK | Names contain only `[a-z0-9_]`. The suffix adds only digits and `_`. The name is passed as a positional `format` argument, so it is not re-formatted |
| 7 | Performance | Finding 1 | No regression for distinct names (0.883 s vs 0.891 s, 8000 definitions) |
| 8 | Maintainability | Finding 4 | Small, well-commented helper. Root lookup relies on an implicit invariant |
| 9 | Readability | OK | Comment explains the trailing `_`. Docstring is accurate |
| 10 | Testability | OK | Behaviour is observable through `compile()` and `compile_to_code()` |
| 11 | Test coverage | Finding 3 | 36 test cases (18 new ones fail on master). Missing: a pin for the trailing `_` decision, and the `compile_to_code()` root name |
| 12 | Compatibility | OK / Finding 5 | Suite: byte-identical `compile_to_code()` for 1204/1204 schemas (56 raise the same exception type). Names change only in colliding schemas |
| 13 | Architecture | OK | Mapping in the generator (which owns the `def`s) is reasonable. Resolver stays stateless for naming |
| 14 | Integration | OK (note) | horejsek#224 (open) dedupes inside `get_scope_name()` with suffix `_N` (no trailing `_`). It touches `ref_resolver.py` and CHANGELOG, this PR touches `generator.py` and CHANGELOG, so there is no textual conflict in code. If both land, names are deduplicated twice: redundant but still unique. The PR body's "whichever is merged second has to be adapted" is accurate. Drop one of the two mechanisms then |
| 15 | Data integrity | OK | The schema is not mutated by this change |
| 16 | Usability | OK / Finding 5 | Error messages unchanged |
| 17 | Accessibility | N/A | Library |
| 18 | Observability | N/A | Library |
| 19 | Documentation | OK / Finding 2 | CHANGELOG line present under UNRELEASED and accurate apart from the `?#` caveat. Commit message matches the code |
| 20 | Regression | OK | Full suite: 4776 passed, 415 xfailed, 970 xpassed. xfail and XPASS lists identical to master (1385 entries). Pylint messages identical |

## Verification log

Scripts are in `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-8/`.

- **`repro.py` and `further.py`** (issue code): master reproduces every reported row, including both `NameError`s. On the branch, every row is `valid`.
- **New tests on master code:** `test_integration.py` copied with `conftest.py` and run with `PYTHONPATH=wt-master`: `18 failed, 18 passed`. All 18 new tests fail.
- **Branch:** `pytest tests/test_integration.py`: 36 passed. Full suite: `4776 passed, 12 skipped, 415 xfailed, 970 xpassed`.
- **`pytest -rxX tests/json_schema`** on master vs branch: the sorted XFAIL and XPASS lists are identical (1385 lines each).
- **`pylint fastjsonschema`:** message lists identical to master (with line numbers stripped). Score 9.90 vs 9.91, from the added lines only.
- **`fuzz.py 1`** (random keys from `a A - _ 2 3 ~ / space ä . "`, optional root `$id`, refs to the root under various spellings, random `fast_fail`):
  - master: `bad 4297` (DUP, FALSE REJECT, ROOT REPLACED);
  - branch: `bad 161`, all `ValueError unknown url type: '?'`, the same 161 as on master (Finding 2).
  - Seed 2: branch 163, all the same `ValueError`.
- **`handler.py`** (root `$id` `a-b.json`, handler docs `a_b.json` and `A-B.json`, each with a colliding `#/definitions/x`, plus `$ref: '#'`): master raises `data must be integer` on valid data. The branch rejects every bad case in both modes, and generates 6 distinct `def`s.
- **`det.py`** under `PYTHONHASHSEED` 0, 1, 2, 3 and random: identical sha1 `4172a063…`.
- **`perf.py`:** numbers in Finding 1. With the per-base-index fix (`perf_fix.py`): 0.913 s. `fuzz_fix.py` gives the same result as the branch.
- **`suite.py`** (`compile_to_code()` over draft4/6/7/2019-09 suite schemas, with the folder's `$schema` set when missing and `http`/`https` handlers returning `{}`): 1204 schemas, 56 exceptions, **0 differences** to master. This is a spot check of the PR body's identical-code claim. My count differs from the PR's 2493 because I enumerated the schemas differently.
- **`grep`:** `get_scope_name` is called directly only at `__init__.py:295` (root lookup) and in `generator.py:224` (the new helper). No docs or tests depend on the generated names.
- **`gh pr view/diff 224 -R horejsek/python-fastjsonschema`** (read only): the upstream PR is open. It adds `_scope_names` and `_used_scope_names` to `RefResolver` with suffix `_{n}` starting at 1, and also changes `resolve_path` for empty pointer tokens.
