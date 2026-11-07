import json, sys
outcomes = {}
class P:
    def pytest_runtest_logreport(self, report):
        if report.when == 'call' or (report.when == 'setup' and report.outcome != 'passed'):
            o = report.outcome
            if hasattr(report, 'wasxfail'):
                o = 'xpass' if o == 'passed' else 'xfail'
            outcomes[report.nodeid] = o
import pytest
pytest.main(sys.argv[2:], plugins=[P()])
json.dump(outcomes, open(sys.argv[1], 'w'), indent=0)
