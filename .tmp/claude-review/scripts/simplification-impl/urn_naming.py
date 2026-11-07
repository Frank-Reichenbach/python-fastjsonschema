import fastjsonschema
schema = {'$id': 'urn:example:root',
          'definitions': {'a': {'$id': '#foo', 'type': 'integer'}, 'b': {'$id': 'urn:example:root:foo', 'type': 'string'}},
          'properties': {'a': {'$ref': '#foo'}, 'b': {'$ref': 'urn:example:root:foo'}}}
for data in ({'a': 1, 'b': 'x'}, {'b': 1}, {'a': 'x'}):
    try:
        print(data, '->', fastjsonschema.compile(schema)(data))
    except Exception as e:
        print(data, '->', type(e).__name__, getattr(e, 'message', e))
