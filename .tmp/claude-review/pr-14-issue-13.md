# PR #14 / Issue #13: Register $id and resolve refs in definitions next to a $ref

Branch `origin/fix/ref-sibling-definitions` (commit `2375eb3`), parent `fix/handler-schema-nested-id` (`5fd4ad5`). Stack tip.
Scratch scripts are in `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-14/`.

## Verdict

**Approve with nits.** The fix is correct and draft-gated the right way. I compared it with `jsonschema` 4.26 / `referencing` on adversarial schemas in draft-04, draft-07 and 2019-09, including schemas without `$schema`, and every case where the oracle can decide agrees with the branch. The parent disagrees in most of them. Across all 1204 suite schemas, the generated code for draft-04, draft-06 and draft-07 is byte-identical to the parent's. Only 12 2019-09 schemas, all with `$ref` next to `$defs`, get different code. No suite case regresses, and exactly the claimed 11 2019-09 outcomes go from XFAIL to XPASS. The full suite and lint are clean at the stack tip. Nothing blocks the merge. The open points are minor: (1) the change of behaviour for schemas without `$schema` is real, and the `compile()` docstring still tells users that draft-07 is the default; (2) an invalid-URI `$id` that is now walked raises a raw `ValueError` where the schema compiled before; (3) the resolver detects the draft separately from the code generator, which already makes the suite harness print the wrong debug code.

## Issue review

The issue is accurate.
- **Reproduction:** the main repro and the "Further cases" script give exactly the stated "actual" output on master and on the parent (`wt-handler-schema-nested-id`). The branch gives the expected output, and the control row stays `invalid: data.b must be string`.
- **Spec citations:** correct. They cover Draft-07 §8.2/§8.3/§8.3.2, Draft-06 §8/§9.2, Draft-04 §7.1 with JSON Reference §3, and 2019-09 §8.2.2/§8.2.4.1. The reading that "siblings are ignored" means ignored for validation, not removed from the document, matches `referencing`: with the oracle, a JSON pointer or `$id` lookup into definitions next to a `$ref` resolves in draft-04, draft-07 and 2019-09 (`d7scope.py`, below).
- **2019-09 suite counts:** consistent. The issue says 15 outcomes depend on the bug and 6 of them ("ref to if/then/else") stay. The PR fixes 9 + 2 = 11, because it also honours the sibling `$id` in 2019-09. Three of the 11 are the `$recursiveRef`/`$recursiveAnchor` valid-data cases, as stated.
- **Small inaccuracy:** "an unused definition nested about 500 levels deep" is really about **249** nested `definitions` levels. Each map level counts 2 depth units, and the limit is 500 units (`depth.py`).

## Findings

### 1. Minor: schemas without `$schema` change behaviour, and the docs still say draft-07 is the default
**Area:** Compatibility, Documentation, Usability.
**Where:** `fastjsonschema/ref_resolver.py:310-319`; `CHANGELOG.txt:17`; `fastjsonschema/__init__.py:212-214` (the "latest implementation is used (draft-07)" docstring is older than this PR).

Without `$schema`, the resolver now applies 2019-09 semantics to an `$id` next to a `$ref`. That is spec-correct and the oracle agrees. But users who follow the `compile()` docstring write draft-07-style schemas without `$schema`, and those schemas change:

```
# adv.py, no $schema, {"$defs": {"int": {...}}, "properties": {"foo": {"$id": "http://e.com/foo.json", "$ref": "#/$defs/int"}}}
parent: {"foo": 1} valid, {"foo": "x"} invalid
branch: COMPILE JsonSchemaDefinitionException: Unresolvable ref: $defs      (oracle Draft201909: also an error)
# no $schema, root $id http://e.com/root.json, {"a": {"$id": "sub/a.json", "$ref": "thing.json"}}
parent loads http://e.com/thing.json, branch loads http://e.com/sub/thing.json  (oracle agrees with branch)
```

The third CHANGELOG line describes this as "Fixed ... being ignored in 2019-09". For users of `$schema`-less schemas it is a behaviour change that can turn a compiling schema into a compile error, or load a different remote URI.

