import runpy, sys
src = open('perf_fix.py').read().split('sys.argv =')[0]
exec(src)
sys.argv = ['fuzz.py', '2']
runpy.run_path('fuzz.py', run_name='__main__')
