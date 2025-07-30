from typing import List

import numpy as np

from stgem import merge_dictionary, SearchSpace
from stgem.features import FeatureVector
from stgem.testgenerator.model import Model


class TestGenerator:
    """Base class for all test case generators."""

    default_parameters = {}

    def __init__(self,
                 models: List[Model] | Model = None,
                 parameters: dict = None):
        if models is None:
            self.models = []
        else:
            try:
                _ = len(models)
                self.models = models
            except TypeError:
                self.models = [models]

        if parameters is None:
            parameters = {}

        # Merge default_parameters and parameters.
        self.parameters = merge_dictionary(parameters, self.default_parameters)

        self.search_space = None
        self.setup_done = False

    def __str__(self):
        return self.__class__.__name__ + " Generator"

    def setup(self, search_space: SearchSpace = None, input_dimension: int = 0):
        """Set up a generator. Consequent calls to this function do nothing.

        Args:
            search_space (SearchSpace): The search space for the generator. Optional if input_dimension defined. Defaults to None.
            input_dimension (int): Specifies the input dimension when a search space is not defined. Defaults to 0.
        """

        if self.setup_done: return

        if search_space is None:
            if input_dimension == 0:
                raise ValueError("If no search space is defined, input dimension must be given.")
            search_space = SearchSpace(input_dimension=input_dimension)

        self.search_space = search_space

        # Set up the models.
        for model in self.models:
            model.setup(self.search_space)

        self.setup_done = True

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__.get(name)
        elif "parameters" in self.__dict__ and name in self.parameters:
            return self.parameters.get(name)
        else:
            raise AttributeError(name)

    def get_models(self):
        return self.models

    def train(self, I: np.array, O: np.array, remaining: float = 1.0, **kwargs):
        raise NotImplementedError

    def train_on_search_space(self, remaining: float = 1.0):
        return self.train(self.search_space.known_inputs(), self.search_space.known_outputs(), remaining)

    def generate_next_normalized(self, remaining: float = 1.0) -> tuple[np.array, float]:
        raise NotImplementedError

    def generate_next(self, remaining: float = 1.0) -> tuple[FeatureVector, float]:
        assert self.search_space.input_vector
        nv, estimate, performance = self.generate_next_normalized(remaining=remaining)

        v = self.search_space.new_ifv()
        v.set_packed(nv)

        return v, estimate, performance
