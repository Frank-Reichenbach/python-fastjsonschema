import fastjsonschema
def h(uri): raise RuntimeError('handler called with ' + uri)
for sid in ['http://x/a/./item.json', 'http://x/a/b/../item.json', 'a/./item.json', 'a/b/../item.json', 'HTTP://x/a/item.json', 'FILE:a/item.json']:
    s = {'$schema': 'http://json-schema.org/draft-07/schema#', '$id': sid, 'properties': {'p': {'$ref': 'item.json'}, 'v': {'type': 'integer'}}}
    try:
        v = fastjsonschema.compile(s, handlers={'': h, 'http': h, 'file': h}); v({'p': {'v': 1}})
        try: v({'p': {'v': 'a'}}); r = 'NOT caught'
        except fastjsonschema.JsonSchemaValueException: r = 'caught'
        print(f'{sid:28} ok {r}')
    except Exception as e: print(f'{sid:28} {type(e).__name__} {e}')
