import copy
from fastjsonschema.ref_resolver import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
from fastjsonschema import JsonSchemaException
calls = []
remote = {'$id': 'urn:ex:real', 'definitions': {'i': {'type': 'integer'}}, 'properties': {'v': {'$ref': '#/definitions/i'}, 'self': {'$ref': '#'}}}
def h(uri):
    calls.append(uri); return copy.deepcopy(remote)
root = {'properties': {'p': {'$ref': 'urn:ex:alias'}}}
res = RefResolver.from_schema(root, handlers={'urn': h}, store={}, cache=False)
gen = CodeGeneratorDraft07(root, resolver=res)
g = gen.global_state; exec(gen.func_code, g)
f = g[res.get_scope_name()]
for d in ({'p': {'v': 1}}, {'p': {'self': {'v': 'x'}}}):
    try: f(d); print('valid')
    except JsonSchemaException as e: print('invalid', e.message)
print('handler calls', calls)
