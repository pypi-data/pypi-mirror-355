import math, time
from typing import List

from stgem.features import FeatureVector, Real
from stgem.sut import SystemUnderTest

class MO3D(SystemUnderTest):
    """Implements a certain mathematical function as a SUT.

    The function is from
    L. Mathesen, G. Pedrielli, and G. Fainekos. Efficient optimization-based
    falsification of cyber-physical systems with multiple conjunctive
    requirements. In 2021 IEEE 17th International Conference on Automation
    Science and Engineering (CASE), pages 732-737, 2021.

    We fix the input domain of the function to be [-15, 15]^3."""
    
    def execute_test(self, input) -> List[float]:
        time_start = time.perf_counter()

        x1 = input[0]
        x2 = input[1]
        x3 = input[2]

        h1 = 305-100*(math.sin(x1/3)+math.sin(x2/3)+math.sin(x3/3))
        h2 = 230-75*(math.cos(x1/2.5+15)+math.cos(x2/2.5+15)+math.cos(x3/2.5+15))
        h3 = (x1-7)**2+(x2-7)**2+(x3-7)**2 - (math.cos((x1-7)/2.75) + math.cos((x2-7)/2.75) + math.cos((x3-7)/2.75))

        return [h1, h2, h3], {"execution_time": time.perf_counter() - time_start}

    def new_ifv(self) -> FeatureVector:
        return FeatureVector(features=[
            Real("x1", -15, 15),
            Real("x2", -15, 15),
            Real("x3", -15, 15)
        ])

    def new_ofv(self) -> FeatureVector:
        return FeatureVector(features=[
            Real("y1", 0, 350, clip=True),
            Real("y2", 0, 350, clip=True),
            Real("y3", 0, 350, clip=True)
        ])

    def from_ifv_to_testinput(self, input_fv):
        return [input_fv.x1, input_fv.x2, input_fv.x3]

    def from_testouput_to_ofv(self, output):
        output_fv = self.new_ofv()
        output_fv.y1 = output[0]
        output_fv.y2 = output[1]
        output_fv.y3 = output[2]
        return output_fv
