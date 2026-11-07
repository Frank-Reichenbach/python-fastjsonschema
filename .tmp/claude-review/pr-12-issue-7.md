# PR #12 / Issue #7: Resolve each URI once under a relative $id with a directory

## Verdict

**Approve with nits.** The commit (a1e7dc3, on top of `fix/walk-schema-arrays`) fixes every form of the double resolution that the issue describes, and every other relative-`$id` form I tried: `schemas/item.json`, `file:` and `FILE:`, a trailing `#`, a query, `../`, `./`, nested relative ids, the subschema self-ref that hung, and handler-loaded documents under a relative base. Results match `jsonschema` wherever it gives a usable answer. For absolute ids it changes nothing: `compile_to_code()` output is byte-identical to the parent for all 2428 schema and `fast_fail` combinations from the official suite and `tests/examples`. The suite's XFAIL/XPASS sets are unchanged, and so is lint. Every new test fails on the parent and passes on the branch. The only findings are about text (the PR body, the issue, and the CHANGELOG) and one internal-API signature nit.

## Issue review

- **Main repro:** reproduced exactly on master and the parent (`handler called with schemas/schemas/schemas/schemas/schemas/schemas/item.json`). Fixed on the branch: `{'count': 1} -> valid`, `{'count': 'a'} -> invalid: data.count must be integer`.
- **Further cases:** all three reproduce on master and the parent as stated (`a/b/a/b/.../other.json`, `compile() still running after 10 s`, `file:schemas/schemas/.../item.json`). On the branch they give `handler called with a/b/other.json` (the expected URI), `valid` and `valid`.
- **Cause analysis:** accurate for the code as it was. Each step maps to one change in the commit: the root `$id` applied twice (fixed by `base_uri_is_id`/`id_applied`), the generator re-resolving resolved URIs (fixed by `resolving(..., resolved=True)`), re-resolving walked refs (fixed by `is_resolved`), and re-walking a subschema with an `$id` (fixed by `_walked_uris.add` in `walk`).
- **Spec citations:** Draft-07 §8.1, §8.2, §8.2.1 and §8.3.2, and RFC 3986 §5.1 and §5.2.2–5.2.3, are used correctly. The issue says honestly that resolution against a relative base is fastjsonschema's own convention.
- **Stale parts (nit, Finding 2):**
  - The "Possible fix" section describes the pre-#16 design ("`walk` remembers which `$ref` values it rewrote").
  - The "Limitation" paragraph says compiling the same object twice still fails. With #16 underneath, it works, and `test_schema_with_relative_root_id_with_directory_compiled_twice` proves it.
  - The outputs are labelled `fastjsonschema 2.22.2`; master is now 2.22.3, with the same output.
- **Unverified:** the claims about older releases (2.13, 2.19.1, 2.21.2, 2.22.2) and real Python 3.10/3.11; none of those are installed. As a stand-in for 3.10/3.11 I loaded CPython 3.9's `urllib.parse`, which also turns `file:schemas/item.json` into `file:///schemas/item.json`. With it, all 134 tests in `tests/test_integration.py` pass on the branch.

## Findings

### 1. nit: the PR body says the commit "only needs #2"; it also needs #16
- **Area:** Documentation, Integration
- **Where:** PR body, first paragraph: "Of the earlier fixes, it only needs #2, because it changes the same calls in `in_scope` and `resolving`".
- **Problem:** `is_resolved` reads `self._resolved_refs`, and the generator hunks call `get_ref`. Both come from #16 (`keep-schema-unchanged`). The body later says "Builds on the new #16", so it contradicts itself.
- **Repro:**
  ```
  urn-id-local-refs      grep -c '_resolved_refs\|def get_ref' ref_resolver.py -> 0
  keep-schema-unchanged  -> 5
  git apply --check a1e7dc3.patch onto the tree of origin/fix/urn-id-local-refs:
    error: patch failed: fastjsonschema/generator.py:246
    error: patch failed: fastjsonschema/ref_resolver.py:155
  ```
- **Fix:** "Of the earlier fixes, it needs #2 and #16 (it uses `get_ref` and the `_resolved_refs` map from #16)."

### 2. nit: issue #7's "Possible fix" and "Limitation" sections describe the superseded design
- **Area:** Documentation
- **Where:** issue #7, "Possible fix" and the "Limitation" paragraph.
- **Problem:** Both describe `walk` rewriting `$ref` in place, and say that compiling the same object a second time fails. On this stack that is no longer true.
- **Repro:** `test_schema_with_relative_root_id_with_directory_compiled_twice[True|False]` passes on the branch.
- **Fix:** edit the issue. Point "Possible fix" at #16 + #12 and drop the Limitation, or mark it as fixed by #16. Optionally relabel the outputs with 2.22.3.

