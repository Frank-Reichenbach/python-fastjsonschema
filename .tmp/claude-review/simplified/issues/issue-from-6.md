TITLE: $ref and $id inside const, enum, default or examples values are treated as part of the schema

## Summary

The values of `const`, `enum`, `default` and `examples` are data, not schemas, but fastjsonschema treats a `$ref` or `$id` inside them as a reference or identifier. Depending on the schema:

- `compile()` fails with `Unresolvable ref`, or with `ValueError` if the `$ref` string isn't a valid URI.
- Data equal to a `const` value is rejected, because the `$ref` inside the value was rewritten.
- `use_default=True` inserts a different value than the schema's `default`.
- An `$id` inside such a value replaces the real subschema with that `$id`.

Such values occur in schemas that describe JSON Reference objects or other schemas. All drafts are affected. 2.22.2, 2.22.3 and master behave the same, so this is not a regression.

## Reproduction

```python
import copy

import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)

POINTER = {"$ref": "#/definitions/x"}  # a JSON Reference object, used here as plain data

for label, schema in (
    ("without $id", {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "properties": {"pointer": {"const": POINTER}},
    }),
    ("with $id", {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "http://example.com/root.json",
        "definitions": {"x": {"type": "string"}},
        "properties": {"pointer": {"const": POINTER}},
    }),
):
    try:
        validate = fastjsonschema.compile(copy.deepcopy(schema))
    except fastjsonschema.JsonSchemaDefinitionException as exc:
        print(f"{label:12} compile error: {exc}")
        continue
    data = {"pointer": copy.deepcopy(POINTER)}
    try:
        validate(data)
        print(f"{label:12} {data} -> valid")
    except fastjsonschema.JsonSchemaException as exc:
        print(f"{label:12} {data} -> {exc.message}")
```

## Actual result

On 2.22.3 and master:

```text
fastjsonschema 2.22.3
without $id  compile error: Unresolvable ref: definitions
with $id     {'pointer': {'$ref': '#/definitions/x'}} -> data.pointer must be same as const definition: {'type': 'string'}
```

Both lines should end in `-> valid`: the schemas are valid and the data equals the `const` value. In the second schema the `const` value became `{"$ref": "http://example.com/root.json#/definitions/x"}`, and the error message shows definition `x` instead of the `const` value.

Further cases (draft-07; `D` is `{"$ref": "#/definitions/x"}`, `S` is `http://example.com/string.json`):

| Case | Actual on master | Expected |
| --- | --- | --- |
| `{"enum": [D]}`, data `D` | compile error: `Unresolvable ref: definitions` | valid |
| `{"type": "object", "examples": [D]}`, data `{}` | compile error: `Unresolvable ref: definitions` | valid |
| `{"default": D}` under a root `$id`, `use_default=True`, data `{}` | inserts `{'$ref': 'http://example.com/root.json#/definitions/x'}` | inserts `D` |
| `{"default": {"$ref": "http://[bad"}}` under a root `$id` | compile error: `ValueError: Invalid IPv6 URL` | compiles |
| `"q": {"const": {"$id": S, "type": "integer"}}` next to `definitions.s = {"$id": S, "type": "string"}`; `"v": {"$ref": S}`, data `{"v": "a"}` | `data.v must be integer` | valid |
| same with `default` instead of `const` | `data.v must be integer` | valid |

## Expected behavior and why

A `$ref` or `$id` inside these values is a plain member, to be compared, inserted and reported as it is. Such an `$id` is not registered, so a `$ref` to its URI is loaded through the `handlers` like any other URI. The same holds for an `$id` in an entry named like one of these keywords inside a custom keyword (for example `"x-defs": {"default": {"$id": ...}}`).

- [Draft-07 Core §4.3.3](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.4.3.3): "Some keywords take schemas themselves, allowing JSON Schemas to be nested". Only those keywords' values are subschemas.
- Draft-07 Validation defines these values as data: `enum` ([§6.1.2](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.6.1.2)) "might be of any value", `const` ([§6.1.3](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.6.1.3)) "MAY be of any type", `default` ([§10.2](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.10.2)) has "no restrictions", and `examples` ([§10.4](https://json-schema.org/draft-07/draft-handrews-json-schema-validation-01#rfc.section.10.4)) is an array of example values.
- The official suite tests this in `optional/id.json` (draft4, draft6, draft7, 2019-09): "id inside an enum is not a real identifier" puts an identifier inside an `enum` and a `const` value next to a real schema with the same identifier. Its case "match $ref to id" fails today because of the `const` value; `tests/json_schema/` marks `id.json` as an expected failure. An `$id` inside an unknown keyword (`optional/unknownKeyword.json`) is a separate question.

## Cause

Links point to release 2.22.2 (`b88fa37`).

- [`RefResolver.walk`, lines 198–204](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L198-L204) descends into every object value, whatever its keyword, so also into `const` and `default` values. There it rewrites a `$ref` against the base URI and registers an `$id` in the store ([lines 192–197](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L192-L197)); `urljoin` raises `ValueError` for `http://[bad`. `walk` skips arrays, so `enum` and `examples` aren't affected here.
- [`CodeGenerator._expand_refs`, lines 326–334](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L326-L334) builds the `definition` for each `JsonSchemaValueException` ([line 322](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L322)). It replaces every object with a `$ref`, in arrays too, by its target, so it also resolves `$ref`s inside `const`, `enum` and `examples` values and fails with `Unresolvable ref` if the target doesn't exist.

`walk` has done this since 2018 (`3b964b0`), `_expand_refs` since 2022 (`84cf29b`).

## Workaround

Don't put objects with a `$ref` or `$id` member into these values. To accept exactly `{"$ref": "#/definitions/x"}`, describe it with keywords instead of `const`:

```json
{
    "type": "object",
    "properties": {"$ref": {"const": "#/definitions/x"}},
    "required": ["$ref"],
    "additionalProperties": false
}
```

## Environment

fastjsonschema 2.22.2, 2.22.3 and master (2.22.3 plus one unrelated fix); CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
