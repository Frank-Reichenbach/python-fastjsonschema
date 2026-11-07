import fastjsonschema
def nest(n, kw):
    d = {"type": "integer"}
    for _ in range(n):
        d = {kw: [d]} if kw in ('allOf','anyOf','oneOf','items') else {kw: d}
    return d
for kw in ('allOf', 'anyOf', 'items', 'not'):
    last = None
    for n in range(150, 260):
        try: fastjsonschema.compile(nest(n, kw)); last = n
        except Exception as e: first_fail = (n, type(e).__name__); break
    print(kw, "max ok:", last, "first fail:", first_fail)
