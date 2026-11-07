import fastjsonschema
for uri, sid in [('dir/main.json','dir/main.json'), ('schemas/main.json','main.json'), ('http://h/dir/main.json','dir/main.json'), ('http://h/dir/main.json','http://h/dir/main.json')]:
    loaded=[]
    def handler(u):
        loaded.append(u)
        if u == uri: return {'$id': sid, 'properties': {'c': {'$ref': 'child.json'}}}
        return {'type': 'integer'}
    try:
        fastjsonschema.compile({'$ref': uri}, handlers={'http': handler, '': handler})({'c':1})
        print(' ', uri, sid, loaded)
    except Exception as e: print(' ', uri, sid, loaded, type(e).__name__, e)
