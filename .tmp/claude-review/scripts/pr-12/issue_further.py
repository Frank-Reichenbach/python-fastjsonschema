import threading

import fastjsonschema

D7 = "http://json-schema.org/draft-07/schema#"


def handler(uri):
    raise RuntimeError("handler called with " + uri)


def check(label, schema, data):
    result = []

    def run():
        try:
            validate = fastjsonschema.compile(schema, handlers={"": handler, "file": handler})
            validate(data)
            result.append("valid")
        except fastjsonschema.JsonSchemaValueException as exc:
            result.append("invalid: " + exc.message)
        except Exception as exc:
            result.append(f"{type(exc).__name__}: {exc}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(10)
    print(f"{label:24} {result[0] if result else 'compile() still running after 10 s'}")


# 1. A $ref to another file in the same directory
#    (expected: handler called with a/b/other.json)
check("$ref to other.json", {"$schema": D7, "$id": "a/b/item.json",
      "properties": {"x": {"$ref": "other.json"}}}, {"x": 1})

# 2. A subschema with such an $id that refers to itself (expected: valid)
check("subschema, $ref #", {"$schema": D7, "properties": {"p": {"$id": "schemas/node.json",
      "properties": {"q": {"$ref": "#"}}}}}, {"p": {"q": {}}})

# 3. An $id with a scheme and a relative path (expected: valid)
check("file:schemas/item.json", {"$schema": D7, "$id": "file:schemas/item.json",
      "definitions": {"count": {"type": "integer"}},
      "properties": {"count": {"$ref": "#/definitions/count"}}}, {"count": 1})
