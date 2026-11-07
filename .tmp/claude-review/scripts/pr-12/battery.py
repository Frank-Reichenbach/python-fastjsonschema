import sys, threading, copy, json
import fastjsonschema
D7 = "http://json-schema.org/draft-07/schema#"
D4 = "http://json-schema.org/draft-04/schema#"

def run(label, schema, datas, docs=None, fast_fail=True, oracle=True):
    docs = docs or {}
    loaded = []
    def handler(uri):
        loaded.append(uri)
        if uri in docs:
            return copy.deepcopy(docs[uri])
        raise RuntimeError('handler called with ' + uri)
    out = []
    def go():
        try:
            v = fastjsonschema.compile(copy.deepcopy(schema), handlers={'': handler, 'file': handler, 'http': handler, 'urn': handler}, fast_fail=fast_fail)
            for d in datas:
                try:
                    v(copy.deepcopy(d)); out.append('valid')
                except fastjsonschema.JsonSchemaException as e:
                    out.append('invalid')
        except Exception as e:
            out.append(f'{type(e).__name__}: {str(e)[:90]}')
    t = threading.Thread(target=go, daemon=True); t.start(); t.join(8)
    res = out if out else ['HANG']
    orc = ''
    if oracle:
        try:
            import jsonschema, referencing
            from referencing import Registry, Resource
            from referencing.jsonschema import DRAFT7, DRAFT4
            oloaded = []
            def retrieve(uri):
                oloaded.append(uri)
                if uri in docs:
                    return Resource.from_contents(docs[uri], default_specification=DRAFT7)
                raise referencing.exceptions.NoSuchResource(uri)
            reg = Registry(retrieve=retrieve)
            cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)
            val = cls(schema, registry=reg)
            o = []
            for d in datas:
                try:
                    o.append('valid' if val.is_valid(d) else 'invalid')
                except Exception as e:
                    o.append(type(e).__name__)
            orc = f' | oracle={o} loaded={oloaded}'
        except Exception as e:
            orc = f' | oracle err {type(e).__name__}: {str(e)[:60]}'
    print(f'{label:38} {res} loaded={loaded}{orc}')

