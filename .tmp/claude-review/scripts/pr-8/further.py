from urllib.parse import quote

import fastjsonschema

D7 = "http://json-schema.org/draft-07/schema#"


def check(label, schema, data, **kwargs):
    validate = fastjsonschema.compile(schema, **kwargs)
    try:
        validate(data)
        print(f"{label:46} valid")
    except fastjsonschema.JsonSchemaException:
        print(f"{label:46} invalid")
    except Exception as exc:
        print(f"{label:46} {type(exc).__name__}: {exc}")


def pointer(key):
    return "#/definitions/" + quote(key.replace("~", "~0").replace("/", "~1"))


# 1. Two definitions, one integer and one string. "b" refers to the string
#    one, so {"b": "x"} should be valid in every row.
pairs = [
    ("Address", "address", "case"),
    ("user-id", "user_id", "hyphen"),
    ("user.id", "user_id", "dot"),
    ("user id", "user_id", "space, as %20"),
    ("a/b", "a_b", "slash, as ~1"),
    ("größe", "grüße", "non-ASCII letters"),
    ("id", "id_", "trailing underscore"),
]
for int_key, str_key, label in pairs:
    schema = {"$schema": D7,
              "definitions": {int_key: {"type": "integer"}, str_key: {"type": "string"}},
              "properties": {"a": {"$ref": pointer(int_key)}, "b": {"$ref": pointer(str_key)}}}
    check(f"{label}: b = 'x'", schema, {"b": "x"})
    check(f"{label}: b = 'x', fast_fail=False", schema, {"b": "x"}, fast_fail=False)

# 2. Two subschemas whose $id URIs differ only in punctuation
#    (expected: valid)
schema = {"$schema": D7,
          "definitions": {"i": {"$id": "http://example.com/user-id.json", "type": "integer"},
                          "s": {"$id": "http://example.com/user_id.json", "type": "string"}},
          "properties": {"a": {"$ref": "http://example.com/user-id.json"},
                         "b": {"$ref": "http://example.com/user_id.json"}}}
check("two $id URIs: b = 'x'", schema, {"b": "x"})

# 3. One $ref that URI normalization changes, next to a second $ref to the
#    normalized form (expected: valid, valid)
for label, ref in (("empty query", "?#/definitions/ab"), ("raw tab", "#/definitions/a\tb")):
    schema = {"$schema": D7,
              "definitions": {"ab": {"type": "integer"}},
              "properties": {"x": {"$ref": ref}, "y": {"$ref": "#/definitions/ab"}}}
    check(f"{label}: x = 1", schema, {"x": 1})
    check(f"{label}: y = 1", schema, {"y": 1})
