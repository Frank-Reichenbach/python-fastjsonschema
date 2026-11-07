import fastjsonschema
from fastjsonschema.ref_resolver import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
loaded=[]
DOC = {'$id': 'http://e/doc.json', 'properties': {'n': {'$id': 'sub/n.json', 'properties': {'v': {'$ref': 'other.json'}}}}}
def h(u):
    loaded.append(u)
    return DOC if u == 'http://e/doc.json' else {'type': 'integer'}
def build(schema, store):
    r = RefResolver.from_schema(schema, handlers={'http': h})
    g = CodeGeneratorDraft07(schema, resolver=r); gs = g.global_state; exec(g.func_code, gs); return gs[r.get_scope_name()]
store = {}
build({'$ref': 'http://e/doc.json'}, store)({'n': {'v': 1}})
print(' first ', loaded); loaded.clear()
try:
    build({'$ref': 'http://e/sub/n.json'}, store)({'v': 1}); print(' second', loaded)
except Exception as e: print(' second', loaded, type(e).__name__, e)
