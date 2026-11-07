#!/bin/zsh
# parentcheck.sh <branch> <parent> <module...> : run the branch's new test modules against the parent's code
S=/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad; V=$S/impl/verify; G=/Users/frankreichenbach/Development/private/python-fastjsonschema
b=$1; p=$2; shift 2
cd $V && git checkout -q -f --detach $p && git clean -qfd tests
for m in "$@"; do git -C $G show "${b}:tests/${m}" > tests/$m; done
echo "== $b on parent $p"
$S/impl/rt.sh $V --timeout 20 $(for m in "$@"; do echo tests/$m; done) 2>&1 | grep -E "passed|failed|error" | tail -1
cd $V && rm -f $(for m in "$@"; do echo tests/$m; done)
