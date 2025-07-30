import importlib

import numpy as np
import torch

from stgem import config, filter_arguments, logging, SearchSpace
from stgem.exceptions import AlgorithmException
from stgem.testgenerator.model import Model
from stgem.testsuitegenerator.parameters import get_WOGAN_parameters as get_parameters

class WOGAN_Model(Model):
    """Implements an online Wasserstein generative adversarial network (WOGAN) for test generation.

    Attributes:
        modelA (Model): An instance of an Analyzer model, predicts objective function values.
        modelG (Model): An instance of a Generator model, generates tests.
        modelC (Model): An instance of a Critic model, used to train the WGAN.
    """

    # The default parameters will be fetched via the function get_parameters.
    default_parameters = {}

    def __init__(self, parameters: dict = None):
        if parameters is None:
            parameters = get_parameters("default")["model_parameters"]
        super().__init__(parameters)
        self.modelA = None
        self.modelG = None
        self.modelC = None

    def setup(self, search_space: SearchSpace):
        super().setup(search_space)

        self.noise_dim = self.generator_mlm_parameters["noise_dim"]

        # Infer input and output dimensions for ML models.
        self.parameters["analyzer_parameters"]["analyzer_mlm_parameters"][
            "input_shape"] = self.search_space.input_dimension
        self.parameters["generator_mlm_parameters"]["output_shape"] = self.search_space.input_dimension
        self.parameters["critic_mlm_parameters"]["input_shape"] = self.search_space.input_dimension

        # Load the specified analyzer unless it is already loaded.
        module = importlib.import_module("stgem.testgenerator.wogan.analyzer")
        analyzer_class = getattr(module, self.analyzer)
        if self.modelA is None:
            self.modelA = analyzer_class(parameters=self.analyzer_parameters)
        # Setup the analyzer.
        self.modelA.setup(rng=self.search_space.rng)

        # Load the specified generator and critic unless they are already loaded.
        module = importlib.import_module("stgem.testgenerator.wogan.mlm")
        generator_class = getattr(module, self.generator_mlm)
        critic_class = getattr(module, self.critic_mlm)
        if self.modelG is None:
            self.modelG = generator_class(rng=self.search_space.rng, **self.generator_mlm_parameters).to(config.device)
        else:
            self.modelG = self.modelG.to(config.device)
        if self.modelC is None:
            self.modelC = critic_class(rng=self.search_space.rng, **self.critic_mlm_parameters).to(config.device)
        else:
            self.modelC = self.modelC.to(config.device)

        # Load the specified optimizers.
        module = importlib.import_module("torch.optim")
        generator_optimizer_class = getattr(module, self.generator_optimizer)
        generator_parameters = {k[10:]: v for k, v in self.parameters.items() if k.startswith("generator")}
        self.optimizerG = generator_optimizer_class(self.modelG.parameters(), **filter_arguments(generator_parameters, generator_optimizer_class))
        critic_optimizer_class = getattr(module, self.critic_optimizer)
        critic_parameters = {k[7:]: v for k, v in self.parameters.items() if k.startswith("critic")}
        self.optimizerC = critic_optimizer_class(self.modelC.parameters(), **filter_arguments(critic_parameters, critic_optimizer_class))
    
    def to_device(self, device):
        self.modelA.to_device(device)
        self.modelC = self.modelC.to(device)
        self.modelG = self.modelG.to(device)

    def _generate_test(self, N=1):
        if self.modelG is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        if N <= 0:
            raise ValueError("The number of tests should be positive.")

        training_G = self.modelG.training

        # Generate uniform noise in [-1, 1].
        noise = (2 * torch.rand(N, self.modelG.input_shape, generator=self.search_space.rng.get_rng("torch")) - 1).to(config.device)

        # Pass the noise through the generator.
        self.modelG.train(False)
        result = self.modelG(noise)
        if torch.any(torch.isinf(result)) or torch.any(torch.isnan(result)):
            raise AlgorithmException("Generator produced a test with inf or NaN entries.")
        self.modelG.train(training_G)

        return result.cpu().detach().numpy()

    def generate_test(self, N=1):
        """
        Generate N random tests.

        Args:
          N (int): Number of tests to be generated.

        Returns:
          output (np.ndarray): Array of shape (N, self.input_dimensions).
        """

        return self._generate_test(N)

    def predict_objective(self, test):
        """
        Predicts the objective function value for the given test.

        Args:
          test (np.ndarray): Array with shape (1, N) or (N).

        Returns:
          output (float)
        """

        if self.modelA is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        return self.modelA.predict(test)

    def train_analyzer_with_batch(self, data_X, data_Y, train_settings):
        """
        Train the analyzer part of the model with a batch of training data.

        Args:
            data_X (np.ndarray): Array of tests of shape (N, self.input_dimensions).
            data_Y (np.ndarray): Array of test outputs of shape (N, 1).
            train_settings (dict): A dictionary setting up the number of training epochs for various parts of the model.
                                   The keys are as follows: 
                                   analyzer_epochs: How many total runs are made with the given training data.
                                   The default for each missing key is 1. Keys not found above are ignored.

        Returns:
            list: List of analyzer losses observed.
        """

        losses = []
        for _ in range(train_settings["analyzer_epochs"]):
            loss = self.modelA.train_with_batch(data_X, data_Y, train_settings)
            losses.append(loss)

        m = np.mean(losses)
        logging.debug("Analyzer epochs {}, Loss: {} -> {} (mean {})".format(train_settings["analyzer_epochs"], losses[0], losses[-1], m))

        return losses

    def train_with_batch(self, data_X, train_settings=None):
        """
        Train the WGAN with a batch of training data.

        Args:
            data_X (np.ndarray): Array of tests of shape (M, self.input_dimensions).
            train_settings (dict): A dictionary setting up the number of training epochs for various parts of the model.
                                   The keys are as follows:
                                     critic_steps: How many times the critic is trained per epoch.
                                     generator_steps: How many times the generator is trained per epoch.
                                   The default for each missing key is 1. Keys not found above are ignored.

        Returns:
            tuple: Contains lists of critic losses, generator losses, and gradient penalties observed.
        """

        if train_settings is None:
            train_settings = self.default_parameters["train_settings"]

        data_X = torch.from_numpy(data_X).float().to(config.device)
        rng = self.search_space.rng.get_rng("torch")

        # Unpack values from the epochs dictionary.
        critic_steps = train_settings["critic_steps"] if "critic_steps" in train_settings else 1
        generator_steps = train_settings["generator_steps"] if "generator_steps" in train_settings else 1

        # Save the training modes for later restoring.
        training_C = self.modelC.training
        training_G = self.modelG.training

        # Train the critic.
        # ---------------------------------------------------------------------
        self.modelC.train(True)
        C_losses = []
        gradient_penalties = []
        for m in range(critic_steps):
            # Here the mini batch size of the WGAN-GP is set to be the number
            # of training samples for the critic
            M = data_X.shape[0]

            # Loss on real data.
            real_inputs = data_X
            real_outputs = self.modelC(real_inputs)
            real_loss = real_outputs.mean(0)

            # Loss on generated data.
            # For now we use as much generated data as we have real data.
            noise = (2 * torch.rand(M, self.modelG.input_shape, generator=rng) - 1).to(config.device)
            fake_inputs = self.modelG(noise)
            fake_outputs = self.modelC(fake_inputs)
            fake_loss = fake_outputs.mean(0)

            # Gradient penalty.
            # Compute interpolated data.
            e = torch.rand(M, 1, generator=rng).to(config.device)
            interpolated_inputs = e * real_inputs + (1 - e) * fake_inputs
            # Get critic output on interpolated data.
            interpolated_outputs = self.modelC(interpolated_inputs)
            # Compute the gradients wrt to the interpolated inputs.
            # Warning: Showing the validity of the following line requires some
            # pen and paper calculations.
            gradients = torch.autograd.grad(inputs=interpolated_inputs,
                                            outputs=interpolated_outputs,
                                            grad_outputs=torch.ones_like(interpolated_outputs).to(config.device),
                                            create_graph=True,
                                            retain_graph=True,
                                            )[0]

            # We add epsilon for stability.
            epsilon = self.eps if "eps" in self.parameters else 1e-7
            gradients_norms = torch.sqrt(torch.sum(gradients ** 2, dim=1) + epsilon)
            gradient_penalty = ((gradients_norms - 1) ** 2).mean()
            # gradient_penalty = ((torch.linalg.norm(gradients, dim=1) - 1)**2).mean()

            C_loss = fake_loss - real_loss + self.gp_coefficient * gradient_penalty
            C_losses.append(C_loss.item())
            gradient_penalties.append(self.gp_coefficient * gradient_penalty.item())
            self.optimizerC.zero_grad()
            C_loss.backward()
            self.optimizerC.step()

        m1 = np.mean(C_losses)
        m2 = np.mean(gradient_penalties)
        logging.debug("Critic steps {}, Loss: {} -> {} (mean {}), GP: {} -> {} (mean {})".format(critic_steps, C_losses[0], C_losses[-1], m1, gradient_penalties[0], gradient_penalties[-1], m2))

        self.modelC.train(False)

        # Visualize the computational graph.
        # print(make_dot(C_loss, params=dict(self.modelC.named_parameters())))

        # Train the generator.
        # ---------------------------------------------------------------------
        self.modelG.train(True)
        G_losses = []
        noise_batch_size = self.noise_batch_size
        for m in range(generator_steps):
            noise = (2 * torch.rand(noise_batch_size, self.modelG.input_shape, generator=rng) - 1).to(config.device)
            outputs = self.modelC(self.modelG(noise))

            G_loss = -outputs.mean(0)
            G_losses.append(G_loss.item())
            self.optimizerG.zero_grad()
            G_loss.backward()
            self.optimizerG.step()

        m = np.mean(G_losses)
        logging.debug("Generator steps {}, Loss: {} -> {} (mean {})".format(generator_steps, G_losses[0], G_losses[-1], m))

        self.modelG.train(False)

        report_wd = self.report_wd if "report_wd" in self.parameters else False
        if report_wd:
            # Same as above in critic training.
            real_inputs = data_X
            real_outputs = self.modelC(real_inputs)
            real_loss = real_outputs.mean(0)

            # For now we use as much generated data as we have real data.
            noise = (2 * torch.rand(real_inputs.shape[0], self.modelG.input_shape, generator=rng) - 1).to(config.device)
            fake_inputs = self.modelG(noise)
            fake_outputs = self.modelC(fake_inputs)
            fake_loss = fake_outputs.mean(0)

            W_distance = real_loss - fake_loss

            logging.debug("Batch W. distance: {}".format(W_distance[0]))

        # Visualize the computational graph.
        # print(make_dot(G_loss, params=dict(self.modelG.named_parameters())))

        # Restore the training modes.
        self.modelC.train(training_C)
        self.modelG.train(training_G)

        return C_losses, G_losses, gradient_penalties
