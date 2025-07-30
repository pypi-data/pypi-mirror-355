import importlib
from typing import List

import numpy as np

from stgem import SearchSpace
from stgem.testgenerator import TestGenerator
from stgem.testgenerator.random.model import Model, Uniform


class Random(TestGenerator):
    """Generator that generates tests by sampling a model. By default, the
    sampling is uniform random search on the search space."""

    default_parameters = {
        "model_sampler": "ModelSampler"
    }

    def __init__(self,
                 models: List[Model] | Model = None,
                 parameters: dict = None):
        super().__init__(models, parameters)
        if len(self.models) == 0:
            self.models = [Uniform()]

    def setup(self, search_space: SearchSpace = None, input_dimension: int = 0):
        if self.setup_done: return
        super().setup(search_space=search_space, input_dimension=input_dimension)

        # Set up the model sampler.
        module = importlib.import_module("stgem.testgenerator.sampler")
        model_sampler_class = getattr(module, self.parameters["model_sampler"])
        model_sampler_parameters = self.model_sampler_parameters if "model_sampler_parameters" in self.parameters else {}
        self.model_sampler = model_sampler_class(model_sampler_parameters)
        self.model_sampler.setup(search_space=self.search_space)

    def train(self, I: np.array, O: np.array, remaining: float = 1.0) -> dict:
        return {"training_time": 0}

    def generate_next_normalized(self, remaining: float = 1.0) -> tuple[np.array, float, dict]:
        # Currently we support only a single model.
        model = self.get_models()[0]

        try:
            candidate_test, estimated_objective, performance = self.model_sampler(model, remaining=remaining)
        except:
            raise

        return candidate_test.reshape(-1), estimated_objective, performance
