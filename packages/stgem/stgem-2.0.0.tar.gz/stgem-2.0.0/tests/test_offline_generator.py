import math

from stgem.features import Real
from stgem.limit import WallTime, TestCount
from stgem.sut import as_SystemUnderTest
from stgem.task import generate_tests_offline, generate_critical_tests
from stgem.testgenerator.random import RandomGenerator
from stgem.testgenerator.random.model import LHS
from stgem.testsuitegenerator import run, OfflineTestGeneration


# Define some arbitrary but complicated function.
def f1(
        x1: Real(min_value=0, max_value=2 * math.pi),
        x2: Real(min_value=0, max_value=2 * math.pi),
        x3: Real(min_value=0, max_value=2 * math.pi)) \
        -> Real("result", min_value=-10, max_value=300):
    result = 300 - 101 * (math.sin(x1) + math.sin(x2 * 2) + math.sin(x3 * 3))
    return result


def test_offline_test_generation():
    tester = OfflineTestGeneration(
        sut=as_SystemUnderTest(f1),
        limit=TestCount(20),
        generator=RandomGenerator())
    results = run(tester)


def test_offline_test_generation2():
    tester = OfflineTestGeneration(
        generator=RandomGenerator(models=LHS({"samples": 20})),
        sut=as_SystemUnderTest(f1),
        limit=TestCount(20))
    results = run(tester)


def test_offline_test_generation3():
    generate_tests_offline(f1, limit=20, generator="Uniform")
    generate_tests_offline(f1, limit=20, generator="LHS")
    generate_tests_offline(f1, limit=WallTime(2), generator="Halton")


def test_offline_test_generation4():
    # first train a wogan generator online
    critical_tests, all_tests, tester = generate_critical_tests(f1, "result>0", limit=WallTime(4), generator="WOGAN")
    # then use trained wogan offline
    trained_wogan = tester.exploit_generator
    generate_tests_offline(f1, limit=20, generator=trained_wogan)
