import importlib

import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor

from stgem import config, filter_arguments, logging, SearchSpace
from stgem.testgenerator.model import Model
from stgem.testsuitegenerator.parameters import get_DIFFUSION_parameters as get_parameters

class Diffusion_Model(Model):
    """Implements the diffusion model consisting of an analyzer and a DDPM
    model."""

    # The default parameters will be fetched via the function get_parameters.
    default_parameters = {}

    def __init__(self, parameters: dict = None):
        if parameters is None:
            parameters = get_parameters("default")["model_parameters"]
        super().__init__(parameters)
        self.modelA = None
        self.modelDDPM = None

    def setup(self, search_space: SearchSpace):
        super().setup(search_space)

        # Infer input and output dimensions for ML models.
        self.parameters["analyzer_parameters"]["input_shape"] = self.search_space.input_dimension
        self.parameters["backward_model_parameters"]["input_size"] = self.search_space.input_dimension

        # Load the specified analyzer unless it is already loaded.
        if self.analyzer != "RandomForest":
            raise ValueError("Currently only random forest regression is supported as a diffusion analyzer.")
        if self.modelA is None:
            self.modelA = RandomForestRegressor(random_state=self.search_space.get_rng("numpy"))

        # Load and setup the specified DDPM model unless it is already loaded.
        module = importlib.import_module("stgem.testgenerator.diffusion.ddpm")
        ddpm_class = getattr(module, self.ddpm)
        backward_model_class = getattr(module, self.backward_model)
        if self.modelDDPM is None:
            rng = self.search_space.rng
            backward_model = backward_model_class(device=config.device, rng=rng, **self.backward_model_parameters).to(
                config.device)
            self.modelDDPM = ddpm_class(backward_model=backward_model, device=config.device, rng=rng,
                                        **self.ddpm_parameters).to(config.device)
        else:
            self.modelDDPM = self.modelDDPM.to(config.device)

        # DDPM loss.
        self.ddpm_loss = nn.MSELoss()

        # Load the specified DDPM optimizer.
        module = importlib.import_module("torch.optim")
        parameters = self.ddpm_optimizer_parameters
        ddpm_optimizer_class = getattr(module, parameters["optimizer"])
        self.optimizerDDPM = ddpm_optimizer_class(self.modelDDPM.parameters(),
                                                  **filter_arguments(parameters, ddpm_optimizer_class))

    def _generate_test(self, N=1, device=None):
        if self.modelDDPM is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        if N <= 0:
            raise ValueError("The number of tests should be positive.")

        training_DDPM = self.modelDDPM.training
        self.modelDDPM.train(False)

        rng = self.search_space.rng.get_rng("torch")

        with torch.no_grad():
            # Generate noise to be denoised.
            x = torch.randn(N, self.backward_model_parameters["input_size"], generator=rng, device=device)
            # Denoise.
            for t in range(self.modelDDPM.N_steps, 1, -1):
                x = self.modelDDPM.denoise(x, t)
            # Clamp the test to the correct range.
            torch.clamp(x, -1, 1, out=x)

        self.modelDDPM.train(training_DDPM)
        return x.cpu().detach().numpy().reshape(N, -1)

    def generate_test(self, N=1):
        try:
            return self._generate_test(N, config.device)
        except:
            raise

    def predict_objective(self, test, device=None):
        if self.modelA is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        return self.modelA.predict(test)

    def train_analyzer_with_batch(self, dataX, dataY):
        # Reset the model every time 
        self.modelA = RandomForestRegressor(random_state=self.search_space.get_rng("numpy"))
        self.modelA.fit(dataX, dataY)

        return 0

    def train_ddpm_with_batch(self, data_X):
        # Save the training mode for later restoring.
        training = self.modelDDPM.training
        self.modelDDPM.train(True)

        rng = self.search_space.rng.get_rng("torch")

        # Training data.
        x0 = torch.from_numpy(data_X).float().to(config.device)
        n = len(x0)
        # True noise to each image.
        noise = torch.randn(x0.size(), generator=rng, device=config.device)
        # Timesteps to train on.
        t = torch.randint(0, self.modelDDPM.N_steps, (n,), generator=rng, device=config.device)
        # Add noise to x0 at the given timesteps.
        noisy_images = self.modelDDPM(x0, t, noise=noise)
        # Get the model estimated noise.
        estimated_noise = self.modelDDPM.backward(noisy_images, t)
        # Compute the loss.
        loss = self.ddpm_loss(noise, estimated_noise)
        # Backpropagate error.
        self.optimizerDDPM.zero_grad()
        loss.backward()
        self.optimizerDDPM.step()

        logging.debug("DDPM batch loss: {}".format(loss.item()))

        self.modelDDPM.train(training)

        return loss.item()
