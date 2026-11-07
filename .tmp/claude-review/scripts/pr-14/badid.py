import fastjsonschema
cases = {
 '2019 $id next to $ref': {'properties': {'a': {'$id': 'http://[bad', '$ref': '#/definitions/x'}}, 'definitions': {'x': {'type': 'integer'}}},
 'd7 unused def next to $ref': {'$schema': 'http://json-schema.org/draft-07/schema#', '$ref': '#/definitions/a', 'definitions': {'a': {'type': 'integer'}, 'b': {'$id': 'http://[bad'}}},
 'd7 unused def, no $ref (pre-existing)': {'$schema': 'http://json-schema.org/draft-07/schema#', 'definitions': {'a': {'type': 'integer'}, 'b': {'$id': 'http://[bad'}}},
}
for k, s in cases.items():
    try:
        v = fastjsonschema.compile(s); v({'a': 1} if '2019' in k else 1); print('%-40s compiles, valid' % k)
    except Exception as e:
        print('%-40s %s: %s' % (k, type(e).__name__, e))
