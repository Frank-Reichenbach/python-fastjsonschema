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
