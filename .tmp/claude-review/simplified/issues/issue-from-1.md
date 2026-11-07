TITLE: Local $ref inside a urn: $id subschema resolves against the root schema

## Summary

Inside a subschema (not the root) whose `$id` has a scheme not listed in `urllib.parse.uses_relative`, such as `urn:`, `tag:` or `s3:`, local references point to the root schema:

- `"$ref": "#"` and `"$ref": "#/definitions/x"` resolve against the root schema.
- A plain-name `"$id": "#foo"` collides with a `#foo` in the root schema.

Validation then accepts invalid data, rejects valid data, or the schema fails to compile. `http:`, `https:` and `file:` ids are not affected. Every supported draft is affected (Draft-04 to 2020-12, and no `$schema`). 2.22.2, 2.22.3 and master behave the same.

## Reproduction

```python
import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)

NODE = {
    "$id": "urn:example:node",
    "type": "object",
    "properties": {
        "all": {"type": "array", "items": {"$ref": "#"}},  # "#" = this node schema
        "eq": {"type": "array", "maxItems": 2},
    },
    "additionalProperties": False,
}
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {"p": {"$ref": "urn:example:node"}},
    "definitions": {"node": NODE},
}

validate = fastjsonschema.compile(schema)
for data in ({"p": {"eq": [1, 2, 3]}}, {"p": {"all": [{"eq": [1, 2, 3]}]}}):
    try:
        validate(data)
        print(data, "-> valid")
    except fastjsonschema.JsonSchemaException as exc:
        print(data, "->", exc.message)
```

## Actual result

On master (2.22.3 plus one unrelated fix):

```text
fastjsonschema 2.22.3
{'p': {'eq': [1, 2, 3]}} -> data.p.eq must contain less than or equal to 2 items
{'p': {'all': [{'eq': [1, 2, 3]}]}} -> valid
```

The second value breaks `maxItems` behind `"$ref": "#"`, but its element is checked against the root schema, which accepts it (no `p` property). The expected result, `data.p.all[0].eq must contain less than or equal to 2 items`, is what you get with `http://example.com/node.json` as `$id` and `$ref`. If the root also has `"additionalProperties": false`, the valid `{"p": {"all": [{"eq": [1, 2]}]}}` is rejected instead.

Further cases, same results on 2.22.2, 2.22.3 and master:

1. `NODE` from the reproduction, data `{"p": {"all": [{"eq": [1, 2, 3]}]}}`.
2. Root `properties.p` is `{"$id": "urn:example:item", "properties": {"v": {"$ref": "#/definitions/x"}}, "definitions": {"x": {"type": "integer"}}}`.
3. Root `definitions` holds `{"$id": "#foo", "type": "string"}` and `{"$id": "urn:example:item", "definitions": {"i": {"$id": "#foo", "type": "integer"}}}`. Root `properties.r` is `{"$ref": "#foo"}`. Nothing refers to the `urn:` subschema.
4. As 3, but the `urn:` subschema also has `"properties": {"x": {"$ref": "#foo"}}` and root `properties` also has `"p": {"$ref": "urn:example:item"}`.

| case | actual on master | expected |
|---|---|---|
| 1, `NODE` under `definitions`, loaded through `handlers`, or with `fast_fail=False` | valid | invalid |
| 1, `NODE` in place of `p`: Draft-04 (`id`), Draft-06, Draft-07, 2019-09, 2020-12, no `$schema` | valid | invalid |
| 1, `$id` `tag:example.com,2026:node` or `s3://bucket/node.json` | valid | invalid |
| 1, `$id` `http://example.com/node.json` or `file:///schemas/node.json` (control) | invalid | invalid |
| 2, root also defines `x` as string; `{"p": {"v": 1}}` | invalid | valid |
| 2, root also defines `x` as string; `{"p": {"v": "a"}}` | valid | invalid |
| 2, root lacks `x`; `{"p": {"v": 1}}` | compile error `Unresolvable ref: definitions` | valid |
| 3, `{"r": "a"}` | invalid | valid |
| 3, `{"r": 1}` | valid | invalid |
| 4, properties order `r, p`; `{"r": "a"}` / `{"p": {"x": 1}}` | invalid / valid | valid / valid |
| 4, properties order `p, r`; `{"r": "a"}` / `{"p": {"x": 1}}` | valid / invalid | valid / valid |

