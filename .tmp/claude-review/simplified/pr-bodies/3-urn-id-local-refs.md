Fixes #{I_URN}.

Based on #{P_DATA}. Overview: #{META}.

**Merge after horejsek/python-fastjsonschema#224 (unique function names).** Under a root `$id` like `urn:example:root`, `#foo` now resolves to `urn:example:root#foo`. Without horejsek/python-fastjsonschema#224, that URI gets the same generated function name as `urn:example:root:foo`. The second commit adds a test for that case and marks it as a strict expected failure until that PR is in.

**Needs #{P_DATA}.** Without it, `walk()` also rewrites a `$ref` inside a `const` or `default` value. Under a `urn:` `$id`, `urljoin` used to leave `{"$ref": "#"}` there unchanged by accident. `join_uri()` alone would turn it into `{"$ref": "urn:example:root#"}`, so equal data would be rejected. `test_ref_object_in_data_keyword_under_urn_id_is_data` covers that.

`urllib.parse.urljoin` returns a relative reference unchanged when the scheme of the base URI is not in `urllib.parse.uses_relative`, for example `urn:`, `tag:` or `s3:`. So local refs (`#`, `#/definitions/...`) and plain-name `$id`s (`#foo`) inside such a subschema resolved against the root schema.

## Changes

- `join_uri()`: for a ref that starts with `#` and a base URI with such a scheme, it keeps the base URI and replaces its fragment, as RFC 3986 §5.2.2 defines. Everything else still goes through `urljoin`. All four `urljoin` calls in `ref_resolver.py` use it.

## Decisions

- **Fix in fastjsonschema, not in `urljoin`.** `python/cpython#63028` has been open since 2013. Adding schemes to the global `uses_relative` would change `urljoin` for the whole process.
- **Only refs starting with `#`, and only for schemes outside `uses_relative`.** Full RFC 3986 resolution would also change other relative refs, which this bug doesn't need. For `http:` and the like, `urljoin` already works and normalizes the URI (for example, it lowercases the scheme).
- **`base.partition('#')`, not `urldefrag`.** `urldefrag` normalizes the URI only when it has a fragment, differently per Python version.

## Behavior changes (in the CHANGELOG)

- A `#...` ref inside such a subschema whose target exists only in the root schema now raises `JsonSchemaDefinitionException`, as with an `http:` `$id`.
- For a root `$id` with such a scheme, `compile_to_code()` names the functions for `#...` refs after the root `$id`. `"$ref": "#"` no longer generates a second copy of the root function.

## Tests

`tests/test_ref_urn.py`. On #{P_DATA}, the cases of every test except two fail:
- `test_join_uri` can't run there, because `join_uri()` is new.
- `test_ref_object_in_data_keyword_under_urn_id_is_data` passes there. It is the guard for the dependency above, and it fails if this change is applied without #{P_DATA}.
