"""Public API: a registry of schemas, each compiled, and a handler serving the registry objects."""
import sys
sys.path.insert(0, sys.argv[1])
import fastjsonschema
order = sys.argv[2]
registry = {
    'http://ex/n.json': {'$id': 'http://ex/n.json', 'type': 'object', 'properties': {'m': {
        '$id': 'sub/m.json', 'definitions': {'k': {'type': 'integer'}},
        'properties': {'k': {'$ref': '#/definitions/k'}}}}},
    'http://ex/b.json': {'$id': 'http://ex/b.json', '$ref': 'http://ex/n.json'},
}
handlers = {'http': lambda uri: registry[uri]}
validators = {}
for uri in (['http://ex/n.json', 'http://ex/b.json'] if order == 'n-first' else ['http://ex/b.json', 'http://ex/n.json']):
    try:
        validators[uri] = fastjsonschema.compile(registry[uri], handlers=handlers)
        try:
            validators[uri]({'m': {'k': 'x'}}); r = 'ACCEPTS invalid'
        except fastjsonschema.JsonSchemaException: r = 'rejects invalid'
        print(uri, r)
    except Exception as e:
        print(uri, 'EXC', type(e).__name__, e)