### 3. nit: the CHANGELOG line omits the worst symptom and the behavior change
- **Area:** Documentation, Usability
- **Where:** `CHANGELOG.txt:11`
- **Problem:** The line mentions `schemas/schemas/item.json`. Users who hit this saw one of three symptoms: a `ValueError: unknown url type` (or a handler call with a doubled URI), or `compile()` never returning for a subschema with such an `$id` that refers to itself. The hang is the symptom most worth finding in a changelog. The PR's "Behavior changes" section is also user-visible and not in the changelog: a nested relative `$id` is no longer registered a second time under the doubled URI, so a `$ref` to the doubled URI is now loaded through the handler.
- **Fix (suggestion):** "Fixed a relative `$id` with a directory, such as `schemas/item.json`, being applied more than once, so that refs below it resolved to `schemas/schemas/item.json` (or made `compile()` not return for a subschema with such an `$id` that refers to itself)".

### 4. nit: `resolved` changes the call contract of `in_scope`/`resolving` for overrides, and the new flags have three names
- **Area:** Compatibility, Consistency
- **Where:** `fastjsonschema/ref_resolver.py:184,196`; `generator.py:158,250,356`
- **Problem:** The generator now calls `resolving(uri, resolved=True)` and `in_scope(..., resolved=...)`. A `RefResolver` subclass that overrides either method with the old signature, and is passed to a `CodeGenerator*` via `resolver=`, now fails. `RefResolver` is not in `__all__`, not documented, and `compile()` takes no resolver, so the impact is small.
- **Repro** (`pr-12/subclass.py`):
  ```
  parent: 2 functions
  branch: TypeError MyResolver.resolving() got an unexpected keyword argument 'resolved'
  ```
- **Opinion:** one idea has three names: `base_uri_is_id` (constructor), `id_applied` (`walk`, keyword-only) and `resolved` (`in_scope`/`resolving`, positional-or-keyword). Making `resolved` keyword-only too (`*, resolved=False`) would match `walk` and keep the positional slot free. Not blocking.

