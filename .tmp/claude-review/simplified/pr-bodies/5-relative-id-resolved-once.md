Fixes #{I_REL}.

Based on #{P_UNCHANGED}, and needs it: the generator now uses the `$ref`s that `walk()` resolved, as `get_ref()` returns them. #{P_HANDLER} builds on this one. Overview: #{META}.

A relative `$id` with a directory, such as `schemas/item.json`, was applied more than once. `urljoin(uri, uri)` returns `uri` only for absolute URIs and for paths without a directory. So refs below such an `$id` resolved to `schemas/schemas/item.json`, and `compile()` didn't return for a subschema with such an `$id` that refers to itself.

## Changes

Every URI is resolved once:
- `walk()` doesn't apply the root `$id` to itself. `from_schema()` already starts the resolver in that scope and says so with `base_uri_is_id`.
- `resolving()` and `in_scope()` take `resolved=True` for a URI that is already resolved: the URIs the generator passes, and the document URI.
- `generate_ref()` and `_expand_refs()` use the `$ref`s that `walk()` resolved as they are (`is_resolved()`). Every other `$ref` is resolved against the scope as before.
- `walk()` marks every subschema with an `$id` as walked, so `resolving()` doesn't walk and register it again.

## Decisions

- **The root `$id` is skipped by provenance, not by comparing strings.** A caller of `RefResolver(base_uri, schema)` may pass a retrieval URI that equals a relative root `$id`. There the `$id` is still applied, as on `master`.
- **`resolved` and `id_applied` are keyword-only.**

## Behavior changes (in the CHANGELOG)

- A nested relative `$id` is no longer also registered under the doubled URI. A `$ref` to the doubled URI is loaded through the handlers.

## Tests

`tests/test_ref_relative_id.py`. On #{P_UNCHANGED}, 16 of 18 cases fail; the self-referencing ones hang there (run with a timeout). The 2 cases of `test_resolver_applies_root_id_to_base_uri` pass there. They guard the absolute-`$id` behaviour and a retrieval URI passed to `RefResolver` directly.
