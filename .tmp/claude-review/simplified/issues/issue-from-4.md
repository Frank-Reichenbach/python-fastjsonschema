TITLE: $ref inside allOf, anyOf, oneOf or items ignores the $id of its subschema

## Summary

A `$ref` inside `allOf`, `anyOf`, `oneOf` or an array-form `items` ignores the `$id` of the subschema it is in and resolves against the base URI of an outer schema. Validation then accepts invalid data, rejects valid data, or `compile()` fails. An `$id` inside such an array isn't registered either, so a `$ref` to it is loaded through a handler or `urlopen`, or gives `Unresolvable ref` for a plain name such as `#int`.

This affects every draft. 18 cases of the official test suite fail because of it. 2.22.2, 2.22.3 and master behave the same; it is not a regression.

## Reproduction

```python
import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)


def node(v):
    return {
        "$id": "http://example.com/node.json",
        "definitions": {"x": {"type": "integer"}},  # "#/definitions/x" inside node.json
        "properties": {"v": v},
    }


for label, v in (("$ref", {"$ref": "#/definitions/x"}),
                 ("allOf: [$ref]", {"allOf": [{"$ref": "#/definitions/x"}]})):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": {"x": {"type": "string"}},  # "#/definitions/x" in the root
        "properties": {"p": node(v)},
    }
    validate = fastjsonschema.compile(schema)
    for data in ({"p": {"v": 1}}, {"p": {"v": "a"}}):
        try:
            validate(data)
            print(f"{label:14} {data} -> valid")
        except fastjsonschema.JsonSchemaException as exc:
            print(f"{label:14} {data} -> {exc.message}")
```

## Actual result

On 2.22.3 and master:

```text
fastjsonschema 2.22.3
$ref           {'p': {'v': 1}} -> valid
$ref           {'p': {'v': 'a'}} -> data.p.v must be integer
allOf: [$ref]  {'p': {'v': 1}} -> data.p.v must be string
allOf: [$ref]  {'p': {'v': 'a'}} -> valid
```

Wrapped in `allOf`, `#/definitions/x` resolves against the root (string), not `node.json` (integer).

Further cases, using `node()` from above (draft-07, root `x` is a string) unless stated. The `$id` cases use an `http` handler that raises:

| case | actual (2.22.2, 2.22.3, master) | expected |
|---|---|---|
| `allOf: [$ref]`, data `1` | invalid | valid |
| `anyOf: [$ref]`, data `1` | invalid | valid |
| `oneOf: [$ref]`, data `1` | invalid | valid |
| `items: [$ref]`, data `[1]` | invalid | valid |
| `allOf: [{"properties": {"w": $ref}}]`, data `{"w": 1}` | invalid | valid |
| `allOf: [$ref]` in draft-04 with `id` | invalid | valid |
| `allOf: [$ref]` without `$schema` | invalid | valid |
| `allOf: [$ref]`, root without `definitions` | `Unresolvable ref: definitions` | valid |
| `allOf: [$ref]`, node.json inside `a.json` (`x` a string), which the root refers to | invalid | valid |
| root `$id` `http://example.com/root.json`, `anyOf: [{"$id": "item.json", "type": "integer"}, …]` in `definitions`, `"$ref": "item.json"` | handler called for `http://example.com/item.json` | valid |
| `allOf: [{"$id": "#int", "type": "integer"}]` in `definitions`, `"$ref": "#int"` | `Unresolvable ref: int` | valid |

## Expected behavior and why

Inside `node.json`, `#/definitions/x` should refer to its `definitions`, in an array or not, and an `$id` in an array should identify its subschema like any other. Draft-07 Core:

- [§8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2): `$id` sets "the base URI that other URI references within the schema are resolved against", with no exception for arrays.
- [§8.3.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3.2): "dereferencing a "$ref" reference involves first resolving its value as a URI reference against the current base URI", and "If the resulting URI identifies a schema within the current document, ..., then that schema SHOULD be used automatically."
- [§8.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3): "implementations SHOULD NOT assume they should perform a network operation when they encounter a network-addressable URI."

## Cause

Links point to 2.22.2 (`b88fa37`); master has the same logic.

[`RefResolver.walk`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L181-L204) walks the schema before code generation. It resolves each `$ref` against the base URI in effect there ([lines 192–194](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L192-L194)) and registers each `$id` in the store ([line 197](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L197)). But it only descends into values that are objects ([lines 198–200](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L198-L200), [202–204](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L202-L204)), so it has never visited subschemas in arrays (since 2018, `3b964b0`).

A `$ref` that `walk` skipped is resolved in [`CodeGenerator.generate_ref`, line 227](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L227), against the base URI of the function being generated. `$id`s inside that function are ignored. A `$ref` to an `$id` that `walk` skipped isn't found in the store, and [`RefResolver.resolving`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L138-L143) passes it to [`resolve_remote`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L53-L68), which calls the handler or `urlopen`.

Because of this, `tests/json_schema/` marks draft6 and draft7 `ref.json` as expected failures: "refs with relative uris and defs", "relative refs with absolute uris and defs" (`$ref` in `allOf`), and in draft7 "ref to if", "ref to then", "ref to else" (`$id` in `allOf`).

## Workaround

Inside these arrays, write a `$ref` as an absolute URI, such as `"http://example.com/node.json#/definitions/x"`. Don't put an `$id` inside them; move the subschema to `definitions` and refer to it from the array.

## Environment

fastjsonschema 2.22.2, 2.22.3 and master (2.22.3 plus one unrelated fix), CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
