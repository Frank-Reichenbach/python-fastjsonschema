import fastjsonschema, copy
from fastjsonschema import RefResolver
from fastjsonschema.draft2019 import CodeGeneratorDraft2019
from fastjsonschema.draft07 import CodeGeneratorDraft07
S = {'$ref': '#/definitions/a', 'definitions': {'a': {'$id': 'http://e.com/n.json', 'definitions': {'y': {'type': 'integer'}}, 'properties': {'b': {'$ref': '#/definitions/y'}}}, 'y': {'type': 'string'}}}
code = fastjsonschema.compile_to_code(S)
ns = {}; exec(code, ns)
for d in ({'b': 1}, {'b': 'x'}):
    try: ns['validate'](d); print('ctc', d, 'valid')
    except Exception as e: print('ctc', d, e)
doc = S
calls=[]
def h(u): calls.append(u); return copy.deepcopy(doc)
root = {'properties': {'p': {'$ref': 'http://e.com/doc.json'}, 'q': {'$ref': 'http://e.com/doc.json#/definitions/a'}}}
for cache in (True, False):
    calls.clear()
    r = RefResolver.from_schema(root, handlers={'http': h}, cache=cache, store={})
    g = CodeGeneratorDraft2019(root, resolver=r)
    ns = {}; exec(g.global_state_code + '\n' + g.func_code, ns)
    for d in ({'p': {'b': 1}, 'q': {'b': 1}}, {'p': {'b': 'x'}}, {'q': {'b': 'x'}}):
        try: ns['validate'](d); print('cache=%s %s valid' % (cache, d))
        except Exception as e: print('cache=%s %s %s' % (cache, d, e))
    print('calls', len(calls))
# self recursion
v = fastjsonschema.compile({'properties': {'a': {'$id': 'http://e.com/a.json', '$ref': 'http://e.com/a.json'}}})
try: v({'a': 1}); print('self ref valid')
except RecursionError: print('self ref RecursionError at validation')
