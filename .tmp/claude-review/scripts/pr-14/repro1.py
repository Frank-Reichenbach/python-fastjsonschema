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
