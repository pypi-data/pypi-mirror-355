import math

import numpy as np
from matplotlib import pyplot as plt

from stgem.features import Real, FeatureVector
from stgem.limit import ExecutionCount, TestCount
from stgem.monitor.stl import STLRobustness
from stgem.search import SearchSpace
from stgem.sut import as_SystemUnderTest
from stgem.task import falsify
from stgem.testgenerator.ogan import OGANGenerator
from stgem.testgenerator.random import RandomGenerator
from stgem.testsuitegenerator import TestSuiteGenerator
from stgem.testsuitegenerator import run, ExploreExploitOneGoal


def test_demo1():
    def f1(x1: Real(min_value=0, max_value=2 * math.pi),
           x2: Real(min_value=0, max_value=2 * math.pi),
           x3: Real(min_value=0, max_value=2 * math.pi)
           ) -> Real("result", min_value=-3, max_value=300):
        return 300 - 101 * (math.sin(x1) + math.sin(x2 * 2) + math.sin(x3 * 3))

    falsify(sut=f1, formula="result>0", limit=TestCount(300))


def test_ss():
    def normalize(x, minimum, maximum):
        return min(1, max(0, (x - minimum) / (maximum - minimum)))

    def f1(x1: Real(min_value=0, max_value=2 * math.pi),
           x2: Real(min_value=0, max_value=2 * math.pi),
           x3: Real(min_value=0, max_value=2 * math.pi)
           ) -> Real("result", min_value=-3, max_value=300):
        return 300 - 101 * (math.sin(x1) + math.sin(x2 * 2) + math.sin(x3 * 3))

    # part 1: feature vectors
    ifv = FeatureVector(features=[
        Real(name="x1", min_value=0, max_value=2 * math.pi),
        Real(name="x2", min_value=0, max_value=2 * math.pi),
        Real(name="x3", min_value=0, max_value=2 * math.pi)])

    ofv = FeatureVector(features=[Real("result", min_value=-3, max_value=300)])

    # part 2: monitor
    monitor = STLRobustness("result>0", scale=True)

    # part 3: Search Space
    ss = SearchSpace(input_vector=ifv)
    for i in np.linspace(0, 1, 11):
        ifv.x1, ifv.x2, ifv.x3 = i, i * 2, i * 3
        ofv.result = f1(ifv.x1, ifv.x2, ifv.x3)
        robustness = monitor(ofv)
        ss.record_normalized(ifv.pack(), robustness)

        print(np.array([ifv.x1, ifv.x2, ifv.x2, ofv.result]))
    print(np.concatenate((ss.I, ss.O), axis=1))

    plot = True

    # part 4 generators
    ss = SearchSpace(input_vector=ifv)
    random = RandomGenerator()
    random.setup(ss)
    ogan = OGANGenerator()
    ogan.setup(ss)

    for n in range(50):
        next_normalized_input, _, _ = random.generate_next_normalized()
        ifv.unpack(next_normalized_input)
        ofv.result = f1(ifv.x1, ifv.x2, ifv.x3)
        robustness = monitor(ofv)
        ss.record_normalized(next_normalized_input, robustness)

    for n in range(50, 200):
        ogan.train_on_search_space()
        next_normalized_input, _, _ = ogan.generate_next_normalized()
        ifv.unpack(next_normalized_input)
        ofv.result = f1(ifv.x1, ifv.x2, ifv.x3)
        robustness = monitor(ofv)
        ss.record_normalized(next_normalized_input, robustness)

    for n in range(200, 250):
        next_normalized_input, _, _ = ogan.generate_next_normalized()
        ifv.unpack(next_normalized_input)
        ofv.result = f1(ifv.x1, ifv.x2, ifv.x3)
        robustness = monitor(ofv)
        ss.record_normalized(next_normalized_input, robustness)

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(range(len(ss.known_outputs())),
                   ss.known_outputs(),
                   linewidth=2.0)
        ax.vlines(x=50, ymin=0, ymax=1, colors='r')
        ax.vlines(x=200, ymin=0, ymax=1, colors='r')
        plt.title("OGAN")
        plt.show()

    # Part 5: TestSuiteGenerator

    sut = as_SystemUnderTest(f1)
    monitor = STLRobustness("result > 0", scale=True)
    tester = ExploreExploitOneGoal(
        sut=sut,
        goal=monitor,
        limit=ExecutionCount(250),
        explore_generator=RandomGenerator(),
        exploit_generator=OGANGenerator(),
        resources_for_exploration=0.2, resources_for_training=0.8
    )
    run(tester)

    # Part 6: Own TSG

    class ProbabilisticTestSuiteGenerator(TestSuiteGenerator):
        def step(self):
            if self.search_space.rng.rand() < self.min_objective + 0.05:
                generator = self.random  # random exploration
            else:
                generator = self.ogan  # OGAN generator
            # geneare next test
            generator.train_on_search_space()
            input_fv, next_estimation, _ = generator.generate_next()
            # excecute next test
            output_fv, output_features = self.sut.execute_test_fv(input_fv)
            # report the test if relevant
            objective = self.goal(input_fv | output_fv)
            if objective <= self.objective_threshold:
                self.limit.add("critical_test_count")
            # update ground truth in the search space
            self.min_objective = min(objective, self.min_objective)

