import fastjsonschema
def h(uri): raise RuntimeError('handler called with ' + uri)
for sid in ['http://x/item.json#frag', 'item.json#frag', 'schemas/item.json#frag', 'schemas/item.json#']:
    s = {'$schema': 'http://json-schema.org/draft-07/schema#', '$id': sid, 'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}}}
    try:
        v = fastjsonschema.compile(s, handlers={'': h, 'http': h}); v({'c': 1}); print(sid, 'ok')
    except Exception as e: print(sid, type(e).__name__, e)
