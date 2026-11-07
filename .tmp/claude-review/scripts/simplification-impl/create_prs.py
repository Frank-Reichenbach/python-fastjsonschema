"""Create the meta issue and the 7 PRs on the fork, filling the {PLACEHOLDERS} in the bodies."""
import json
import re
import subprocess

R = 'Frank-Reichenbach/python-fastjsonschema'
B = '/Users/frankreichenbach/Development/private/python-fastjsonschema/.tmp/claude-review/simplified'
N = {'I_DATA': 17, 'I_UNCHANGED': 18, 'I_URN': 19, 'I_ARRAYS': 20, 'I_REL': 21, 'I_HANDLER': 22, 'I_SIB': 23}

PRS = [
    ('P_DATA', '1-data-keyword-values.md', 'simple/data-keyword-values', 'master',
     'Treat the values of const, enum, default and examples as data'),
    ('P_UNCHANGED', '2-keep-schema-unchanged.md', 'simple/keep-schema-unchanged', 'master',
     'Leave the $ref values of the schema unchanged'),
    ('P_URN', '3-urn-id-local-refs.md', 'simple/urn-id-local-refs', 'simple/data-keyword-values',
     'Resolve local refs inside a subschema with a urn: $id'),
    ('P_ARRAYS', '4-walk-schema-arrays.md', 'simple/walk-schema-arrays', 'simple/base-for-walk-schema-arrays',
     'Resolve refs inside allOf, anyOf, oneOf and items arrays against their $id'),
    ('P_REL', '5-relative-id-resolved-once.md', 'simple/relative-id-resolved-once', 'simple/keep-schema-unchanged',
     'Resolve each URI once under a relative $id with a directory'),
    ('P_HANDLER', '6-handler-schema-nested-id.md', 'simple/handler-schema-nested-id', 'simple/relative-id-resolved-once',
     'Walk schemas loaded through handlers like the main schema'),
    ('P_SIB', '7-ref-sibling-definitions.md', 'simple/ref-sibling-definitions', 'simple/integration-base',
     'Register $id and resolve refs in definitions next to a $ref'),
]
# Every PR body refers to the PR numbers of the others, which exist only after creation:
# predict nothing, create with the known numbers first, then edit each body once all exist.


def gh(*args, body=None):
    return subprocess.run(['gh', *args], input=body, capture_output=True, text=True, check=True).stdout.strip()


def fill(text):
    def repl(m):
        return str(N[m.group(1)]) if m.group(1) in N else m.group(0)
    return re.sub(r'\{([A-Z_]+)\}', repl, text)


meta_url = gh('issue', 'create', '-R', R, '--title', 'Resolver fixes: overview and merge order',
              '--body', 'Overview of the resolver PRs. The table follows once the PRs exist.')
N['META'] = int(meta_url.rsplit('/', 1)[1])

created = []
for key, fname, head, base, title in PRS:
    body = fill(open(B + '/pr-bodies/' + fname).read())
    url = gh('pr', 'create', '-R', R, '--head', head, '--base', base, '--title', title, '--body-file', '-', body=body)
    N[key] = int(url.rsplit('/', 1)[1])
    created.append((key, url))

# Second pass: now every number is known.
for key, fname, head, base, title in PRS:
    body = fill(open(B + '/pr-bodies/' + fname).read())
    assert not re.search(r'\{[A-Z_]+\}', body), (key, 'placeholder left')
    gh('pr', 'edit', str(N[key]), '-R', R, '--body-file', '-', body=body)

meta = open(B + '/issues/meta.md').read().split('\n', 2)[2]
meta = fill(meta)
assert not re.search(r'\{[A-Z_]+\}', meta)
gh('issue', 'edit', str(N['META']), '-R', R, '--body-file', '-', body=meta)

json.dump({'numbers': N, 'prs': created, 'meta': meta_url}, open(B + '/created.json', 'w'), indent=2)
print(json.dumps(N, indent=2))
