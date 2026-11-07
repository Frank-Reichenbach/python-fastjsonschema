import fastjsonschema, copy
base = {'definitions': {'x': {'type': 'string'}},
        'properties': {'p': {'$id': 'urn:ex:item', 'properties': {'v': {'$ref': '#/definitions/x'}}}}}
for label, s in [('ref to root-only def', base)]:
    try: fastjsonschema.compile(copy.deepcopy(s)); print(label, 'compiles')
    except fastjsonschema.JsonSchemaDefinitionException as e: print(label, '-> JsonSchemaDefinitionException:', repr(str(e)))
w = copy.deepcopy(base); w['$id'] = 'urn:ex:root'; w['properties']['p']['properties']['v']['$ref'] = 'urn:ex:root#/definitions/x'
v = fastjsonschema.compile(w)
for d in ({'p': {'v': 'a'}}, {'p': {'v': 1}}):
    try: v(d); print('workaround', d, 'valid')
    except fastjsonschema.JsonSchemaException as e: print('workaround', d, e.message)
