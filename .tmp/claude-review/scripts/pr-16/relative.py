import sys
sys.path.insert(0, sys.argv[1])
import fastjsonschema
r = {"properties": {"p": {"$id": "schemas/main.json", "definitions": {"x": {"type": "integer"}}, "properties": {"q": {"$ref": "#/definitions/x"}}}}}
for i in range(2):
    try:
        v = fastjsonschema.compile(r, handlers={"http": lambda u: 1/0})
        try: v({"p": {"q": "a"}}); res = "ACCEPTS invalid"
        except fastjsonschema.JsonSchemaException: res = "rejects invalid"
        print("compile", i, res, "; ref now", r["properties"]["p"]["properties"]["q"]["$ref"])
    except Exception as exc:
        print("compile", i, type(exc).__name__, exc, "; ref now", r["properties"]["p"]["properties"]["q"]["$ref"])
