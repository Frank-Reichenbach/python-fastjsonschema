import json, glob, sys, os, copy, hashlib
import fastjsonschema
root = sys.argv[1]; out = {}
for d in ('draft4', 'draft7', 'draft2019-09'):
    for f in sorted(glob.glob(os.path.join(root, 'JSON-Schema-Test-Suite/tests', d, '**/*.json'), recursive=True)):
        for i, case in enumerate(json.load(open(f))):
            key = '%s#%d' % (os.path.relpath(f, root), i)
            try:
                out[key] = hashlib.md5(fastjsonschema.compile_to_code(copy.deepcopy(case['schema']), handlers={'http': lambda u: (_ for _ in ()).throw(RuntimeError(u)), 'https': lambda u: (_ for _ in ()).throw(RuntimeError(u))}).encode()).hexdigest()
            except Exception as e:
                out[key] = 'ERR ' + type(e).__name__
json.dump(out, sys.stdout)
