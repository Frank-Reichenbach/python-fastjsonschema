TITLE: $ref under a relative $id such as schemas/item.json resolves to schemas/schemas/item.json

## Summary

fastjsonschema applies a relative `$id` with a directory, such as `schemas/item.json`, more than once, so a `$ref` below it resolves to `schemas/schemas/item.json` and longer:

- As the root `$id`, it breaks every `$ref` resolved against it, local ones such as `#/definitions/count` included (an absolute `$ref` still works). `compile()` passes the doubled URI to the handler, or to `urlopen` (`ValueError: unknown url type`).
- As the `$id` of a subschema with a `$ref` to itself (`"$ref": "#"`), `compile()` never returns on 2.22.3 and master: the generator keeps adding functions for `schemas/node.json`, `schemas/schemas/node.json`, …

`file:schemas/item.json` behaves the same. Not affected: an absolute `$id` (`https://example.com/schemas/item.json`, `file:///schemas/item.json`), an absolute path (`/schemas/item.json`), a name without a directory (`item.json`). The same doubling was [reported for 2.19.1](https://github.com/horejsek/python-fastjsonschema/issues/56#issuecomment-1913734224).

## Reproduction

```python
import fastjsonschema

print("fastjsonschema", fastjsonschema.VERSION)


def handler(uri):
    raise RuntimeError("handler called with " + uri)


schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "schemas/item.json",
    "definitions": {"count": {"type": "integer"}},
    "properties": {"count": {"$ref": "#/definitions/count"}},
}

try:
    validate = fastjsonschema.compile(schema, handlers={"": handler})
except RuntimeError as exc:
    print("compile error:", exc)
else:
    for data in ({"count": 1}, {"count": "a"}):
        try:
            validate(data)
            print(data, "-> valid")
        except fastjsonschema.JsonSchemaValueException as exc:
            print(data, "-> invalid:", exc.message)
```

## Actual result

2.22.3 and master:

```text
fastjsonschema 2.22.3
compile error: handler called with schemas/schemas/schemas/schemas/schemas/schemas/item.json
```

2.22.2 repeats `schemas/` more often. Expected:

```text
fastjsonschema 2.22.3
{'count': 1} -> valid
{'count': 'a'} -> invalid: data.count must be integer
```

Further cases (draft-07, raising handlers for `""` and `file`, each run under `timeout 10`):

| Case | 2.22.3 and master | Expected |
|---|---|---|
| `$id: a/b/item.json`, `$ref: other.json` | handler called with `a/b/a/b/a/b/a/b/a/b/a/b/other.json` | handler called with `a/b/other.json` |
| `properties.p` with `$id: schemas/node.json` and `$ref: "#"` below it | `compile()` doesn't return (killed after 10 s); 2.22.2: handler called with `schemas/schemas/schemas/schemas/node.json` | valid |
| `$id: file:schemas/item.json`, `$ref: #/definitions/count` | handler called with `file:schemas/schemas/schemas/schemas/schemas/schemas/item.json` | valid |

## Expected behavior and why

Each `$id` and `$ref` is resolved once: "A subschema's "$id" is resolved against the base URI of its parent schema" ([Draft-07 Core §8.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2)), and a `$ref` "as a URI reference against the current base URI per RFC 3986" ([§8.3.2](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.3.2)).

Without parent or retrieval URI, [RFC 3986 §5.1](https://www.rfc-editor.org/rfc/rfc3986#section-5.1) (via [§8.1](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.1)) leaves the base URI to the application. Against any absolute base, `schemas/item.json` is applied once ([RFC 3986 §5.2.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2.2), [§5.2.3](https://www.rfc-editor.org/rfc/rfc3986#section-5.2.3)). With the relative `$id` itself as base, as fastjsonschema does for `item.json`, the expected URIs are `schemas/item.json#/definitions/count` and `a/b/other.json`. No reading resolves the same URI repeatedly. An absolute root `$id` is only recommended ([§8.2.1](https://json-schema.org/draft-07/draft-handrews-json-schema-01#rfc.section.8.2.1), SHOULD); any URI reference is valid (§8.2).

## Cause

fastjsonschema resolves URIs with `urllib.parse.urljoin`, at several points a second time. That goes unnoticed while `urljoin(uri, uri) == uri`, as for the unaffected forms; `urljoin('schemas/item.json', 'schemas/item.json')` is `schemas/schemas/item.json`. Links point to 2.22.2 (`b88fa37`):

1. `from_schema` uses the root `$id` as base URI ([L109](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L109)) and the resolver starts in that scope ([L94](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L94)). `walk` then applies the root `$id` again ([L196](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L196) via `in_scope`, [L121](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L121)), registers the root under `schemas/schemas/item.json` and resolves the `$ref`s below against it.
2. The generator passes already resolved URIs to `resolving` ([`generator.py` L154](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L154)), which resolves them against the current scope again ([L133](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L133)) and enters the document scope the same way ([L150](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/ref_resolver.py#L150)).
3. `generate_ref` ([`generator.py` L227](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L227)) and `_expand_refs` ([`generator.py` L332](https://github.com/horejsek/python-fastjsonschema/blob/b88fa37cd46bb81e8d9dce91a7e1bc4debedd3a2/fastjsonschema/generator.py#L332)) resolve a `$ref` that `walk` already resolved.

For a subschema with such an `$id`, `resolving` walks it again under each longer URI and registers it there, so each `$ref` finds its target and the generator never stops adding functions. Before horejsek/python-fastjsonschema#219 (in 2.22.3), that walk also resolved the `$ref` again, so the target was missing and the handler was called.

## Workaround

Use an absolute `$id`, such as `https://example.com/schemas/item.json`, with a handler for its scheme. An `$id` without a directory, or none, works too.

## Environment

fastjsonschema 2.22.2, 2.22.3 and master (2.22.3 plus one unrelated fix), CPython 3.14 on macOS.

Found and analyzed with AI assistance (Claude Code and Codex).
