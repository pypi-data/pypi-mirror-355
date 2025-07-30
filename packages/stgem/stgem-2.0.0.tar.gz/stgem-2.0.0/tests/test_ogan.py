from stgem.limit import ExecutionCount
from stgem.system.mo3d import MO3D
from stgem.task import falsify
from stgem.testsuitegenerator.ogan.ogan import OGANAlgorithm


def test_falsify_OGAN():
    # Test falsify with an OGAN generator.
    falsify(MO3D(), "y1 > 10", 10, exploit_generator="OGAN")


def test_OGAN():
    # Test falsify with the OGAN test heuristic.
    falsify(
        sut=MO3D(),
        formula="y1 > 10",
        limit=ExecutionCount(10),
        test_suite_generator=OGANAlgorithm()
    )
