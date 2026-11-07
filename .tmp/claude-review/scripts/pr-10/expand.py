import fastjsonschema
calls = []
def h(u): calls.append(u); return {"type": "string"}
fastjsonschema.compile({"type": "integer", "x-list": [{"$ref": "http://e.com/foo.json"}]}, handlers={"http": h})
print("x-list array $ref fetched while expanding error definition:", calls)
calls.clear()
# unknown keyword dict holding allOf with $id: registered now (documented limitation)
v = fastjsonschema.compile({"$id": "http://e.com/root.json", "x-meta": {"allOf": [{"$id": "t.json", "type": "string"}]},
    "properties": {"p": {"$ref": "t.json"}}}, handlers={"http": h})
print("x-meta>allOf $id registered (no handler call):", calls == [], calls)
# draft-07 'id' annotation in allOf item changes base URI
try:
    v = fastjsonschema.compile({"$schema": "http://json-schema.org/draft-07/schema#", "definitions": {"x": {"type": "string"}},
        "allOf": [{"id": "http://e.com/other.json", "properties": {"p": {"$ref": "#/definitions/x"}}}]}, handlers={"http": h})
    v({"p": "a"}); print("draft7 id in allOf: valid, calls", calls)
except Exception as e:
    print("draft7 id in allOf:", type(e).__name__, str(e)[:80], "calls", calls)
