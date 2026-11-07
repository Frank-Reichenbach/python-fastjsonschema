import fastjsonschema
loaded=[]
def handler(u):
    loaded.append(u)
    if u=='http://a/x.json': return {'$id':'http://b/y.json','definitions':{'d':{'type':'string'}},'properties':{'c':{'$ref':'child.json'},'d':{'$ref':'#/definitions/d'}}}
    return {'type':'integer'}
v=fastjsonschema.compile({'$ref':'http://a/x.json'}, handlers={'http':handler})
for d in ({'c':1,'d':'s'},{'c':'x'},{'d':1}):
    try: v(d); print(' ',d,'valid')
    except Exception as e: print(' ',d,e)
print(' ', loaded)