for ff in (True, False):
    print('--- fast_fail', ff)
    cnt = {'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}}}
    for sid in ['schemas/item.json#', 'schemas/item.json?v=1', '../schemas/item.json', './a/item.json', 'a/./b/item.json', 'a/b/../item.json', 'FILE:schemas/item.json', 'schemas/item.json#frag', '//host/a/item.json', '/abs/a/item.json']:
        run(f'local ref, $id={sid}', dict(cnt, **{'$schema': D7, '$id': sid}), [{'c': 1}, {'c': 'a'}], fast_fail=ff)
    run('draft4 id schemas/item.json#', dict(cnt, **{'$schema': D4, 'id': 'schemas/item.json#'}), [{'c': 1}, {'c': 'a'}], fast_fail=ff)
    run('../ other.json', {'$schema': D7, '$id': '../s/item.json', 'properties': {'x': {'$ref': 'other.json'}}}, [{'x': 1}, {'x': 'a'}], docs={'../s/other.json': {'type': 'integer'}}, fast_fail=ff)
    run('query id other.json', {'$schema': D7, '$id': 's/item.json?v=1', 'properties': {'x': {'$ref': 'other.json'}}}, [{'x': 1}, {'x': 'a'}], docs={'s/other.json': {'type': 'integer'}}, fast_fail=ff)
    # nested relative ids
    nested = {'$schema': D7, '$id': 'a/b/root.json',
              'definitions': {'n': {'$id': 'c/node.json', 'properties': {'self': {'$ref': '#'}, 'v': {'type': 'integer'}}},
                              'm': {'$id': '../x/m.json', 'properties': {'v': {'type': 'string'}, 'to_n': {'$ref': '../b/c/node.json'}}}},
              'properties': {'n': {'$ref': 'c/node.json'}, 'm': {'$ref': '#/definitions/m'}, 'm2': {'$ref': '../x/m.json'}}}
    run('nested rel ids', nested, [{'n': {'self': {'v': 1}}, 'm': {'v': 's', 'to_n': {'v': 2}}, 'm2': {'v': 's'}},
                                   {'n': {'self': {'v': 'a'}}}, {'m': {'to_n': {'v': 'a'}}}, {'m2': {'v': 1}}], fast_fail=ff)
    # handler doc under relative base: local ref, sibling ref, own $id
    run('loaded doc sibling ref', {'$schema': D7, '$id': 'a/b/root.json', 'properties': {'o': {'$ref': 'other.json'}}}, [{'o': 1}, {'o': 'a'}],
        docs={'a/b/other.json': {'$ref': 'third.json'}, 'a/b/third.json': {'type': 'integer'}}, fast_fail=ff)
    run('loaded doc own $id=other.json', {'$schema': D7, '$id': 'a/b/root.json', 'properties': {'o': {'$ref': 'other.json'}}}, [{'o': {'c': 1}}, {'o': {'c': 'a'}}],
        docs={'a/b/other.json': {'$id': 'other.json', 'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}}}}, fast_fail=ff)
    run('loaded doc recursion #', {'$schema': D7, '$id': 'a/b/root.json', 'properties': {'o': {'$ref': 'other.json'}}}, [{'o': {'o': {'v': 1}}}, {'o': {'o': {'v': 'a'}}}],
        docs={'a/b/other.json': {'properties': {'o': {'$ref': '#'}, 'v': {'type': 'integer'}}}}, fast_fail=ff)
    # root $ref with $id sibling
    run('root $ref + $id', {'$schema': D7, '$id': 'schemas/item.json', '$ref': '#/definitions/a', 'definitions': {'a': {'$ref': '#/definitions/b'}, 'b': {'type': 'integer'}}}, [1, 'a'], fast_fail=ff, oracle=False)
    # recursion with root rel id
    run('recursive tree', {'$schema': D7, '$id': 's/tree.json', 'properties': {'kids': {'type': 'array', 'items': {'$ref': '#'}}, 'v': {'type': 'integer'}}},
        [{'kids': [{'kids': [{'v': 1}]}]}, {'kids': [{'kids': [{'v': 'a'}]}]}], fast_fail=ff)
    run('self by name item.json', {'$schema': D7, '$id': 's/item.json', 'properties': {'p': {'$ref': 'item.json'}, 'v': {'type': 'integer'}}}, [{'p': {'v': 1}}, {'p': {'v': 'a'}}], fast_fail=ff)
    run('abs sub under rel root', {'$schema': D7, '$id': 's/item.json', 'properties': {'p': {'$id': 'http://x/node.json', 'properties': {'q': {'$ref': 'other.json'}}}}}, [{'p': {'q': 1}}, {'p': {'q': 'a'}}],
        docs={'http://x/other.json': {'type': 'integer'}}, fast_fail=ff)
    run('rel sub under no root id, anyOf', {'$schema': D7, 'anyOf': [{'$id': 'a/b/n.json', 'properties': {'q': {'$ref': '#/definitions/i'}}, 'definitions': {'i': {'type': 'integer'}}}]}, [{'q': 1}, {'q': 'a'}], fast_fail=ff)
    run('draft4 plain-name under rel id', {'$schema': D4, 'id': 's/item.json', 'definitions': {'f': {'id': '#foo', 'type': 'integer'}}, 'properties': {'p': {'$ref': '#foo'}}}, [{'p': 1}, {'p': 'a'}], fast_fail=ff)
    run('urn root with rel-looking', {'$schema': D7, '$id': 'urn:a:b/c', 'definitions': {'c': {'type': 'integer'}}, 'properties': {'c': {'$ref': '#/definitions/c'}}}, [{'c': 1}, {'c': 'a'}], fast_fail=ff)
