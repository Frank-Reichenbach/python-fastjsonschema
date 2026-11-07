import fastjsonschema

D4 = "http://json-schema.org/draft-04/schema#"
D6 = "http://json-schema.org/draft-06/schema#"
D7 = "http://json-schema.org/draft-07/schema#"
D2019 = "https://json-schema.org/draft/2019-09/schema"
D2020 = "https://json-schema.org/draft/2020-12/schema"


def node(node_id, id_key="$id"):
    return {
        id_key: node_id,
        "type": "object",
        "properties": {
            "all": {"type": "array", "items": {"$ref": "#"}},
            "eq": {"type": "array", "maxItems": 2},
        },
        "additionalProperties": False,
    }


def check(label, schema, data, **kwargs):
    try:
        validate = fastjsonschema.compile(schema, **kwargs)
    except fastjsonschema.JsonSchemaDefinitionException as exc:
        print(f"{label:34} compile error: {exc}")
        return
    try:
        validate(data)
        print(f"{label:34} valid")
    except fastjsonschema.JsonSchemaException:
        print(f"{label:34} invalid")


bad = {"p": {"all": [{"eq": [1, 2, 3]}]}}  # invalid according to the spec

# 1. "#" inside the urn: subschema, in different setups (expected: invalid)
ref = {"$schema": D7, "properties": {"p": {"$ref": "urn:example:node"}}}
check("embedded under definitions", dict(ref, definitions={"n": node("urn:example:node")}), bad)
check("loaded through handlers", ref, bad, handlers={"urn": lambda uri: node("urn:example:node")})
check("fast_fail=False", dict(ref, definitions={"n": node("urn:example:node")}), bad, fast_fail=False)
check("evaluated in place", {"$schema": D7, "properties": {"p": node("urn:example:node")}}, bad)
check("draft-04 (id)", {"$schema": D4, "properties": {"p": node("urn:example:node", "id")}}, bad)
check("draft-06", {"$schema": D6, "properties": {"p": node("urn:example:node")}}, bad)
check("2019-09", {"$schema": D2019, "properties": {"p": node("urn:example:node")}}, bad)
check("2020-12", {"$schema": D2020, "properties": {"p": node("urn:example:node")}}, bad)
check("no $schema", {"properties": {"p": node("urn:example:node")}}, bad)
check("tag: scheme", {"$schema": D7, "properties": {"p": node("tag:example.com,2026:node")}}, bad)
check("s3: scheme", {"$schema": D7, "properties": {"p": node("s3://bucket/node.json")}}, bad)
check("http: scheme (control)", {"$schema": D7, "properties": {"p": node("http://example.com/node.json")}}, bad)
check("file: scheme (control)", {"$schema": D7, "properties": {"p": node("file:///schemas/node.json")}}, bad)

# 2. "#/definitions/x" inside the urn: subschema (expected: 1 valid, "a" invalid)
item = {"$id": "urn:example:item", "properties": {"v": {"$ref": "#/definitions/x"}},
        "definitions": {"x": {"type": "integer"}}}
both = {"$schema": D7, "properties": {"p": item}, "definitions": {"x": {"type": "string"}}}
check("pointer, root defines x: 1", both, {"p": {"v": 1}})
check("pointer, root defines x: 'a'", both, {"p": {"v": "a"}})
check("pointer, root lacks x: 1", {"$schema": D7, "properties": {"p": item}}, {"p": {"v": 1}})

# 3. Plain-name "#foo" in the urn: subschema breaks the root's own "#foo"
#    (expected: 'a' valid, 1 invalid; nothing refers to the urn: subschema)
plain = {"$schema": D7,
         "definitions": {"s": {"$id": "#foo", "type": "string"},
                         "item": {"$id": "urn:example:item",
                                  "definitions": {"i": {"$id": "#foo", "type": "integer"}}}},
         "properties": {"r": {"$ref": "#foo"}}}
check("root #foo: 'a'", plain, {"r": "a"})
check("root #foo: 1", plain, {"r": 1})

# 4. As case 3, but the urn: subschema refers to its own "#foo" and the root
#    refers to the subschema. The order of "properties" decides which of the
#    two "#foo" references breaks. (expected: valid, valid)
def plain_with_ref(order):
    sub = {"$id": "urn:example:item", "properties": {"x": {"$ref": "#foo"}},
           "definitions": {"i": {"$id": "#foo", "type": "integer"}}}
    props = {"r": {"$ref": "#foo"}, "p": {"$ref": "urn:example:item"}}
    return {"$schema": D7,
            "definitions": {"item": sub, "s": {"$id": "#foo", "type": "string"}},
            "properties": {k: props[k] for k in order}}

for order in (("r", "p"), ("p", "r")):
    schema = plain_with_ref(order)
    check(f"order {','.join(order)}: root #foo 'a'", schema, {"r": "a"})
    check(f"order {','.join(order)}: urn: #foo 1", schema, {"p": {"x": 1}})