## Expected behavior and why

Inside a subschema with `"$id": "urn:example:node"`, `"$ref": "#"` should refer to that subschema. Draft-07 Core:

- [§8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2): `$id` sets "the base URI that other URI references within the schema are resolved against".
- [§8.3.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3.2): "dereferencing a "$ref" reference involves first resolving its value as a URI reference against the current base URI".
- [§8.2.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2.3): a plain-name `$id` like `#foo` is resolved against the base URI of the subschema it is in.
- [§8.2.4](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2.4): for a subschema with `"$id": "urn:uuid:ee564b8a-…"`, the example lists `urn:uuid:ee564b8a-…#`, so `#` inside it means the subschema itself.

[RFC 3986 §5.2.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2.2) resolves a fragment-only reference the same way for every scheme: keep the base URI, replace the fragment. `#` against `urn:example:node` gives `urn:example:node#`. The [deviations listed in the `fastjsonschema/__init__.py` docstring](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/__init__.py#L66-L76) don't include `$id`/`$ref` resolution.

Resolving these refs as with an `http:` `$id` changes two results that don't depend on the data:

- A ref inside such a subschema whose target exists only in the root schema compiles today and uses the root's target. It should raise `JsonSchemaDefinitionException`.
- When the root `$id` has such a scheme, the function names in `compile_to_code()` change, and `"$ref": "#"` no longer generates a second copy of the root function named `validate`.

## Cause

`fastjsonschema/ref_resolver.py` builds URIs with `urllib.parse.urljoin` in four places (links to 2.22.2, `b88fa37`):

- [`in_scope`, line 121](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L121) sets the base URI on entering an `$id`.
- [`resolving`, line 133](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L133) resolves a `$ref`.
- [`resolving`, line 153](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L153) looks up a plain-name identifier.
- [`walk`, line 194](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L194) rewrites `$ref` values.

For a base scheme not in `uses_relative`, `urljoin` returns the reference unchanged:

```python
>>> urljoin("http://example.com/node.json", "#")
'http://example.com/node.json#'
>>> urljoin("urn:example:node", "#")
'#'
>>> urljoin("urn:example:node", "#/definitions/x")
'#/definitions/x'
```

So `#` and `#/definitions/x` resolve against the root document. In `compile_to_code(schema)` for the reproduction, the loop in `validate_urn_example_node` calls `validate(data__all_item, ...)` instead of `validate_urn_example_node`. A plain-name `$id` in the `urn:` subschema is stored under the bare key `#foo`, the same key as a root `#foo`, so the one stored last wins.

The official test suite misses this: its draft6 and draft7 URN tests in `ref.json` put the `urn:` `$id` on the root, where the unqualified ref happens to reach the right schema. The draft2019-09 test "URN ref with nested pointer ref" has the `urn:` `$id` on a subschema but fails for other reasons: the root has a `$ref` next to `$defs`, where fastjsonschema doesn't register the `urn:` subschema (reported separately), and fastjsonschema ignores an `$id` next to a `$ref`, which 2019-09 applies ([2019-09 Core §8.2.2](https://json-schema.org/draft/2019-09/json-schema-core.html#rfc.section.8.2.2)). `tests/json_schema/` marks the draft6, draft7 and draft2019-09 `ref.json` as expected failures.

## Workaround

Inside such a subschema, write local refs as absolute refs to its own `$id` (`"urn:example:node#"`, `"urn:example:node#/definitions/x"`), and use those instead of plain-name `$id`s. Or give the subschema an `$id` with a scheme in `uses_relative`, such as `https:`.

## Environment

fastjsonschema 2.22.2, 2.22.3 and master; CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
