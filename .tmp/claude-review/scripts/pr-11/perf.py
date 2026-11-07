import time, fastjsonschema
from fastjsonschema.ref_resolver import RefResolver
from fastjsonschema.draft07 import CodeGeneratorDraft07
N=2000
DOC={'definitions':{f'd{i}':{'type':'object','properties':{'a':{'type':'string'},'b':{'type':'integer','minimum':i}}} for i in range(N)}}
def run(nrefs, cache):
    schema={'properties':{f'p{i}':{'$ref':f'http://e/doc.json#/definitions/d{i}'} for i in range(nrefs)}}
    t=time.perf_counter()
    r=RefResolver.from_schema(schema, handlers={'http':lambda u: DOC}, store={}, cache=cache)
    g=CodeGeneratorDraft07(schema, resolver=r); g.func_code
    return time.perf_counter()-t
for nrefs, cache in ((200,True),(200,False),(1000,True)):
    print(f'  nrefs={nrefs} cache={cache}: {min(run(nrefs,cache) for _ in range(3)):.3f}s')
