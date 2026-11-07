# PR #9 / Issue #6: Treat the values of const, enum, default and examples as data

Reviewed commit: `a467003` (origin/fix/data-keyword-values) against parent `2ee7fbb` (fix/unique-validation-function-names).

## Verdict

**Approve with nits.** The fix is small and correct, and it follows the issue's proposed design. `walk` and `_expand_refs` now skip the values of `const`/`enum`/`default`/`examples`, and they tell keywords apart from names inside `properties`, `definitions`, `$defs`, `patternProperties`, `dependencies` and `dependentSchemas`. Every repro in the issue now behaves as `jsonschema` does. Entries named `const`/`default`/`enum`/`examples` inside real schema maps are still walked as schemas, in draft-04, draft-07 and 2019-09. The depth limit behaves the same as before. Lint and timing are unchanged. Generated code is byte-identical for 925 of the 931 suite schemas I compiled. The six that differ are the intended ones: `id.json` and the "naive replacement of $ref" `enum` case in `ref.json`. All new tests fail on the parent except the one guard test the PR says passes on master. Mutation checks show each branch of the new code is covered by a test. The `id.json` xfail removals match exactly the cases that now pass, and no newly passing case is left XPASS.

The remaining findings are behaviour changes at the edges. None is a correctness bug in what JSON Schema defines:
- A `$ref` pointer into a data value that itself holds a relative `$ref` now resolves against a different base (finding 1).
- Some schemas that used to resolve an `$id` locally now trigger a remote fetch at `compile()` time (finding 2). The PR body documents this, the CHANGELOG doesn't.

## Issue review

The issue is accurate. I reproduced every row of "Actual result" and "Further cases" on master and on the parent: the same compile errors, the rewritten `default`, `ValueError: Invalid IPv6 URL`, and `data.v must be integer` for the `$id` cases (`adv.py` rows A1–A7 below). The cause analysis is correct:
- `walk` descends into every dict value, but not into arrays. On the parent, `$id` inside an `examples` array is already harmless (row A7 "examples_wrap").
- `_expand_refs` also descends into arrays, so it breaks `enum`/`examples` (rows A3/A4).

The spec citations check out. Draft-07 Core §4.3.3 "Root Schema and Subschemas" contains "Some keywords take schemas themselves…", and §4.3.1 contains "Unknown keywords SHOULD be ignored". The suite claim is correct too: "match $ref to id" (2019-09: "match $ref to $id") was XFAIL in all four drafts, and the other `id.json` cases were XPASS. The statement that `unknownKeyword.json` fails "for the same reason" holds, and it still fails after the PR, as the issue anticipates ("needs a separate decision"). One small point: the "Possible fix" doesn't mention that `_expand_refs` keeps descending into lists while `walk` doesn't. That is issue #4's territory, so it's fine to leave out.

## Findings

### 1. Minor (Correctness / Regression): a `$ref` pointer into a data value now resolves the `$ref` inside that value against the document's base, not the enclosing `$id`
`fastjsonschema/ref_resolver.py:232-236`, consequence of `subschemas()` skipping `default`.

Suppose a schema uses `{"$ref": "#/properties/n/default"}` to point at a `default` value, and that value contains a relative `$ref`. If the `default` sits under a nested `$id`, the relative `$ref` used to be made absolute by `walk` against that `$id`. It is now left relative, and the generator resolves it against the document URI. Pointing through the nested `$id` URI (`http://example.com/n/n.json#/default`) still works (row E4).

```python
{"$schema": D7, "$id": "http://example.com/root.json", "definitions": {"x": {"type": "string"}},
 "properties": {"n": {"$id": "http://example.com/n/n.json", "definitions": {"x": {"type": "integer"}},
                      "default": {"$ref": "#/definitions/x"}},
                "b": {"$ref": "#/properties/n/default"}}}
```
```
parent : E5 {"b": 1} valid                  {"b": "x"} invalid: data.b must be integer   (matches jsonschema)
branch : E5 {"b": 1} invalid: data.b must be string   {"b": "x"} valid                  (jsonschema: valid / invalid)
```
Draft-07 §8.3 only says `$ref` "identifies the URI of a schema to use". Using a `default`/`enum` value as a schema is outside what the spec defines, so this is a very unusual schema, and the new behaviour follows from "data is data". No code change is needed. Optionally, mention it next to the other edge cases under "Decisions" in the PR body.

