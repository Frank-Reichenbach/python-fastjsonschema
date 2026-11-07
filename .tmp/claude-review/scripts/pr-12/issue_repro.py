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
