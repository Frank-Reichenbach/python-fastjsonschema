import sys, copy, time
import fastjsonschema
from fastjsonschema import JsonSchemaException, JsonSchemaValueException
D7 = "http://json-schema.org/draft-07/schema#"

# 8 weird id
s = {"$schema": D7, "$id": "http://e.com/root.json",
    "definitions": {"l": {"anyOf": [{"$id": "a\"b{c}'d.json", "type": "integer"}]}},
    "properties": {"p{x}\"": {"$ref": "a\"b{c}'d.json"}}}
try:
    code = fastjsonschema.compile_to_code(copy.deepcopy(s), handlers={"http": lambda u: (_ for _ in ()).throw(RuntimeError(u))})
    ns = {}; exec(code, ns)
    f = [k for k in ns if k.startswith('validate')]
    print("8 compile_to_code ok, functions:", f)
    v = fastjsonschema.compile(copy.deepcopy(s), handlers={"http": lambda u: (_ for _ in ()).throw(RuntimeError(u))})
    for d in ({"p{x}\"": 1}, {"p{x}\"": "a"}):
        try: v(d); print("  ", d, "valid")
        except JsonSchemaException as e: print("  ", d, e.message)
except Exception as e:
    print("8 error", type(e).__name__, e)

# 9 shared dict (not in array) under two $ids on one root: first wins? 
N = {"$ref": "#/definitions/x"}
s = {"$schema": D7, "$id": "http://e.com/root.json",
    "properties": {
        "a": {"$id": "one.json", "definitions": {"x": {"type": "integer"}}, "properties": {"p": {"not": N}}},
        "b": {"$id": "two.json", "definitions": {"x": {"type": "boolean"}}, "properties": {"p": {"not": N}}}}}
v = fastjsonschema.compile(s)
for d in ({"b": {"p": 1}}, {"b": {"p": True}}):
    try: v(d); print("9 dict-shared", d, "valid")
    except JsonSchemaException as e: print("9 dict-shared", d, e.message)

# 10 error definition expansion of a definition containing allOf with $ref under nested $id
s = {"$schema": D7, "definitions": {"x": {"type": "string"}},
     "properties": {"p": {"$id": "http://e.com/n.json", "definitions": {"x": {"type": "integer"}},
        "properties": {"v": {"type": "array", "anyOf": [{"$ref": "#/definitions/x"}, {"type": "array"}]}}}}}
v = fastjsonschema.compile(s)
try: v({"p": {"v": 1}})
except JsonSchemaValueException as e: print("10 error definition:", e.definition)

# 11 depth
def nest(n, kw):
    d = {"type": "integer"}
    for _ in range(n):
        d = {kw: [d]} if kw != 'properties' else {kw: {"a": d}}
    return d
for kw in ('allOf', 'properties'):
    for n in (100, 150, 200, 249, 250, 300):
        try:
            fastjsonschema.compile(nest(n, kw)); r = "ok"
        except RecursionError: r = "RecursionError"
        except Exception as e: r = type(e).__name__ + ": " + str(e)[:60]
        print(f"11 {kw} x{n}: {r}")
