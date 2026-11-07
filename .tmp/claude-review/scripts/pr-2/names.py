import re, fastjsonschema, copy
schemas = {
 'root urn, # and #/definitions/i and #foo': {'$id': 'urn:example:root', 'definitions': {'i': {'type': 'integer'}, 'f': {'$id': '#foo', 'type': 'string'}},
      'properties': {'a': {'$ref': '#'}, 'b': {'$ref': '#/definitions/i'}, 'c': {'$ref': '#foo'}}},
 'root http (control)': {'$id': 'http://e.com/root', 'definitions': {'i': {'type': 'integer'}},
      'properties': {'a': {'$ref': '#'}, 'b': {'$ref': '#/definitions/i'}}},
 'no id': {'definitions': {'i': {'type': 'integer'}}, 'properties': {'a': {'$ref': '#'}, 'b': {'$ref': '#/definitions/i'}}},
}
for label, s in schemas.items():
    code = fastjsonschema.compile_to_code(copy.deepcopy(s))
    names = re.findall(r'^def (\w+)', code, re.M)
    calls = sorted(set(re.findall(r'(validate\w*)\(data', code)))
    print(label, '\n   defs:', names, '\n   calls:', calls)
    ns = {}
    exec(code, ns)
    try:
        ns[names[0] if label!='x' else None]({'a': {'b': 'x'}})
        print('   standalone: valid')
    except fastjsonschema.JsonSchemaException as e:
        print('   standalone: invalid:', e.message)
    v = fastjsonschema.compile(copy.deepcopy(s))
    print('   compile() returns', v.__name__)
