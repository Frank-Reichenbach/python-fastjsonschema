import timeit, json, fastjsonschema, glob, os
p = [x for x in glob.glob(os.environ['WT'] + '/tests/json_schema/metaschemas/**/*.json', recursive=True) if 'draft-07' in x or 'draft7' in x][0]
s = json.load(open(p))
s2 = dict(s, **{'$id': 'schemas/meta.json'})
for lab, x in [('draft7 meta', s)]:
    print(lab, round(min(timeit.repeat(lambda: fastjsonschema.compile_to_code(x), number=50, repeat=5)) / 50 * 1000, 3), 'ms')
