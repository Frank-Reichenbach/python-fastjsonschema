import fastjsonschema
from fastjsonschema.ref_resolver import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
DOC = {'$id': 'http://e/doc.json', 'properties': {'n': {'$id': 'sub/n.json',
        'definitions': {'x': {'type': 'integer'}}, 'properties': {'v': {'$ref': '#/definitions/x'}}}}}
def build(schema):
    # default store argument: shared between resolvers
    r = RefResolver.from_schema(schema, handlers={'http': lambda u: DOC})
    g = CodeGeneratorDraft07(schema, resolver=r); gs = g.global_state; exec(g.func_code, gs); return gs[r.get_scope_name()]
v1 = build({'$ref': 'http://e/doc.json'})
print(' first ', v1({'n': {'v': 1}}))
try:
    v2 = build({'$ref': 'http://e/sub/n.json'})
    print(' second', v2({'v': 1}))
except Exception as e: print(' second', type(e).__name__, e)
