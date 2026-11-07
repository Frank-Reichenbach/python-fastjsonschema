import fastjsonschema, copy, jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
docs = {'a/b/other.json': {'$id': 'a/b/other.json', 'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}, 't': {'$ref': 'third.json'}}},
        'a/b/third.json': {'type': 'string'}, 'a/b/a/b/third.json': {'type': 'boolean'}}
for base in ['a/b/root.json', 'http://h/a/b/root.json']:
    loaded = []
    def h(uri):
        loaded.append(uri); key = uri.replace('http://h/', '')
        return copy.deepcopy(docs[key])
    root = {'$schema': 'http://json-schema.org/draft-07/schema#', '$id': base, 'properties': {'o': {'$ref': 'other.json'}}}
    try:
        v = fastjsonschema.compile(root, handlers={'': h, 'http': h})
        r = []
        for d in [{'o': {'t': 's'}}, {'o': {'t': True}}]:
            try: v(d); r.append('valid')
            except fastjsonschema.JsonSchemaException: r.append('invalid')
    except Exception as e: r = [repr(e)[:100]]
    ol = []
    def ret(uri):
        ol.append(uri); key = uri.replace('http://h/', '')
        return Resource.from_contents(docs[key], default_specification=DRAFT7)
    val = jsonschema.Draft7Validator(root, registry=Registry(retrieve=ret))
    o = []
    for d in [{'o': {'t': 's'}}, {'o': {'t': True}}]:
        try: o.append('valid' if val.is_valid(d) else 'invalid')
        except Exception as e: o.append(type(e).__name__)
    print(base, 'fjs', r, loaded, '| oracle', o, ol)