**Suggested fix:** phrase that line as "Changed" and name the effect, for example "a `$ref` next to such an `$id` now resolves against it, so a pointer into the outer schema raises `JsonSchemaDefinitionException`". Optionally fix the stale draft-07 claim in the `compile()` docstring, which now matters more, or call it out in the PR.

### 2. Minor: an invalid-URI `$id` that is now walked raises a raw `ValueError` at compile time
**Area:** Robustness, Regression, Data integrity.
**Where:** `fastjsonschema/ref_resolver.py:316` (`in_scope(node_id, ...)`) and the `_walk_ref` descent (`:290-292`), which reaches the pre-existing `$id` branch at `:320`.

Schemas that compiled on the parent now fail with `ValueError`, not `JsonSchemaDefinitionException`:

```
# badid.py
                                         parent                 branch
2019 $id next to $ref ('http://[bad')    compiles, valid        ValueError: Invalid IPv6 URL
d7 unused def next to $ref               compiles, valid        ValueError: Invalid IPv6 URL
d7 unused def, no $ref (pre-existing)    ValueError             ValueError
```

The root cause, `join_uri` in `in_scope` for `$id`, is older than this PR. The PR only extends it to objects that weren't walked before. The stack already treats this class of failure as a bug: see the CHANGELOG line on a `$ref` "that isn't a valid URI inside the value of an unknown keyword".

**Suggested fix:** at least mention it next to the depth-limit CHANGELOG line. Better, convert the `ValueError` from `in_scope` for an `$id` into `JsonSchemaDefinitionException`, or ignore such an `$id` the way an invalid `$ref` is ignored in `_walk_ref`. That is arguably a separate PR because it touches the existing `$id` branch.

### 3. Minor: the resolver detects the draft separately from the code generator
**Area:** Architecture, Integration, Testability.
**Where:** `fastjsonschema/ref_resolver.py:100-110,176`; `tests/json_schema/utils.py:116-122`.

`id_next_to_ref_applies` copies the string matching of `_get_code_generator_class`, and `RefResolver.__init__` applies it to whatever schema it gets. The generator that uses the resolver is chosen elsewhere. Three effects:

**a) The suite harness prints the wrong debug code.** `template_test` builds its debug `RefResolver` **before** `schema.setdefault('$schema', schema_version)`. So for draft-04..07 suite cases, the code printed on failure is generated with 2019-09 resolver semantics, not the code that runs. Verified on draft-07 `ref.json` "$ref prevents a sibling $id from changing the base uri" (`debuggen.py`):

```
debug funcs: ['validate_http___localhost_1234_sibling_id_base', 'validate_http___localhost_1234_sibling_id_foo_json']
real  funcs: ['validate_http___localhost_1234_sibling_id_base', 'validate_http___localhost_1234_sibling_id_base_foo_json']
```

The debug code resolves to the wrong `foo.json`. The tests still pass because only `compile()` is asserted, but a 2019-only compile error in the debug resolver would fail a draft-07 case for the wrong reason.

**b) Public-API users get mismatched semantics.** Code that builds `RefResolver.from_schema(schema)` and passes it to `CodeGeneratorDraft07` (the pattern `template_test` uses) gets 2019-09 resolver semantics when the schema has no `$schema`.

**c) The two functions disagree on odd `$schema` values.** `{'$schema': ['draft-07']}` gives resolver 2019 but generator `CodeGeneratorDraft07`, because `in` on a list. `test_resolver_reads_the_draft_like_the_compiler` claims agreement but only tests strings, `{}` and `True`. Garbage input, so this is only a nit.

**Suggested fix:** make the generator class the single source of truth. Let `_factory` pass `id_next_to_ref_applies=_get_code_generator_class(definition) is CodeGeneratorDraft2019`, or the class itself, to `RefResolver.from_schema`, and keep inference only as the default for direct users. In `template_test`, move the `setdefault('$schema', ...)` above the debug resolver.

### 4. Nit: the comment about `id` contradicts the branch below it
**Area:** Consistency, Readability.
**Where:** `fastjsonschema/ref_resolver.py:310` ("Only $id: in 2019-09, the id of draft-04 is an unknown keyword").

