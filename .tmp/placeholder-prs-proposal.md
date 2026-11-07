# Proposal: the `placeholder/*` PR set

Date: 2026-11-05. **Proposal only.** Nothing was changed in the repository, on the fork or upstream. No CI was run, and none is needed: everything below was measured locally, in a throwaway prototype built outside the repository. The prototype is kept as patches in `.tmp/placeholder-prs-prototype/`.

## 1. Summary

Nine PRs on the fork, in one linear stack, with no new issues and no links to any issue.

| | `fix/*` | `simple/*` | `placeholder/*` (proposed) |
|---|---|---|---|
| PRs | 8 | 7 | 9 |
| Helper branches without a PR | 0 | 2 | 0 |
| Conflicts between the PRs | none | 5 code hunks, resolved only in helper merges | none |
| Depends on an outside PR | no | yes, upstream #224 | no |
| Bug #3 (wrong function called) fixed | yes | no | yes |
| Empty JSON pointer keys fixed (other half of #224) | no | no | yes |
| Expected failures left | 0 | 2 | 0 |
| Library code vs `master` | +185/−39 | +214/−44 | +201/−57 |
| Regressions inside a PR's end state | old `RecursionError` and `TypeError` | #26 alone | none |
| Full local suite | 5123 passed | 5117 passed, 2 xfailed | **5160 passed**, 0 failed |

The set does more than `simple` and is still smaller: it adds the naming fix, the pointer fix and the `?#` fix, and has 13 fewer added lines.

Generated code for all 1204 official-suite schemas is byte-identical to the `simple` tip, so the rework changes the structure, not the behaviour. The exceptions are the intended ones in section 4.

## 2. The 2 expected failures in `simple`

They are one test, `test_plain_name_ref_under_urn_id_next_to_similar_urn`, run with `fast_fail` on and off. It's marked `xfail(strict=True)`.

```python
{'$id': 'urn:example:root',
 'definitions': {'a': {'$id': '#foo', 'type': 'integer'},
                 'b': {'$id': 'urn:example:root:foo', 'type': 'string'}},
 'properties': {'a': {'$ref': '#foo'}, 'b': {'$ref': 'urn:example:root:foo'}}}
```

**Why it fails.** The urn PR makes `#foo` resolve correctly to `urn:example:root#foo`. The function name replaces every character other than a letter or digit with `_`, so `urn:example:root#foo` and `urn:example:root:foo` both become `validate_urn_example_root_foo`. The generated code has two `def`s with that name and Python keeps the last one. Both properties then call the same function:

| Data | `master` | `simple` from #27 on | Correct |
|---|---|---|---|
| `{'a': 1, 'b': 'x'}` | valid | rejected: `data.b must be integer` | valid |
| `{'b': 1}` | rejected | **accepted** | rejected |

**Why it's "expected".** It isn't a flaky or harmless test. It's bug #3 in a new place, and it was marked as a known failure because the naming fix was handed to upstream #224. `strict=True` makes it fail once names are unique, so the mark can't be forgotten.

**Correction.** I told you no intermediate state of `simple` regresses against `master`. That was wrong for this case: it works on `master` and is wrong from #27 onward. My check missed it for two reasons: an xfail isn't counted as a failure, and the test module doesn't even import on `master`. The matrix in section 8 closes both gaps.

In `placeholder/*`, unique names come first, so this test simply passes.

## 3. What the set includes

| Source | Content | PR |
|---|---|---|
| `fix` #8 / `simple` none | Different URIs get different function names (bug #3) | 1 |
| Upstream #224 | Unique names, in a better form (section 6) | 1 |
| Upstream #224 | Empty JSON pointer keys, **which neither of your sets has** | 2 |
| Draft comment for #224 | `?#/definitions/ab`: `resolving()` compares normalized URIs | 1 |
| `simple` #30 | A `$ref` that isn't a valid URI, moved into its own PR | 3 |
| `simple` #25 | Data keywords | 4 |
| `simple` #27 | `urn:` local refs, without the xfail | 5 |
| `simple` #26, #29, #30 | Schema unchanged, resolve once, loaded schemas | 6 |
| `simple` #28 | Schema arrays, `_expand_refs` shares the keyword tables | 7 |
| `simple` #31 | `$id` next to `$ref` in 2019-09, split out | 8 |
| `simple` #31 | Definitions next to `$ref` | 9 |

All additions of `simple` over `fix` are kept:
- `copy_document()` instead of `copy.deepcopy`: clean depth error, and any mapping works.
- The root `$id` rule for loaded schemas (your decision).
- `ID_NEXT_TO_REF` on the generator classes.
- The `compile()` docstring fix.
- Keyword-only `resolved`.
- `_expand_refs()` following the same tables as `walk()`.
- One test module per topic.
- Changelog lines in the PR that causes the change.

`#224` becomes irrelevant: all 16 of its tests pass on the prototype, so does its handler-loaded case, and no code from the PR is still missing. All 18 naming tests of `fix` #8 pass as well.

## 4. New findings that change code

1. **`simple` #30 has an undocumented behaviour change.** `JsonSchemaException` subclasses `ValueError`, so `except ValueError` in `_expand_refs()` also swallows `Unresolvable ref`. On `simple`, `{'type': 'integer', 'x-note': {'$ref': '#/nope'}}` compiles; on `master` it raises `JsonSchemaDefinitionException`. No changelog line says so. PR 3 re-raises `JsonSchemaDefinitionException`, so this stays as on `master`. All tests pass and the generated code doesn't change.
2. **The window of `simple` #26 has no test.** A document compiled first and then served through a handler validates wrongly until #30 is in. PR 6 adds the missing test.
3. **The invalid-URI failure is wider than the `simple` changelog says.** It also happens without `$id` if the schema has a keyword such as `type`. PR 3 covers both.
4. **The `is_resolved()` method and `id_next_to_ref_applies()` aren't needed.** See section 6.

## 5. How the fixes relate

**Dependency:** B is wrong or doesn't work without A, so A must come first.
**Atomic:** one problem. Its parts are wrong on their own, so they belong in one PR.
**Relation:** same area or idea, but each is correct alone. Their order is free.

```
1 names ──┬── 2 pointer keys
          └─────────────┐
4 data keywords ────────┴── 5 urn
   │
   │     3 invalid URI ── 6 resolve once (atomic: 3 commits)
   │                            │     │
   └────────────── 7 arrays ────┘     │
                      │               │
                      │    8 $id next to $ref
                      └───────┬───────┘
                       9 definitions next to $ref
```

### Dependencies

| Needs | PR | Evidence (each measured by removing the first one) |
|---|---|---|
| 1 names | 2 pointer keys | With the pointer fix alone, `#/` gets the root function's name and replaces it: 7 of 16 tests fail, and `validate(42)` returns `42` for a schema of type `object`. That's worse than `master`. |
| 1 names | 5 urn | The two expected failures of section 2. |
| 4 data keywords | 5 urn | `urljoin` left a `{"$ref": "#"}` in a `const` value unchanged by accident. `join_uri()` would rewrite it, so equal data is rejected. Guard test: `test_ref_object_in_data_keyword_under_urn_id_is_data`. |
| 3 invalid URI | 6 resolve once | PR 6 resolves refs in loaded schemas too. Without PR 3, an invalid `$ref` in an unknown keyword of a loaded schema stops `compile()`, which works on `master`. 5 tests fail. |
| 6 resolve once | 7 arrays | Otherwise an array shared by two schemas keeps the first base URI. Guard test: `test_schema_array_shared_by_schemas_with_different_ids`. |
| 4 data keywords | 7 arrays | PR 7 extends `subschemas()`, and `items` inside a `const` value must stay data. |
| 6 resolve once | 8 `$id` next to `$ref` | PR 8 uses the `walk()` of PR 6. |
| 8 `$id` next to `$ref` | 9 definitions | Without the rule, a relative `$id` in those definitions is registered at the wrong URI, where it can replace another schema. 4 tests and 2 official-suite cases fail. |
| 7 arrays | 9 definitions | Refs inside arrays in those definitions. 12 tests failed without it when measured on the `fix` stack. |

### Atomic problems

| Parts | Why they can't be split |
|---|---|
| Schema unchanged + resolve once + loaded schemas (**PR 6**) | One cause: a `$ref` is resolved in two places. The regression matrix shows it directly. After commit 1 and after commit 2, `test_handler_serving_an_object_that_was_compiled_before` fails, though it passes on `master`. After commit 3 it passes. Commit 2 needs the table of commit 1, and commit 3 needs both. |
| Loaded schemas + `copy_document()` | Without the copy, 4 tests of objects shared by handlers fail. That's the bug 2.22.3 fixed. |
| Loaded schemas + root `$id` rule | Without the rule, your decision is lost: 4 tests fail. |
| Unique names + `?#` comparison (**PR 1**) | `?#/x` needs both: one gives `NameError`, the other `ValueError`. |

### Relations only

| PRs | Relation |
|---|---|
| 4 data keywords, 7 arrays, 9 definitions | One idea: what is a subschema? They could be one PR, but each is correct alone, so they stay small. |
| 3 invalid URI, 4 data keywords | Both stop `walk()` tripping over non-schema values. PR 3 already fixes the `ValueError` case for data values. |
| 5 urn, 6 resolve once | No logical link. PR 5 comes first so that every `urljoin` call becomes `join_uri` once and PR 6 is written against it. |
| 7 arrays, 8 `$id` next to `$ref` | Independent: PR 8 applies cleanly without PR 7 and its tests pass. Their order is free. |
| 1, 3, 4 | Independent in logic, but 3 and 4 change the same lines of `_expand_refs()`, and 3 and 5 the same lines of `walk()`. |

## 6. What makes the fixes easier to understand

1. **One linear stack.** Independence in logic didn't mean they merge independently: nearly every fix touches `walk()`. `simple` showed the cost: 5 conflicts and 2 helper branches. A stack has no conflicts, and each PR text still states what it really needs.
2. **Bottom-up order.** Each fix is written once, in its final place. `simple` adds code in #26 and rewrites it in #29 and #30.
3. **One mechanism per PR.** PR 6 explains one cause instead of three partial states. PR 8 separates a behaviour change that can break schemas from the plain bug fix in PR 9, whose fix in `walk()` is now 3 lines.
4. **Each PR text stands alone:** problem, runnable repro, actual and expected result, cause, change, and what it needs.
5. **Less code and fewer concepts,** all verified by the full suite:

   | Change | Effect |
   |---|---|
   | `get_ref()` always returns a resolved URI | `is_resolved()` removed, and both generator call sites become `resolved=True` |
   | The draft rule has one source, the generator class | `id_next_to_ref_applies()` removed |
   | Function names live in `RefResolver.get_scope_name()`, as in #224, not in the generator as in #8 | `compile()` and the generator ask the same place, and the generator doesn't change |
   | A counter per name instead of searching a free suffix | 8000 colliding names: **0.23 s**, against 5.76 s (#8) and 5.57 s (#224) |
   | Flat `walk()`, with one `with` for all cases | 45 lines instead of 52, and `pylint: disable=too-many-branches` removed |

6. **No mixed-in fixes.** The invalid-URI fix was hidden inside the loaded-schema PR. Now it has its own title.

## 7. The PRs

| # | Branch | Base | Needs | Library | Tests | New tests failing on base |
|---|---|---|---|---|---|---|
| 1 | `placeholder/unique-function-names` | `master` | – | +16/−6 | +125 | 21 of 21 |
| 2 | `placeholder/empty-pointer-keys` | 1 | 1 | +4/−2 | +82 | 14 of 16 |
| 3 | `placeholder/invalid-ref-uri` | 2 | – | +11/−4 | +22 | 3 of 5 |
| 4 | `placeholder/data-keyword-values` | 3 | – | +35/−8 | +85 | 13 of 18 |
| 5 | `placeholder/urn-id-local-refs` | 4 | 1, 4 | +23/−4 | +151 | 29 of 33 |
| 6 | `placeholder/resolve-refs-once` | 5 | 3 | +101/−48 (3 commits, net +90/−37) | +451 | 31 of 49 |
| 7 | `placeholder/walk-schema-arrays` | 6 | 4, 6 | +14/−8 | +155 | 26 of 31 |
| 8 | `placeholder/id-next-to-ref` | 7 | 6 | +28/−10 | +103 | 5 of 10 |
| 9 | `placeholder/ref-sibling-definitions` | 8 | 7, 8 | +3/−1 | +215 | 45 of 51 |

Each test that passes on its base is a guard, and each PR text says what it guards.

Below are the drafted PR texts. The numbers come from the prototype and should be re-measured when the branches are created. Every "On `master`" output was run on `master` (`4999d6b`). PR texts refer to each other by branch name, because PR numbers don't exist yet.

### PR 1: `placeholder/unique-function-names`

Title: **Use one validation function name per URI**

````markdown
fastjsonschema generates one Python function per `$ref` target and names it after the target's URI: it lowercases the URI and replaces everything except ASCII letters and digits with `_`. Different URIs can therefore get the same name, and Python keeps only the last `def`. A `$ref` then validates against the wrong schema, and nothing reports it:

```python
import fastjsonschema

validate = fastjsonschema.compile({
    'definitions': {'user-id': {'type': 'integer'}, 'user_id': {'type': 'string'}},
    'properties': {'a': {'$ref': '#/definitions/user-id'}, 'b': {'$ref': '#/definitions/user_id'}},
})
print(validate({'b': 'x'}))
```

On `master` this raises `data.b must be integer`, although `b` refers to a string. With this change it prints `{'b': 'x'}`. A `$ref` "identifies the URI of a schema to use" ([Draft-07 Core §8.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3)), so each `$ref` must use its own target.

The same cause has more forms:

- Targets that differ in case, in `-` and `_`, in `/` and `_`, in non-ASCII letters or in a trailing `_`.
- A target that gets the name of the root function. With `{'-': {'type': 'integer'}, 'type': 'object', 'properties': {'a': {'$ref': '#/-'}}}`, `compile()` returns the validator of `-`: `5` is accepted, and `{'a': 1}` is rejected with `data must be integer`.
- The reverse: one URI with two spellings gets two names. With `?#/definitions/ab` next to `#/definitions/ab`, validation raises `NameError: name 'validate____definitions_ab' is not defined`. In a schema with a keyword such as `type`, `compile()` raises `ValueError: unknown url type: '?'`, because `resolving()` compares the URI before normalizing it.

## Changes

- `RefResolver.get_scope_name()` keeps one name per normalized URI. If another URI already has a name, the new one gets the suffix `_2_`, `_3_` and so on.
- `resolving()` compares normalized URIs.

## Decisions

- **The names live in the resolver.** `compile()` finds the root function with `get_scope_name()`, so the generator and `compile()` use one source.
- **A counter per name instead of a search for a free suffix.** Naming stays linear: 8000 colliding names compile in 0.23 s, against about 5.6 s with a search.
- **The suffix ends in `_`.** A sanitized name never ends in `_`, so a suffixed name is never the plain name of another URI. A URI without a collision keeps its name, whichever URI comes first.

## Behavior changes

Function names in `compile_to_code()` change only where different URIs collided.

## Tests

`tests/test_ref_names.py`: all 21 cases fail on `master`.

## Relation to other PRs

Independent. `placeholder/empty-pointer-keys` and `placeholder/urn-id-local-refs` need it.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 2: `placeholder/empty-pointer-keys`

Title: **Preserve empty keys in JSON pointers**

````markdown
In a JSON pointer, every `/` starts a reference token, and a token can be empty: `/` means the key `""`, and `//child` means the key `child` below the key `""` ([RFC 6901 §4](https://www.rfc-editor.org/rfc/rfc6901#section-4)). `resolve_path()` strips all leading `/`, so `#/` means the whole document and `#//child` means `child` in the root:

```python
import fastjsonschema

validate = fastjsonschema.compile({
    '': {'type': 'integer'},
    'type': 'object',
    'properties': {'value': {'$ref': '#/'}},
})
print(validate({'value': 42}))
```

On `master` this raises `data.value must be object`: the `$ref` points to the root schema instead of the key `""`. With this change it prints `{'value': 42}`.

## Changes

`resolve_path()` removes one leading `/`, not all of them. An empty fragment still means the whole document, and a fragment without a leading `/` still works for direct callers.

## Behavior changes

`#/` and `#//...` now point to the key `""`, as the RFC defines. This can break a schema that works today: one that uses `#/` to mean the whole document, without a key `""`, now raises `Unresolvable ref`. `#` is the correct form for that.

## Tests

`tests/test_ref_pointer.py`: 14 of the 16 cases fail on the base branch. The other two guard ordinary pointers and the function names.

## Relation to other PRs

**Needs `placeholder/unique-function-names`.** `#/` gets the same function name as the root schema. Without unique names, the function for `#/` replaces the root function: `compile()` then returns a validator that accepts `42` for a schema of type `object`.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 3: `placeholder/invalid-ref-uri`

Title: **Ignore a $ref that is not a valid URI in an unknown keyword**

````markdown
A schema can hold anything under an unknown keyword. But fastjsonschema looks for `$ref` there too, and if the value isn't a valid URI, `compile()` fails, although nothing uses it:

```python
import fastjsonschema

validate = fastjsonschema.compile({
    '$id': 'http://example.com/a.json',
    'x-note': {'$ref': 'http://[bad'},
})
print(validate({}))
```

On `master` this raises `ValueError: Invalid IPv6 URL`. With this change it prints `{}`. It also fails on `master` without `$id` if the schema has a keyword such as `type`.

There are two causes. `walk()` resolves every `$ref` it reaches, and it descends into unknown keywords on purpose, so that a subschema kept there can be referred to by its `$id`. And `_expand_refs()`, which builds the `definition` of an exception, resolves it again.

## Changes

- `walk()` leaves a `$ref` that isn't a valid URI as it is.
- `_expand_refs()` shows it as written.

## Decisions

- **Only an invalid URI is ignored.** `JsonSchemaException` is a `ValueError`, so `_expand_refs()` re-raises `JsonSchemaDefinitionException`. An unresolvable `$ref` behaves as before.

## Behavior changes

None apart from the fix. A `$ref` that isn't a valid URI and is used still fails with `ValueError`.

## Tests

`tests/test_ref_invalid_uri.py`: 3 of the 5 cases fail on the base branch. The other two guard a used `$ref` and an unresolvable one.

## Relation to other PRs

Independent. `placeholder/resolve-refs-once` needs it: that PR also resolves the refs of schemas loaded through handlers, where such a `$ref` works today.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 4: `placeholder/data-keyword-values`

Title: **Treat the values of const, enum, default and examples as data**

````markdown
The values of `const`, `enum`, `default` and `examples` are data, not schemas ([Draft-07 Validation §6.1.2](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.6.1.2), [§6.1.3](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.6.1.3), [§10.2](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.10.2), [§10.4](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.10.4)). fastjsonschema still treats a `$ref` or `$id` inside them as part of the schema:

```python
import fastjsonschema

validate = fastjsonschema.compile({'properties': {'pointer': {'const': {'$ref': '#/definitions/x'}}}})
print(validate({'pointer': {'$ref': '#/definitions/x'}}))
```

On `master`, `compile()` raises `Unresolvable ref: definitions`. With this change it prints the data. Depending on the schema, `master` also:

- rejects data equal to a `const` value, because the `$ref` in the value was rewritten;
- inserts a different `default`: `{'p': {'$ref': 'http://example.com/root.json#/a'}}` instead of `{'p': {'$ref': '#/a'}}`;
- lets an `$id` inside such a value replace the real subschema with that `$id`.

The cause is that `walk()` descends into every object of a schema, and `_expand_refs()` into every object and array.

## Changes

- `DATA_KEYWORDS` and `SCHEMA_MAPS` in `ref_resolver.py`, and `subschemas()`, which yields the subschemas of a node. It skips the values of data keywords and descends into the values of keywords that map names to schemas, so a property named `default` or `const` is still a schema.
- `walk()` visits what `subschemas()` yields. `_expand_refs()` follows the same rules.
- The `$ref`/`$id` cases of `id.json` in the official test suite pass now, and their xfail entries are removed.

## Decisions

- **Keywords are told apart from property names**, so `properties`, `definitions`, `$defs`, `patternProperties`, `dependencies` and `dependentSchemas` are handled as maps.
- **`subschemas()` is a generator.** It adds no stack frame, so the depth limit of `walk()` still raises `JsonSchemaDefinitionException` before Python's recursion limit.
- **Other unknown keywords are walked as before**, so subschemas kept under a custom keyword and referred to by `$id` still work.

## Behavior changes

- An `$id` inside such a value, or inside an entry named like a data keyword in a custom keyword such as `x-defs`, is no longer registered. A `$ref` to it is loaded through the handlers like any other URI.
- A `$ref` that points into a data value, such as `#/properties/n/default`, still works.

## Tests

`tests/test_ref_data_keywords.py`: 13 of the 18 cases fail on the base branch. Four guard properties named like data keywords. One passes because `placeholder/invalid-ref-uri` already covers it.

## Relation to other PRs

Independent. `placeholder/urn-id-local-refs` and `placeholder/walk-schema-arrays` need it.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 5: `placeholder/urn-id-local-refs`

Title: **Resolve local refs inside a subschema with a urn: $id**

````markdown
Inside a subschema whose `$id` has a scheme such as `urn:`, `tag:` or `s3:`, local references (`#`, `#/definitions/...`) and plain-name `$id`s (`#foo`) resolve against the root schema instead of that subschema. Validation then accepts invalid data, rejects valid data, or `compile()` fails:

```python
import fastjsonschema

node = {'$id': 'urn:example:node', 'properties': {
    'children': {'items': {'$ref': '#'}},
    'tags': {'maxItems': 2},
}}
validate = fastjsonschema.compile({'properties': {'p': node}})
print(validate({'p': {'children': [{'tags': [1, 2, 3]}]}}))
```

On `master` this prints the data, although the inner `tags` has more than 2 items. With this change it raises `data.p.children[0].tags must contain less than or equal to 2 items`. References resolve against the `$id` of the subschema, for every scheme ([Draft-07 Core §8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2), [§8.3.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3.2)).

The cause: `urllib.parse.urljoin` returns a relative reference unchanged if the scheme of the base URI isn't in `urllib.parse.uses_relative`.

## Changes

`join_uri()`: for a ref that starts with `#` and a base URI with such a scheme, it keeps the base URI and replaces its fragment, as [RFC 3986 §5.2.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2.2) defines. Everything else still goes through `urljoin`. All `urljoin` calls in `ref_resolver.py` use it.

## Decisions

- **Fixed here, not in `urllib`.** Adding schemes to the global `uses_relative` would change `urljoin` for the whole process.
- **Only refs starting with `#`, and only for schemes outside `uses_relative`.** Full RFC 3986 resolution would change other relative refs, which this bug doesn't need.
- **`base.partition('#')`, not `urldefrag`.** `urldefrag` normalizes the URI only when it has a fragment, differently per Python version.

## Behavior changes

- A `#...` ref inside such a subschema whose target exists only in the root schema now raises `JsonSchemaDefinitionException`, as with an `http:` `$id`.
- For a root `$id` with such a scheme, `compile_to_code()` names the functions for `#...` refs after the root `$id`. `"$ref": "#"` no longer generates a second copy of the root function.

## Tests

`tests/test_ref_urn.py`: 29 of the 33 cases fail on the base branch. The other four are the guards for the two dependencies below.

## Relation to other PRs

- **Needs `placeholder/unique-function-names`.** `#foo` under `urn:example:root` now resolves to `urn:example:root#foo`, which sanitizes to the same function name as `urn:example:root:foo`.
- **Needs `placeholder/data-keyword-values`.** `urljoin` left a `{"$ref": "#"}` inside a `const` value unchanged by accident. `join_uri()` would rewrite it, and equal data would be rejected.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 6: `placeholder/resolve-refs-once`

Title: **Resolve every $ref once and leave the schema unchanged**

Three commits, in this order: `Leave the $ref values of the schema unchanged`, `Resolve each URI once under a relative $id with a directory`, `Walk schemas loaded through handlers like the main schema`.

````markdown
A `$ref` is resolved in two places. `walk()` writes the resolved URI into the schema it was given, and the generator resolves the value it finds there again. Since 2.22.3 (commit `c9a311e`), `walk()` skips the `$ref`s of schemas loaded through handlers, to avoid that second resolution. This one design causes three bugs.

**1. `compile()` changes the schema, so it can't be reused.**

```python
import fastjsonschema

shared = {'$ref': '#/definitions/x'}
one = {'$id': 'http://example.com/one.json', 'definitions': {'x': {'type': 'integer'}}, 'properties': {'p': shared}}
two = {'$id': 'http://example.com/two.json', 'definitions': {'x': {'type': 'string'}}, 'properties': {'p': shared}}

fastjsonschema.compile(one)
print(shared)
print(fastjsonschema.compile(two)({'p': 'a'}))
```

On `master`, `shared` becomes `{'$ref': 'http://example.com/one.json#/definitions/x'}`, and compiling `two` downloads `one.json`. With this change `shared` stays as it is and the last line prints `{'p': 'a'}`.

**2. A relative `$id` with a directory is applied more than once.**

```python
import fastjsonschema

def handler(uri):
    raise RuntimeError('handler called with ' + uri)

validate = fastjsonschema.compile({
    '$id': 'schemas/item.json',
    'definitions': {'count': {'type': 'integer'}},
    'properties': {'count': {'$ref': '#/definitions/count'}},
}, handlers={'': handler})
print(validate({'count': 1}))
```

On `master`, `compile()` raises `handler called with schemas/schemas/schemas/schemas/schemas/schemas/item.json`, because `urljoin(uri, uri)` repeats the directory of a relative path. For a subschema with such an `$id` that refers to itself, `compile()` doesn't return. With this change it prints the data. A `$ref` is resolved "against the current base URI" ([Draft-07 Core §8.3.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3.2)), once.

**3. In a schema loaded through a handler, a `$ref` ignores the `$id` of its subschema** (regression in 2.22.3).

```python
import fastjsonschema

DOC = {
    '$id': 'http://example.com/doc.json',
    'definitions': {'x': {'type': 'string'}},
    'properties': {'p': {
        '$id': 'http://example.com/node.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'v': {'$ref': '#/definitions/x'}},
    }},
}
validate = fastjsonschema.compile({'$ref': 'http://example.com/doc.json'}, handlers={'http': lambda uri: DOC})
print(validate({'p': {'v': 1}}))
```

On `master` this raises `data.p.v must be string`. 2.22.0 to 2.22.2 and this change print the data.

## Why this is one PR

These are three symptoms of one cause, and the steps can't be released separately:

- Commit 2 needs the table of commit 1, and commit 3 needs both.
- After commit 1 or 2 alone, a document compiled first and then served through a handler validates wrongly. On `master`, its rewritten `$ref`s hide bug 3 by accident. `test_handler_serving_an_object_that_was_compiled_before` covers that.

Each commit is green and can be reviewed alone.

## Changes

- **Commit 1:** `walk()` keeps the resolved URIs in a table keyed by `id()` of the object with the `$ref`, and no longer writes into the schema. `get_ref()` returns them.
- **Commit 2:** every URI is resolved once. `get_ref()` always returns a resolved URI, and `in_scope()` and `resolving()` take `resolved=True` for such a URI. `walk()` doesn't apply the root `$id` to itself; `from_schema()` says so with `base_uri_is_id`.
- **Commit 3:** `walk()` treats a loaded schema like the main schema, so the `rewrite_refs` special case goes away. `resolving()` copies what a handler returns with `copy_document()`. `walk()` remembers the objects it walked instead of their URIs, which also fixes a second load with `cache=False`.

## Decisions

- **A table instead of a copy of the schema.** `copy.deepcopy` keeps objects shared inside one schema shared, so it wouldn't change what the generator sees, and it would cost a full copy on every compile.
- **The first base URI wins** if `walk()` reaches the same object twice.
- **`copy_document()`, not `copy.deepcopy`.** A handler can return the same objects for several URIs, and `walk()` resolves an object once, so each document needs its own objects. It stops at the depth limit of `walk()`, so a deep document still raises `JsonSchemaDefinitionException`, and it accepts any mapping.
- **The base URI of a loaded schema stays the URI it was loaded from, whatever its own `$id` says**, as in 2.22.3 and in `jsonschema` 4.26. RFC 3986 would turn `dir/main.json` with `"$id": "dir/main.json"` into `dir/dir/…`. The schema is still registered under that `$id`, and the `$id`s of its subschemas apply.

## Behavior changes

- The `definition` of a `JsonSchemaValueException` shows a `$ref` inside a referenced schema as written, not rewritten.
- A nested relative `$id` is no longer also registered under the doubled URI.

## Limitations

An object that appears twice in one schema, under two different `$id`s, still resolves against the first one in both places, as on `master`.

## Tests

`tests/test_ref_schema_unchanged.py`, `tests/test_ref_relative_id.py` and `tests/test_ref_handlers.py`: 31 of the 49 cases fail on the base branch, and the self-referencing ones hang there (run with a timeout). The others guard what 2.22.3 got right: relative refs resolved once, objects shared by handlers, and the root `$id` rule.

## Relation to other PRs

**Needs `placeholder/invalid-ref-uri`:** this PR resolves the refs of loaded schemas too, where a `$ref` that isn't a valid URI works today. `placeholder/walk-schema-arrays` and `placeholder/id-next-to-ref` need this PR.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 7: `placeholder/walk-schema-arrays`

Title: **Resolve refs inside allOf, anyOf, oneOf and items arrays against their $id**

````markdown
A `$ref` inside `allOf`, `anyOf`, `oneOf` or an array-form `items` ignores the `$id` of the subschema it is in, and an `$id` inside such an array isn't registered:

```python
import fastjsonschema

validate = fastjsonschema.compile({
    'definitions': {'x': {'type': 'string'}},
    'properties': {'p': {
        '$id': 'http://example.com/node.json',
        'definitions': {'x': {'type': 'integer'}},
        'properties': {'v': {'allOf': [{'$ref': '#/definitions/x'}]}},
    }},
})
print(validate({'p': {'v': 1}}))
```

On `master` this raises `data.p.v must be string`: `#/definitions/x` resolves against the root schema instead of `node.json`. With this change it prints the data. An `$id` defines "the base URI that other URI references within the schema are resolved against" ([Draft-07 Core §8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2)), with no exception for arrays.

The cause: `walk()` descends only into object values, so it skips arrays.

## Changes

- `SCHEMA_ARRAYS`: `subschemas()` also yields the subschemas in these arrays.
- `_expand_refs()` follows the same rules. It expands the `$ref`s in these arrays and leaves arrays of other keywords as written. It used to resolve a `$ref` in any array, which could load it through a handler at compile time.
- Draft-06 and draft-07 `ref.json` of the official test suite pass completely now. Their xfail entries are removed (18 cases).

## Behavior changes

- An `id` inside these arrays now sets the base URI there too, as in every other subschema and every draft, although draft-06 and later don't define `id`.
- The `definition` of an error keeps `$ref`s inside arrays of other keywords as written.

## Tests

`tests/test_ref_arrays.py`: 26 of the 31 cases fail on the base branch. Five guard an array shared by two schemas, and arrays in unknown keywords and in data values.

## Relation to other PRs

- **Needs `placeholder/data-keyword-values`:** `items` inside a `const` value must stay data.
- **Needs `placeholder/resolve-refs-once`:** otherwise an array shared by two schemas with different `$id`s keeps the base URI of the first one.

`placeholder/ref-sibling-definitions` needs this PR.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 8: `placeholder/id-next-to-ref`

Title: **Use an $id next to a $ref in 2019-09**

````markdown
Since 2019-09, "other keywords can appear alongside of "$ref"" ([2019-09 Core §8.2.4.1](https://json-schema.org/draft/2019-09/json-schema-core.html#rfc.section.8.2.4.1)), and an `$id` "also serves as the base URI for relative URI-references in keywords within the schema resource" ([§8.2.2](https://json-schema.org/draft/2019-09/json-schema-core.html#rfc.section.8.2.2)). fastjsonschema ignores an `$id` next to a `$ref` in every draft:

```python
import fastjsonschema

def handler(uri):
    print('loads', uri)
    return {'type': 'integer'}

fastjsonschema.compile({
    '$schema': 'https://json-schema.org/draft/2019-09/schema',
    '$id': 'http://example.com/root.json',
    'properties': {'p': {'$id': 'http://example.com/sub/', '$ref': 'item.json'}},
}, handlers={'http': handler})
```

On `master` this prints `loads http://example.com/item.json`. With this change it prints `loads http://example.com/sub/item.json`. Draft-04 to draft-07 must keep ignoring it: "All other properties in a "$ref" object MUST be ignored" ([Draft-07 Core §8.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3)).

## Changes

- `ID_NEXT_TO_REF` is `True` on `CodeGeneratorDraft2019` and `False` on the earlier drafts.
- `compile()`, `compile_to_code()` and a generator that builds its own resolver pass it to `RefResolver` as `id_next_to_ref`.
- `walk()` registers such an `$id` and resolves the `$ref` in its scope.
- The test-suite harness builds its debug generator for the draft it tests. It used to print 2019-09 code for every draft.
- The `compile()` docstring says that 2019-09 is used without `$schema`, as the code does. It used to say draft-07.

## Decisions

- **The draft has one source, the generator class.** `walk()` runs before the generator exists, so the rule is passed in.
- **`id_next_to_ref` defaults to `False`.** A `RefResolver` created directly behaves as on `master`.
- **Only `$id` counts, not `id`.** Draft-04 is the only draft with `id`, and it ignores everything next to a `$ref`.
- **The `$id` of a loaded document doesn't change its base URI here either.**

## Behavior changes

Schemas without `$schema` use 2019-09, so this applies to them. It can break a schema that works today:

- A `$ref` next to an `$id` can no longer point into the outer schema with `#/...`. It raises `JsonSchemaDefinitionException`.
- A relative `$ref` there resolves against that `$id`.

## Tests

`tests/test_ref_id_next_to_ref.py`: 5 of the 10 cases fail on the base branch. The others guard draft-04 to draft-07, where nothing changes.

## Relation to other PRs

**Needs `placeholder/resolve-refs-once`.** It doesn't need `placeholder/walk-schema-arrays`; the order of these two is free. `placeholder/ref-sibling-definitions` needs this PR.

Assisted-by: Claude Opus 5.5 (code generation)
````

### PR 9: `placeholder/ref-sibling-definitions`

Title: **Register $id and resolve refs in definitions next to a $ref**

````markdown
`walk()` doesn't look inside a schema object that has a `$ref`. If that object also has `definitions` and a `$ref` points into them, the schemas there lose their `$id`:

```python
import fastjsonschema

validate = fastjsonschema.compile({
    '$schema': 'http://json-schema.org/draft-07/schema#',
    '$ref': '#/definitions/a',
    'definitions': {
        'a': {
            '$id': 'http://example.com/node.json',
            'definitions': {'y': {'type': 'integer'}},
            'properties': {'b': {'$ref': '#/definitions/y'}},
        },
        'y': {'type': 'string'},
    },
})
print(validate({'b': 1}))
```

On `master` this raises `data.b must be string`: `#/definitions/y` inside `node.json` resolves against the root schema. With this change it prints the data.

"All other properties in a "$ref" object MUST be ignored" ([Draft-07 Core §8.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3)) keeps `definitions` from validating anything. It doesn't remove the schemas there from the document: a JSON pointer still identifies them, and their `$id` applies within them ([§8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2)).

## Changes

Next to a `$ref`, `walk()` also descends into the schemas under `definitions` and `$defs`. Below them, it walks as everywhere else.

## Decisions

- **Only `definitions` and `$defs`.** The generator ignores every other keyword next to a `$ref`, so only schemas that another `$ref` points into matter. Walking the rest would register `$id`s from data.

## Behavior changes

Schemas under `definitions` and `$defs` next to a `$ref` count toward the nesting limit, as schemas everywhere else do.

## Limitations

In 2019-09, keywords next to a `$ref` other than the definitions, such as `if` or `not`, aren't walked, as on `master`.

## Tests

`tests/test_ref_siblings.py`: 45 of the 51 cases fail on the base branch. The other six guard what must stay ignored next to a `$ref`. In the official test suite, 11 cases of 2019-09 now pass. Those files stay listed as expected failures because other cases in them still fail, so the new passes show as XPASS.

## Relation to other PRs

- **Needs `placeholder/id-next-to-ref`:** without it, a relative `$id` in these definitions is registered at the wrong URI if the `$ref` object has its own `$id`, where it can replace another schema.
- **Needs `placeholder/walk-schema-arrays`** for refs inside arrays in these definitions.

Assisted-by: Claude Opus 5.5 (code generation)
````

## 8. Verification

All local, Python 3.14, on macOS, with the official JSON-Schema-Test-Suite. No CI.

**Final prototype:**

| Check | Result |
|---|---|
| Full suite | 5160 passed, 0 failed, 382 xfailed, 835 xpassed |
| Against the `simple` tip | Of 6324 shared tests, 2 outcomes change: the two expected failures now pass |
| Official-suite outcomes | Same as both old tips (382 xfailed, 835 xpassed) |
| Generated code, 1204 official schemas | Byte-identical to the `simple` tip, same 51 exceptions |
| Pylint | Same 9 messages as `master` |
| Upstream #224's 16 tests | All pass |
| Old `test_integration.py` of `fix` | 206 of 215 pass. Failing: 2 from your root-`$id` decision, 7 from the removed `id_next_to_ref_applies()` |
| Repro of every PR | Actual output on `master`, expected output on the prototype |
| Very deep handler document | `JsonSchemaDefinitionException`, as on `master` |
| `MappingProxyType` from a handler | Works, as on `master` |

**Regression matrix.** All tests of the final set were run on `master` and after each of the 11 commits, with test modules forced to import on every state and xfail counted as not passing: 6371 tests, 5769 pass on `master`.

| After commit | Regressions vs `master` |
|---|---|
| Names, pointer keys, invalid URI, data keywords, urn | 0 |
| **Resolve once, commit 1** | **1**, the handler guard |
| **Resolve once, commit 2** | **1**, the same guard |
| Resolve once, commit 3 | 0 |
| Arrays, `$id` next to `$ref`, definitions | 0 |

That matrix ran before the last small edit (the narrower `except` in PR 3, new test cases, and the split of the sibling tests). After that edit, the final tree passed everything above again and each branch passed its own tests.

**Not verified:** 
- Python versions other than 3.14.
- Linux and Windows, since there's no CI.
- The dependencies "data keywords before urn", "resolve once before arrays" and "arrays before definitions" were measured earlier on the `fix` and `simple` stacks, not re-measured on this one.

## 9. Decisions for you

1. **PR 6 as one PR with three commits (recommended), or three stacked PRs?** One PR is 451 test lines, but it explains one cause, and no merged state regresses. Three PRs are smaller to read, but the first two leave `master` with the regression above until the third is merged. On your fork that window costs little, so this is purely a matter of taste.
2. **PR 2's tests.** The prototype uses the 16 tests of upstream #224 unchanged, and its `resolve_path()` change is nearly the same. As you asked, nothing links to it. I'd rewrite the tests in the style of the other modules. If you'd rather credit the author, a `Co-authored-by:` line would do it.
3. **`Unresolvable ref` in an unknown keyword.** I kept `master`'s behaviour, so the schema still fails to compile. That's the conservative choice; `simple` silently changed it. If you prefer the `simple` behaviour, it should be its own stated change.
4. **Two PRs can break a schema that works today, because the spec says so.** PR 2: `#/` used to mean the whole document. PR 8: a `$ref` next to an `$id` pointing into the outer schema, also in schemas without `$schema`. Both are correct per the spec, and PR 8 was already in `simple`. Say so if you'd rather leave either out; PR 9 needs PR 8.
5. **Codex review.** The drafts carry only the code-generation line. If Codex reviews the set before it's published, each PR and commit gets `Assisted-by: GPT-6.1 Terra (code review)` as well.

## 10. Creating the set, if you approve

1. Create the 9 branches from the patches. Write the changelog lines the prototype still lacks (PRs 6, 8 and 9; the wording is in the `simple` CHANGELOG) and final commit messages with `Assisted-by:` lines.
2. Re-measure the numbers in the PR texts on each branch. Run the full suite with the official test suite and pylint on each branch.
3. Run each PR text through `check_trailers.py`, and check that no text contains an issue reference.
4. Push the branches and open 9 PRs on the fork, each based on the one before it. Pushes and PRs don't start CI on the fork, and I won't start it by hand.
5. Leave `fix/*`, `simple/*` and all their issues and PRs as they are until you decide about them.

Merge in order with merge commits, which is the only method the fork allows. After a merge, check that the next PR's base moved to `master`.
