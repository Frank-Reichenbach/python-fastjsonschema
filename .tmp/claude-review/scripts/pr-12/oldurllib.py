import sys, importlib.util, urllib
spec = importlib.util.spec_from_file_location('urllib.parse', '/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/urllib/parse.py')
mod = importlib.util.module_from_spec(spec); sys.modules['urllib.parse'] = mod; spec.loader.exec_module(mod); urllib.parse = mod
print('urljoin file:', mod.urljoin('file:schemas/item.json', '#/definitions/c'), mod.urlsplit('file:schemas/item.json').geturl())
import pytest
sys.exit(pytest.main(sys.argv[1:]))
