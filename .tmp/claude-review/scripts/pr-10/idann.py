import fastjsonschema
s = {"$schema": "http://json-schema.org/draft-07/schema#", "definitions": {"name": {"type": "string"}},
     "properties": {"user": {"allOf": [{"id": "user", "properties": {"name": {"$ref": "#/definitions/name"}}}]}}}
try:
    v = fastjsonschema.compile(s); v({"user": {"name": "a"}}); print("valid")
except Exception as e: print(type(e).__name__, e)
s2 = {"$schema": "http://json-schema.org/draft-07/schema#", "definitions": {"name": {"type": "string"}},
     "properties": {"user": {"id": "user", "properties": {"name": {"$ref": "#/definitions/name"}}}}}
try:
    v = fastjsonschema.compile(s2); v({"user": {"name": "a"}}); print("object position: valid")
except Exception as e: print("object position:", type(e).__name__, e)
