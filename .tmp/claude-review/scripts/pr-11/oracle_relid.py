import jsonschema, referencing
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7
loaded=[]
def retrieve(u):
    loaded.append(u)
    if u=='http://h/dir/main.json': return Resource.from_contents({'$schema':'http://json-schema.org/draft-07/schema#','$id':'dir/main.json','properties':{'c':{'$ref':'child.json'}}})
    return Resource.from_contents({'type':'integer'}, default_specification=DRAFT7)
v=jsonschema.Draft7Validator({'$ref':'http://h/dir/main.json'}, registry=Registry(retrieve=retrieve))
print(v.is_valid({'c':1}), v.is_valid({'c':'x'}), loaded)
