import sys
sys.path.insert(0, sys.argv[1])
import fastjsonschema
print("fastjsonschema", fastjsonschema.VERSION)
def no_download(uri):
    raise RuntimeError("handler called with " + uri)
shared = {"$ref": "#/definitions/x"}
one = {"$schema": "http://json-schema.org/draft-07/schema#", "$id": "http://example.com/one.json",
       "definitions": {"x": {"type": "integer"}}, "properties": {"p": shared}}
two = {"$schema": "http://json-schema.org/draft-07/schema#", "$id": "http://example.com/two.json",
       "definitions": {"x": {"type": "string"}}, "properties": {"p": shared}}
fastjsonschema.compile(one, handlers={"http": no_download})
print("one after compile():", one["properties"]["p"])
try:
    print("two:", fastjsonschema.compile(two, handlers={"http": no_download})({"p": "a"}))
except Exception as exc:
    print("two:", type(exc).__name__, exc)
# claim 2: compiled again after $id changed
s = {"$id": "http://example.com/v1.json", "definitions": {"x": {"type": "integer"}}, "properties": {"p": {"$ref": "#/definitions/x"}}}
fastjsonschema.compile(s, handlers={"http": no_download}); s["$id"] = "http://example.com/v2.json"
try:
    print("id changed:", fastjsonschema.compile(s, handlers={"http": no_download})({"p": 1}))
except Exception as exc:
    print("id changed:", type(exc).__name__, exc)
# claim 3: relative base URI
r = {"$id": "schemas/main.json", "definitions": {"x": {"type": "integer"}}, "properties": {"p": {"$ref": "#/definitions/x"}}}
for i in range(2):
    try:
        fastjsonschema.compile(r, handlers={"http": no_download}); print("relative compile", i, "ok; ref now", r["properties"]["p"]["$ref"])
    except Exception as exc:
        print("relative compile", i, type(exc).__name__, exc, "; ref now", r["properties"]["p"]["$ref"])