### 2. Minor (Compatibility / Documentation / Security-adjacent): some schemas that resolved an `$id` locally now make `compile()` fetch the URI remotely, and the CHANGELOG doesn't say so
`fastjsonschema/ref_resolver.py:59-71`, `CHANGELOG.txt:5`.

If an `$id` is no longer registered, a `$ref` to it falls through to `resolve_remote`. With the default handlers, that is `urlopen`, an outbound HTTP request at `compile()` time for a schema that used to compile offline. Three cases (my handlers raise to make the fetch visible):
```
D1 {"x-defs": {"default": {"$id": "http://example.com/d.json", "type": "integer"}}, "properties": {"a": {"$ref": "http://example.com/d.json"}}}
   parent: valid / "data.a must be integer"   branch: compile RuntimeError: fetch http://example.com/d.json
D3 draft-07 {"$defs": {"$id": "http://example.com/d.json", "type": "integer"}, ...}      same change
E8 {"properties": {"a": {"const": {"$id": "http://example.com/only.json", "type": "integer"}}, "b": {"$ref": "http://example.com/only.json"}}}
   parent: valid   branch: compile RuntimeError: fetch http://example.com/only.json
```
- E8 is the intended, spec-correct behaviour. `jsonschema` can't resolve it either (`_WrappedReferencingError`).
- D1 and D3 are the trade-offs listed under "Decisions" in the PR body (custom maps with entries named like data keywords; a schema placed directly under `$defs` in older drafts). `jsonschema` doesn't resolve them either.

The concern is only visibility. Users who relied on the old behaviour now get a network fetch, or a handler error, instead of a local resolution, and nothing in the CHANGELOG says so. Suggested fix: append a clause to the CHANGELOG line, for example: "An `$id` inside such a value, or inside an entry named like one of these keywords in a custom keyword, is no longer registered".

### 3. Nit (Maintainability): the traversal rules now live in two places
`fastjsonschema/generator.py:348-366` and `fastjsonschema/ref_resolver.py:59-71`. `_expand_refs` reimplements the `subschemas()` rules by hand. The comment points at `subschemas`, and the tests catch drift both ways (mutations M1/M2), so this is acceptable. It is also why `_expand_refs` still descends into lists while `walk` doesn't (pre-existing, issue #4 / PR #10). This is an opinion, and no change is needed in this PR. A later PR in the stack that changes `subschemas` (for example, the array walking in #10) has to remember to update `_expand_refs` too.

