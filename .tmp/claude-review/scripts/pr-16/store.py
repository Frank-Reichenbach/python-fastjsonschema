"""Shared default `store` of RefResolver across resolvers (internal API; compile() uses store={})."""
import copy, sys
sys.path.insert(0, sys.argv[1])
from fastjsonschema import RefResolver, JsonSchemaException
from fastjsonschema.draft07 import CodeGeneratorDraft07

def n_node():
    return {'$id': 'http://ex/n.json', 'type': 'object', 'properties': {'m': {
        '$id': 'sub/m.json', 'definitions': {'k': {'type': 'integer'}},
        'properties': {'k': {'$ref': '#/definitions/k'}}}}}

def no_dl(uri): raise RuntimeError('download ' + uri)
def remote(uri):
    assert uri == 'http://ex/n.json', uri
    return n_node()

def build(schema, store=None, handlers={'http': no_dl}):
    kw = {} if store is None else {'store': store}
    r = RefResolver.from_schema(schema, handlers=handlers, **kw)
    g = CodeGeneratorDraft07(schema, resolver=r)
    ns = g.global_state; exec(g.func_code, ns)
    return ns[r.get_scope_name()]

def check(label, fn):
    try:
        v = fn()
        try:
            v({'m': {'k': 'x'}}); print(label, 'k="x" ACCEPTED')
        except JsonSchemaException: print(label, 'k="x" rejected')
    except Exception as e:
        print(label, 'EXC', type(e).__name__, e)

s1 = {'$id': 'http://ex/a.json', 'definitions': {'n': n_node()}}
build(s1)  # default (shared) store now holds s1's node n.json and sub/m.json
check('shared default store, S2 -> n.json:', lambda: build({'$ref': 'http://ex/n.json'}))
check('fresh store + handler, S2 -> n.json:', lambda: build({'$ref': 'http://ex/n.json'}, store={}, handlers={'http': remote}))
