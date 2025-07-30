import importlib
import time
from typing import List

from stgem import logging, SearchSpace
from stgem.testgenerator import TestGenerator
from stgem.testgenerator.ogan.model import Model, OGAN_Model
from stgem.testsuitegenerator.parameters import get_OGAN_parameters as get_parameters

class OGAN(TestGenerator):
    """Implements the test generator for the online generative adversarial
    network (OGAN) algorithm."""

    # The default parameters will be fetched via the function get_parameters.
    default_parameters = {}

    def __init__(self,
                 models: List[Model] | Model = None,
                 parameters: dict = None,
                 model_parameters: dict = None):
        if parameters is None:
            parameters = get_parameters("default")["generator_parameters"]
        super().__init__(models, parameters)
        if len(self.models) > 1:
            raise NotImplementedError("The OGAN generator currently supports only one model.")
        if len(self.models) == 0:
            self.models = [OGAN_Model(parameters=model_parameters)]

        self.model_sampler = None

    def setup(self, search_space: SearchSpace = None, input_dimension: int = 0):
        if self.setup_done: return
        super().setup(search_space=search_space, input_dimension=input_dimension)

        # Set up the model sampler.
        module = importlib.import_module("stgem.testgenerator.sampler")
        model_sampler_class = getattr(module, self.parameters["model_sampler"])
        self.model_sampler = model_sampler_class(self.model_sampler_parameters)
        self.model_sampler.setup(search_space=self.search_space)

    def train(self, I, O, remaining=1.0):
        performance = {}
        discriminator_losses = []
        generator_losses = []
        performance["discriminator_losses"] = discriminator_losses
        performance["generator_losses"] = generator_losses

        # Currently we support only a single OGAN model.
        model = self.get_models()[0]

        time_start = time.perf_counter()

        logging.debug("Training the OGAN model...")
        train_settings = model.train_settings
        epochs = train_settings["epochs"]
        for _ in range(epochs):
            D_losses, G_losses = model.train_with_batch(I,
                                                        O,
                                                        train_settings=train_settings
                                                        )
            discriminator_losses.append(D_losses)
            generator_losses.append(G_losses)

        performance["training_time"] = time.perf_counter() - time_start

        return performance

    def generate_next_normalized(self, remaining=1.0):
        # Currently we support only a single OGAN model.
        model = self.get_models()[0]

        try:
            candidate_test, estimated_objective, performance = self.model_sampler(model, remaining=remaining)
        except:
            raise

        return candidate_test.reshape(-1), estimated_objective, performance
