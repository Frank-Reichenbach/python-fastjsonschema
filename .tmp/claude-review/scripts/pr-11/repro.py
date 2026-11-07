import copy, fastjsonschema
print("fastjsonschema", fastjsonschema.VERSION, fastjsonschema.__file__.split('scratchpad/')[1])
DOC = {
    "$id": "http://example.com/doc.json",
    "definitions": {"x": {"type": "string"}},
    "properties": {"p": {"$id": "http://example.com/node.json",
            "definitions": {"x": {"type": "integer"}},
            "properties": {"v": {"$ref": "#/definitions/x"}}}},
}
for scheme, uri in [('http','http://example.com/doc.json'), ('', 'schemas/main.json'), ('file','file:schemas/main.json')]:
    validate = fastjsonschema.compile({"$ref": uri}, handlers={scheme: lambda u: copy.deepcopy(DOC)})
    out=[]
    for data in ({"p": {"v": 1}}, {"p": {"v": "a"}}):
        try:
            validate(data); out.append("valid")
        except fastjsonschema.JsonSchemaException as exc:
            out.append(exc.message)
    print(' ', uri, out)
