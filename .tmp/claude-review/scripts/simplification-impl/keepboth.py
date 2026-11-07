"""keepboth.py FILE SEP -> resolve every conflict block in FILE as ours + SEP + theirs"""
import re, sys
p, sep = sys.argv[1], sys.argv[2].encode().decode('unicode_escape')
s = open(p).read()
pat = re.compile(r'<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n', re.S)
n = len(pat.findall(s))
s = pat.sub(lambda m: m.group(1).rstrip('\n') + sep + m.group(2), s)
open(p, 'w').write(s)
print(p, 'resolved', n)
