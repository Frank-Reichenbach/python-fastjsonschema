import copy, json, sys
import fastjsonschema
try:
    import jsonschema
except ImportError:
    jsonschema = None

D4 = "http://json-schema.org/draft-04/schema#"
D7 = "http://json-schema.org/draft-07/schema#"
D19 = "https://json-schema.org/draft/2019-09/schema"
P = {"$ref": "#/definitions/x"}
fetched = []
def h(uri):
    fetched.append(uri); raise RuntimeError("fetch " + uri)
HANDLERS = {"http": h, "https": h, "urn": h}

def oracle(schema, data):
    if jsonschema is None: return '?'
    try:
        cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)
        return 'valid' if cls(schema).is_valid(data) else 'invalid'
    except Exception as e:
        return 'ERR ' + type(e).__name__

def check(label, schema, datas, **kw):
    for d in datas:
        out = []
        for ff in (True, False):
            fetched.clear()
            try:
                v = fastjsonschema.compile(copy.deepcopy(schema), handlers=HANDLERS, fast_fail=ff, **kw)
            except Exception as e:
                out.append('compile %s: %s%s' % (type(e).__name__, str(e)[:70], ' fetched=%s' % fetched if fetched else ''))
                continue
            try:
                r = v(copy.deepcopy(d)); out.append('valid -> %s' % json.dumps(r) if kw.get('use_default') else 'valid')
            except fastjsonschema.JsonSchemaValuesException as e:
                out.append('invalid: ' + e.errors[0].message)
            except fastjsonschema.JsonSchemaException as e:
                out.append('invalid: ' + e.message)
            except Exception as e:
                out.append('run %s: %s' % (type(e).__name__, e))
        o = out[0] if out[0] == out[1] else ' | '.join(out)
        print('%-40s %-14s %s   [oracle: %s]' % (label, json.dumps(d)[:14], o, oracle(schema, d)))

# A issue repro
check("A1 const ptr no $id", {"$schema": D7, "properties": {"pointer": {"const": P}}}, [{"pointer": P}])
check("A2 const ptr with $id", {"$schema": D7, "$id": "http://example.com/root.json", "definitions": {"x": {"type": "string"}}, "properties": {"pointer": {"const": P}}}, [{"pointer": P}])
check("A3 enum", {"$schema": D7, "properties": {"p": {"enum": [P]}}}, [{"p": P}])
check("A4 examples", {"$schema": D7, "properties": {"p": {"type": "object", "examples": [P]}}}, [{"p": {}}])
check("A5 default use_default", {"$schema": D7, "$id": "http://example.com/root.json", "properties": {"p": {"default": P}}}, [{}], use_default=True)
check("A6 default bad URI", {"$schema": D7, "$id": "http://example.com/root.json", "properties": {"p": {"default": {"$ref": "http://[bad"}}}}, [{}])
for kw in ("const", "default", "examples_wrap"):
    val = {"$id": "http://example.com/string.json", "type": "integer"}
    sub = {"examples": [val]} if kw == "examples_wrap" else {kw: val}
    check("A7 $id in %s" % kw, {"$schema": D7, "definitions": {"s": {"$id": "http://example.com/string.json", "type": "string"}}, "properties": {"q": sub, "v": {"$ref": "http://example.com/string.json"}}}, [{"v": "a"}, {"v": 1}])

# B draft-04 'id' in const/default (const not a draft-04 keyword)
check("B1 d4 id in default", {"$schema": D4, "definitions": {"s": {"id": "http://example.com/s.json", "type": "string"}}, "properties": {"q": {"default": {"id": "http://example.com/s.json", "type": "integer"}}, "v": {"$ref": "http://example.com/s.json"}}}, [{"v": "a"}])
check("B2 2019 $defs + const $id", {"$schema": D19, "$defs": {"s": {"$id": "http://example.com/s.json", "type": "string"}}, "properties": {"q": {"const": {"$id": "http://example.com/s.json", "type": "integer"}}, "v": {"$ref": "http://example.com/s.json"}}}, [{"v": "a"}])

# C maps with entries named like data keywords
for name in ("const", "default", "enum", "examples"):
    check("C1 definitions/%s $id" % name, {"$schema": D7, "definitions": {name: {"$id": "http://example.com/d.json", "type": "integer"}}, "properties": {"a": {"$ref": "http://example.com/d.json"}}}, [{"a": 1}, {"a": "x"}])
check("C2 $ref #/definitions/default", {"$schema": D7, "$id": "http://example.com/r.json", "definitions": {"default": {"type": "integer"}}, "properties": {"a": {"$ref": "#/definitions/default"}}}, [{"a": 1}, {"a": "x"}])
check("C3 patternProperties ^default$ w/ $id scope", {"$schema": D7, "$id": "http://example.com/r.json", "definitions": {"x": {"type": "string"}},
    "properties": {"n": {"$id": "http://example.com/n/n.json", "definitions": {"x": {"type": "integer"}}, "patternProperties": {"default": {"$ref": "#/definitions/x"}}}}}, [{"n": {"default": 1}}, {"n": {"default": "a"}}])
