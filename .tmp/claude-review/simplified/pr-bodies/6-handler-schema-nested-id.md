Fixes #{I_HANDLER}.

Based on #{P_REL}, and needs it and #{P_UNCHANGED}. Release it together with #{P_UNCHANGED} (see there). Overview: #{META}.

Since `c9a311e` (horejsek/python-fastjsonschema#219, in 2.22.3), `walk()` doesn't resolve the `$ref`s of a schema loaded through a handler. It skips them so that the generator doesn't resolve a relative `$ref` twice (horejsek/python-fastjsonschema#218). The generator then resolves them against the URI of the loaded document, so a `$ref` inside a subschema with its own `$id` ignored that `$id`. 2.22.0 to 2.22.2 resolved it correctly.

## Changes

- `walk()` resolves the refs of a loaded schema like those of the main schema, and the `rewrite_refs` special case goes away. That is safe now: #{P_UNCHANGED} leaves the schema unchanged, and #{P_REL} resolves each URI once. The objects that handlers return stay unchanged too, so a handler can return the same objects to every `compile()` (the test of horejsek/python-fastjsonschema#219).
- **The base URI of a loaded schema stays the URI it was loaded from, whatever its own `$id` says**, as in 2.22.3 and in `jsonschema` 4.26. The schema is still registered under that `$id`, so a `$ref` to it finds the loaded schema. The `$id`s of its subschemas apply as in the main schema.
- `resolving()` copies what a handler returns, with `copy_document()`. `walk()` resolves the refs of an object once, so an object in two loaded documents would otherwise get the base URI of only one of them. `copy_document()` stops at the depth limit of `walk()`, so a deeply nested document still raises `JsonSchemaDefinitionException`, and it turns any mapping into a `dict`.
- A `$ref` that isn't a valid URI stays unresolved, as horejsek/python-fastjsonschema#219 did for loaded schemas, now in the main schema too. So such a `$ref` inside an unknown keyword no longer makes `compile()` fail in a schema with an `$id`. `_expand_refs()` shows it as written in the definition of an error. A `$ref` that is used still fails with `ValueError`.
- `walk()` remembers the objects it walked instead of their URIs, so with `cache=False` each new copy of a loaded document is walked too.

## Decisions

- **Root `$id` of a loaded schema:** RFC 3986 would resolve it against the retrieval URI (`dir/main.json` with `"$id": "dir/main.json"` → `dir/dir/…`). 2.22.3 and `jsonschema` keep the retrieval URI instead. Repository-style handlers rely on that, and this PR keeps it.

## Tests

`tests/test_ref_handlers.py`. On #{P_REL} and on `master`, 8 of 24 cases fail:
- `test_ref_in_handler_loaded_schema_uses_id_of_its_subschema` (the regression);
- `test_handler_loaded_schema_without_cache`;
- `test_invalid_uri_in_unknown_keyword_of_schema_with_id`.

The other 16 pass there and guard what 2.22.3 got right: the root `$id` rule above, horejsek/python-fastjsonschema#218 and horejsek/python-fastjsonschema#219, and objects shared by handlers.
