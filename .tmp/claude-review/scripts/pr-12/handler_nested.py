import fastjsonschema, copy, threading
docs = {
 'http://x/other.json': {'definitions': {'n': {'$id': 'sub/n.json', 'properties': {'s': {'$ref': '#'}, 'v': {'type': 'integer'}, 'w': {'$ref': 'w.json'}}}},
                         'properties': {'n': {'$ref': 'sub/n.json'}, 'n2': {'$ref': '#/definitions/n'}}},
 'http://x/sub/w.json': {'type': 'string'},
 'http://x/w.json': {'type': 'boolean'},
}
loaded = []
def h(uri):
    loaded.append(uri)
    if uri in docs: return copy.deepcopy(docs[uri])
    raise RuntimeError('handler called with ' + uri)
for root in [{'$id': 'http://x/root.json', 'properties': {'o': {'$ref': 'other.json'}}}, {'$id': 'r/root.json', 'properties': {'o': {'$ref': 'http://x/other.json'}}}]:
  for ff in (True, False):
    loaded.clear(); out = []
    def go():
        try:
            v = fastjsonschema.compile(root, handlers={'http': h, '': h}, fast_fail=ff)
            for d in [{'o': {'n': {'s': {'v': 1}, 'w': 'x'}, 'n2': {'w': 'x'}}}, {'o': {'n': {'s': {'v': 'a'}}}}, {'o': {'n2': {'w': True}}}]:
                try: v(d); out.append('valid')
                except fastjsonschema.JsonSchemaException: out.append('invalid')
        except Exception as e: out.append(f'{type(e).__name__}: {e}')
    t = threading.Thread(target=go, daemon=True); t.start(); t.join(8)
    print(root['$id'], ff, out or 'HANG', loaded)