### Not a finding (pre-existing, for the record)
- `{"$ref": "#/properties/a/const/b"}` where `const` is a string fails with `TypeError: string indices must be integers` (in `resolve_path`, `ref_resolver.py:49`). The same happens on master and the parent, so it isn't caused by this PR. A `JsonSchemaDefinitionException` would be the sensible failure.
- Row C5 (2019-09 `dependentSchemas` with a relative `$ref` under a nested `$id`) accepts data that `jsonschema` rejects. The same happens on master, the parent and the branch.
- An unknown keyword holding `{"$ref": "#/nope"}` still fails compile in `_expand_refs` (F2). This is the unknown-keyword decision deferred in the issue, and it is unchanged.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | All issue repros fixed and they match `jsonschema` (A1–A7, B1, B2, F3). Maps with entries named like data keywords still resolve (C1–C6), in d4, d7 and 2019. |
| 2 | Completeness | OK | `const`/`enum`/`default`/`examples` are the only standard keywords whose values can be arbitrary JSON objects. The rest are strings, numbers, bools or string arrays, or are schemas. `$vocabulary` maps URIs to booleans and is harmless. Draft-04 `id` in `default` is fixed (B1). Unknown keywords are deliberately unchanged. |
| 3 | Consistency | Finding 3 | Rules are duplicated in `_expand_refs`, which still descends into lists (pre-existing). |
| 4 | Robustness | OK | `ValueError` from `http://[bad` in `default` is gone (A6). Pointers into `enum/0` and `default` still work (E1–E4, E6). |
| 5 | Reliability | OK | The depth limit still raises `JsonSchemaDefinitionException` at the same depth as on the parent: properties nested 260 deep and `not` nested 600 deep give the same results on both. Map entries still count +2. |
| 6 | Security | Finding 2 | No new code-injection surface: the data value goes through `repr_default` as before, and `compile_to_code` with `{'k': '{a}'}` in `default` works. The new remote-fetch cases are documented in the PR body only. |
| 7 | Performance | OK | Compiling a schema with 200 definitions × 30 properties three times took 2.59–2.64 s on the parent and 2.59–3.07 s on the branch, which is noise. `walk` now also skips data subtrees. |
| 8 | Maintainability | OK / Finding 3 | Small generator, named constants, comment cross-reference. |
| 9 | Readability | OK | The loop in `_expand_refs` is clearer than the nested conditional proposed in the issue. |
| 10 | Testability | OK | The new tests are direct integration tests with no network access needed. |
| 11 | Test coverage | OK | Mutations: removing map handling in `walk` fails 4 tests; in `_expand_refs`, 2 tests; removing the data-keyword skip in `_expand_refs`, 8 tests. 14 of the 18 new tests fail on the parent; the 4 `test_property_named_like_data_keyword_is_schema` cases pass on the parent, as the PR says. Depth counting (`yield sub, 2` changed to `1`) isn't covered by any test, which is acceptable. |
| 12 | Compatibility | Finding 1, Finding 2 | The edge behaviour changes are listed in the PR "Decisions". |
| 13 | Architecture | OK | Keeps one traversal for all drafts, which is a reasonable trade-off and is documented. |
| 14 | Integration | OK | Doesn't depend on #8. Full suite passes on the branch. |
| 15 | Data integrity | OK | `use_default=True` now inserts `{"$ref": "#/definitions/x"}` unchanged (A5). The schema's data values are no longer mutated by `walk`. |
| 16 | Usability | OK | The error message now shows the real `const` value: `must be same as const definition: {'$ref': '#/definitions/x'}`; it used to show the resolved `{'type': 'string'}` (F1). |
| 17 | Accessibility | N/A | Library; error-message clarity is covered under 16. |
| 18 | Observability | N/A | |
| 19 | Documentation | Finding 2 (nit part) | The CHANGELOG line is accurate but doesn't mention the dropped `$id` registrations. The `subschemas` docstring and constant comments are fine. |
| 20 | Regression | OK | Code is unchanged for 925 of 931 suite schemas (d4, d7, 2019-09); only the 3 `id.json` schemas and the 3 `ref.json` "naive replacement" `enum` schemas differ, by an error-definition-only change. XFAIL/XPASS diff vs. parent is limited to `id.json`. |

## Verification log

Scripts are in `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-9/`: `adv.py` (output in `adv.out`), `depth.py`, `codes.py`, and `*.rx` (XFAIL/XPASS lists).

- Full suite, parent `wt-unique-validation-function-names`: `4776 passed, 12 skipped, 415 xfailed, 970 xpassed`.
- Full suite, branch `wt-data-keyword-values`: `4814 passed, 12 skipped, 411 xfailed, 954 xpassed`.
- `-k id.json` in `tests/json_schema`: the parent gives `21 passed, 4 xfailed, 16 xpassed`, and the 4 XFAILs are "match $ref to id/$id" in d4, d6, d7 and 2019. The branch gives `41 passed`, with no xfail or xpass.
- XFAIL/XPASS diff, parent vs. branch, over `tests/json_schema`: only `id.json` lines removed, nothing added. `unknownKeyword.json` still has 6 XFAIL and 3 XPASS cases, which is expected and out of scope.
- The branch's new tests on the parent: `14 failed, 4 passed`. The 4 passing are `test_property_named_like_data_keyword_is_schema[*]`, as the PR states.
- Mutation runs on a copy (`pr-9/mut`), `tests/test_integration.py`: M1 (no map handling in `walk`) gives 4 failed; M2 (no map handling in `_expand_refs`) gives 2 failed; M3 (no data skip in `_expand_refs`) gives 8 failed; M4 (map depth +1 instead of +2) passes everything.
- `adv.py` on master, parent and branch, with both `fast_fail` settings and `jsonschema` as the oracle: see the rows quoted above. Master and parent are identical everywhere.
- `depth.py`: identical results on parent and branch. Nesting 240 deep gives `IndentationError` from Python (pre-existing); `not` nested 260 deep gives `RecursionError` (pre-existing); 600 deep gives `JsonSchemaDefinitionException`. `compile_to_code` with a `$ref` in `const`/`default` works on the branch, and on the parent fails with `Unresolvable ref: definitions`.
- `codes.py`: 931 suite schemas compiled with `compile_to_code`; 6 differ, as listed in checklist row 20.
- `pylint fastjsonschema`: same messages on parent and branch, none in the changed code (9.91/10).
