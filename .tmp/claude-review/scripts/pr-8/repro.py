import fastjsonschema
print("fastjsonschema", fastjsonschema.VERSION)
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {"user-id": {"type": "integer"}, "user_id": {"type": "string"}},
    "properties": {"a": {"$ref": "#/definitions/user-id"}, "b": {"$ref": "#/definitions/user_id"}},
}
validate = fastjsonschema.compile(schema)
for data in ({"a": 1}, {"b": "x"}):
    try:
        validate(data); print(data, "-> valid")
    except fastjsonschema.JsonSchemaException as exc:
        print(data, "->", exc.message)
