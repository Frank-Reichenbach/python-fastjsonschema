Fixes #{I_ARRAYS}.

**Needs #{P_DATA} and #{P_UNCHANGED}.** Its base branch `simple/base-for-walk-schema-arrays` is just a merge of those two, so the diff shows only this change. Once both are merged, retarget it to `master`. Overview: #{META}.

- **#{P_DATA}:** `subschemas()` tells data from schemas, so an `items` array inside a `const` value stays data.
- **#{P_UNCHANGED}:** without it, `walk()` would write the resolved URIs into these arrays too. An array shared by two schemas with different `$id`s, such as `{"anyOf": [{"$ref": "#/definitions/x"}, {"type": "null"}]}`, would then keep the base URI of the schema compiled first. `test_schema_array_shared_by_schemas_with_different_ids` passes on `master` and fails if this change is applied without #{P_UNCHANGED}.

`walk()` descended only into object values, so it skipped the arrays of `allOf`, `anyOf`, `oneOf` and an array-form `items`. A `$ref` inside them ignored the `$id` of its subschema, and an `$id` inside them wasn't registered.

## Changes

- `SCHEMA_ARRAYS`: `subschemas()` also yields the subschemas in these arrays.
- `_expand_refs()`, which builds the `definition` of a `JsonSchemaValueException`, follows the same rules. It expands the `$ref`s in these arrays and leaves arrays of other keywords as written. It used to resolve a `$ref` in any array, including one in an unknown keyword, and that could load it through a handler at compile time. This puts the traversal rules in the keyword tables of `ref_resolver.py`, which `walk()` and `_expand_refs()` share.
- Draft-06 and draft-07 `ref.json` of the official test suite pass completely now. Their xfail entries are removed (18 cases).

## Behavior changes (in the CHANGELOG)

- An `id` inside these arrays now sets the base URI there too. `walk()` already does this in every other subschema and in every draft, although draft-06 and later don't define `id`. Reading `id` only in draft-04 would be a separate change.
- The `definition` of an error keeps `$ref`s inside arrays of other keywords as written.

## Tests

`tests/test_ref_arrays.py`. On the base branch, 26 of 31 cases fail. Five pass there:
- `test_schema_array_shared_by_schemas_with_different_ids` (the guard above);
- the tests showing that an array in an unknown keyword or in a data value is not walked.
