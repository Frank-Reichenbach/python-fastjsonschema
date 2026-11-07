import json, sys, re, difflib
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
diff_keys = []
kinds = {'definition_only': 0, 'other': 0}
for k in a:
    if k.startswith('__'): continue
    for ff in ('True', 'False'):
        if a[k][ff] != b[k][ff]:
            diff_keys.append((k, ff))
            la, lb = a[k][ff].splitlines(), b[k][ff].splitlines()
            changed = [l for l in difflib.unified_diff(la, lb, lineterm='', n=0) if l[:1] in '+-' and not l.startswith(('+++', '---'))]
            if all('definition=' in l for l in changed):
                kinds['definition_only'] += 1
            else:
                kinds['other'] += 1
                print('NON-DEFINITION DIFF', k, ff); print('\n'.join(changed[:10]))
print('differing (schema, fast_fail) pairs:', len(diff_keys), 'distinct schemas:', len({k for k, _ in diff_keys}), kinds)
for k in sorted({k for k, _ in diff_keys}): print('  ', k)
