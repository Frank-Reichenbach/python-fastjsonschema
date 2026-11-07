# PR #11 / Issue #5: Walk schemas loaded through handlers like the main schema

Branch `origin/fix/handler-schema-nested-id` (commit `5fd4ad5`), parent `fix/relative-id-resolved-once` (`a1e7dc3`).
Scratch scripts: `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-11/` (`$P` below). `$S` is the scratchpad.

## Verdict

**Approve with nits.** The core fix is correct and well reasoned. Once #16 (no in-place rewrite) and #12 (generator uses the resolved refs as they are) are in place, the `rewrite_refs=False` special case is unnecessary. Removing it restores the 2.22.0–2.22.2 results for the issue's repro without bringing back #218. I verified the repro on 2.21.2, 2.22.0, 2.22.2, 2.22.3, master, the parent and the branch. The 9 claimed "fails on master" tests fail on the parent and on master and pass on the branch. The deep-copy claim also holds: without the copy, exactly the 4 `test_objects_shared_by_handler_loaded_schemas` cases fail. Suite outcomes are identical to the parent's, and lint is unchanged. I found no blocker or major issue. The remaining findings are all minor or nits:
- The deep copy bypasses the walk's depth guard (Finding 1), which is cheap to fix in this PR.
- `cache=False` is now much slower (Finding 2). This is documented, but worth a decision.
- Store entries the resolver did not load itself are walked uncopied and with their `$id` applied again (Finding 3).
- The CHANGELOG and tests have gaps: a behavior change and the main-schema `ValueError` case have no test, and one line is worded too narrowly.

## Issue review

The issue is accurate.

- **Regression in 2.22.3: confirmed.** `c9a311e` is an ancestor of `v2.22.3` but not of `v2.22.2` (`git merge-base --is-ancestor`). `$P/repro.py` gives these results for `{"p":{"v":1}}` and `{"p":{"v":"a"}}`, loaded as `http://…`, `schemas/main.json` and `file:schemas/main.json`:
  - 2.21.2: `['data.p.v must be string', 'valid']` (wrong; it never walked loaded docs, as the issue says)
  - 2.22.0 and 2.22.2: `['valid', 'data.p.v must be integer']` (correct)
  - 2.22.3, master and the parent: `['data.p.v must be string', 'valid']` (wrong)
  - this branch: `['valid', 'data.p.v must be integer']` for all three URIs
- **The same schema embedded is correct on master** (`$P/embedded.py` → `{'p': {'v': 1}}`).
- **The cause section matches the code.** In 2.22.2, `_ensure_walked` at lines 162–167 calls `self.walk(schema)` and has no `rewrite_refs` flag. `c9a311e` added `rewrite_refs=False`.
- **The `cache=False` claim ("already fails on 2.22.2") is confirmed.** `test_handler_loaded_schema_without_cache` fails on 2.22.2 with `data.a.v must be string`.
- **The spec citation is right.** Draft-07 §8.2 says `$id` sets the base URI, with no distinction between embedded and loaded schemas.
- **One subtlety the issue doesn't cover: the relative root `$id`.** 2.22.2 was also wrong there (`dir/dir/dir/child.json`, see Finding 4), so the "regression in 2.22.3" label only fits the nested-`$id` part.

## Findings

### 1. Minor: deep copy of handler results bypasses `MAX_SCHEMA_WALK_DEPTH`, giving a raw `RecursionError`
Areas: Robustness, Security, Regression. Location: `fastjsonschema/ref_resolver.py:217`.

`copy.deepcopy(resolve_remote(...))` recurses before `walk()` can apply its depth guard. The guard was added in `65dcd12` and is tested in `tests/test_security.py:112`. A deeply nested loaded document now raises `RecursionError` from `copy.py` instead of `JsonSchemaDefinitionException('Schema is too deeply nested …')`. The main schema still gets the proper exception.

Repro `$P/deep.py` (an `items` chain of depth n, CPython 3.14, recursion limit 1000):
```
parent:  n=600 handler: JSDefinitionException: Schema is too deeply nested   n=5000 handler: JSDefinitionException
branch:  n=600 handler: RecursionError                                       n=5000 handler: RecursionError
         n=600 main:    JSDefinitionException (unchanged)
```
Depths of 250–450 already hit `RecursionError` in the generator on the parent, so that part is pre-existing. The regression is that the guard no longer protects remote documents, which come from the most likely untrusted source.

Suggested fix: copy with a depth-bounded JSON copy that raises `JsonSchemaDefinitionException` past `MAX_SCHEMA_WALK_DEPTH`. Alternatively, catch `RecursionError` around the `deepcopy` and re-raise it as the same definition exception. Add a handler variant to `test_deeply_nested_schema_raises_definition_exception`.

