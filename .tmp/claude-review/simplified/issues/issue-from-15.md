TITLE: compile() rewrites the $ref values of the schema in place, so reusing it under another $id fails

## Summary

`compile()` and `compile_to_code()` modify their input: `RefResolver.walk` replaces every `$ref` it reaches with the URI resolved against the base URI of that compilation. A later compilation of the same objects under another base URI uses the old one. Reusing schema fragments, such as a "nullable ref" constant, is common in Python code.

| Case | 2.22.3 and master | Expected |
|---|---|---|
| Object shared by two schemas with different `$id`s (below) | second `compile()` loads the first schema's URI through a handler, or downloads it | each resolves against its own `$id` |
| Schema compiled again after its `$id` changed | loads the old `$id` | uses the new `$id` |
| `$ref` inside a nested subschema with `"$id": "schemas/main.json"`, compiled twice | second compile: `ValueError: unknown url type: 'schemas/schemas/schemas/main.json'` | works |

A root `$id` with a directory fails already on the first compile; that is a separate bug.

## Reproduction

```python
import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)

def no_download(uri):
    raise RuntimeError("handler called with " + uri)

shared = {"$ref": "#/definitions/x"}
draft7 = "http://json-schema.org/draft-07/schema#"
one = {"$schema": draft7, "$id": "http://example.com/one.json",
       "definitions": {"x": {"type": "integer"}}, "properties": {"p": shared}}
two = {"$schema": draft7, "$id": "http://example.com/two.json",
       "definitions": {"x": {"type": "string"}}, "properties": {"p": shared}}

fastjsonschema.compile(one, handlers={"http": no_download})
print("shared:", shared)
try:
    print("two:", fastjsonschema.compile(two, handlers={"http": no_download})({"p": "a"}))
except Exception as exc:
    print("two:", type(exc).__name__, exc)
```

## Actual result

```text
fastjsonschema 2.22.3
shared: {'$ref': 'http://example.com/one.json#/definitions/x'}
two: RuntimeError handler called with http://example.com/one.json
```

Expected: `shared: {'$ref': '#/definitions/x'}` and `two: {'p': 'a'}`.

## Expected behavior and why

Compiling shouldn't modify its input; the documentation of `compile()` doesn't say it does. In `two`, `#/definitions/x` is resolved against `http://example.com/two.json` ([Draft-07 Core §8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2)).

## Cause

- [`RefResolver.walk`, lines 206–209](https://github.com/horejsek/python-fastjsonschema/blob/4999d6b7923921274c4cdfe326e62e8c78f5a19c/fastjsonschema/ref_resolver.py#L206-L209) writes the resolved URI into the schema.
- [`generate_ref`, line 227](https://github.com/horejsek/python-fastjsonschema/blob/4999d6b7923921274c4cdfe326e62e8c78f5a19c/fastjsonschema/generator.py#L227) and [`_expand_refs`, line 332](https://github.com/horejsek/python-fastjsonschema/blob/4999d6b7923921274c4cdfe326e62e8c78f5a19c/fastjsonschema/generator.py#L332) read it from there. An absolute value then wins over the current base URI; a relative one is resolved against it again.

## Workaround

`fastjsonschema.compile(copy.deepcopy(schema))`.

## Environment

fastjsonschema 2.22.2, 2.22.3 and master (2.22.3 plus one unrelated fix), CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
