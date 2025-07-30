import copy
import importlib

import numpy as np
import torch

from stgem import config, filter_arguments, logging, SearchSpace
from stgem.exceptions import AlgorithmException
from stgem.testgenerator.model import Model
from stgem.testsuitegenerator.parameters import get_OGAN_parameters as get_parameters

class OGAN_Model(Model):

    # The default parameters will be fetched via the function get_parameters.
    default_parameters = {}

    def __init__(self, parameters: dict = None):
        if parameters is None:
            parameters = get_parameters("default")["model_parameters"]
        super().__init__(parameters)
        self.modelG = None
        self.modelD = None

    def setup(self, search_space: SearchSpace):
        super().setup(search_space)

        # Infer input and output dimensions for ML models.
        self.parameters["generator_mlm_parameters"]["output_shape"] = self.search_space.input_dimension
        self.parameters["discriminator_mlm_parameters"]["input_shape"] = self.search_space.input_dimension

        self._initialize()

    def _initialize(self, hard_reset=False):
        # Load the specified generator and discriminator machine learning
        # models unless they are already loaded.
        module = importlib.import_module("stgem.testgenerator.ogan.mlm")
        generator_class = getattr(module, self.generator_mlm)
        discriminator_class = getattr(module, self.discriminator_mlm)

        if self.modelG is None or hard_reset:
            self.modelG = generator_class(rng=self.search_space.rng, **self.generator_mlm_parameters).to(config.device)
        else:
            self.modelG = self.modelG.to(config.device)
        if self.modelD is None or hard_reset:
            self.modelD = discriminator_class(rng=self.search_space.rng, **self.discriminator_mlm_parameters).to(config.device)
        else:
            self.modelD = self.modelD.to(config.device)

        # Load the specified optimizers.
        module = importlib.import_module("torch.optim")
        optimizer_class = getattr(module, self.optimizer)
        generator_parameters = {k[10:]: v for k, v in self.parameters.items() if k.startswith("generator")}
        self.optimizerG = optimizer_class(self.modelG.parameters(), **filter_arguments(generator_parameters, optimizer_class))
        discriminator_parameters = {k[14:]: v for k, v in self.parameters.items() if k.startswith("discriminator")}
        self.optimizerD = optimizer_class(self.modelD.parameters(), **filter_arguments(discriminator_parameters, optimizer_class))

        # Loss functions.
        def get_loss(loss_s):
            loss_s = loss_s.lower()
            if loss_s == "mse":
                loss = torch.nn.MSELoss()
            elif loss_s == "l1":
                loss = torch.nn.L1Loss()
            elif loss_s == "mse,logit" or loss_s == "l1,logit":
                # When doing regression with values in [0, 1], we can use a
                # logit transformation to map the values from [0, 1] to \R
                # to make errors near 0 and 1 more drastic. Since logit is
                # undefined in 0 and 1, we actually first transform the values
                # to the interval [0.01, 0.99].
                L = 0.001
                g = torch.logit
                if loss_s == "mse,logit":
                    def f(X, Y):
                        return ((g(0.98*X + 0.01) - g(0.98*Y + 0.01))**2 + L * (g((1 + X - Y) / 2))**2).mean()
                else:
                    def f(X, Y):
                        return (torch.abs(g(0.98*X + 0.01) - g(0.98*Y + 0.01)) + L*torch.abs(g((1 + X - Y) / 2))).mean()
                loss = f
            else:
                raise Exception("Unknown loss function '{}'.".format(loss_s))

            return loss

        try:
            self.lossG = get_loss(self.generator_loss)
            self.lossD = get_loss(self.discriminator_loss)
        except:
            raise

    def reset(self):
        self._initialize(hard_reset=True)

    def __getstate__(self):
        state = copy.deepcopy(self.__dict__)

        state["modelG"] = state["modelG"].to("cpu") if state["modelG"] is not None else None
        state["modelD"] = state["modelD"].to("cpu") if state["modelD"] is not None else None

        return state

    def _generate_test(self, N=1):
        if self.modelG is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        if N <= 0:
            raise ValueError("The number of tests should be positive.")

        training_G = self.modelG.training

        # Generate uniform noise in [-1, 1].
        noise = (torch.rand(N, self.modelG.input_shape, generator=self.search_space.get_rng("torch"))*2 - 1).to(config.device)

        # Pass the noise through the generator.
        self.modelG.train(False)
        result = self.modelG(noise)
        if torch.any(torch.isinf(result)) or torch.any(torch.isnan(result)):
            raise AlgorithmException("Generator produced a test with inf or NaN entries.")
        self.modelG.train(training_G)

        return result.cpu().detach().numpy()

    def generate_test(self, N=1):
        """Generate N random tests.

        Args:
          N (int):      Number of tests to be generated.

        Returns:
          output (np.ndarray): Array of shape (N, self.input_ndimension).

        Raises:
        """

        return self._generate_test(N)

    def predict_objective(self, test):
        """Predicts the objective function value of the given tests.

        Args:
          test (np.ndarray): Array of shape (N, self.input_ndimension).

        Returns:
          output (np.ndarray): Array of shape (N, 1).

        Raises:
        """

        return self._predict_objective(test)

    def _predict_objective(self, test):
        if self.modelG is None or self.modelD is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        test_tensor = torch.from_numpy(test).float().to(config.device)
        return self.modelD(test_tensor).cpu().detach().numpy().reshape(-1)

    def train_with_batch(self, dataX, dataY, train_settings=None):
        """
        Train the OGAN with a batch of training data.

        Args:
            dataX (np.ndarray): Array of tests of shape (N, self.input_dimension).
            dataY (np.ndarray): Array of test outputs of shape (N, 1).
            train_settings (dict): A dictionary setting up the number of training epochs for various parts of the model.
                                The keys are as follows:
                                  discriminator_epochs (int): How many times the discriminator is trained per call.
                                  generator_batch_size (int): How large batches of noise are used at a training step.
                                The default for each missing key is 1. Keys not found above are ignored.

        Returns:
            tuple: Contains lists of discriminator losses and generator losses.

        """

        if self.modelG is None or self.modelD is None:
            raise Exception("No machine learning models available. Has the model been setup correctly?")

        if train_settings is None:
            train_settings = self.default_parameters["train_settings"]

        if len(dataY) < len(dataX):
            raise ValueError("There should be at least as many training outputs as there are inputs.")

        dataX = torch.from_numpy(dataX).float().to(config.device)
        dataY = torch.from_numpy(dataY).float().to(config.device)

        # Unpack values from the train_settings dictionary.
        discriminator_epochs = train_settings["discriminator_epochs"] if "discriminator_epochs" in train_settings else 1
        generator_batch_size = train_settings[
            "generator_batch_size"] if "generator_batch_size" in train_settings else 32

        # Save the training modes for restoring later.
        training_D = self.modelD.training
        training_G = self.modelG.training

        # Train the discriminator.
        # ---------------------------------------------------------------------
        # We want the discriminator to learn the mapping from tests to test
        # outputs.
        self.modelD.train(True)
        D_losses = []
        for _ in range(discriminator_epochs):
            D_loss = self.lossD(self.modelD(dataX), dataY)
            D_losses.append(D_loss.cpu().detach().numpy().item())
            self.optimizerD.zero_grad()
            D_loss.backward()
            self.optimizerD.step()

        m = np.mean(D_losses)
        if discriminator_epochs > 0:
            logging.debug("Discriminator epochs {}, Loss: {} -> {} (mean {})".format(discriminator_epochs, D_losses[0], D_losses[-1], m))

        self.modelD.train(False)

        # Visualize the computational graph.
        # print(make_dot(D_loss, params=dict(self.modelD.named_parameters())))

        # Train the generator on the discriminator.
        # -----------------------------------------------------------------------
        # We generate noise and label it to have output 0 (min objective).
        # Training the generator in this way should shift it to generate tests
        # with low output values (low objective). Notice that we need to
        # validate the generated tests as no invalid tests with high robustness
        # exist.
        self.modelG.train(False)
        inputs = np.zeros(shape=(self.noise_batch_size, self.modelG.input_shape))
        k = 0
        while k < inputs.shape[0]:
            noise = torch.rand(1, self.modelG.input_shape, generator=self.search_space.get_rng("torch"))*2 - 1
            new_test = self.modelG(noise.to(config.device)).cpu().detach().numpy()
            # if self.search_space.is_valid(new_test) == 0: continue
            inputs[k, :] = noise[0, :]
            k += 1
        self.modelG.train(True)
        inputs = torch.from_numpy(inputs).float().to(config.device)

        fake_label = torch.zeros(size=(generator_batch_size, 1)).to(config.device)

        # Notice the following subtlety. Below the tensor 'outputs' contains
        # information on how it is computed (the computation graph is being kept
        # track off) up to the original input 'inputs' which does not anymore
        # depend on previous operations. Since 'self.modelD' is used as part of
        # the computation, its parameters are present in the computation graph.
        # These parameters are however not updated because the optimizer is
        # initialized only for the parameters of 'self.modelG' (see the
        # initialization of 'self.modelG').

        G_losses = []
        for n in range(0, self.noise_batch_size, generator_batch_size):
            outputs = self.modelD(self.modelG(inputs[n:n + generator_batch_size]))
            G_loss = self.lossG(outputs, fake_label[:outputs.shape[0]])
            G_losses.append(G_loss.cpu().detach().numpy().item())
            self.optimizerG.zero_grad()
            G_loss.backward()
            self.optimizerG.step()

        m = np.mean(G_losses)
        if self.noise_batch_size > 0:
            logging.debug(
                "Generator steps {}, Loss: {} -> {}, mean {}".format(self.noise_batch_size // generator_batch_size + 1, G_losses[0], G_losses[-1], m))

        self.modelG.train(False)

        # Visualize the computational graph.
        # print(make_dot(G_loss, params=dict(self.modelG.named_parameters())))

        # Restore the training modes.
        self.modelD.train(training_D)
        self.modelG.train(training_G)

        return D_losses, G_losses
