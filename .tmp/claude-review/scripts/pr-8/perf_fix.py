import sys, runpy
from fastjsonschema import generator
def _validation_function_name(self):
    uri = self._resolver.get_uri()
    if uri not in self._validation_function_names:
        base = name = self._resolver.get_scope_name()
        nxt = self.__dict__.setdefault('_next_suffix', {})
        index = nxt.get(base, 2)
        while name in self._taken_validation_function_names:
            name = '{}_{}_'.format(base, index)
            index += 1
        nxt[base] = index
        self._validation_function_names[uri] = name
        self._taken_validation_function_names.add(name)
    return self._validation_function_names[uri]
generator.CodeGenerator._validation_function_name = _validation_function_name
sys.argv = ['perf.py'] + sys.argv[1:]
runpy.run_path('perf.py', run_name='__main__')
