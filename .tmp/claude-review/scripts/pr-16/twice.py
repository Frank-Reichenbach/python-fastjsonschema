import sys
sys.path.insert(0, sys.argv[1])
import fastjsonschema
for base in ('http://ex.com/', ''):
    twice = {'$ref': '#/definitions/x'}
    schema = {'$id': base + 'root.json', 'properties': {'a': {'$id': base + 'a/x.json', 'definitions': {'x': {'type': 'integer'}}, 'properties': {'v': twice}},
                                   'b': {'$id': base + 'b/y.json', 'definitions': {'x': {'type': 'null'}}, 'properties': {'v': twice}}}}
    if not base: del schema['$id']
    try:
        v = fastjsonschema.compile(schema, handlers={'http': lambda u: 1/0})
        out = []
        for d in ({'a': {'v': 1}}, {'b': {'v': None}}, {'b': {'v': 1}}):
            try: v(d); out.append('valid')
            except fastjsonschema.JsonSchemaException: out.append('invalid')
        print(repr(base), "a.v=1, b.v=None, b.v=1 ->", out)
    except Exception as e:
        print(repr(base), 'EXC', type(e).__name__, e)
