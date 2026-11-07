import copy, re, fastjsonschema
def run(label, schema, datas, **kw):
    calls = []
    hs = kw.pop('remote', None)
    if hs:
        def h(uri):
            calls.append(uri); return copy.deepcopy(hs[uri])
        kw['handlers'] = {s: h for s in {u.split(':')[0] for u in hs}}
    try:
        v = fastjsonschema.compile(copy.deepcopy(schema), **kw)
    except Exception as e:
        print('%-55s COMPILE %s: %s' % (label, type(e).__name__, e)); return
    out = []
    for d in datas:
        try: v(copy.deepcopy(d)); out.append('valid')
        except fastjsonschema.JsonSchemaException: out.append('invalid')
        except Exception as e: out.append('RUN-' + type(e).__name__)
    print('%-55s %s calls=%d' % (label, out, len(calls)))

for scheme_id in ('urn:ex:root', 'http://ex.com/root'):
    s = {'$id': scheme_id, 'definitions': {'i': {'type': 'integer'}},
         'allOf': [{'properties': {'a': {'$ref': '#/definitions/i'}}}],
         'properties': {'b': {'$ref': '#/definitions/i'}, 'r': {'$ref': '#'}}}
    run('root %s, refs in allOf + properties' % scheme_id, s, [{'a': 1, 'b': 1, 'r': {'a': 1}}, {'r': {'a': 'x'}}, {'a': 'x'}])
    # subschema with id inside array (walk doesn't descend arrays at this stage)
    sub_id = scheme_id.replace('root', 'sub')
    s = {'definitions': {'i': {'type': 'string'}},
         'allOf': [{'$id': sub_id, 'definitions': {'i': {'type': 'integer'}}, 'properties': {'a': {'$ref': '#/definitions/i'}}}]}
    run('sub %s inside allOf, a=1 / a="x"' % sub_id, s, [{'a': 1}, {'a': 'x'}])

for scheme in ('urn:ex:', 'http://ex.com/'):
    remote = {scheme + 'alias': {'$id': scheme + 'real', 'definitions': {'i': {'type': 'integer'}},
                                 'properties': {'v': {'$ref': '#/definitions/i'}, 'self': {'$ref': '#'}}}}
    root = {'definitions': {'i': {'type': 'string'}}, 'properties': {'p': {'$ref': scheme + 'alias'}}}
    for cache in (True,):
        run('remote alias %s cache=%s v=1 / v="x" / self.v="x"' % (scheme, cache), root,
            [{'p': {'v': 1}}, {'p': {'v': 'x'}}, {'p': {'self': {'v': 'x'}}}], remote=remote)
