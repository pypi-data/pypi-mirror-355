import matplotlib.pyplot as plt
import numpy as np

from stgem.search import SearchSpace
from stgem.testgenerator.diffusion import Diffusion
from stgem.testgenerator.ogan import OGANGenerator
from stgem.testgenerator.random import RandomGenerator
from stgem.testgenerator.wogan import WOGAN


def test_ogan(plot=False):
    def function(x1: float, x2: float, x3: float) -> float:
        h1 = 300 - 110 * (np.sin(x1 * 2) + np.cos(x2 * 5) + np.sin(x3 * 7))
        return max(0, min(h1 / 300, 1))

    ss = SearchSpace(input_dimension=3)
    random = RandomGenerator()
    random.setup(ss)
    ogan = OGANGenerator()
    ogan.setup(ss)

    for n in range(20):
        next_input, next_estimation, _ = random.generate_next_normalized()
        actual_output = function(*next_input)
        ss.record_normalized(next_input, actual_output)

    for n in range(21, 100):
        ogan.train_on_search_space()
        next_input, next_estimation, _ = ogan.generate_next_normalized()
        actual_output = function(*next_input)
        ss.record_normalized(next_input, actual_output)

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(range(len(ss.known_outputs())),
                   ss.known_outputs(),
                   linewidth=2.0)
        ax.vlines(x=20, ymin=0, ymax=1, colors='r')
        plt.title("OGAN")
        plt.show()


def test_wogan(plot=False):
    def function(x1: float, x2: float, x3: float) -> float:
        h1 = 300 - 110 * (np.sin(x1 * 2) + np.cos(x2 * 5) + np.sin(x3 * 7))
        return max(0, min(h1 / 300, 1))

    ss = SearchSpace(input_dimension=3)
    random = RandomGenerator()
    random.setup(input_dimension=3)
    wogan = WOGAN()
    wogan.setup(input_dimension=3)

    for n in range(100):
        if n < 25:
            next_input, next_estimation, _ = random.generate_next_normalized()
        else:
            wogan.train(ss.known_inputs(), ss.known_outputs())
            next_input, next_estimation, _ = wogan.generate_next_normalized()

        actual_output = function(*next_input)
        ss.record_normalized(next_input, actual_output)

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(range(len(ss.known_outputs())),
                   ss.known_outputs(),
                   linewidth=2.0)
        ax.vlines(x=25, ymin=0, ymax=1, colors='r')
        plt.title("WOGAN")
        plt.show()


def test_diffusion(plot=False):
    def function(x1: float, x2: float, x3: float) -> float:
        h1 = 300 - 110 * (np.sin(x1 * 2) + np.cos(x2 * 5) + np.sin(x3 * 7))
        return max(0, min(h1 / 300, 1))

    ss = SearchSpace(input_dimension=3)
    random = RandomGenerator()
    random.setup(input_dimension=3)
    diffusion = Diffusion()
    diffusion.setup(input_dimension=3)

    for n in range(100):
        if n < 25:
            next_input, next_estimation, _ = random.generate_next_normalized()
        else:
            diffusion.train(ss.known_inputs(), ss.known_outputs())
            next_input, next_estimation, _ = diffusion.generate_next_normalized()

        actual_output = function(*next_input)
        ss.record_normalized(next_input, actual_output)

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(range(len(ss.known_outputs())),
                   ss.known_outputs(),
                   linewidth=2.0)
        ax.vlines(x=25, ymin=0, ymax=1, colors='r')
        plt.title("Diffusion")
        plt.show()
