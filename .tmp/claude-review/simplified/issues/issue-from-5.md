TITLE: Regression in 2.22.3: $ref in a handler-loaded schema ignores the $id of its subschema

## Summary

In a schema loaded through `handlers`, a `$ref` inside a subschema with its own `$id` resolves against the URI of the loaded document instead of that `$id`, so invalid data passes and valid data fails.

2.22.0 and 2.22.2 resolve it correctly; 2.21.2, 2.22.3 and master don't. It came with commit `c9a311e` (`horejsek/python-fastjsonschema#219`, fixing `horejsek/python-fastjsonschema#218`). Embedded, the schema works on master.

## Reproduction

```python
import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)

DOC = {
    "$id": "http://example.com/doc.json",
    "definitions": {"x": {"type": "string"}},  # in doc.json
    "properties": {
        "p": {
            "$id": "http://example.com/node.json",
            "definitions": {"x": {"type": "integer"}},  # in node.json
            "properties": {"v": {"$ref": "#/definitions/x"}},
        },
    },
}

validate = fastjsonschema.compile(
    {"$ref": "http://example.com/doc.json"},
    handlers={"http": lambda uri: DOC},
)
for data in ({"p": {"v": 1}}, {"p": {"v": "a"}}):
    try:
        validate(data)
        print(data, "-> valid")
    except fastjsonschema.JsonSchemaException as exc:
        print(data, "->", exc.message)
```

## Actual result

2.22.3 and master (`4999d6b`, 2.22.3 plus one unrelated fix):

```text
fastjsonschema 2.22.3
{'p': {'v': 1}} -> data.p.v must be string
{'p': {'v': 'a'}} -> valid
```

2.22.2 gives the expected result: the first is valid, the second fails with `data.p.v must be integer`.

Type that `v` requires in further cases (`jsonschema` 4.26 gives Expected):

| Case | 2.22.3 and master | Expected |
|---|---|---|
| Loaded as `schemas/main.json` or `file:schemas/main.json` | string | integer |
| Without the root `$id` | string | integer |
| Subschema `"$id": "node.json"` | string | integer |
| Same, loaded as `schemas/main.json` (also wrong on 2.22.2) | string | integer |
| Without the root `$id`, two `$ref`s into it, `RefResolver(..., cache=False)` | string (2.22.2: for one `$ref`) | integer |

## Expected behavior and why

`#/definitions/x` inside the subschema with `"$id": "http://example.com/node.json"` refers to that subschema's `definitions`. [Draft-07 Core §8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2): `$id` sets "the base URI that other URI references within the schema are resolved against"; it makes no exception for loaded schemas.

Not part of this report: a loaded schema's root `$id`. Its base URI stays the URI it was loaded from, as in 2.22.3 and `jsonschema` (2.22.2 applied the root `$id`).

## Cause

Links go to 2.22.2 (`b88fa37`).

[`RefResolver._ensure_walked`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L162-L167) walks a loaded schema once; [`walk` rewrites each `$ref`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L192-L194) against the current base URI. Since `c9a311e`, `_ensure_walked` calls `walk(schema, rewrite_refs=False)`, which registers the `$id`s but rewrites no `$ref`. [`CodeGenerator.generate_ref`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L227) resolves the `$ref` against the generated function's URI, `http://example.com/doc.json`; the generator doesn't track `$id`s inside a function.

`c9a311e` disabled the rewrite because `generate_ref` resolves a rewritten `$ref` again: in `horejsek/python-fastjsonschema#218`, `main.json#/definitions/string` in `schemas/main.json` became `schemas/schemas/main.json#/definitions/string`. An absolute `$ref`, such as `http://example.com/node.json#/definitions/x`, doesn't have that problem.

## Workaround

Write such a `$ref` as an absolute URI: `"http://example.com/node.json#/definitions/x"`.

## Environment

fastjsonschema 2.21.2, 2.22.0, 2.22.2, 2.22.3, master `4999d6b`; CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
