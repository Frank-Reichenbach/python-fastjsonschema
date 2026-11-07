import fastjsonschema, copy, warnings
warnings.simplefilter('ignore')
from fastjsonschema import _get_code_generator_class
from fastjsonschema.draft2019 import CodeGeneratorDraft2019
def run(label, schema, data=None, **kw):
    try:
        v = fastjsonschema.compile(copy.deepcopy(schema), handlers={'http': lambda u: (_ for _ in ()).throw(RuntimeError('handler '+u))}, **kw)
        try:
            v(data); r = 'valid'
        except fastjsonschema.JsonSchemaException as e:
            r = 'invalid: ' + e.message
    except Exception as e:
        r = '%s: %s' % (type(e).__name__, e)
    print('%-55s %s' % (label, r[:110]))

run('2019 invalid-URI $id next to $ref', {'properties': {'a': {'$id': 'http://[bad', '$ref': '#/definitions/x'}}, 'definitions': {'x': {}}}, {})
run('2019 invalid-URI $id (no $ref)', {'properties': {'a': {'$id': 'http://[bad', 'type': 'string'}}}, {})
run('d7  invalid-URI $id next to $ref', {'$schema': 'http://json-schema.org/draft-07/schema#', 'properties': {'a': {'$id': 'http://[bad', '$ref': '#/definitions/x'}}, 'definitions': {'x': {}}}, {})
run('2019 self-ref via sibling $id (compile only)', {'properties': {'a': {'$id': 'http://e.com/a.json', '$ref': 'http://e.com/a.json'}}}, {})
run('2019 root id + $ref (draft-04 key)', {'id': 'http://e.com/r.json', '$ref': 'x.json'}, 1)
run('2019 nested id (no $ref) honoured?', {'id': 'http://e.com/r/', 'properties': {'a': {'id': 'sub/', 'properties': {'b': {'$ref': 'x.json'}}}}}, {'a': {'b': 1}})
run('2019 nested id next to $ref', {'id': 'http://e.com/r/', 'properties': {'a': {'id': 'sub/', '$ref': 'x.json'}}}, {'a': 1})
# $schema non-string
for sv in (['draft-07'], None, 7):
    from fastjsonschema.ref_resolver import id_next_to_ref_applies
    try:
        g = _get_code_generator_class({'$schema': sv}).__name__
    except Exception as e:
        g = type(e).__name__
    print('$schema=%r: resolver 2019=%s, generator=%s' % (sv, id_next_to_ref_applies({'$schema': sv}), g))
# key with braces / quotes in definitions next to $ref
run('braces/quotes in defs names next to $ref', {'$ref': '#/definitions/a%7Bb%7D', 'definitions': {'a{b}': {'$id': 'http://e.com/q"{x}.json', 'definitions': {'y': {'type': 'integer'}}, 'properties': {'b': {'$ref': '#/definitions/y'}}}}}, {'b': 'x'})
run('compile_to_code sanity', {'$ref': '#/definitions/a', 'definitions': {'a': {'$id': 'http://e.com/n.json', 'definitions': {'y': {'type': 'integer'}}, 'properties': {'b': {'$ref': '#/definitions/y'}}}}}, {'b': 'x'})
code = fastjsonschema.compile_to_code({'$ref': '#/definitions/a', 'definitions': {'a': {'$id': 'http://e.com/n.json', 'definitions': {'y': {'type': 'integer'}}, 'properties': {'b': {'$ref': '#/definitions/y'}}}}})
ns = {}; exec(code, ns)
fn = [k for k in ns if k.startswith('validate')]
print('compile_to_code functions:', fn)
try:
    ns[fn[-1]]({'b': 'x'}); print('ctc: valid')
except Exception as e: print('ctc:', e)
# cache=False / RefResolver direct
from fastjsonschema import RefResolver
doc = {'$ref': '#/definitions/a', 'definitions': {'a': {'$id': 'http://e.com/n.json', 'definitions': {'y': {'type': 'integer'}}, 'properties': {'b': {'$ref': '#/definitions/y'}}}, 'y': {'type': 'string'}}}
calls=[]
def h(u): calls.append(u); return copy.deepcopy(doc)
for cache in (True, False):
    calls.clear()
    r = RefResolver.from_schema({'properties': {'p': {'$ref': 'http://e.com/doc.json'}, 'q': {'$ref': 'http://e.com/doc.json'}}}, handlers={'http': h}, cache=cache, store={})
    g = CodeGeneratorDraft2019({'properties': {'p': {'$ref': 'http://e.com/doc.json'}, 'q': {'$ref': 'http://e.com/doc.json'}}}, resolver=r)
    ns = {}; exec(g.global_state_code + '\n' + g.func_code, ns)
    f = ns[[k for k in ns if k.startswith('validate')][-1]]
    for d in ({'p': {'b': 1}, 'q': {'b': 1}}, {'q': {'b': 'x'}}):
        try: f(d); print('cache=%s %s valid calls=%d' % (cache, d, len(calls)))
        except Exception as e: print('cache=%s %s %s calls=%d' % (cache, d, e, len(calls)))
