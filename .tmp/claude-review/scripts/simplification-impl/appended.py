"""appended.py COMMIT -> print the '+' lines of the last hunk of COMMIT's diff of tests/test_integration.py"""
import subprocess, sys
G = ['git', '-C', '/Users/frankreichenbach/Development/private/python-fastjsonschema']
diff = subprocess.run(G + ['show', sys.argv[1], '--format=', '-U0', '--', 'tests/test_integration.py'], capture_output=True, text=True).stdout
hunk = diff.split('\n@@')[-1].split('\n', 1)[1]
print('\n'.join(l[1:] for l in hunk.splitlines() if l.startswith('+')).strip('\n'))
