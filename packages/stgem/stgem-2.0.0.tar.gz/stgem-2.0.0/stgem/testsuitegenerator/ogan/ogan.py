from stgem.limit import Limit
from stgem.monitor import Monitor
from stgem.rng import RandomNumberGenerator
from stgem.sut import SystemUnderTest
from stgem.testgenerator.ogan.generator import OGAN
from stgem.testgenerator.random import RandomGenerator, Uniform, LHS
from stgem.testsuitegenerator import TestSuiteGenerator, ExploreExploitOneGoal
from stgem.testsuitegenerator.parameters import get_OGAN_parameters as get_parameters

class OGAN_TestSuiteGenerator(ExploreExploitOneGoal):
    """Implements the OGAN test suite generator as described in the paper

    J. Peltomäki, I. Porres: Requirement falsification for cyber-physical
    systems using generative models (2023), arXiv:2310.20493."""

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

        self.random_exploration = False
        self.random_generator = None
        self.explore_generator = None
        self.ogan_generator = None
        self.ogan_selected = 0

        self.robustness_threshold = 0.0

    def __str__(self):
        str1 = "{} {}".format(self.random_search, self.random_search_proportion)
        str2 = "reset training" if self.reset_each_training else ""
        str3 = ",θ={}".format(self.random_exploration_probability) if self.random_exploration else ""
        return "{}({},{}{})".format(self.__class__.__name__, str1, str2, str3)

    def setup(self,
              sut: SystemUnderTest | None = None,
              goal: Monitor | None = None,
              limit: Limit | None = None,
              seed: int | None = None,
              rng: RandomNumberGenerator | None = None):
        # The inheritance is a bit complicated. We want to use the step method
        # from ExploreExploitGoal but its __init__ is quite different.
        TestSuiteGenerator.setup(self, sut=sut, goal=goal, limit=limit, seed=seed, rng=rng)

    def initialize(self):
        if self.has_been_initialized: return
        TestSuiteGenerator.initialize(self)

        if self.search_space is None:
            raise Exception("Search space not set up when initializing the test suite generator.")

        self.random_search_limit = (1 - self.random_search_proportion)*self.limit.remaining()
        match self.random_search.lower():
            case "uniform":
                random_model = Uniform()
            case "lhs":
                random_model = LHS({"samples": self.lhs_samples})
            case _:
                raise ValueError("Unknown random search type '{}'.".format(self.random_search_lower))
        self.random_generator = RandomGenerator(random_model)
        self.random_generator.setup(search_space=self.search_space)

        if "random_exploration_probability" in self.parameters and self.random_exploration_probability > 0.0:
            self.random_exploration = True
            self.explore_generator = RandomGenerator(Uniform())
            self.explore_generator.setup(search_space=self.search_space)
            if "exploration_warm_up" not in self.parameters:
                self.parameters["exploration_warm_up"] = 30

        generator_parameters = self.parameters["generator_parameters"] if "generator_parameters" in self.parameters else None
        model_parameters = self.parameters["model_parameters"] if "model_parameters" in self.parameters else None
        self.ogan_generator = OGAN(parameters=generator_parameters, model_parameters=model_parameters)
        self.ogan_generator.setup(search_space=self.search_space)

        self.perform_generator_training = False
        self.never_trained = True
        self.not_trained_count = 0
    
    def set_generator(self, random_generator=None, generator=None):
        raise NotImplementedError()

    def select_generator(self):
        if self.limit.remaining() > self.random_search_limit:
            generator = self.random_generator
            self.perform_generator_training = False
        else:
            # If an exploration probability is specified, then the explore
            # generator (uniform random search) is used according to this
            # probability instead of the OGAN generator. During the warm-up
            # period only OGAN generator is selected.
            if self.random_exploration and self.ogan_selected > self.exploration_warm_up and self.search_space.get_rng("numpy").uniform() <= self.random_exploration_probability:
                generator = self.explore_generator
                self.perform_generator_training = False
            else:
                generator = self.ogan_generator
                self.perform_generator_training = self.never_trained or self.not_trained_count >= self.train_delay - 1
                self.never_trained = False
                self.ogan_selected += 1

        return generator

    def train_generator(self, generator):
        if self.perform_generator_training:
            if self.reset_each_training:
                for model in generator.get_models():
                    model.reset()
            training_performance = generator.train_on_search_space(remaining=self.limit.remaining())
            self.not_trained_count = 0

            self.perform_generator_training = False
        else:
            training_performance = {}
            self.not_trained_count += 1

        return training_performance


OGANAlgorithm = OGAN_TestSuiteGenerator