check("C4 dependencies/const schema", {"$schema": D7, "$id": "http://example.com/r.json", "definitions": {"x": {"type": "string"}},
    "properties": {"n": {"$id": "http://example.com/n/n.json", "definitions": {"x": {"type": "integer"}}, "dependencies": {"enum": {"properties": {"z": {"$ref": "#/definitions/x"}}}}}}}, [{"n": {"enum": 1, "z": 1}}, {"n": {"enum": 1, "z": "a"}}])
check("C5 2019 dependentSchemas/default", {"$schema": D19, "$id": "http://example.com/r.json", "$defs": {"x": {"type": "string"}},
    "properties": {"n": {"$id": "http://example.com/n/n.json", "$defs": {"x": {"type": "integer"}}, "dependentSchemas": {"default": {"properties": {"z": {"$ref": "#/$defs/x"}}}}}}}, [{"n": {"default": 1, "z": 1}}, {"n": {"default": 1, "z": "a"}}])
check("C6 prop 'properties' containing 'default'", {"$schema": D7, "$id": "http://example.com/r.json", "definitions": {"x": {"type": "string"}},
    "properties": {"n": {"$id": "http://example.com/n/n.json", "definitions": {"x": {"type": "integer"}}, "properties": {"properties": {"properties": {"default": {"$ref": "#/definitions/x"}}}}}}}, [{"n": {"properties": {"default": 1}}}, {"n": {"properties": {"default": "a"}}}])
# D custom maps
check("D1 x-defs/default $id (documented)", {"$schema": D7, "x-defs": {"default": {"$id": "http://example.com/d.json", "type": "integer"}}, "properties": {"a": {"$ref": "http://example.com/d.json"}}}, [{"a": 1}, {"a": "x"}])
check("D2 x-defs/foo $id", {"$schema": D7, "x-defs": {"foo": {"$id": "http://example.com/d.json", "type": "integer"}}, "properties": {"a": {"$ref": "http://example.com/d.json"}}}, [{"a": 1}, {"a": "x"}])
check("D3 d7 $defs direct $id (documented)", {"$schema": D7, "$defs": {"$id": "http://example.com/d.json", "type": "integer"}, "properties": {"a": {"$ref": "http://example.com/d.json"}}}, [{"a": 1}, {"a": "x"}])
# E $ref pointer into data
check("E1 $ref into default", {"$schema": D7, "properties": {"a": {"default": {"type": "integer"}}, "b": {"$ref": "#/properties/a/default"}}}, [{"b": 1}, {"b": "x"}])
check("E2 $ref into enum/0", {"$schema": D7, "properties": {"a": {"enum": [{"type": "integer"}]}, "b": {"$ref": "#/properties/a/enum/0"}}}, [{"b": 1}, {"b": "x"}])
check("E3 $ref into const holding $ref", {"$schema": D7, "definitions": {"x": {"type": "integer"}}, "properties": {"a": {"const": {"$ref": "#/definitions/x"}}, "b": {"$ref": "#/properties/a/const"}}}, [{"b": 1}, {"b": "x"}])
check("E4 $ref into default holding rel $ref, nested $id", {"$schema": D7, "$id": "http://example.com/root.json", "definitions": {"x": {"type": "string"}},
    "properties": {"n": {"$id": "http://example.com/n/n.json", "definitions": {"x": {"type": "integer"}}, "default": {"$ref": "#/definitions/x"}}, "b": {"$ref": "http://example.com/n/n.json#/default"}}}, [{"b": 1}, {"b": "x"}])
check("E5 $ref into default holding rel $ref, nested $id, via root ptr", {"$schema": D7, "$id": "http://example.com/root.json", "definitions": {"x": {"type": "string"}},
    "properties": {"n": {"$id": "http://example.com/n/n.json", "definitions": {"x": {"type": "integer"}}, "default": {"$ref": "#/definitions/x"}}, "b": {"$ref": "#/properties/n/default"}}}, [{"b": 1}, {"b": "x"}])
check("E6 $ref into const with $id", {"$schema": D7, "$id": "http://example.com/root.json", "definitions": {"x": {"type": "string"}},
    "properties": {"a": {"const": {"$id": "http://example.com/c/c.json", "definitions": {"x": {"type": "integer"}}, "$ref": "#/definitions/x"}}, "b": {"$ref": "#/properties/a/const"}}}, [{"b": 1}, {"b": "x"}])
check("E7 $ref into const string", {"$schema": D7, "properties": {"a": {"const": "abc"}, "b": {"$ref": "#/properties/a/const/b"}}}, [{"b": 1}])
check("E8 $ref to $id only inside const", {"$schema": D7, "properties": {"a": {"const": {"$id": "http://example.com/only.json", "type": "integer"}}, "b": {"$ref": "http://example.com/only.json"}}}, [{"b": 1}])
# F error definition
check("F1 error def with const $ref", {"$schema": D7, "definitions": {"x": {"type": "string"}}, "properties": {"p": {"const": P, "type": "object"}}}, [{"p": {"a": 1}}, {"p": 1}])
check("F2 unknown kw $ref (pre-existing)", {"$schema": D7, "x-example": {"$ref": "#/nope"}, "type": "string"}, [1])
check("F3 enum with $ref in 'not' error", {"$schema": D7, "not": {"enum": [P]}}, [P, 1])
check("F4 if/then default $ref", {"$schema": D7, "if": {"default": P}, "then": {"type": "integer"}}, [1, "a"])
