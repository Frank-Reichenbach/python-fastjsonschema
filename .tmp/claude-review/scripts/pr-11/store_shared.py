import fastjsonschema
from fastjsonschema.ref_resolver import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
ref = {'$ref': 'defs.json'}
store = {
 'http://e/a/doc.json': {'properties': {'c': ref}},
 'http://e/b/doc.json': {'properties': {'c': ref}},
 'http://e/a/defs.json': {'type': 'string'},
 'http://e/b/defs.json': {'type': 'integer'},
}
schema = {'properties': {'a': {'$ref': 'http://e/a/doc.json'}, 'b': {'$ref': 'http://e/b/doc.json'}}}
r = RefResolver.from_schema(schema, store=store, handlers={'http': lambda u: (_ for _ in ()).throw(AssertionError(u))})
g = CodeGeneratorDraft07(schema, resolver=r); gs = g.global_state; exec(g.func_code, gs); v = gs[r.get_scope_name()]
for d in ({'a': {'c': 'x'}, 'b': {'c': 1}},):
    try: v(d); print(' valid')
    except fastjsonschema.JsonSchemaException as e: print(' ', e)
