Fixes #{I_DATA}.

Based on `master`, independent of the other resolver PRs. #{P_URN} and #{P_ARRAYS} build on it. Overview of all of them: #{META}.

`walk()` descended into every object of a schema, and `_expand_refs()` into every object and array. So both treated a `$ref` or `$id` inside the value of `const`, `enum`, `default` or `examples` as part of the schema.

## Changes

- `DATA_KEYWORDS` and `SCHEMA_MAPS` in `ref_resolver.py`, and `subschemas()`, which yields the subschemas of a node. It skips the values of data keywords and descends into the values of keywords that map names to schemas, so a property named `default` or `const` is still a schema.
- `walk()` visits what `subschemas()` yields. `_expand_refs()` follows the same rules.
- The `$ref`/`$id` cases of `id.json` in the official test suite pass now; their xfail entries are removed (draft-04, -06, -07, 2019-09).

## Decisions

- **Keywords are told apart from property names**, so `properties`, `definitions`, `$defs`, `patternProperties`, `dependencies` and `dependentSchemas` are handled as maps.
- **`subschemas()` is a generator.** It adds no stack frame, so the depth limit of `walk()` still raises `JsonSchemaDefinitionException` before Python's recursion limit.
- **Both lists apply to every draft**, which keeps one traversal. A custom keyword that maps names to schemas, such as `x-defs`, is walked like a schema, so an entry in it named like a data keyword is skipped as data.
- **Other unknown keywords are walked as before**, so subschemas kept under a custom keyword and referred to by `$id` still work.

## Behavior changes

- An `$id` inside such a value, or inside an entry named like a data keyword in a custom keyword, is no longer registered. A `$ref` to it is loaded through the handlers like any other URI (in the CHANGELOG).
- A `$ref` that points into a data value, such as `#/properties/n/default`, still works. A relative `$ref` inside that value now resolves against the document's base URI, not against an `$id` around the value. Using data as a schema is outside what the spec defines.

## Tests

`tests/test_ref_data_keywords.py`. On `master`, 14 of the 18 cases fail. The 4 cases of `test_property_named_like_data_keyword_is_schema` pass there and guard against skipping properties named like data keywords.