The very next `elif` (`:320`) honours `id` in 2019-09 through `get_id`. Verified (`edge.py`): without `$schema`, `{'id': 'http://e.com/r/', 'properties': {'a': {'id': 'sub/', 'properties': {'b': {'$ref': 'x.json'}}}}}` loads `http://e.com/r/sub/x.json`. The PR's choice not to start honouring `id` next to a `$ref` is fine, because it keeps the parent's behaviour. The comment gives a spec reason that the rest of `walk` doesn't follow.

**Suggested fix:** reword the comment, for example "Only `$id`, so that the `id` of draft-04 next to a `$ref` stays ignored as before".

### 5. Nit: test file style
**Area:** Maintainability.
**Where:** `tests/test_integration.py`.

- Three blank lines before `node_with_own_y` (line 1003).
- A trailing blank line at EOF.
- The new imports aren't merged or ordered: `from fastjsonschema import _get_code_generator_class` sits on its own line beside the existing `from fastjsonschema import (...)` block, and `draft2019` and `ref_resolver` come before `draft07`.

### 6. Nit / opinion: the newly passing suite cases are only XPASS
**Area:** Test coverage.
**Where:** `tests/json_schema/test_draft2019.py` (`ref.json` and `refRemote.json` in `ignored_suite_files`).

The 11 newly passing 2019-09 cases don't guard against regressions, because their files stay whole-file xfail. The PR says so, and `test_integration.py` reproduces their shapes ("order of evaluation", URN, absolute-path ref). Still, after this PR only 10 descriptions fail in `ref.json` (19 outcomes) and 3 in `refRemote.json` (6 outcomes).

**Suggestion (opinion):** move those two files to `ignore_tests` with the failing descriptions, which would pin about 85 passing outcomes. The `$recursiveRef`/`unevaluated*` files must stay whole-file. This could be a follow-up for the whole stack.

### 7. Nit: wording of the depth limit
**Area:** Documentation.
**Where:** `CHANGELOG.txt:16`, PR body, issue.

"nesting limit of 500 levels" means 500 depth units, which is 249 nested `definitions` (`depth.py`), and the limit is `min(500, recursionlimit // 2)`. This matches the existing error message, so it's acceptable. "about 500 levels deep" in the PR body and the issue is off by a factor of 2.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | Branch = `jsonschema` oracle in all decidable adversarial cases for draft-04, draft-07, 2019-09 and no-`$schema` (`adv.py`, `d7scope.py`); issue repro fixed |
| 2 | Completeness | OK | `definitions` and `$defs`, `id`/`$id`, handler-loaded docs, `cache=False`, `compile_to_code` all work. if/then/else limitation documented |
| 3 | Consistency | Finding 4 | 2019 `$id` branch mirrors the `$id` branch (store, `_walked`, `id_applied`). The generator still ignores all `$ref` siblings in 2019 (applicator semantics, "ref applies alongside sibling keywords" stays XFAIL). Registering the sibling `$id` is identification only, so it doesn't conflict with that |
| 4 | Robustness | Finding 2 | Invalid-URI `$id` now walked gives raw `ValueError`. Boolean or non-dict defs are skipped correctly; a self-referencing `$id`+`$ref` compiles (RecursionError at validation, as in any infinite schema) |
| 5 | Reliability | OK | Deterministic; first-base-URI-wins kept for `_resolved_refs` |
| 6 | Security | OK | No new code emission. Keys with braces and quotes in defs names and in `$id` validate correctly (`edge.py`). Unknown keywords next to `$ref` deliberately not walked (`test_id_in_other_keyword_next_to_ref_is_ignored`) |
| 7 | Performance | OK | Only definitions next to a `$ref` are walked in addition (linear); suite codegen unchanged for 1192/1204 schemas |
| 8 | Maintainability | Finding 3, 5 | Duplicated draft detection |
| 9 | Readability | Finding 4 | Otherwise clear; `_walk_ref` extraction is good |
| 10 | Testability | Finding 3 | Debug code in the suite harness uses the wrong draft for draft-04..07 |
| 11 | Test coverage | OK / Finding 6 | 80 new parametrized tests. 52 fail on the parent and 63 on master, exactly the ones the PR lists; the 4 "pass there" tests pass on the parent |
| 12 | Compatibility | Finding 1 | No-`$schema` schemas with an `$id` next to a `$ref` change; depth-limit change documented |
| 13 | Architecture | Finding 3 | Resolver infers the draft separately from the generator |
| 14 | Integration | OK | Works with #11 (handler-loaded doc), #10 (`allOf` below defs), #9 (`default` next to `$ref` stays data) |
| 15 | Data integrity | OK | Schema not mutated (`test_data_keyword_next_to_ref_is_data`); no foreign `$id` from `x-`/`not` registered in draft-07 |
| 16 | Usability | Finding 1 | |
| 17 | Accessibility | N/A | Library. The error for a pointer that now fails is a clear `Unresolvable ref: $defs` |
| 18 | Observability | N/A | |
| 19 | Documentation | Finding 1, 7 | CHANGELOG has 3 lines; docstring of `id_next_to_ref_applies` is accurate |
| 20 | Regression | OK | No XPASS→XFAIL and no passing test lost. Full suite 5123 passed (parent 5062) |

