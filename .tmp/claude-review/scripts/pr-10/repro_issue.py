import fastjsonschema

D4 = "http://json-schema.org/draft-04/schema#"
D7 = "http://json-schema.org/draft-07/schema#"
calls = []

def handler(uri):
    calls.append(uri)
    raise RuntimeError("no remote schemas in this test")

def check(label, schema, data):
    calls.clear()
    try:
        validate = fastjsonschema.compile(schema, handlers={"http": handler})
    except Exception as exc:
        print(f"{label:34} compile error: {type(exc).__name__}: {exc}" + (f" (handler called for {calls})" if calls else ""))
        return
    try:
        validate(data)
        print(f"{label:34} valid")
    except fastjsonschema.JsonSchemaException:
        print(f"{label:34} invalid")

def node(v, id_key="$id"):
    return {id_key: "http://example.com/node.json",
            "definitions": {"x": {"type": "integer"}}, "properties": {"v": v}}

ref = {"$ref": "#/definitions/x"}
root_x = {"x": {"type": "string"}}
for kw in ("allOf", "anyOf", "oneOf"):
    check(f"{kw}: 1", {"$schema": D7, "definitions": root_x, "properties": {"p": node({kw: [ref]})}}, {"p": {"v": 1}})
check("items (array form): [1]", {"$schema": D7, "definitions": root_x, "properties": {"p": node({"items": [ref]})}}, {"p": {"v": [1]}})
check("allOf > properties: 1", {"$schema": D7, "definitions": root_x,
      "properties": {"p": node({"allOf": [{"properties": {"w": ref}}]})}}, {"p": {"v": {"w": 1}}})
check("draft-04 (id), allOf: 1", {"$schema": D4, "definitions": root_x, "properties": {"p": node({"allOf": [ref]}, "id")}}, {"p": {"v": 1}})
check("no $schema, allOf: 1", {"definitions": root_x, "properties": {"p": node({"allOf": [ref]})}}, {"p": {"v": 1}})
check("root lacks x, allOf: 1", {"$schema": D7, "properties": {"p": node({"allOf": [ref]})}}, {"p": {"v": 1}})
a = {"$id": "http://example.com/a.json", "definitions": root_x, "properties": {"b": node({"allOf": [ref]})}}
check("inside a.json, allOf: 1", {"$schema": D7, "definitions": {"a": a},
      "properties": {"p": {"$ref": "http://example.com/a.json"}}}, {"p": {"b": {"v": 1}}})
check("$id in anyOf: 1", {"$schema": D7, "$id": "http://example.com/root.json",
      "definitions": {"l": {"anyOf": [{"$id": "item.json", "type": "integer"}, {"type": "null"}]}},
      "properties": {"p": {"$ref": "item.json"}}}, {"p": 1})
check("plain-name $id in allOf: 1", {"$schema": D7,
      "definitions": {"l": {"allOf": [{"$id": "#int", "type": "integer"}]}},
      "properties": {"p": {"$ref": "#int"}}}, {"p": 1})
