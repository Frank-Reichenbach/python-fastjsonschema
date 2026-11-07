import time, json, fastjsonschema
from fastjsonschema.ref_resolver import RefResolver
big = {"$schema": "http://json-schema.org/draft-07/schema#", "definitions": {"x": {"type": "integer"}},
       "properties": {f"p{i}": {"anyOf": [{"$ref": "#/definitions/x"}, {"type": "null"}, {"allOf": [{"minimum": 0}, {"maximum": 9}]}]} for i in range(500)},
       "enum": [{"k": list(range(50))} for _ in range(2000)]}
for label, fn in (("RefResolver walk", lambda: RefResolver.from_schema(big, store={})), ("compile", lambda: fastjsonschema.compile(big))):
    best = 1e9
    for _ in range(5):
        t = time.perf_counter(); fn(); best = min(best, time.perf_counter() - t)
    print(f"{label}: {best*1000:.1f} ms")