## Verification log

Paths are relative to the scratchpad. `$PY` is `venv/bin/python` there.

- **Issue repro** (`pr-14/repro1.py`, `pr-14/repro2.py` extracted from the issue): on master and the parent, output identical to the issue's "actual". On the branch, `{'b': 1} -> valid`, `{'b': 'x'} -> data.b must be integer`. All "Further cases" rows give their expected results and the control is unchanged.
- **Branch tests on the parent and master** (`pr-14/ptests`, the branch's `test_integration.py` with the new import made optional, `-k` for the new tests):
  - parent: 52 failed, 28 passed;
  - master: 63 failed, 17 passed (the extra failures come from earlier stack PRs' tests);
  - branch: 80 passed.

  The failing set matches the PR's list. `test_id_in_unknown_keyword_inside_definitions_is_registered` fails only in its `$ref` form.
- **Full suite:**
  - branch (stack tip): `5123 passed, 12 skipped, 382 xfailed, 835 xpassed`;
  - parent: `5062 passed, 12 skipped, 393 xfailed, 824 xpassed`;
  - non-suite tests only: `1047 passed, 12 skipped`.
- **XFAIL/XPASS diff, parent to branch:** 11 outcomes XFAIL→XPASS, all 2019-09: `ref.json` "order of evaluation: $id and $ref" ×2, "ref with absolute-path-reference" ×2, "URN ref with nested pointer ref" ×2, "$ref with $recursiveAnchor / extra items allowed for inner arrays"; `refRemote.json` "remote HTTP ref with nested absolute ref" ×2; `unevaluatedItems`/`unevaluatedProperties` "with $recursiveRef / with no unevaluated ..." ×1 each. No XPASS→XFAIL. No draft-04..07 change.
- **Codegen diff** (`pr-14/codediff.py`): `compile_to_code` over all 1204 suite schemas. 12 differ, all 2019-09 schemas with `$ref` next to `$defs` (anchor.json ×3, ref.json ×4, refRemote.json ×3, unevaluated* ×2). Zero draft-04/06/07 differences.
- **Oracle comparison** (`pr-14/adv.py`, `pr-14/d7scope.py`): `jsonschema` 4.26 with a `referencing` Registry. The branch equals the oracle in every case except:
  - fragment-only `$id: "#foo"` in 2019, which `referencing` rejects and both fastjsonschema branches accept;
  - eager-vs-lazy compile errors on deliberately broken refs.

  The parent differs from the oracle in 12 cases.
- **Depth** (`pr-14/depth.py`): with and without `$ref`, both fail at 249 nested `definitions`/`$defs`. A chain of `$ref` objects with definitions fails at 250 (parent: never).
- **Edge cases** (`pr-14/edge.py`, `pr-14/edge2.py`, `pr-14/badid.py`): `compile_to_code` output validates correctly; with `cache=True` the handler is called once, with `cache=False` twice, results correct; invalid-URI `$id` gives `ValueError` (Finding 2); `$schema` list or None mismatch (Finding 3c); `id` honoured in 2019 without `$ref` (Finding 4).
- **Lint:** `pylint fastjsonschema` on the branch is 9.91/10 with 9 messages. The set is identical to the parent and master, and none is in `ref_resolver.py`.
