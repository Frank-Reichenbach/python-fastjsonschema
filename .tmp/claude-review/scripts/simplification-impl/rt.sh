#!/bin/zsh
# rt.sh <worktree> [pytest args...]  run tests with the suite symlinked in, then restore the empty submodule dir
S=/private/tmp/claude-501/-Users-frankreichenbach-Development-private-python-fastjsonschema/c0b91713-08d3-4aa6-8263-00ceb7610f99/scratchpad
W=$1; shift
cd $W || exit 1
rmdir JSON-Schema-Test-Suite 2>/dev/null; ln -sfn /Users/frankreichenbach/Development/private/python-fastjsonschema/JSON-Schema-Test-Suite JSON-Schema-Test-Suite
PYTHONPATH=$W $S/venv/bin/python -m pytest -q -W default --benchmark-skip -p no:cacheprovider "$@"
rc=$?
rm JSON-Schema-Test-Suite; mkdir JSON-Schema-Test-Suite
exit $rc
