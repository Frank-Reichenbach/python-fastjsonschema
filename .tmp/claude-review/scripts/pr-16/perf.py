import copy, sys, time, json
sys.path.insert(0, sys.argv[1])
import fastjsonschema
from fastjsonschema import RefResolver
N = 2000
big = {'$schema': 'http://json-schema.org/draft-07/schema#', '$id': 'http://ex.com/big.json',
       'definitions': {'d%d' % i: {'type': 'integer'} for i in range(N)},
       'properties': {'p%d' % i: {'$ref': '#/definitions/d%d' % (i % 50)} for i in range(N)}}
def best(fn, n=5):
    ts = []
    for _ in range(n):
        s = copy.deepcopy(big); t = time.perf_counter(); fn(s); ts.append(time.perf_counter() - t)
    return min(ts)
print('walk only (RefResolver):  %.4fs' % best(lambda s: RefResolver.from_schema(s, store={})))
print('compile_to_code:          %.4fs' % best(lambda s: fastjsonschema.compile_to_code(s)))
meta = json.load(open(sys.argv[1] + '/tests/json_schema/metaschemas/draft7.json')) if False else None