### Out of scope (checked; not caused or made worse by this PR)
- **Root `$id` with a non-empty fragment** (`schemas/item.json#frag`, also `http://x/item.json#frag`): a local `$ref` still calls the handler with the un-fragmented URI. This happens on master and the parent too, also for absolute ids. The PR improves the relative case from `schemas/schemas/item.json` to `schemas/item.json`, the same as for absolute ids.
- **`$id` with dot segments** (`a/./item.json`, `http://x/a/./item.json`) and `$ref: "item.json"` to itself: the handler is called with the dot-free URI. This already happens for absolute ids on the parent, and `jsonschema` also fails. The PR brings relative ids to parity with absolute ones.
- **Handler-loaded documents with a nested `$id`** (#5): the parent and this branch give the same results (`['invalid','invalid','valid']`), and `fix/handler-schema-nested-id` (#11) fixes them. This PR doesn't make them worse.
- **For the #11 reviewer (unverified whether intended):** a handler-loaded `a/b/other.json` whose own root `$id` is `a/b/other.json`, containing `$ref: "third.json"`:
  - On this branch it loads `a/b/third.json`, which matches `jsonschema`.
  - On `fix/handler-schema-nested-id` it loads `a/b/a/b/third.json`, which follows RFC 3986 when the relative `$id` is resolved against the retrieval URI.
  - The same happens under an `http://h/...` base. Repro: `pr-12/remote_selfid.py`.

## Checklist

| # | Area | Result | Note |
|---|------|--------|------|
| 1 | Correctness | OK | All 9 relative-root forms, nested and `../` ids, handler docs, recursion and self-ref by name are correct in both modes and match `jsonschema` (battery below). |
| 2 | Completeness | OK | Covers all four causes listed in the issue (walk, `resolving`, `generate_ref`/`_expand_refs`, re-walk). The leftovers (fragment and dot-segment ids, #5) predate this PR and also affect absolute ids. |
| 3 | Consistency | Finding 4 | Three names for one flag; `resolved` is positional and `id_applied` keyword-only. |
| 4 | Robustness | OK | The former infinite loop is gone (`compile()` returns at once); empty base, `$ref` at the root next to `$id`, and bool schemas all work. |
| 5 | Reliability | OK | Deterministic. `is_resolved` relies on `id()`, which is safe because `_resolved_refs` holds the objects (#16). |
| 6 | Security | OK | No new values from the schema reach the generated code; function names still go through `get_scope_name` sanitising. |
| 7 | Performance | OK | One dict lookup per `$ref`. Draft-07 metaschema `compile_to_code`: 4.28 ms on the parent vs 3.92 ms on the branch (noise). |
| 8 | Maintainability | OK | Small, local change (+27/−8 in code); the docstrings explain each flag. |
| 9 | Readability | OK | Clear; `is_resolved` next to `get_ref` reads naturally. |
| 10 | Testability | OK | `RefResolver(..., store={})` is tested directly without touching the shared default store. |
| 11 | Test coverage | OK (nit) | 18 new test cases, both modes, `file:` variant, the formerly hanging case. Not covered, though verified manually: a draft-04 `id` with a trailing `#`, query, `../`, and the `compile_to_code` names. |
| 12 | Compatibility | Finding 4 | Absolute-id output is byte-identical (2428/2428). Internal resolver overrides break. CI on 3.10/3.11 for `file:` is plausibly fine (simulated with 3.9's `urllib.parse`). |
| 13 | Architecture | OK | Fits #16's design (resolve once in `walk`, the generator uses the result); records where an id came from instead of comparing strings, as reasoned in the PR. |
| 14 | Integration | Finding 1 | The stack order is right, but the body's dependency statement is wrong. #11 builds on it (checked one interaction, see out of scope). |
| 15 | Data integrity | OK | The schema object stays unchanged (relies on #16); compiling twice works. |
| 16 | Usability | OK | Error messages unchanged; `definition` in errors shows the referenced schema (tested). |
| 17 | Accessibility | N/A | Library. |
| 18 | Observability | N/A | — |
| 19 | Documentation | Findings 1–3 | Docstrings accurate. PR body, issue and CHANGELOG nits. |
| 20 | Regression | OK | Full suite 5042 passed / 393 xfailed / 824 xpassed, same XFAIL/XPASS set as the parent; generated code for the suite identical; no xfail-list edits needed (no suite case uses a relative root `$id`), and none were made. |

## Verification log

Scratch: `/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad/pr-12/`

- **Full suite on the branch:** `pytest -q -W default --benchmark-skip` → `5042 passed, 12 skipped, 393 xfailed, 824 xpassed`.
- **Suite XFAIL/XPASS lists** (`tests/json_schema -rxX`), parent vs branch: 1217 lines each, `diff` empty. The commit doesn't touch the xfail lists; nothing newly XPASSes.
- **pylint:** 9.91/10 on both; the 10 messages are identical apart from line numbers.
- **New tests**, run one by one with a 15 s timeout (`run_each.py`, from a scratch copy of `tests/`):
  - master: all fail. `test_resolver_applies_root_id_to_base_uri` fails with `AttributeError: no attribute 'get_ref'`; `test_ref_to_subschema_with_relative_id_with_directory[*]` times out.
  - parent (`walk-schema-arrays`): all fail except `test_resolver_applies_root_id_to_base_uri` (2/2 pass, as the PR states); the self-ref cases time out.
  - branch: 18/18 pass.
- **Issue repro and further cases** (`issue_repro.py`, `issue_further.py`): master and the parent print what the issue shows; the branch prints the expected output.
- **Adversarial battery** (`battery.py`, both `fast_fail` modes, `jsonschema` as oracle; output in `battery.out`):
  - Fixed on the branch, broken on the parent: `schemas/item.json#`, `?v=1`, `../schemas/item.json`, `./a/item.json`, `a/./b/item.json`, `a/b/../item.json`, `FILE:schemas/item.json`, draft-04 `id: schemas/item.json#`, a query `$id` with `other.json` (loads `s/other.json`), nested relative ids including `../x/m.json` and a `#` self-ref, a loaded doc with a sibling ref (`a/b/other.json` → `a/b/third.json`), a loaded doc with its own `$id`, recursion with `#` in a loaded doc, `$ref` at the root next to `$id`, a recursive tree, a self-ref by `item.json`, and a draft-04 plain name `#foo`.
  - Unchanged and correct: `//host/...`, `/abs/...`, `urn:`, an absolute sub-`$id` under a relative root.
  - The `../ other.json` row shows `RuntimeError: handler called with s/other.json` because the scratch handler had no document under that key (it was keyed `../s/other.json`). `s/other.json` is the URI `jsonschema` also requests, since `urljoin` drops the leading `..`. Not a bug.
- **Generated code**, `compile_to_code` for every suite schema (draft4/6/7/2019-09) plus `tests/examples`, both modes (`gencode.py`): `total 2428 differ 0`.
- **Names** (`names.py`): `validate_schemas_item_json`, `validate_schemas_item_json__definitions_c`, `validate_schemas_other_json`; `schemas/item.json#` → `validate_schemas_item_json`; the generated code `exec`s fine.
- **Python 3.10/3.11 `urllib` stand-in** (`oldurllib.py`, CPython 3.9 `urllib/parse.py`): `urljoin('file:schemas/item.json', '#/definitions/c')` = `file:///schemas/item.json#/definitions/c`; `tests/test_integration.py`: 134 passed.
- **Handler docs with nested `$id`** (`handler_nested.py`): parent = branch; #11 differs (fixes it).
- **Timing** (`perf.py`): draft-07 metaschema `compile_to_code`, 4.28 ms on the parent vs 3.92 ms on the branch.
- **Subclass compatibility** (`subclass.py`): TypeError on the branch (Finding 4).
