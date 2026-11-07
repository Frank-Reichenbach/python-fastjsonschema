import fastjsonschema
DOC = {"$id": "http://example.com/doc.json","definitions": {"x": {"type": "string"}},
 "properties": {"p": {"$id": "http://example.com/node.json","definitions": {"x": {"type": "integer"}},"properties": {"v": {"$ref": "#/definitions/x"}}}}}
v=fastjsonschema.compile(DOC); print(' ', v({'p':{'v':1}}))
