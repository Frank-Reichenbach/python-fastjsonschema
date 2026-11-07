TITLE: $id of a schema in definitions next to a $ref is ignored

## Summary

`RefResolver.walk` doesn't look inside a schema object that has a `$ref`. If that object also has `definitions` and another `$ref` points into them, the schemas there lose their `$id`:

- A `$ref` inside such a schema resolves against the outer base URI instead of that `$id`.
- A `$ref` to that `$id` is loaded through a handler (or downloaded) instead of resolving to the schema.

Validation then accepts invalid data or rejects valid data. A common form is a root schema that is a `$ref` with its definitions next to it: `{"$ref": "#/definitions/a", "definitions": {"a": {...}}}`.

It affects draft-04 (`id`), draft-06, draft-07 and schemas without `$schema` (validated as 2019-09). 2.22.2, 2.22.3 and master give the same results.

## Reproduction

```python
import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)

schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$ref": "#/definitions/a",
    "definitions": {
        "a": {
            "$id": "http://example.com/node.json",
            "definitions": {"y": {"type": "integer"}},  # "#/definitions/y" in node.json
            "properties": {"b": {"$ref": "#/definitions/y"}},
        },
        "y": {"type": "string"},  # "#/definitions/y" in the root
    },
}

validate = fastjsonschema.compile(schema)
for data in ({"b": 1}, {"b": "x"}):
    try:
        validate(data)
        print(data, "-> valid")
    except fastjsonschema.JsonSchemaException as exc:
        print(data, "->", exc.message)
```

## Actual result

On 2.22.3 and master (2.22.2 prints the same):

```text
fastjsonschema 2.22.3
{'b': 1} -> data.b must be string
{'b': 'x'} -> valid
```

`#/definitions/y` inside `node.json` resolves against the root schema, whose `y` requires a string. Expected: `{'b': 1}` valid, `{'b': 'x'}` -> `data.b must be integer`.

Further cases. `node` is `definitions.a` of the reproduction (with `id` for draft-04), the root has `"definitions": {"y": {"type": "string"}}`, and the `http` handler raises:

| case | actual on master | expected |
|---|---|---|
| draft-07, root `$ref`, data `{"b": "x"}` | valid | invalid |
| same without `$schema` | valid | invalid |
| same in draft-04 (`id`) | valid | invalid |
| same in draft-06 | valid | invalid |
| draft-07, `"properties": {"p": {"$ref": "#/properties/p/definitions/a", "definitions": {"a": node}}}`, data `{"p": {"b": "x"}}` | valid | invalid |
| draft-07, root `$ref`, data `{"b": 1}` | invalid: must be string | valid |
| draft-07, root `"$ref": "http://example.com/node.json"`, data `{"b": "x"}` | handler called with `http://example.com/node.json` | invalid, no handler call |
| first row's schema loaded through a handler | valid | invalid |
| control, draft-07: `"b": {"$id": "http://example.com/other.json", "$ref": "#/definitions/y"}`, data `{"b": 1}` | invalid: must be string | invalid: must be string |

## Expected behavior and why

`#/definitions/a` is a JSON pointer into the document. It identifies the schema at that location, and that schema's own `$id` applies within it.

- [Draft-07 Core §8.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3): `$ref`, "Resolved against the current URI base, it identifies the URI of a schema to use." [§8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2): "The "$id" keyword defines a URI for the schema, and the base URI that other URI references within the schema are resolved against."
- §8.3 also says "All other properties in a "$ref" object MUST be ignored." So `definitions` next to the `$ref` validates nothing, and an `$id` directly next to it doesn't change the base URI (the control row; draft-07 suite `ref.json`, "$ref prevents a sibling $id from changing the base uri"). It doesn't remove the schemas under `definitions` from the document: a JSON Pointer still identifies them ([RFC 6901 §4](https://www.rfc-editor.org/rfc/rfc6901#section-4)), and "If the resulting URI identifies a schema within the current document [...] then that schema SHOULD be used automatically" ([Draft-07 Core §8.3.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3.2)).
- Draft-06 says the same ([§8](https://json-schema.org/draft-06/draft-wright-json-schema-01.html#rfc.section.8), [§9.2](https://json-schema.org/draft-06/draft-wright-json-schema-01.html#rfc.section.9.2)). Draft-04 uses `id` to "alter the base URI against which a reference must resolve" ([Draft-04 Core §7.1](https://json-schema.org/draft-04/json-schema-core.html#rfc.section.7.1)) and ignores the other members of a `$ref` object ([JSON Reference §3](https://datatracker.ietf.org/doc/html/draft-pbryan-zyp-json-ref-03#section-3)).
- 2019-09 goes further: "other keywords can appear alongside of "$ref"" ([2019-09 Core §8.2.4.1](https://json-schema.org/draft/2019-09/json-schema-core.html#rfc.section.8.2.4.1)), and an `$id` there "also serves as the base URI for relative URI-references in keywords within the schema resource" ([§8.2.2](https://json-schema.org/draft/2019-09/json-schema-core.html#rfc.section.8.2.2)), the `$ref` next to it included. `walk` ignores such an `$id` in every draft, so 2019-09 schemas (and schemas without `$schema`) get the draft-07 behaviour there. In the official 2019-09 suite, 11 outcomes in `ref.json`, `refRemote.json`, `unevaluatedItems.json` and `unevaluatedProperties.json` fail on master because of this, for example "order of evaluation: $id and $ref" and "remote HTTP ref with nested absolute ref"; `tests/json_schema/` marks these files as expected failures.

## Cause

Links point to release 2.22.2 (`b88fa37`); master has the same logic.

[`RefResolver.walk`](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L181-L204) registers an `$id` in the store only for an object without `$ref` ([line 197](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L197)). For an object with a `$ref`, it only rewrites that `$ref` against the base URI in effect ([lines 192–194](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L192-L194)) and, unlike the other branches ([line 198](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L198), [line 202](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L202)), doesn't descend into its other values. No `$id` under them is registered and no `$ref` under them rewritten.

The generator still reaches `#/definitions/a` through the pointer. [`CodeGenerator.generate_ref`, line 227](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L227) resolves the unrewritten `$ref` against the URI of the function being generated, the document URI, so the `$id` of `a` is ignored. `http://example.com/node.json` isn't in the store, so [`RefResolver.resolving`, line 143](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L143) loads it as a remote schema.

`walk` has stopped at a `$ref` since 2018 (`f0c8a0b`).

## Workaround

Move the `$ref` into `allOf`, so that the definitions sit next to `allOf`:

```json
{
    "allOf": [{"$ref": "#/definitions/a"}],
    "definitions": {"a": {...}}
}
```

This gives the expected result in the reproduction on 2.22.2, 2.22.3 and master. `walk` doesn't reach a `$ref` inside `allOf` either, but this one points into the root schema, so the function's base URI is the right one.

## Environment

fastjsonschema 2.22.2, 2.22.3 and master (2.22.3 plus one unrelated fix); CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
