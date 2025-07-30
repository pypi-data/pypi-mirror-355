import copy
import traceback
import unittest

import numpy as np
import pandas as pd

import stgem.monitor.pystl.robustness as STL
from stgem.features import FeatureVector, Real, Signal
from stgem.monitor.pystl.parser import parse
from stgem.monitor.stl import STLRobustness


class TestSTL(unittest.TestCase):

    def test_moving_window(self):
        # Test the moving window from pystl.
        # ---------------------------------------------------------------------
        sequence = [2, 1, 2, 3, 4, 5, 6, 7, 0, 9]
        window = STL.Window(sequence)
        assert window.update(10, 15) == -1
        assert window.update(-5, -2) == -1
        assert window.update(9, 15) == 9
        assert window.update(8, 14) == 8
        assert window.update(7, 10) == 8
        assert window.update(7, 8) == 7
        assert window.update(4, 6) == 4
        assert window.update(0, 5) == 1
        assert window.update(0, 4) == 1
        assert window.update(2, 4) == 2
        assert window.update(1, 6) == 1
        assert window.update(3, 8) == 3
        assert window.update(1, 9) == 8
        assert window.update(2, 8) == 2

    def test_dict(self):
        # Test robustness computation with dictionaries.
        # ---------------------------------------------------------------------
        # Conversion from scalar, no ranges.
        d = {
            "x1": 0,
            "x2": 10,
            "x3": 20
        }
        formula = "x1 > -10 and x2 < 15"
        monitor = STLRobustness(formula)
        assert monitor(d) == 5.0
        try:
            monitor(d, scale=True) == 5.0
        except Exception as E:
            if E.args[0] != "Scaling of robustness values requested but no scale available.":
                traceback.print_exc()
                raise

        # ---------------------------------------------------------------------
        # No conversion, no ranges.
        d = {
            "s1": [[0.0, 0.5, 1.0, 1.5, 2.0], [4.0, 6.0, 2.0, 8.0, -1.0]],
            "s2": [[0.0, 0.5, 1.0, 1.5, 2.0], [3.0, 6.0, 1.0, 0.5, 3.0]]
        }
        formula = "always[0,1] (s1 >= 0 and s2 >= 0)"
        monitor = STLRobustness(formula)
        assert monitor(d) == 1.0

        # ---------------------------------------------------------------------
        # No conversion, scaled.
        d = {
            "s1": [[0.0, 0.5, 1.0, 1.5, 2.0], [4.0, 6.0, 2.0, 8.0, -1.0], [-1, 8]],
            "s2": [[0.0, 0.5, 1.0, 1.5, 2.0], [3.0, 6.0, 1.0, 0.5, 3.0], [0, 8]]
        }
        formula = "always[0,1] (s1 >= 0 and s2 >= 0)"
        monitor = STLRobustness(formula)
        assert monitor(d, scale=False) == 1.0
        assert monitor(d, scale=True) == 0.125

        # ---------------------------------------------------------------------
        # One monitor, changing ranges.
        d1 = {
            "s1": [[0.0, 0.5, 1.0, 1.5, 2.0], [4.0, 6.0, 2.0, 8.0, -1.0], [-1, 8]],
            "s2": [[0.0, 0.5, 1.0, 1.5, 2.0], [3.0, 6.0, 1.0, 0.5, 3.0], [0, 8]]
        }
        d2 = copy.deepcopy(d1)
        d2["s2"][2] = [0, 16]
        formula = "always[0,1] (s1 >= 0 and s2 >= 0)"
        monitor = STLRobustness(formula)
        assert monitor(d1, scale=False) == 1.0
        assert monitor(d1, scale=True) == 0.125
        assert monitor(d2, scale=False) == 1.0
        assert monitor(d2, scale=True) == 0.0625

    def test_feature_vectors(self):
        # Test robustness computation with feature vectors.
        # ---------------------------------------------------------------------
        # No signals.
        f = FeatureVector(features=[
            Real("x1", min_value=0, max_value=10),
            Real("x2", min_value=0, max_value=20),
            Real("x3", min_value=0, max_value=30)
        ]).set([5, 3, 10])

        formula = "x1 > -10 and x2 < 15"
        monitor = STLRobustness(formula)
        assert monitor(f, scale=False) == 12
        assert monitor(f, scale=True) == 0.8
        monitor = STLRobustness("not ({})".format(formula))
        assert monitor(f, scale=False) == -12
        assert monitor(f, scale=True) == 0

        # ---------------------------------------------------------------------
        # Signals.
        f = FeatureVector(features=[
            Signal(name="x1", min_value=0, max_value=10),
            Signal(name="x2", min_value=0, max_value=10),
        ]).set([[0, 1, 2, 3, 4, 5], [5, 4, 3, 2, 1, 0]])

        formula = "always[0,2] ( (x1 <= 4) and (x2 > 3) )"
        monitor = STLRobustness(formula)
        assert monitor(f, scale=False) == 0.0
        assert monitor(f, scale=True) == 0.0

    def test_stl(self):
        # Test the STL implementation with more complicated precomputed data.
        # ---------------------------------------------------------------------
        data = pd.read_csv("data/stl_at.csv")
        time = data["time"].tolist()
        speed = data["SPEED"].tolist()
        rpm = data["RPM"].tolist()
        s3 = 10000 * np.ones_like(speed)

        d = {
            "SPEED": [time, speed],
            "RPM": [time, rpm],
            "VERUM": [time, s3]
        }

        # Error tolerance.
        eps = 1e-5

        formula = "(always[0,30] RPM <= 3000) -> (always[0,4] SPEED <= 35)"
        correct_robustness = -4.5100706388202525
        monitor = STLRobustness(formula, default_sampling_period=0.01)
        assert abs(monitor(d) - correct_robustness) < eps
        
        formula = "(always[0,30] RPM <= 3000) -> (always[0,8] SPEED < 50)"
        correct_robustness = 4.936960098864567
        monitor = STLRobustness(formula, default_sampling_period=0.01)
        assert abs(monitor(d) - correct_robustness) < eps

        formula = "(always[0,30] RPM <= 3000) -> (always[0,20] SPEED < 65)"
        correct_robustness = 19.936960098864567
        monitor = STLRobustness(formula, default_sampling_period=0.01)
        assert abs(monitor(d) - correct_robustness) < eps

        # ---------------------------------------------------------------------
        # Test until operator.
        formula = "SPEED < 2.10 until[0.1,0.2] RPM > 2000"
        correct_robustness = 0.0033535970602489584
        monitor = STLRobustness(formula, default_sampling_period=0.01)
        assert abs(monitor(d) - correct_robustness) < eps

        formula = "(not (VERUM until[0,30] RPM > 3000)) -> (not (VERUM until[0,4] SPEED > 35))"
        correct_robustness = -4.5100706388202525
        monitor = STLRobustness(formula, default_sampling_period=0.01)
        assert abs(monitor(d) - correct_robustness) < eps

        # ---------------------------------------------------------------------
        # Test time horizon.
        t = [0.5 * i for i in range(21)]
        #     0  0.5 1.0 1.5 2.0 2.5 3.0 3.5 4.0 4.5 5.0 5.5 6.0 6.5 7.0 7.5 8.0 8.5 9.0 9.5 10
        s1 = [0, 0, 0, 6, 0, 0, 6, 0, 0, 6, 0, 0, 5, 0, 0, 0, 0, 0, 6, 0, 0]
        s2 = [0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 4, 0, 4, 4, 4, 0, 0, 0, 4, 0, 0]
        d = {
            "s1": [t, s1],
            "s2": [t, s2]
        }

        formula = "always[0,10] ( (s1 >= 5) -> (eventually[0,1] s2 <= 3) )"
        correct_robustness = 0
        monitor = STLRobustness(formula)

        # Check with strict horizon check.
        try:
            monitor(d)
        except Exception as E:
            if not E.args[0].startswith("The horizon"):
                traceback.print_exc()
                raise
        # Check without strict horizon check.
        assert monitor.horizon == 11
        assert abs(monitor(d, strict_horizon_check=False) - correct_robustness) < eps

        # ---------------------------------------------------------------------
        # Test timestamp adjustment.
        t1 = [0, 1, 2, 3]
        s1 = [1, 3, 4, 1]
        t2 = [0, 0.5, 1, 2, 2.5, 3]
        s2 = [2, 2, 2, 2, 2, 2]
        d = {
            "s1": [t1, s1],
            "s2": [t2, s2]
        }

        formula = "always[0,3] s1 >= s2"
        correct_robustness = -1.0
        monitor = STLRobustness(formula)

        assert monitor.horizon == 3
        assert abs(monitor(d) - correct_robustness) < eps

        # ---------------------------------------------------------------------
        # Test signal ranges.
        t = [0, 1, 2]
        d = {
            "s1": [0.1, 0.1, 0.3],
            "s2": [0.2, 0.1, 0.0]
        }
        signal_ranges = {
            "s1": [0.0, 0.2],
            "s2": [-0.05, 0.3]
        }
        formula = parse("s1 == s2")
        trajectories = STL.Traces(timestamps=t, signals=d)
        _, _range, _ = formula.eval(trajectories, signal_ranges)
        assert _range == [-0.25, 1]

        t = [0, 1, 2, 3, 4, 5]
        d = {
            "s1": [100, 150, 70, 30, 190, 110],
            "s2": [4500, 100, 0, 2300, -100, -5]
        }
        signal_ranges = {
            "s1": [0, 200],
            "s2": [-200, 4500]
        }

        formula = parse("3*s1 <= s2")
        trajectories = STL.Traces(timestamps=t, signals=d)
        _, _range, _ = formula.eval(trajectories, signal_ranges)
        assert _range == [-800, 4500]

        # ---------------------------------------------------------------------
        # Test signal effective ranges.

        formula = parse("s1 and s2")
        _, _, effective_range = formula.eval(trajectories, signal_ranges)
        assert (effective_range[0] == [0, 200]).all()
        assert (effective_range[1] == [-200, 4500]).all()

        formula = parse("3*s1 or (3*s1 <= s2)")
        _, _, effective_range = formula.eval(trajectories, signal_ranges)
        assert (effective_range[0] == [-800, 4500]).all()
        assert (effective_range[1] == [0, 600]).all()

        formula = parse("always[3,4] (s1 and s2)")
        _, _, effective_range = formula.eval(trajectories, signal_ranges)
        assert (effective_range[0] == [-200, 4500]).all()

        formula = parse("s1 until[0,4] (not s2)")
        _, _, effective_range = formula.eval(trajectories, signal_ranges)
        assert (effective_range[0] == [0, 200]).all()

        formula = parse("s1 until[0,2] (not s2)")
        _, _, effective_range = formula.eval(trajectories, signal_ranges)
        assert (effective_range[0] == [-4500, 200]).all()


if __name__ == "__main__":
    TestSTL().test_stl()
