import copy, sys, json, warnings
warnings.simplefilter('ignore')
import fastjsonschema
from fastjsonschema import JsonSchemaException, JsonSchemaValueException
import jsonschema, referencing

D7 = "http://json-schema.org/draft-07/schema#"
D19 = "https://json-schema.org/draft/2019-09/schema"

def fjs(schema, data, handlers=None, fast_fail=True):
    loaded = []
    def h(uri):
        loaded.append(uri)
        return (handlers or {}).get(uri, {"type": "null"})
    try:
        v = fastjsonschema.compile(copy.deepcopy(schema), handlers={"http": h, "urn": h, "": h}, fast_fail=fast_fail)
    except Exception as e:
        return "COMPILE %s: %s" % (type(e).__name__, str(e)[:80]), loaded
    try:
        v(copy.deepcopy(data)); return "valid", loaded
    except JsonSchemaException as e:
        return "invalid", loaded
    except Exception as e:
        return "RUN %s: %s" % (type(e).__name__, str(e)[:80]), loaded

def oracle(schema, data, draft, handlers=None):
    cls = {D7: jsonschema.Draft7Validator, D19: jsonschema.Draft201909Validator, None: jsonschema.Draft201909Validator,
           "http://json-schema.org/draft-04/schema#": jsonschema.Draft4Validator}[draft]
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT201909, DRAFT7, DRAFT4
    spec = {D7: DRAFT7, D19: DRAFT201909, None: DRAFT201909, "http://json-schema.org/draft-04/schema#": DRAFT4}[draft]
    def retrieve(uri):
        return Resource(contents=(handlers or {}).get(uri, {"type": "null"}), specification=spec)
    try:
        v = cls(schema, registry=Registry(retrieve=retrieve))
        return "valid" if v.is_valid(data) else "invalid"
    except Exception as e:
        return "ERR %s" % type(e).__name__

CASES = []
def case(label, schema, datas, draft, handlers=None):
    CASES.append((label, schema, datas, draft, handlers))

for d in (None, D7):
    sch = lambda s: dict(s, **({"$schema": d} if d else {}))
    case("pointer-ref next to sibling $id (outer defs)", sch({"$defs": {"int": {"type": "integer"}},
         "properties": {"foo": {"$id": "http://e.com/foo.json", "$ref": "#/$defs/int"}}}), [{"foo": 1}, {"foo": "x"}], d)
    case("relative ref next to relative $id", sch({"$id": "http://e.com/root.json",
         "properties": {"a": {"$id": "sub/a.json", "$ref": "thing.json"}}}), [{"a": None}, {"a": 1}], d,
         {"http://e.com/thing.json": {"type": "string"}, "http://e.com/sub/thing.json": {"type": "integer"}})
    case("ref to sibling-$id by URI", sch({"$id": "http://e.com/root.json",
         "properties": {"a": {"$id": "a.json", "$ref": "#/$defs/s", "$defs": {"s": {"type": "string"}}},
                        "b": {"$ref": "a.json"}}}), [{"b": "x"}, {"b": 1}], d)
    case("own $defs via sibling $id", sch({"$id": "http://e.com/root.json", "$defs": {"s": {"type": "integer"}},
         "properties": {"a": {"$id": "a.json", "$ref": "#/$defs/s", "$defs": {"s": {"type": "string"}}}}}), [{"a": "x"}, {"a": 1}], d)
    case("urn sibling $id with pointer", sch({"$defs": {"s": {"type": "integer"}},
         "properties": {"a": {"$id": "urn:ex:a", "$ref": "#/$defs/s", "$defs": {"s": {"type": "string"}}}}}), [{"a": "x"}, {"a": 1}], d)
    case("$id with fragment-only next to $ref", sch({"$defs": {"s": {"type": "integer"}},
         "properties": {"a": {"$id": "#foo", "$ref": "#/$defs/s"}}}), [{"a": 1}, {"a": "x"}], d)
    case("nested $ref chains w/ definitions", sch({"$ref": "#/definitions/a", "definitions": {
         "a": {"$ref": "#/definitions/a/definitions/b", "definitions": {"b": {"$id": "http://e.com/b.json",
               "definitions": {"y": {"type": "integer"}}, "properties": {"v": {"$ref": "#/definitions/y"}}}}},
         "y": {"type": "string"}}}), [{"v": 1}, {"v": "x"}], d)
    case("boolean defs next to $ref", sch({"$ref": "#/definitions/t", "definitions": {"t": True, "f": False}}), [1], d)
    case("defs with $ref to id in sibling defs", sch({"$ref": "http://e.com/x.json", "definitions": {"x": {"$id": "http://e.com/x.json", "type": "string"}}}), ["x", 1], d)

for label, schema, datas, draft, handlers in CASES:
    for data in datas:
        r1, l1 = fjs(schema, data, handlers)
        r2, _ = fjs(schema, data, handlers, fast_fail=False)
        o = oracle(schema, data, draft, handlers)
        flag = "" if (r1 == o or (r1.startswith("COMPILE") and o.startswith("ERR"))) else "  <-- DIFF"
        print("%-4s %-45s %-14s ff=%-10s noff=%-10s oracle=%-12s loaded=%s%s" % ("2019" if draft is None else "d7", label, json.dumps(data), r1[:60], r2[:10], o, l1, flag))
