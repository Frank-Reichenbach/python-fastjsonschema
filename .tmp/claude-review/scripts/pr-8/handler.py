import fastjsonschema, re
docs = {
  'http://example.com/a_b.json': {'definitions': {'x': {'type': 'string'}}, '$ref': '#/definitions/x'},
  'http://example.com/A-B.json': {'definitions': {'x': {'type': 'boolean'}}, '$ref': '#/definitions/x'},
}
calls = []
def h(uri): calls.append(uri); return docs[uri]
s = {'$schema': 'http://json-schema.org/draft-07/schema#', '$id': 'http://example.com/a-b.json', 'type': 'object',
     'definitions': {'x': {'type': 'integer'}},
     'properties': {'i': {'$ref': '#/definitions/x'}, 's': {'$ref': 'a_b.json'}, 'b': {'$ref': 'A-B.json'},
                    'r': {'$ref': '#'}}}
for ff in (True, False):
    for cache in (True,):
        v = fastjsonschema.compile(s, handlers={'http': h}, fast_fail=ff)
        ok = v({'i': 1, 's': 'x', 'b': True, 'r': {'i': 2}})
        res = []
        for bad in ({'i': 'x'}, {'s': 1}, {'b': 1}, {'r': {'i': 'x'}}, 'str'):
            try: v(bad); res.append('ACCEPTED')
            except fastjsonschema.JsonSchemaException: res.append('rej')
        print(ff, res)
code = fastjsonschema.compile_to_code(s, handlers={'http': h})
print(re.findall(r'^def (\w+)', code, re.M)); print('handler calls', calls)
