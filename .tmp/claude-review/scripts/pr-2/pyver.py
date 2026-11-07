import sys
from urllib import parse as urlparse
print(sys.version.split()[0])
print(' uses_relative =', urlparse.uses_relative)
def join_uri(base, ref):
    if ref.startswith('#'):
        if urlparse.urlsplit(base).scheme not in urlparse.uses_relative:
            return base.partition('#')[0] + ref
    return urlparse.urljoin(base, ref)
for base, ref in [('urn:example:node', '#'), ('urn:example:node', '#/definitions/x'), ('urn:a#frag', '#b'),
                  ('tag:example.com,2026:node', '#x'), ('s3://b/n.json', '#'), ('HTTP://e.com/a', '#x'),
                  ('http://e.com/a', '#'), ('http://e.com/a?', '#x'), ('', '#x'), ('node.json', '#'),
                  ('file:schemas/node.json', '#'), ('urn:ex:\tnode', '#x'), ('localhost:8080', '#x'),
                  ('urn:example:node', 'other'), ('s3://b/a.json', 'b.json'), ('C:\\x\\y.json', '#z')]:
    try:
        r = join_uri(base, ref)
    except Exception as e:
        r = repr(e)
    print('  %-30r %-20r join_uri=%-36r urljoin=%r normalize=%r' % (base, ref, r, urlparse.urljoin(base, ref), urlparse.urlsplit(r).geturl() if not r.startswith('Value') else ''))
