import numpy as np

from stgem.features import Real
from stgem.limit import *
from stgem.task import generate_critical_tests


def f1(
        x1: Real(min_value=0, max_value=10 * 2 * math.pi),
        x2: Real(min_value=0, max_value=10 * 2 * math.pi),
        x3: Real(min_value=0, max_value=10 * 2 * math.pi)) -> Real("result", min_value=-10, max_value=300):
    result = 300 - 101 * (np.sin(x1) + np.sin(x2 * 2) + np.sin(x3 * 3))
    return result


def test_generare_critical_tests():
    generate_critical_tests(f1,
                            "result>0",
                            generator="WOGAN",
                            limit=WallTime(5),
                            robustness_threshold=0.2
    )
