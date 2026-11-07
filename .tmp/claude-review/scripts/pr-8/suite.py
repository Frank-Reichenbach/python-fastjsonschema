import json, glob, os, sys, hashlib, fastjsonschema
root = sys.argv[1]
folders = {'draft4': 'http://json-schema.org/draft-04/schema#', 'draft6': 'http://json-schema.org/draft-06/schema#',
           'draft7': 'http://json-schema.org/draft-07/schema#', 'draft2019-09': 'https://json-schema.org/draft/2019-09/schema'}
h = {'http': lambda u: {}, 'https': lambda u: {}}
out = {}
for folder, sch in folders.items():
    for f in sorted(glob.glob(os.path.join(root, 'tests', folder, '**', '*.json'), recursive=True)):
        for i, case in enumerate(json.load(open(f))):
            s = case['schema']
            if isinstance(s, dict):
                if '$schema' not in s:
                    s = dict(s, **{'$schema': sch})
            key = '%s|%s|%d' % (folder, os.path.relpath(f, root), i)
            try:
                out[key] = hashlib.sha1(fastjsonschema.compile_to_code(s, handlers=h).encode()).hexdigest()
            except Exception as e:
                out[key] = 'EXC:' + type(e).__name__
json.dump(out, sys.stdout, indent=0, sort_keys=True)
