import copy

import fastjsonschema

D7 = "http://json-schema.org/draft-07/schema#"


def handler(uri):
    raise RuntimeError("handler called with " + uri)


def node(id_key="$id"):
    return {
        id_key: "http://example.com/node.json",
        "definitions": {"y": {"type": "integer"}},  # "#/definitions/y" in node.json
        "properties": {"b": {"$ref": "#/definitions/y"}},
    }


def check(label, schema, data):
    try:
        validate = fastjsonschema.compile(copy.deepcopy(schema), handlers={"http": handler})
        validate(copy.deepcopy(data))
        print(f"{label:46} valid")
    except fastjsonschema.JsonSchemaValueException as exc:
        print(f"{label:46} invalid: {exc.message}")
    except Exception as exc:
        print(f"{label:46} {type(exc).__name__}: {exc}")


root_y = {"y": {"type": "string"}}  # "#/definitions/y" in the root

# 1. $ref to a schema with its own $id, inside definitions next to the $ref (expected: invalid)
check("draft-07, root $ref", {"$schema": D7, "$ref": "#/definitions/a", "definitions": {"a": node(), **root_y}}, {"b": "x"})
check("no $schema, root $ref", {"$ref": "#/definitions/a", "definitions": {"a": node(), **root_y}}, {"b": "x"})
check("draft-04 (id), root $ref", {"$schema": "http://json-schema.org/draft-04/schema#", "$ref": "#/definitions/a",
                                   "definitions": {"a": node("id"), **root_y}}, {"b": "x"})
check("draft-06, root $ref", {"$schema": "http://json-schema.org/draft-06/schema#", "$ref": "#/definitions/a",
                              "definitions": {"a": node(), **root_y}}, {"b": "x"})
check("draft-07, $ref object in properties", {"$schema": D7, "definitions": root_y, "properties": {
    "p": {"$ref": "#/properties/p/definitions/a", "definitions": {"a": node()}}}}, {"p": {"b": "x"}})
# 2. The same with valid data (expected: valid)
check("draft-07, root $ref, b = 1", {"$schema": D7, "$ref": "#/definitions/a", "definitions": {"a": node(), **root_y}}, {"b": 1})
# 3. $ref by $id to that schema (expected: invalid, no handler call)
check("draft-07, $ref to node.json by $id", {"$schema": D7, "$ref": "http://example.com/node.json",
                                             "definitions": {"a": node(), **root_y}}, {"b": "x"})
# 4. The root schema of 1, loaded through a handler (expected: invalid)
doc = {"$schema": D7, "$ref": "#/definitions/a", "definitions": {"a": node(), **root_y}}
validate = fastjsonschema.compile({"$ref": "http://example.com/doc.json"}, handlers={"http": lambda uri: copy.deepcopy(doc)})
try:
    validate({"b": "x"})
    print(f"{'draft-07, loaded through a handler':46} valid")
except fastjsonschema.JsonSchemaValueException as exc:
    print(f"{'draft-07, loaded through a handler':46} invalid: {exc.message}")
# 5. Control: an $id directly next to $ref is ignored in draft-07 (expected: invalid: must be string)
check("control: $id next to $ref (draft-07)", {"$schema": D7, "$id": "http://example.com/root.json",
    "definitions": {"y": {"type": "string"}},
    "properties": {"b": {"$id": "http://example.com/other.json", "$ref": "#/definitions/y"}}}, {"b": 1})
