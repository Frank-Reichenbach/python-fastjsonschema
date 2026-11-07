# PR #10 / Issue #4: Resolve refs inside allOf, anyOf, oneOf and items arrays against their $id

Reviewed commit: `35ae4a3` (`origin/fix/walk-schema-arrays`), parent `c4840e2` (`fix/keep-schema-unchanged`). Scripts are in `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-10/`.

## Verdict

**Approve with nits.** The change is small and correct: `subschemas()` now yields the object items of `allOf`, `anyOf`, `oneOf` and array-form `items`, and it still skips data keywords and arrays under any other key. For drafts 4, 6 and 7 (and fastjsonschema's draft-2019 generator, which adds no array keywords), this keyword list matches exactly the array keywords whose items the generator compiles as schemas. Every repro from the issue is fixed. The 18 claimed suite cases pass, and the xfail removals match them exactly. Out of 799 suite and metaschema schemas, the generated code changes only for the 7 schemas that this PR fixes. The depth limit applies to arrays, and nothing that compiled before stops compiling, with one exception: a draft-06+ schema that uses `id` as an annotation inside an array item (Finding 1). The PR body lists that as a limitation, but the CHANGELOG doesn't mention it. The remaining findings are nits.

## Issue review

The issue is accurate.
- Reproduced on `master` and on the parent: every case in the issue's "Further cases" gives `invalid`, an `Unresolvable ref` error, or a handler call. On the branch, every case gives `valid` (see the verification log).
- The cause is described correctly: at `b88fa37`, `walk` (lines 181–204) descends only into `dict` values. This has been the case since `3b964b0` (2018-06-19).
- The count of "18 cases" matches: going from parent to branch, the XFAIL set loses exactly these 18 cases. That's 6 in draft6 `ref.json` and 12 in draft7 `ref.json` ("refs with relative uris and defs", "relative refs with absolute uris and defs", and "ref to if/then/else").
- The spec citation (Draft-07 §8.2: `$id` sets the base URI, with no exception for subschemas inside arrays) is correct. The `jsonschema` oracle agrees with the branch in every adversarial case I compared.
- The issue points out that the key check alone isn't enough without #9 (values of data keywords). That is true, and `subschemas()` from #9 handles it.

## Findings

### 1. minor: Compatibility, Regression, Documentation. A draft-06+ `id` annotation inside an array item now changes the base URI, and a schema that compiled before can now fail to compile
`fastjsonschema/ref_resolver.py:68-71` (together with `get_id`, line 31, and `walk`, line 267)

`walk` treats `id` as an identifier in every draft. Until now, this only happened at object positions. Now it also happens inside `allOf`/`anyOf`/`oneOf`/`items`. In draft-06 and later, `id` is an unknown keyword, so a schema that compiled and validated correctly on the parent now raises an error:

```python
s = {"$schema": "http://json-schema.org/draft-07/schema#", "definitions": {"name": {"type": "string"}},
     "properties": {"user": {"allOf": [{"id": "user", "properties": {"name": {"$ref": "#/definitions/name"}}}]}}}
fastjsonschema.compile(s)({"user": {"name": "a"}})
```
```
master / parent: valid
branch:          JsonSchemaDefinitionException Unresolvable ref: definitions
(the same schema without the allOf wrapper fails at the object position on master already)
```
`jsonschema` (Draft7Validator) treats a similar schema (`id: http://e.com/other.json` inside `allOf`) as valid for `{"p":"a"}` and invalid for `{"p":1}`. That matches the parent, not the branch.

The PR body discloses this under "Limitations", and it is consistent with the existing behavior at object positions. Users who read only the CHANGELOG won't see it, though. Suggested fix: add a "Changed" line to the CHANGELOG, for example "An `id` inside `allOf`/`anyOf`/`oneOf`/`items` now also sets the base URI, as it already did elsewhere, in every draft". Separately, open a follow-up issue to read `id` only for draft-04 (the resolver could take the draft from the root `$schema`). Fixing that is out of scope here.

### 2. nit: Correctness (pre-existing, informational). An array object that appears twice in one schema under two different `$id`s still resolves against the first one
`fastjsonschema/ref_resolver.py:263-264` (first-wins rule from #16)

```python
N = {"anyOf": [{"$ref": "#/definitions/x"}, {"type": "null"}]}
root = {"$id": "http://e.com/root.json", "definitions": {"x": {"type": "string"}}, "properties": {
  "a": {"$id": "one.json", "definitions": {"x": {"type": "integer"}}, "properties": {"p": N}},
  "b": {"$id": "two.json", "definitions": {"x": {"type": "boolean"}}, "properties": {"p": N}}}}
```
```
{"a":{"p":1},"b":{"p":true}}: parent I, branch I, oracle V
{"b":{"p":"s"}}:              parent V, branch I, oracle I
```
On the branch, `b.p` uses `one.json`'s `x`. On the parent, both used the root's `x`, so this is an improvement, not a regression. A shared dict at an object position behaves the same on the parent (script `adv2.py` case 9), so this comes from #16's id()-keyed `_resolved_refs` and isn't caused by this PR. I mention it only because the PR presents the shared "nullable ref" as fixed, and its test (`test_schema_array_shared_by_schemas_with_different_ids`) covers only two separate `compile()` calls. Suggestion: none for this PR. You could optionally state "within one schema, the first base URI wins" in the Limitations section.

### 3. nit: Consistency, Maintainability. `_expand_refs` says it follows "the same rules as in ref_resolver.subschemas", but it still recurses into every list
`fastjsonschema/generator.py:356-366`

`subschemas()` now handles arrays only under `SCHEMA_ARRAYS`. `_expand_refs` recurses into every list, including arrays under unknown keywords, and resolves `$ref`s there. For example, `{"type":"integer","x-list":[{"$ref":"http://e.com/foo.json"}]}` calls the handler for `foo.json` at compile time just to build the error definition. This happens on both the parent and the branch, so it is pre-existing. Still, the comment now overstates the parity, and `test_array_in_unknown_keyword_is_not_walked` suggests that such arrays are never touched. Suggested fix (optional, or as a follow-up): import `SCHEMA_ARRAYS` and limit the list recursion in `_expand_refs` to those keys, or reword the comment.

### 4. nit: Test coverage. The improved error `definition` has no test
This PR also changes the `definition` attached to `JsonSchemaValueException`, because `_expand_refs` uses `get_ref` and now gets the resolved URI for refs inside arrays:
```
v = {"type":"array","anyOf":[{"$ref":"#/definitions/x"},{"type":"array"}]} under $id node.json (x: integer), root x: string
parent: e.definition == {'type': 'array', 'anyOf': [{'type': 'string'}, {'type': 'array'}]}
branch: e.definition == {'type': 'array', 'anyOf': [{'type': 'integer'}, {'type': 'array'}]}
```
The new result is correct. Suggestion: add one assertion on `exc.definition` to `test_ref_in_schema_array_uses_id_of_its_subschema`, or add a small separate test.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | All 11 issue repros fixed. 9 adversarial schemas (nested mixes of oneOf>items>anyOf>allOf, `not`>allOf, additionalItems, dependencies schema vs list, `$id` in array item scoping its own refs) agree with `jsonschema` |
| 2 | Completeness | OK | `SCHEMA_ARRAYS` = exactly the keywords whose list items the generator compiles (draft04 `generate_all_of/any_of/one_of/items`; draft06/07/2019 add only dict-valued schema keywords; there is no `prefixItems` support). `dependencies` list values, `required`, `type` and `enum` stay data |
| 3 | Consistency | Finding 3 (nit) | Arrays count as 2 depth levels, like map values. `_expand_refs` doesn't follow the same rule |
| 4 | Robustness | OK | Booleans and non-dicts in arrays are skipped. `allOf` given as a string or dict, and nested lists, behave as on the parent. `allOf: [1,"x",null]` gives a TypeError on both (generator, pre-existing) |
| 5 | Reliability | OK | Deep nesting: `allOf`×246 compiles on both, ×247–249 RecursionError on both (generator), ×250+ now `JsonSchemaDefinitionException` (was RecursionError). No new failures |
| 6 | Security | OK | No new generated code. An array `$id` of `a"b{c}'d.json` gives the function name `validate_http___e_com_ab_c__d_json`, and the `compile_to_code` output executes correctly |
| 7 | Performance | OK | 500 props × anyOf/allOf + 2000-item enum: walk 0.2 ms → 1.1 ms, compile ~2.7 s on both (dominated by enum) |
| 8 | Maintainability | OK | 10-line change inside the existing `subschemas()` |
| 9 | Readability | OK | Clear branches. The comment notes that `items` can also be a single schema |
| 10 | Testability | OK | Pure resolver change, tested end to end |
| 11 | Test coverage | Finding 4 (nit) | The 24 new tests fail on master and on the parent, and the 5 guard tests pass on both, as claimed. With this PR applied without #16, the shared-array test fails 2/2, as claimed |
| 12 | Compatibility | Finding 1 (minor) | Draft-06+ `id` annotation in array items |
| 13 | Architecture | OK | Uses #9's `subschemas()` and #16's side table. Correctly depends on both |
| 14 | Integration | OK | Handler-loaded documents also get their array `$id`s registered (via `_ensure_walked`). Nested `$id` refs inside handler documents are still wrong (#5/PR #11, out of scope) |
| 15 | Data integrity | OK | Arrays inside `const`/`default` stay data (tests plus my check). The schema stays unchanged (#16) |
| 16 | Usability | OK | Plain-name `$id`s in arrays now resolve. No spurious `urlopen` calls |
| 17 | Accessibility | N/A | Library. Error messages unchanged apart from the now-correct `definition` (Finding 4) |
| 18 | Observability | N/A | |
| 19 | Documentation | Finding 1 (minor) | The CHANGELOG "Fixed" line is accurate. A "Changed" line for the `id` behavior is missing. No docstring changes are needed |
| 20 | Regression | OK (except Finding 1) | Generated code is identical for 792 of 799 suite and metaschema schemas. The 7 that differ are exactly the fixed `ref.json` cases. Full suite green |

## Verification log

```
# full suite (PYTHONPATH=<wt>, -rfxX)
parent  wt-keep-schema-unchanged: 4847 passed, 12 skipped, 411 xfailed, 954 xpassed
branch  wt-walk-schema-arrays:    5024 passed, 12 skipped, 393 xfailed, 824 xpassed
  -> XFAIL diff: only 18 draft6/draft7 ref.json cases removed. No other XFAIL/XPASS changes.
     The remaining draft2019 ref.json XFAILs ("ref to if", "refs with relative uris and defs", ...) use
     $ref with sibling keywords (#13/PR #14), not arrays.
     +177 passed = 18 + 130 former XPASS (ref.json unmarked) + 29 new tests.

# new tests from branch run against other code (tests copied to pr-10/t)
master:            24 failed, 5 passed  (failing: uses_id_of_its_subschema ×20, id/plain-name registered, boolean ×2)
parent:            24 failed, 5 passed
branch:            29 passed
#2 + this diff (no #16): 2 failed (test_schema_array_shared_by_schemas_with_different_ids[True/False]), 27 passed

# issue repro (repro_issue.py): master/parent: 7× invalid, Unresolvable ref ×2, handler call ×1, ...; branch: 11× valid

# generated-code comparison (codediff.py): 799 schemas, 7 differ: draft6/ref.json#18,#19; draft7/ref.json#18,#19,#28,#29,#30

# adv.py / adv2.py / depth.py / expand.py / idann.py / perf.py: outputs quoted in the findings and checklist above

# lint: pylint fastjsonschema -> 9.91/10 on parent and branch, no messages in ref_resolver.py
```
