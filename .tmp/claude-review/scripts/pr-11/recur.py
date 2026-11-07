import fastjsonschema, collections, time
from fastjsonschema.ref_resolver import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
DOCS = {
 'http://e/a.json': {'$id':'http://e/a.json','type':'object','properties':{'b':{'$ref':'b.json'}, 'n':{'$id':'sub/n.json','definitions':{'x':{'type':'integer'}},'properties':{'v':{'$ref':'#/definitions/x'}, 'a':{'$ref':'../a.json'}}}}},
 'http://e/b.json': {'type':'object','definitions':{'x':{'type':'string'}},'properties':{'a':{'$ref':'a.json'}, 'x':{'$ref':'#/definitions/x'}}},
}
def build(cache, fast_fail=True):
    loaded=collections.Counter()
    def h(u): loaded[u]+=1; return DOCS[u]
    schema={'$ref':'http://e/a.json'}
    r=RefResolver.from_schema(schema, handlers={'http':h}, store={}, cache=cache)
    g=CodeGeneratorDraft07(schema, resolver=r, fast_fail=fast_fail)
    gs=g.global_state; exec(g.func_code, gs)
    return gs[r.get_scope_name()], loaded, g.func_code
for cache in (True, False):
  for ff in (True, False):
    v, loaded, code = build(cache, ff)
    res=[]
    for d in ({'b':{'a':{'n':{'v':1,'a':{}}}, 'x':'s'}}, {'n':{'v':'s'}}, {'b':{'x':1}}, {'n':{'a':{'n':{'v':'q'}}}}):
        try: v(d); res.append('valid')
        except fastjsonschema.JsonSchemaException as e: res.append(str(e)[:40])
    print('cache',cache,'ff',ff,res, dict(loaded), code.count('def validate'))
