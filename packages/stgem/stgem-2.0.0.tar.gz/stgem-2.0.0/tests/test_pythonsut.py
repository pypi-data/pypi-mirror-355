import traceback

from stgem.features import *
from stgem.sut import as_SystemUnderTest


def test_annotation_failure():
    # Test some failures in annotation.

    def f(x, y) -> Signal(name="o", min_value=0, max_value=20):
        return np.array(x) * 2

    try:
        sut = as_SystemUnderTest(f)
    except Exception as E:
        if E.args[0] != "No annotation for all input values.":
            traceback.print_exc()
            raise

    def f(x: PiecewiseConstantSignal(piece_durations=[6] * 5, min_value=0, max_value=10)):
        return np.array(x) * 2

    try:
        sut = as_SystemUnderTest(f)
    except Exception as E:
        if E.args[0] != "No annotation specified for the return value.":
            traceback.print_exc()
            raise


def test_1():
    # Test that a wrapped Python function does what is expected.

    def f(x: PiecewiseConstantSignal(piece_durations=[6] * 5, min_value=0, max_value=10)) \
            -> FeatureVector(features=[
                RealVector(name="y", dimension=5, min_value=0, max_value=20),
                Real(name="z", min_value=0, max_value=5 * 20)
            ]):
        return np.array(x) * 2, np.sum(x)

    sut = as_SystemUnderTest(f)

    ifv = sut.new_ifv()
    ifv.set_packed([-1, -1, 0, 0, 1])

    ofv, _ = sut.execute_test_fv(ifv)
    assert np.all(ofv["y"] == np.array([0.0, 0.0, 5.0, 5.0, 10.0]) * 2)
    assert ofv["z"] == np.sum(np.array([0.0, 0.0, 5.0, 5.0, 10.0]))


def test_2():
    # Another test that tests the case when the output is a single real.

    def f(x: Real(min_value=0, max_value=10)) -> FeatureVector(features=[Real(name="o", min_value=0, max_value=20)]):
        return x * 2

    sut = as_SystemUnderTest(f)

    ifv = sut.new_ifv()
    ifv.set_packed([0.0])

    ofv, _ = sut.execute_test_fv(ifv)
    assert ofv["o"] == 10.0
