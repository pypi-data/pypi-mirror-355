import math

from stgem.features import *
from stgem.limit import WallTime, ExecutionCount
from stgem.task import falsify


# Define some arbitrary but complicated function.
def f1(
        x1: Real(min_value=0, max_value=2 * math.pi),
        x2: Real(min_value=0, max_value=2 * math.pi),
        x3: Real(min_value=0, max_value=2 * math.pi)) \
        -> Real("result", min_value=-10, max_value=300):
    result = 300 - 101 * (math.sin(x1) + math.sin(x2 * 2) + math.sin(x3 * 3))
    return result


def test_falsify():
    # Falsify with a time budget for a maximum of 10 seconds.
    falsify(f1, "result>0", limit=WallTime(10) & ExecutionCount(1000))


def test_falsifyUsingRandom():
    # Falsify using a uniform random generator.
    falsify(f1, "result>0", 100, exploit_generator="Random")


def test_s5():
    def f2(x: PiecewiseConstantSignal(piece_durations=[6] * 5, min_value=0, max_value=10)) \
            -> Signal(name="y", min_value=0, max_value=20):
        return [np.array(x) * 2]

    falsify(f2, "always[0,4] y<19", limit=50)


def test_s6():
    def f1(x: PiecewiseConstantSignal(piece_durations=[6] * 5, min_value=0, max_value=10)) \
            -> FeatureVector(features=[
                Signal(name="y", min_value=0, max_value=20),
                Signal(name="z", min_value=0, max_value=30)
            ]):
        return [np.array(x) * 2, np.array(x * 3)]

    falsify(f1, "always[0,4] y<19 and z < 25", limit=50)
