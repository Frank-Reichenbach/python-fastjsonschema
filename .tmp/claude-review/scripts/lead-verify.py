import time, fastjsonschema as f
# PR11-1: deep remote doc
deep = {}; cur = deep
for _ in range(5000): cur['not'] = {}; cur = cur['not']
try: f.compile({'$ref': 'x://d.json'}, handlers={'x': lambda u: deep}); print('deep remote: compiled')
except Exception as e: print('deep remote:', type(e).__name__, str(e)[:80])
try: f.compile(deep); print('deep local: compiled')
except Exception as e: print('deep local:', type(e).__name__, str(e)[:80])
# PR8-1: many colliding names
n = 4000
defs = {('a' + '-'*0 + ''.join('-' if (i>>k)&1 else '_' for k in range(12))): {'type': 'integer'} for i in range(n)}
s = {'definitions': defs, 'properties': {str(i): {'$ref': '#/definitions/' + k} for i, k in enumerate(defs)}}
t = time.time(); f.compile_to_code(s); print('colliding %d: %.2fs' % (n, time.time() - t))
defs2 = {'d%d' % i: {'type': 'integer'} for i in range(n)}
s2 = {'definitions': defs2, 'properties': {str(i): {'$ref': '#/definitions/' + k} for i, k in enumerate(defs2)}}
t = time.time(); f.compile_to_code(s2); print('distinct %d: %.2fs' % (n, time.time() - t))
# PR10-1: id annotation in array item, draft-07
s3 = {'$schema': 'http://json-schema.org/draft-07/schema#', 'definitions': {'n': {'type': 'integer'}},
      'allOf': [{'id': 'other/', 'properties': {'a': {'$ref': '#/definitions/n'}}}]}
try: print('id in allOf:', f.compile(s3)({'a': 1}))
except Exception as e: print('id in allOf:', type(e).__name__, e)
