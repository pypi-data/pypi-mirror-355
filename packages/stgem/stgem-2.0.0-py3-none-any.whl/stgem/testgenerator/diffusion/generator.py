import importlib
import time

import numpy as np

from stgem import logging, SearchSpace
from stgem.testgenerator import TestGenerator
from stgem.testgenerator.diffusion.model import Diffusion_Model
from stgem.testgenerator.model import Model
from stgem.testgenerator.sampler import ModelSampler
from stgem.testsuitegenerator.parameters import get_DIFFUSION_parameters as get_parameters

class Diffusion(TestGenerator):
    """A test generator based on training and sampling a diffusion model."""

    # The default parameters will be fetched via the function get_parameters.
    default_parameters = {}

    def __init__(self,
                 models: Model = None,
                 parameters: dict = None,
                 model_parameters: dict = None):
        if parameters is None:
            parameters = get_parameters("default")["generator_parameters"]
        super().__init__(models, parameters)
        if len(self.models) == 0:
            self.models = [Diffusion_Model(parameters=model_parameters)]

        self.model_sampler = None
        self.first_training = True

    def setup(self, search_space: SearchSpace = None, input_dimension: int = 0):
        if self.setup_done: return
        super().setup(search_space=search_space, input_dimension=input_dimension)

        # Load the training data sampler.
        module = importlib.import_module("stgem.testgenerator.wogan.sampler")
        sampler_class = getattr(module, self.training_data_sampler)
        self.training_data_sampler = sampler_class(parameters=self.training_data_sampler_parameters)
        self.training_data_sampler.setup(search_space=self.search_space)

        # Set up the samplers.
        module = importlib.import_module("stgem.testgenerator.sampler")
        model_sampler_class = getattr(module, self.parameters["model_sampler"])
        self.model_sampler = model_sampler_class(self.model_sampler_parameters)
        self.model_sampler.setup(search_space=self.search_space)

        self.direct_sampler = ModelSampler()
        self.direct_sampler.setup(search_space=self.search_space)

        self.model_trained = 0  # Keeps track on how many tests were generated when a model was previously trained.

    def train(self, I: np.array, O: np.array, remaining: float = 1.0, **kwargs) -> dict:
        performance = {}
        analyzer_losses = []
        backward_process_losses = []
        performance["analyzer_losses"] = analyzer_losses
        performance["backward_process_losses"] = backward_process_losses

        # Currently we support only a single diffusion model.
        model = self.get_models()[0]

        time_start = time.perf_counter()

        # Latest tests (indices) recorded to the search space since previous training.
        latest = kwargs["latest"] if "latest" in kwargs else []

        # Train the analyzer.
        # ---------------------------------------------------------------------
        logging.debug("Training the analyzer...")
        losses = model.train_analyzer_with_batch(I, O.flatten())
        analyzer_losses.append(losses)

        # Train the diffusion model.
        # ---------------------------------------------------------------------
        logging.debug("Training the diffusion model...")
        epochs = model.train_settings["epochs"]
        train_settings = model.train_settings
        for _ in range(epochs):
            # Sample a batch of training data.
            batch_size = min(train_settings["batch_size"], len(O))
            sample_idx = self.training_data_sampler(batch_size, O.flatten(), remaining, new=latest)
            train_X = np.array([I[i] for i in sample_idx])

            # Train the model.
            losses = model.train_ddpm_with_batch(train_X)
            backward_process_losses.append(losses)

        performance["training_time"] = time.perf_counter() - time_start
        self.first_training = False

        return performance

    def generate_next_normalized(self, remaining: float = 1.0):
        # Currently we support only a single model.
        model = self.get_models()[0]

        # Typically, we sample the diffusion model with rejection sampling,
        # but with a given probability we use direct sampling.
        if self.search_space.get_rng("numpy").random() >= self.analyzer_sampling_split:
            sampler = self.model_sampler
        else:
            sampler = self.direct_sampler

        try:
            candidate_test, estimated_objective, performance = sampler(model, remaining=remaining)
        except:
            raise

        return candidate_test.reshape(-1), estimated_objective, performance