### 2. Minor: `cache=False` now deep-copies and re-walks the whole remote document on every `resolving()`
Areas: Performance. Location: `ref_resolver.py:217, 236-239`.

Each `resolving()` into a remote URI with `cache=False` now loads, deep-copies and walks the whole document. That includes one call per generated function and one per `_expand_refs` call for error `definition`s. The parent walked each URI once. All copies are also kept alive in `_walked` for the resolver's lifetime. The new docstring sentence documents this, but the cost is large.

Repro `$P/perf.py` (200 refs into one handler document with 2000 definitions; min of 3 runs):
```
parent: cache=True 0.019s   cache=False 0.019s   (1000 refs, cache=True: 0.081s)
branch: cache=True 0.023s   cache=False 1.752s   (1000 refs, cache=True: 0.089s)
```
That is about 90x slower for `cache=False`. With `cache=True` the overhead is about 10% for 1000 refs, which is fine. `compile()` always uses `cache=True`, so only users of `RefResolver` directly are affected.

Suggested fix (optional): memoize the loaded copy per normalized URI in a resolver-private dict when `cache=False`. Each URI is then loaded, copied and walked once per resolver, and the shared `store` stays unpopulated. This still fixes the 2.22.2 "copies skipped" bug, because there would be only one copy. `test_handler_loaded_schema_without_cache` would need `loaded == [doc]` instead of two loads. Otherwise, keep the current behavior and accept it.

### 3. Minor: store entries the resolver didn't load are walked uncopied, with the `$id` applied again
Areas: Correctness, Data integrity, Integration. Location: `ref_resolver.py:210-211, 225, 236-239`.

The copy only protects handler results. A `store` entry that this resolver did not create is walked in place, at `document_uri` and with `id_applied=False`. There are two cases:
- **Case (a): objects shared between pre-populated store entries.** The first base URI wins, as the PR describes for handlers. On the parent this validated correctly, because refs were resolved at generation time against each document.
- **Case (b): a store shared between resolvers, including the mutable default `store={}` of `RefResolver.__init__`/`from_schema`.** A nested node registered under a relative `$id` gets that `$id` applied again when the second resolver reaches it through its store key.

Neither case affects `compile()`/`validate()`, which pass `store={}` (`__init__.py:361`).

Repro (a), `$P/store_shared.py`: `store={'http://e/a/doc.json': {'properties':{'c': ref}}, 'http://e/b/doc.json': {'properties':{'c': ref}}, 'http://e/a/defs.json': string, 'http://e/b/defs.json': integer}`, validating `{'a': {'c': 'x'}, 'b': {'c': 1}}`:
```
parent: valid
branch: data.a.c must be integer
```
Repro (b), `$P/store_cross2.py` and `$P/store_cross3.py` (the latter uses the default store). `DOC = {'$id':'http://e/doc.json','properties':{'n':{'$id':'sub/n.json','properties':{'v':{'$ref':'other.json'}}}}}`. The first resolver compiles `{'$ref':'http://e/doc.json'}`, then a second resolver on the same store compiles `{'$ref':'http://e/sub/n.json'}`:
```
parent: first ['http://e/doc.json', 'http://e/other.json']      second ['http://e/sub/other.json']
branch: first ['http://e/doc.json', 'http://e/sub/other.json']  second ['http://e/sub/sub/other.json']
```
On the branch the first compile is now right and the second one wrong. On the parent it was the other way round, and the second was only right by coincidence.

Suggested fix: this is mostly an edge of the direct `RefResolver` API, so it could be a follow-up issue. Options:
- Document that a `store` must not be shared between resolvers, and change the default `store={}` to `None` (a pre-existing trap that this PR makes visible).
- Or deep-copy store objects that are not in `self._walked` into a resolver-private memo. Case (b) also needs the resolver to know that a store key is already the resolved `$id` (`id_applied=True`).

### 4. Minor: relative root `$id` equal to the retrieval path is a behavior change vs. 2.22.3, and the CHANGELOG doesn't flag it
Areas: Compatibility, Documentation. Location: `CHANGELOG.txt:12`, `tests/test_integration.py:833-850`.

