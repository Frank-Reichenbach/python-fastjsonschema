# PR #16 / Issue #15: Leave the $ref values of the schema unchanged

Branch `origin/fix/keep-schema-unchanged` (c4840e2), parent `fix/urn-id-local-refs` (77b3985). One commit: CHANGELOG, `generator.py` (2 lines), `ref_resolver.py` (+`_resolved_refs`, `get_ref()`), `tests/test_integration.py`.

Scratch scripts: `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-16/` (`gen.py`, `cmp.py`, `shapes.py`, `issue.py`, `relative.py`, `registry.py`, `registry_silent.py`, `store.py`, `twice.py`, `definition.py`, `perf.py`).

## Verdict

**Approve with nits.** The change is small and does what it says. The resolver keeps a side table keyed by `id()` and pins the node, so within one resolver it has the same identity semantics as the old in-place rewrite. After `compile()` and `compile_to_code()`, all 1637 official-suite schemas and 17 adversarial shapes compare equal to their deep copies (the parent mutated 87 suite schemas). The parent mutated no remotes, and neither does the branch. Across the whole suite, the generated code differs from the parent's only in `definition=` literals: 12 of 1204 schemas for the four tested drafts, as the PR claims (15 of 1637 when 2020-12 is included). There is no performance cost. One behaviour change is not documented. When a handler serves an object that was compiled earlier, the parent's rewrite used to mask the nested-`$id` bug in handler-returned schemas (issue #5). Without the rewrite, that case now silently accepts invalid data until #11 lands (Finding 1). It is minor because it only lasts until #11 in a stack merged in fixed order, and on the parent it already depended on compile order. It should still be named in the PR's Limitations, or #11 should go into the same release.

## Issue review

Accurate. Reproduced on master (4999d6b) and the parent with the issue's script. Both print `one after compile(): {'$ref': 'http://example.com/one.json#/definitions/x'}` and `two: RuntimeError handler called with http://example.com/one.json`. The second bullet (compiling again after the `$id` changed) also reproduces: `RuntimeError handler called with http://example.com/v1.json`. The cited lines are correct: `ref_resolver.py` L206–209 does the `urljoin` write-back, `generator.py` L227 is `in_scope(self._definition['$ref'])`, and L332 is `resolving(definition["$ref"])`. The Draft-07 §8.2 citation fits. `jsonschema` as an oracle agrees with the expected output (`two` is valid for `{'p': 'a'}` and invalid for `{'p': 1}`).

The third bullet (a relative base is resolved again) holds, but only for a **nested** relative `$id`. With `{'properties': {'p': {'$id': 'schemas/main.json', ...}}}`, the first compile works and the second raises `ValueError: unknown url type: 'schemas/schemas/main.json'`. A **root** relative `$id: schemas/main.json` already fails on the first compile on master, the parent and the branch. That is the separate relative-`$id` bug that #12/#7 addresses. The issue's wording ("such as `schemas/main.json`") reads as if the root case worked once, so it is slightly imprecise. Not verified on 2.21.2 (no worktree).

## Findings

### 1. minor: handler-served objects that were compiled earlier lose the rewritten URIs, so #5 now surfaces silently
Areas: Regression, Correctness, Data integrity. Location: `fastjsonschema/ref_resolver.py` (`_ensure_walked` → `walk(..., rewrite_refs=False)`, unchanged) together with the removed write-back in `walk`.

A common setup is a registry of schemas, each compiled, with a handler that returns the registry objects. On the parent, compiling `n.json` first rewrote its nested-`$id` refs to absolute URIs inside the shared object. A later schema that reaches `n.json` through the handler then generated correct code. On the branch, handler-returned documents are walked with `rewrite_refs=False` as before, so they get no `_resolved_refs` entries. Their raw `#/definitions/k` under the nested `$id: sub/m.json` resolves against `n.json` instead. That is issue #5, which the rewrite used to hide in this order. If `n.json` itself has a `definitions/k`, the wrong target is picked silently.

`registry_silent.py` (`n.json` has `definitions.k = string`, its nested `sub/m.json` has `definitions.k = integer`, and `b.json` = `{'$ref': 'http://ex/n.json'}`; handler `lambda uri: registry[uri]`; compile `n` first, then `b`; data `{'m': {'k': 'x'}}`):

```
== urn-id-local-refs n-first
http://ex/n.json rejects invalid
http://ex/b.json rejects invalid
== keep-schema-unchanged n-first
http://ex/n.json rejects invalid
http://ex/b.json ACCEPTS invalid
== handler-schema-nested-id n-first     (#11)
http://ex/b.json rejects invalid
```

The variant without a root `definitions/k` (`registry.py`) raises `JsonSchemaDefinitionException: Unresolvable ref: definitions` on the branch. On the parent this happened only in `b-first` order. The same thing shows with the internal API and a shared default `store` (`store.py`): on the parent, `RefResolver` objects that share the default `{}` store saw the previous resolver's rewritten objects. On the branch they behave like a fresh store, which is more consistent but no longer correct by accident. It is fixed again at #11 and at the stack tip.

Suggested fix: add a line about this to the PR's "Limitations" (the parent was order-dependent, the branch fails consistently until #11), or make sure #11 is in the same release. No code change is needed here if the stack merges as planned.

### 2. nit: "generated functions don't change otherwise" and "first base URI wins, as it did" are not exact for relative bases
Areas: Documentation (PR body), Consistency. Location: PR body "Decisions", "Limitations"; `ref_resolver.py` comment `# The first base URI wins ...`.

The old behaviour matched "first wins" only when the first resolved value was absolute. With a relative first resolution, the parent's second walk resolved the rewritten value again. `twice.py`: the same `{'$ref': '#/definitions/x'}` object sits under `$id: a/x.json` and under `$id: b/y.json`, with no root `$id`:

```
== urn-id-local-refs
'' EXC ValueError unknown url type: 'b/a/x.json'
== keep-schema-unchanged
'' a.v=1, b.v=None, b.v=1 -> ['valid', 'invalid', 'valid']   (same as the http:// variant on both)
jsonschema oracle: [True, True, False]
```

The branch's behaviour is better and matches the documented limitation for absolute ids. Only the claim that the generated code is otherwise unchanged is slightly too strong. Suggested fix: add "(for absolute base URIs)" to the PR text.

### 3. nit: tests do not pin the visible `definition` change or the relative-base case of the issue
Areas: Test coverage. Location: `tests/test_integration.py`.

The CHANGELOG announces a user-visible change: a `$ref` inside `JsonSchemaValueException.definition` is now shown as written. `definition.py` shows it, with an error at the root for data `1` on a schema with `$id: http://ex.com/r.json` and `properties.a → #/definitions/x`, where `x` contains `y: {'$ref': '#/definitions/y'}`:

```
parent: ... 'properties': {'a': {'type': 'object', 'properties': {'y': {'$ref': 'http://ex.com/r.json#/definitions/y'}}}, ...
branch: ... 'properties': {'a': {'type': 'object', 'properties': {'y': {'$ref': '#/definitions/y'}}}, ...
```

No test asserts either value (the full suite passes on both). The third bullet of #15, compiling a nested relative `$id` twice (`relative.py`), has no test either. On the branch it passes twice; on the parent the second compile raises `ValueError`. Both would be one-line additions next to `test_schema_compiled_again_after_its_id_changed`.

Observation, no action needed: since the `deepcopy` was removed in `test_local_ref_in_subschema_with_urn_id`, the shared `URN_NODE` guards against regressions only indirectly. On the parent, the failure shows up in the *next* test (`test_local_ref_in_subschema_with_other_id_outside_uses_relative`, 6 cases, `URLError: unknown url type: urn`), which deep-copies the already mutated constant. The new explicit tests cover the behaviour directly, so this is fine.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | Suite: code differs from parent only in `definition=` (30 pairs, 15 schemas, 0 other diffs); 17 adversarial shapes: 0 code diffs |
| 2 | Completeness | OK | Both read sites (`generate_ref`, `_expand_refs`) switched; no other reader of `$ref` in drafts (grep) |
| 3 | Consistency | Finding 2 | "First wins" mirrors the old identity semantics; the claim is inexact only for relative bases |
| 4 | Robustness | OK | Non-string `$ref` falls back to the raw value, as before (`AttributeError` in `join_uri` on both, pre-existing); `$ref: ''`, booleans, braces/quotes/`~1` keys all fine |
| 5 | Reliability | OK | Recompiling is now deterministic (`stable`=True for all suite schemas); no more mutation of shared input across threads or compilations |
| 6 | Security | OK | No new values are interpolated into code; `get_ref` only feeds `in_scope`/`resolving`. Issue example: no unintended handler call (download) anymore |
| 7 | Performance | OK | 2000-ref schema: walk 5.0 ms vs 5.1 ms, `compile_to_code` 32.2 ms vs 32.2 ms (parent vs branch, best of 5); generated validators are identical |
| 8 | Maintainability | OK | Small and well commented; the pinned node in the tuple prevents `id()` reuse; extra `too-many-instance-attributes` disable only |
| 9 | Readability | OK | `get_ref` docstring and the `walk` docstring updated |
| 10 | Testability | OK | `get_ref()` makes the resolved URI checkable without compiling (used in the renamed test) |
| 11 | Test coverage | Finding 3 | 3 new tests × 2 params, all fail on the parent; `definition` change and relative-base recompile not pinned |
| 12 | Compatibility | Finding 1 | Visible `definition` change is documented; the order-dependent handler case regresses until #11 |
| 13 | Architecture | OK | Table instead of deepcopy is the right call (keeps the identity semantics, no copy cost); matches the fix proposed in the issue |
| 14 | Integration | OK | `compile()`/`compile_to_code()` use `store={}` per call, so the side table and store never outlive a compilation; the stack tip passes |
| 15 | Data integrity | OK / Finding 1 | Input is no longer mutated (0/1637 suite, 0/17 shapes, remotes untouched); see Finding 1 for the silent case |
| 16 | Usability | OK | Reusing fragments and recompiling under a new `$id` now work without `copy.deepcopy` |
| 17 | Accessibility | N/A | Error messages unchanged; `definition` now shows refs as written (arguably clearer, but less informative under nested `$id`; opinion) |
| 18 | Observability | N/A | — |
| 19 | Documentation | OK / Finding 2 | CHANGELOG line present and accurate; PR "12 of 1204" claim verified exactly; `compile()` docstring could say that input is not modified (opinion) |
| 20 | Regression | OK / Finding 1 | Full suite: same xfail/xpass counts as parent (411/954); only the transient #5 exposure |

## Verification log

- Branch full suite: `4847 passed, 12 skipped, 411 xfailed, 954 xpassed`. Parent: `4841 passed, 12 skipped, 411 xfailed, 954 xpassed`. The difference of +6 is the 3 new tests × 2 params; xfail/xpass counts are unchanged, which fits a PR that claims no suite changes.
- pylint: 9.91/10 on both; the sorted message lists are identical (diff empty).
- Branch's `tests/test_integration.py` against a copy of the parent code (`pr-16/parentcopy`): 13 failed. They are `test_compile_leaves_schema_unchanged[False/True]`, `test_object_shared_by_schemas_with_different_ids[True/False]`, `test_schema_compiled_again_after_its_id_changed[True/False]`, `test_local_ref_in_subschema_with_http_id_is_resolved_by_urljoin` (no `get_ref`), and 6× `test_local_ref_in_subschema_with_other_id_outside_uses_relative` (the mutated `URN_NODE` from the previous test; they pass in isolation).
- `gen.py` over all suite schemas (draft4/6/7/2019-09 with `$schema`, 2020-12 without; `compile_to_code` with ff True/False, then `compile`, then a deep compare):
  - parent: `1637 schemas; mutated: 87 unstable: 0 remotes mutated: False`
  - branch: `1637 schemas; mutated: 0 unstable: 0 remotes mutated: False`
  - master: `1637 schemas; mutated: 71 ...`
  - `cmp.py` parent vs branch: `differing pairs: 30 distinct schemas: 15 {'definition_only': 30, 'other': 0}`, i.e. `ref.json`/`refRemote.json` cases. Without 2020-12: 12 of 1204, matching the PR body.
- `shapes.py` (bool root/nested, `$ref` siblings, recursion, urn root/nested, draft-04 `id`, nested http ids, braces/quotes/`~1` keys, refs in `const`/`enum`/`default`, every applicator keyword, 2019-09 `$defs`/`dependentSchemas`/`unevaluatedProperties`, remote http/urn, same object twice, object shared between walked and array positions, non-string and empty `$ref`): branch mutated 0/17, parent 9/17; generated code identical in all 34 (schema, fast_fail) pairs.
- `issue.py`: master and parent reproduce all claims; branch prints `{'$ref': '#/definitions/x'}`, `two: {'p': 'a'}`, `id changed: {'p': 1}`.
- `relative.py` (nested relative `$id`, compiled twice): parent `compile 1 ValueError unknown url type: 'schemas/schemas/main.json'`; branch `rejects invalid` both times.
- `registry*.py`, `store.py`: see Finding 1 (parent / branch / #11 / tip).
- `perf.py`: see checklist item 7.
