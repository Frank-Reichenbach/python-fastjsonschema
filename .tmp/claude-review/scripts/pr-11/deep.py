import fastjsonschema, sys
for n in (150, 250, 300, 350, 450, 600, 5000):
    doc = {'type': 'integer'}
    for _ in range(n): doc = {'items': doc}
    for label, f in (('handler', lambda: fastjsonschema.compile({'$ref': 'http://e/d.json'}, handlers={'http': lambda u: doc})),
                     ('main', lambda: fastjsonschema.compile(doc))):
        try: f(); r='ok'
        except RecursionError as e: r='RecursionError'
        except fastjsonschema.JsonSchemaDefinitionException as e: r='JSDefinitionException: '+str(e)[:40]
        except Exception as e: r=type(e).__name__
        print(f'  n={n} {label}: {r}')
