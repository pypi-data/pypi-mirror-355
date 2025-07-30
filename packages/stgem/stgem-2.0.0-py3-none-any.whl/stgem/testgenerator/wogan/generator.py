import importlib
import time

import numpy as np

from stgem import logging, SearchSpace
from stgem.testgenerator import TestGenerator
from stgem.testgenerator.model import Model
from stgem.testgenerator.wogan.model import WOGAN_Model
from stgem.testsuitegenerator.parameters import get_WOGAN_parameters as get_parameters

class WOGAN(TestGenerator):
    """A test generator based on training and sampling a Wasserstein generative
    adversarial network."""

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
            self.models = [WOGAN_Model(parameters=model_parameters)]

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

        # Set up the model sampler.
        module = importlib.import_module("stgem.testgenerator.sampler")
        model_sampler_class = getattr(module, self.parameters["model_sampler"])
        self.model_sampler = model_sampler_class(self.model_sampler_parameters)
        self.model_sampler.setup(search_space=self.search_space)

        self.model_trained = 0  # Keeps track on how many tests were generated when a model was previously trained.
        
    def to_device(self, device):
        for model in self.models:
            model.to_device(device)

    def train(self, I: np.array, O: np.array, remaining: float = 1.0, **kwargs) -> dict:
        performance = {}
        analyzer_losses = []
        critic_losses = []
        generator_losses = []
        gradient_penalties = []
        performance["analyzer_loss"] = analyzer_losses
        performance["critic_loss"] = critic_losses
        performance["generator_loss"] = generator_losses
        performance["gradient_penalty"] = gradient_penalties

        # Currently we support only a single WOGAN model.
        model = self.get_models()[0]

        time_start = time.perf_counter()

        # Latest tests (indices) recorded to the search space since previous training.
        latest = kwargs["latest"] if "latest" in kwargs else []

        BS = min(self.wgan_batch_size, len(O))

        if len(O) < 2:
            raise Exception("WOGAN needs at least two training data samples to train.")

        # Train the analyzer and the WGAN.
        # -----------------------------------------------------------------
        epochs = model.train_settings_init["epochs"] if self.first_training else model.train_settings["epochs"]
        train_settings = model.train_settings_init if self.first_training else model.train_settings
        for _ in range(epochs):
            # Train the analyzer.
            logging.debug("Training analyzer...")
            losses = model.train_analyzer_with_batch(I,
                                                     O,
                                                     train_settings=train_settings
                                                     )
            analyzer_losses.append(losses)

            # Train the WGAN.
            logging.debug("Training the WGAN model...")
            sample_idx = self.training_data_sampler(BS, O.flatten(), remaining, new=latest)
            train_X = np.array([I[i] for i in sample_idx])
            C_losses, G_losses, gps = model.train_with_batch(train_X,
                                                             train_settings=train_settings
                                                             )
            critic_losses.append(C_losses)
            generator_losses.append(G_losses)
            gradient_penalties.append(gps)

        performance["training_time"] = time.perf_counter() - time_start
        self.first_training = False

        return performance

    def generate_next_normalized(self, remaining=1.0):
        # Currently we support only a single model.
        model = self.get_models()[0]

        try:
            candidate_test, estimated_objective, performance = self.model_sampler(model, remaining=remaining)
        except:
            raise

        return candidate_test.reshape(-1), estimated_objective, performance