A document loaded as `dir/main.json` with `"$id": "dir/main.json"` now resolves `child.json` to `dir/dir/child.json`. This is RFC 3986 §5.1-correct: the relative `$id` is resolved against the retrieval URI. But a repository-style handler such as `repo.__getitem__` (the #218 pattern), whose documents carry an `$id` equal to their repo key, now fails with `KeyError`. On 2.22.3 it worked.

`$P/relid.py` (loads recorded for `uri`/`$id`):
```
                 dir/main.json + $id dir/main.json     http://h/dir/main.json + $id dir/main.json
2.22.2:          dir/dir/dir/child.json                http://h/dir/dir/child.json
2.22.3/parent:   dir/child.json                        http://h/dir/child.json
branch:          dir/dir/child.json                    http://h/dir/dir/child.json
```
`$id: main.json` under `schemas/main.json` is unchanged: `schemas/child.json` everywhere except 2.22.2. As an oracle, `jsonschema`/`referencing` (`$P/oracle_relid.py`) ignores the root `$id` of a retrieved resource and loads `http://h/dir/child.json`. So the branch follows the spec, but differs from 2.22.3 and from `jsonschema`. I don't take that as evidence against the PR: `jsonschema` also ignores an absolute root `$id` (`$P/oracle_absid.py` loads `http://a/child.json`), which is clearly against §8.2.

Suggested fix: keep the behavior, since the test encodes it on purpose. Add a "Changed …" CHANGELOG line along these lines: "a relative `$id` at the root of a schema loaded through `handlers` is now resolved against the URI it was loaded from, so `"$id": "dir/main.json"` in `dir/main.json` makes refs resolve under `dir/dir/`". Users can then find out why their repository handler now raises `KeyError`.

### 5. Nit: CHANGELOG line 12 is too narrow, and one root-`$id` case has no test
Areas: Documentation, Test coverage. Location: `CHANGELOG.txt:12`.

"…and the `$id` of that schema if it is relative (regression in 2.22.3)". An absolute root `$id` that differs from the retrieval URI was ignored too, and this PR fixes it. With `$P/absid.py` (loaded from `http://a/x.json`, `"$id": "http://b/y.json"`, `$ref: child.json`), the parent loads `http://a/child.json` and the branch and 2.22.2 load `http://b/child.json`.

The "regression in 2.22.3" label also covers the relative case, which 2.22.2 got wrong as well (Finding 4).

Suggested fix: reword to "…and the `$id` of that schema when it differs from the URI it was loaded from". Add a parameter to `test_root_id_of_handler_loaded_schema_is_resolved_against_its_uri`: `('http://example.com/a/main.json', 'http://example.org/main.json', 'http://example.org/child.json')`.

### 6. Minor: the third CHANGELOG line (`ValueError` in an unknown keyword) has no test for the case it describes
Areas: Test coverage, Documentation. Location: `CHANGELOG.txt:14`, `tests/test_integration.py:925-937`.

The change is in scope. Without the `contextlib.suppress(ValueError)`, removing `rewrite_refs=False` would make loaded documents with such a `$ref` fail again, as on 2.22.2: `test_invalid_uri_in_unknown_keyword_of_handler_loaded_schema` fails on 2.22.2. Applying the suppression to the main schema too is the simplest consistent rule.

But the CHANGELOG describes the main-schema case ("`compile()` failing … in a schema with an `$id`"). That case fails on 2.22.2, master and the parent, and passes on the branch (`$P/baduri.py`, `$P/misc.py`):
```
compile({'$id':'http://e/s.json','x-note':{'$ref':'http://[bad'}})({})
2.22.2 / master / parent: ValueError Invalid IPv6 URL      branch: {}
```
No test covers it. The handler-loaded test that was added passes on master and the parent. `test_used_ref_that_is_not_a_valid_uri_fails` uses a schema without `$id`, where `urljoin('', ref)` never parses. So it doesn't exercise the new path, where `walk` suppresses the error and `generate_ref` must raise it. That path does raise; I verified it with `$id`, with `fast_fail` on and off, and in a handler document.

Suggested fix: parametrize both tests over `{}` and `{'$id': 'http://example.com/s.json'}` at the root.

### 7. Nit: handlers returning a non-deep-copyable mapping now fail
Areas: Compatibility. Location: `ref_resolver.py:217`.

`handlers={'http': lambda u: types.MappingProxyType({'type': 'integer'})}` worked on the parent. On the branch it raises `TypeError: cannot pickle 'mappingproxy' object` (`$P/misc.py`). `OrderedDict`, `bool` and JSON results are fine. Lists and `None` fail on both, as before.

Suggested fix: if the depth-bounded copy from Finding 1 is a JSON copy (`dict(...)`/`list(...)` recursion), it fixes this too. Otherwise, document that handlers return JSON values.

### 8. Nit: test comment still says "rewrites"
Areas: Readability. Location: `tests/test_integration.py:884`.

"walk() rewrites the $ref to file:///node.json#…". Since #16, `walk` resolves refs; it doesn't rewrite them. Suggested wording: "walk() resolves the $ref to …".

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK / Finding 3 | Repro and all new tests pass on the branch. A differing absolute root `$id`, a relative nested `$id`, a JSON pointer into a nested-`$id` subtree (`$P/ptr.py` → `http://e/sub/other.json`) and mutual recursion between 2 remote docs with nested ids (`$P/recur.py`; the parent crashes with `Unresolvable ref`) all give correct results. Store edge cases are in Finding 3. |
| 2 | Completeness | OK | All handler paths (`cache` True/False, `fast_fail` on/off, `compile_to_code`) are covered by the change. |
| 3 | Consistency | OK | One walk rule for the main and loaded schemas; the special case is gone. |
| 4 | Robustness | Finding 1, 7 | Depth guard bypassed; non-copyable mappings. Booleans from handlers work (`$P/misc.py`). |
| 5 | Reliability | OK | `_walked` holds the objects, so `id()` values can't be reused. Within one resolver, every store entry it creates is in `_walked`, so nothing is skipped or walked twice. Across resolvers, see Finding 3. |
| 6 | Security | Finding 1 | No new interpolation into generated code. The depth guard no longer covers remote documents. |
| 7 | Performance | Finding 2 | `cache=False` is about 90x slower in my benchmark; `cache=True` is about 10% slower with 1000 refs. |
| 8 | Maintainability | OK | Simpler: `rewrite_refs` and the URI-keyed walk tracking are removed. |
| 9 | Readability | Finding 8 | Comments explain the copy and `_walked`. |
| 10 | Testability | OK | Tests use recording handlers and assert the loaded URIs. |
| 11 | Test coverage | Finding 5, 6 | No test for a differing absolute root `$id` or for the main schema with `$id` plus an invalid URI. |
| 12 | Compatibility | Finding 4, 7 | Relative root `$id` behavior change; handler results are now copied, so `resolver.store` holds copies. |
| 13 | Architecture | OK | Copy per load fits #16's "schema unchanged" model and is simpler than keying refs by document. |
| 14 | Integration | OK / Finding 3 | #218 pattern compiled twice works; a loaded dict compiles directly afterwards. |
| 15 | Data integrity | OK | Handler results are unchanged after compile (`DOC unchanged True`). |
| 16 | Usability | OK | Error for a used invalid `$ref` is still a raw `ValueError` (pre-existing). |
| 17 | Accessibility | N/A | Library. Error messages of `JsonSchemaValueException` for loaded docs are correct (`('data.p.v', 'type', {'type': 'integer'})`). |
| 18 | Observability | N/A | |
| 19 | Documentation | Finding 4, 5, 6 | Docstring sentence on `cache=False` is accurate. Two CHANGELOG wording or coverage gaps, and one behavior change is not called out. |
| 20 | Regression | OK / Finding 1 | Fixes the 2.22.3 regression. `test_relative_ref_in_remote_schema_is_resolved_once` (#218) still passes. Suite outcomes are identical to the parent's. |

## Verification log

- Full suite: branch `5062 passed, 12 skipped, 393 xfailed, 824 xpassed`; parent `5042 passed, 12 skipped, 393 xfailed, 824 xpassed`. The difference is the 20 new test items.
- `tests/json_schema -rxXf`: the sorted XPASS/XFAIL/FAILED lists are byte-identical between the parent and the branch (1217 lines each). No xfail-list change is needed; this matches the PR's "no outcome changes".
- Lint: `pylint fastjsonschema` gives the same 16 messages on the parent and the branch (diff ignoring line numbers is empty); 9.91/10.
- New tests run against other code (the branch's `test_integration.py` plus `conftest.py` copied to `$P/t`):
  - Parent: 9 fail, exactly the claimed ones: 6× `uses_id_of_its_subschema`, 2× `root_id_…`, and `without_cache`.
  - Master: the same 9, plus 11 failures from earlier stack PRs.
  - 2.22.2: fails `without_cache`, `relative_ref_in_handler_loaded_schema_is_resolved_once`, `ref_under_id_without_host…`, `invalid_uri_in_unknown_keyword…`, the `dir/main.json` param, and the "pass on master" guards (`…compiled_twice`, `…compiled_directly_afterwards`, `objects_shared…`). This matches the PR body.
  - Branch: all 35 selected pass.
- Copy necessity: with `copy.deepcopy` monkeypatched to the identity function (`$P/t/conftest.py`, `NOCOPY=1`), exactly the 4 `test_objects_shared_by_handler_loaded_schemas` cases fail. The PR's claim is confirmed.
- Version and ancestry checks: `git merge-base --is-ancestor c9a311e v2.22.3` holds and `… v2.22.2` doesn't. Tag sources were extracted with `git archive` into `$P/v2.21.2`, `$P/v2.22.0`, `$P/v2.22.2` and `$P/v2.22.3`; no worktrees were added.
- Scripts in `$P`: `repro.py`, `relid.py`, `absid.py`, `oracle_relid.py`, `oracle_absid.py`, `recur.py`, `store_shared.py`, `store_cross.py`, `store_cross2.py`, `store_cross3.py`, `misc.py`, `deep.py`, `perf.py`, `ptr.py`, `baduri.py`, `embedded.py`. Outputs are quoted in the findings above.
