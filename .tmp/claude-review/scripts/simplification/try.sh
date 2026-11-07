#!/bin/zsh
# usage: try.sh <target-commit> <code-commits...>   -> applies code diffs of listed commits onto master, tests file from target, runs target's new tests
S=/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad; W=$S/simp/wt
R=/Users/frankreichenbach/Development/private/python-fastjsonschema
t=$1; shift
cd $W && git checkout -q -f master -- fastjsonschema tests && git clean -qfd fastjsonschema tests
for c in "$@"; do
  if ! git -C $R show $c --format= -- fastjsonschema/ | git apply -3 --whitespace=nowarn >/dev/null 2>&1; then echo "CONFLICT applying $c"; git checkout -q -f master -- fastjsonschema; exit 0; fi
done
git -C $R show ${t}:tests/test_integration.py > tests/test_integration.py
k=$(paste -sd'|' $S/simp/tests-$t.txt | sed 's/|/ or /g')
out=$(PYTHONPATH=$W $S/venv/bin/python -m pytest -q -p no:cacheprovider --benchmark-skip tests/test_integration.py -k "$k" 2>&1 | tail -1)
echo "$out"
