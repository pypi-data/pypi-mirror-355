from stgem import config
from stgem.limit import Limit
from stgem.monitor import Monitor
from stgem.rng import RandomNumberGenerator
from stgem.sut import SystemUnderTest
from stgem.testgenerator.random import RandomGenerator, Uniform, LHS
from stgem.testgenerator.wogan.generator import WOGAN
from stgem.testsuitegenerator import TestSuiteGenerator, ExploreExploitOneGoal
from stgem.testsuitegenerator.parameters import get_WOGAN_parameters as get_parameters

class WOGAN_TestSuiteGenerator(ExploreExploitOneGoal):
    """Implements the WOGAN test suite generator."""

    # The default parameters will be fetched via the function get_parameters.
    default_parameters = {}

    def __init__(self,
                 *,
                 sut: SystemUnderTest | None = None,
                 goal: Monitor | None = None,
                 limit: Limit | None = None,
                 parameters: dict = None):
        if parameters is None:
            has_signal_input = False
            if sut is not None:
                for feature in sut.new_ifv().flatten_to_list():
                    if isinstance(feature, PiecewiseConstantSignal):
                        has_signal_input = True
                        break
            
            network_type = "convolution" if has_signal_input else "dense"
            parameters = get_parameters("default", network_type=network_type)
        TestSuiteGenerator.__init__(self, sut=sut, goal=goal, limit=limit, parameters=parameters)

        self.random_generator = None
        self.generator_class = WOGAN
        self.generator = None

        self.random_search_limit = None
        self.robustness_threshold = 0.0

    def __str__(self):
        str1 = "{}".format(self.random_search_proportion)
        str2 = "reset training" if self.reset_each_training else ""
        return "{}({},{})".format(self.__class__.__name__, str1, str2)

    def setup(self,
              sut: SystemUnderTest | None = None,
              goal: Monitor | None = None,
              limit: Limit | None = None,
              seed: int | None = None,
              rng: RandomNumberGenerator | None = None):
        # The inheritance is a bit complicated. We want to use the step method
        # from ExploreExploitGoal but its __init__ is quite different.
        TestSuiteGenerator.setup(self, sut=sut, goal=goal, limit=limit, seed=seed, rng=rng)

        if self.random_search_limit is None and self.limit is not None:
            self.random_search_limit = (1 - self.random_search_proportion)*self.limit.remaining()

    def initialize(self):
        if self.has_been_initialized: return
        TestSuiteGenerator.initialize(self)

        if self.search_space is None:
            raise Exception("Search space not set up when initializing the test suite generator.")

        self._initialize_random_generator()
        self._initialize_generator()
        
        self.perform_generator_training = False
        self.never_trained = True
        self.not_trained_count = 0
    
    def _initialize_random_generator(self):
        if "random_search" not in self.parameters or self.random_search == "uniform":
            self.random_generator = RandomGenerator(Uniform())
        elif self.random_search == "lhs":
            self.random_generator = RandomGenerator(LHS())
        else:
            raise ValueError("Unknown random search '{}'.".format(self.random_search))
        self.random_generator.setup(search_space=self.search_space)
    
    def _initialize_generator(self):
        generator_parameters = self.parameters["generator_parameters"] if "generator_parameters" in self.parameters else None
        model_parameters = self.parameters["model_parameters"] if "model_parameters" in self.parameters else None
        self.generator = self.generator_class(parameters=generator_parameters, model_parameters=model_parameters)
        self.generator.setup(search_space=self.search_space)
    
    def set_generator(self, random_generator=None, generator=None):
        """Allow to set either of the used generators to the given generators.
        This method can be used in place of the method initialize as the
        unspecified generators will be set up according to the test suite
        generator parameters. Calling initialize after this method does
        nothing."""

        if self.search_space is None:
            raise Exception("Search space not set up when setting up generators.")
        
        TestSuiteGenerator.initialize(self)
        
        if random_generator is None:
            if self.random_generator is not None:
                self._initialize_random_generator()
        else:
            self.random_generator = random_generator
            self.random_generator.search_space = self.search_space
            self.random_generator.to_device(config.device)
        
        if generator is None:
            if self.generator is None:
                self._initialize_generator()
                self.perform_generator_training = False
                self.never_trained = True
                self.not_trained_count = 0
        else:
            self.generator = generator
            self.generator.search_space = self.search_space
            self.generator.to_device(config.device)
            self.perform_generator_training = False
            self.never_trained = True
            self.not_trained_count = 0

    def select_generator(self):
        if self.limit.remaining() > self.random_search_limit:
            generator = self.random_generator
            self.perform_generator_training = False
        else:
            generator = self.generator
            self.perform_generator_training = self.never_trained or self.not_trained_count >= self.train_delay - 1

        return generator

    def train_generator(self, generator):
        if self.perform_generator_training:
            if self.reset_each_training:
                for model in generator.get_models():
                    model.reset()

            remaining = self.limit.remaining()

            if self.never_trained:
                latest = []
            else:
                latest = [self.search_space.recorded_inputs - 1 - i for i in range(self.train_delay)]

            training_performance = generator.train(self.search_space.known_inputs(), self.search_space.known_outputs(), remaining, latest=latest)

            self.not_trained_count = 0
            self.perform_generator_training = False
            self.never_trained = False
        else:
            training_performance = {}
            self.not_trained_count += 1

        return training_performance


WOGANAlgorithm = WOGAN_TestSuiteGenerator
