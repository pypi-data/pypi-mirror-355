from stgem.limit import ExecutionCount
from stgem.system.mo3d import MO3D
from stgem.task import falsify
from stgem.testsuitegenerator.diffusion.diffusion import DiffusionAlgorithm


def test_falsify_Diffusion():
    # Test falsify with a Diffusion generator.
    falsify(MO3D(), "y1 > 10", limit=30, exploit_generator="Diffusion")


def test_Diffusion():
    # Test falsify with the diffusion test heuristic.
    falsify(
        sut=MO3D(),
        formula="y1 > 10",
        limit=ExecutionCount(30),
        test_suite_generator=DiffusionAlgorithm(),
    )
