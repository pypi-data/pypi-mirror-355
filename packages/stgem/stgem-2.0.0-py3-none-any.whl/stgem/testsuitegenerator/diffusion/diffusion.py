from stgem.limit import Limit
from stgem.monitor import Monitor
from stgem.sut import SystemUnderTest
from stgem.testgenerator.diffusion.generator import Diffusion
from stgem.testsuitegenerator.wogan.wogan import WOGAN_TestSuiteGenerator
from stgem.testsuitegenerator.parameters import get_DIFFUSION_parameters as get_parameters

class Diffusion_TestSuiteGenerator(WOGAN_TestSuiteGenerator):
    """Implements the Diffusion test suite generator."""

    default_parameters = {}

    def __init__(self,
                 *,
                 sut: SystemUnderTest | None = None,
                 goal: Monitor | None = None,
                 limit: Limit | None = None,
                 parameters: dict = None):
        if parameters is None:
            has_signal_input = False
            if sut is not None:
                for feature in sut.new_ifv().flatten_to_list():
                    if isinstance(feature, PiecewiseConstantSignal):
                        has_signal_input = True
                        break
            
            network_type = "convolution" if has_signal_input else "dense"
            parameters = get_parameters("default", network_type=network_type)
        super().__init__(sut=sut, goal=goal, limit=limit, parameters=parameters)
        self.generator_class = Diffusion


DiffusionAlgorithm = Diffusion_TestSuiteGenerator
