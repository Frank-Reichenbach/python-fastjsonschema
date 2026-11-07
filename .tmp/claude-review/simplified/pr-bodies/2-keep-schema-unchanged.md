Fixes #{I_UNCHANGED}.

Based on `master`, independent of the other resolver PRs. #{P_REL} and #{P_ARRAYS} build on it. Overview: #{META}.

**Release it together with #{P_HANDLER}.** Before this change, a schema object that had been compiled already kept its rewritten `$ref`s. Handlers that serve such objects therefore hid the bug of #{I_HANDLER} in some cases. #{P_HANDLER} fixes that bug.

`RefResolver.walk()` wrote the resolved URI of every `$ref` back into the schema, and the generator read it from there. So `compile()` changed the schema it was given, and a second `compile()` under another `$id`, or as part of another schema, used the base URI of the first.

## Changes

- `walk()` keeps the resolved URIs in a table keyed by `id()` of the object with the `$ref`, and holds the object, so the id stays unique while the resolver exists.
- `get_ref()` returns the resolved URI, or the `$ref` as written for an object that `walk()` didn't reach. `generate_ref()` and `_expand_refs()` use it.

## Decisions

- **A table instead of a copy of the schema.** `copy.deepcopy` keeps objects shared inside one schema shared, so it wouldn't change what the generator sees, and it would cost a full copy on every compile.
- **The first base URI wins** if `walk()` reaches the same object twice under different base URIs, as with the rewritten value before.

## Behavior changes

- The `definition` of a `JsonSchemaValueException` shows a `$ref` inside a referenced schema as written, not rewritten (in the CHANGELOG).
- Otherwise the generated code is unchanged, except where the old code crashed: a schema with a nested relative `$id` compiled a second time.

## Limitations

- An object that appears twice in one schema, under two different `$id`s, still resolves against the first one in both places, as on `master`.

## Tests

`tests/test_ref_schema_unchanged.py`: all 6 cases fail on `master`.
