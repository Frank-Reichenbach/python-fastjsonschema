import sys, json, copy, time
import fastjsonschema
from fastjsonschema import JsonSchemaException, JsonSchemaValueException
import jsonschema

def run(label, schema, cases, handlers=None, oracle=True, **kw):
    try:
        v = fastjsonschema.compile(copy.deepcopy(schema), handlers=handlers or {}, **kw)
    except Exception as e:
        print(f"{label}: compile error {type(e).__name__}: {str(e)[:100]}")
        return
    out = []
    for d in cases:
        try:
            v(copy.deepcopy(d)); r = 'V'
        except JsonSchemaException:
            r = 'I'
        except Exception as e:
            r = 'E:' + type(e).__name__
        o = ''
        if oracle:
            try:
                cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)
                o = 'V' if cls(schema).is_valid(d) else 'I'
            except Exception as e:
                o = '?' + type(e).__name__
        out.append(f"{json.dumps(d)}={r}" + (f"(oracle {o})" if oracle else ''))
    print(f"{label}: " + ', '.join(out))

D7 = "http://json-schema.org/draft-07/schema#"

# 1 shared object under two $ids in one schema (first wins)
N = {"anyOf": [{"$ref": "#/definitions/x"}, {"type": "null"}]}
run("1 shared array obj, two $ids, one root", {"$schema": D7, "$id": "http://e.com/root.json",
    "definitions": {"x": {"type": "string"}},
    "properties": {
        "a": {"$id": "one.json", "definitions": {"x": {"type": "integer"}}, "properties": {"p": N}},
        "b": {"$id": "two.json", "definitions": {"x": {"type": "boolean"}}, "properties": {"p": N}}}},
    [{"a": {"p": 1}, "b": {"p": True}}, {"b": {"p": "s"}}])

# 2 nested arrays: allOf inside anyOf inside items array inside oneOf
run("2 deep mix", {"$schema": D7, "definitions": {"x": {"type": "string"}},
    "properties": {"p": {"$id": "http://e.com/n.json", "definitions": {"x": {"type": "integer"}},
        "oneOf": [{"items": [{"anyOf": [{"allOf": [{"$ref": "#/definitions/x"}]}]}]}]}}},
    [{"p": [1]}, {"p": ["a"]}])

# 3 $id in items array, nested $id inside array changes scope for sibling ref
run("3 $id in array item scopes ref in that item", {"$schema": D7, "$id": "http://e.com/root.json",
    "definitions": {"x": {"type": "string"}},
    "allOf": [{"$id": "sub/", "definitions": {"x": {"type": "integer"}}, "properties": {"p": {"$ref": "#/definitions/x"}}}]},
    [{"p": 1}, {"p": "a"}])

# 4 not / if-then-else / contains / additionalItems containing arrays
run("4 not>allOf", {"$schema": D7, "definitions": {"x": {"type": "string"}},
    "properties": {"p": {"$id": "http://e.com/n.json", "definitions": {"x": {"type": "integer"}},
        "not": {"allOf": [{"$ref": "#/definitions/x"}]}}}}, [{"p": 1}, {"p": "a"}])
run("4b additionalItems w/ items array", {"$schema": D7, "definitions": {"x": {"type": "string"}},
    "properties": {"p": {"$id": "http://e.com/n.json", "definitions": {"x": {"type": "integer"}},
        "items": [{}], "additionalItems": {"anyOf": [{"$ref": "#/definitions/x"}]}}}}, [{"p": [0, 1]}, {"p": [0, "a"]}])
run("4c dependencies list + schema", {"$schema": D7, "definitions": {"x": {"type": "string"}},
    "properties": {"p": {"$id": "http://e.com/n.json", "definitions": {"x": {"type": "integer"}},
        "dependencies": {"a": ["b"], "c": {"properties": {"c": {"anyOf": [{"$ref": "#/definitions/x"}]}}}}}}},
    [{"p": {"c": 1}}, {"p": {"c": "a"}}, {"p": {"a": 1}}])

# 5 arrays of non-dicts / booleans / odd values
run("5 allOf with booleans", {"$schema": D7, "allOf": [True, {"type": "integer"}]}, [1, "a"])
for bad in ([1, "x", None], [[{"$id": "x.json"}]], "notalist", {}):
    try:
        fastjsonschema.compile({"$schema": D7, "allOf": bad})
        print("5b allOf", json.dumps(bad), "compiled")
    except Exception as e:
        print("5b allOf", json.dumps(bad), type(e).__name__, str(e)[:80])

# 6 enum/examples/required/type arrays with $id-looking objects are data
loaded = []
def h(uri):
    loaded.append(uri); return {"type": "integer"}
run("6 $id in enum/examples not registered", {"$schema": D7, "$id": "http://e.com/root.json",
    "enum": [{"$id": "t.json"}, 5], "examples": [{"$id": "t.json", "type": "string"}],
    "properties": {"p": {"$ref": "t.json"}}}, [5], handlers={"http": h}, oracle=False)
print("   handler calls:", loaded)

# 7 remote doc (handler) with $id in anyOf
remote = {"$id": "http://r.com/doc.json", "definitions": {"l": {"anyOf": [{"$id": "item.json", "type": "integer"}]}}}
def h2(uri):
    if uri == "http://r.com/doc.json": return remote
    raise RuntimeError("handler called for " + uri)
run("7 $ref to $id inside anyOf of remote doc", {"$schema": D7, "properties": {
    "d": {"$ref": "http://r.com/doc.json"},
    "p": {"$ref": "http://r.com/doc.json#/definitions/l/anyOf/0"}}}, [{"p": 1}, {"p": "a"}], handlers={"http": h2}, oracle=False)
run("7b remote doc has $ref in allOf under nested $id", {"$schema": D7, "properties": {"p": {"$ref": "http://r.com/b.json"}}},
    [{"v": 1}, {"v": "a"}], handlers={"http": lambda u: {"$id": "http://r.com/b.json", "definitions": {"x": {"type": "string"}},
        "properties": {"v": {"$id": "sub/n.json", "definitions": {"x": {"type": "integer"}}, "allOf": [{"$ref": "#/definitions/x"}]}}}}, oracle=False)

# 8 weird ids with quotes/braces in array
run("8 weird $id in array", {"$schema": D7, "$id": "http://e.com/root.json",
    "definitions": {"l": {"anyOf": [{"$id": "a\"b{c}'d.json", "type": "integer"}]}},
    "properties": {"p{x}\"": {"$ref": "a%22b%7Bc%7D'd.json"}}}, [{"p{x}\"": 1}, {"p{x}\"": "a"}], oracle=False)
