import math

from stgem.features import Real
from stgem.limit import ExecutionCount
from stgem.task import generate_critical_tests

calls = 0

def f1(x1: Real(min_value=0, max_value=2 * math.pi),
       x2: Real(min_value=0, max_value=2 * math.pi),
       x3: Real(min_value=0, max_value=2 * math.pi)) \
        -> Real('result', min_value=-10, max_value=300):

    # keep track of calls to SUT
    global calls
    if calls > 10:
        raise Exception('SUT error')
    calls += 1

    return 300 - 101 * (math.sin(x1) + math.sin(x2 * 2) + math.sin(x3 * 3))


def f2(x1: Real(min_value=0, max_value=2 * math.pi),
       x2: Real(min_value=0, max_value=2 * math.pi),
       x3: Real(min_value=0, max_value=2 * math.pi)) \
        -> Real('result', min_value=-10, max_value=300):
    # keep track of calls to SUT
    global calls
    calls += 1

    return 300 - 101 * (math.sin(x1) + math.sin(x2 * 2) + math.sin(x3 * 3))


import traceback

import os


def test_resume():
    try:
        os.remove(".partial")
    except:
        pass

    try:
        critical, all, tester = generate_critical_tests(
            sut=f1,
            formula='result>0',
            limit=ExecutionCount(25),
            checkpoint_name='.partial'
        )
    except Exception as e:
        if str(e)!='SUT error':
            raise e
        print(e,"(as expected)")

    critical, all, tester = generate_critical_tests(
        sut=f2,
        formula='result>0',
        limit=ExecutionCount(25),
        checkpoint_name='.partial'
    )

    print('\n\nAll results:')
    print(all)

    assert calls == 25
    assert len(all.index) == 25


if __name__ == '__main__':
    test_resume()
