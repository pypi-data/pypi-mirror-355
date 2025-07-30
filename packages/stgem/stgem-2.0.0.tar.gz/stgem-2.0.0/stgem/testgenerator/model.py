from stgem import SearchSpace
from stgem.util import merge_dictionary

class Model:
    """Base class for a model"""

    default_parameters = {}

    def __init__(self, parameters: dict = None):
        if parameters is None:
            parameters = {}
        self.parameters = merge_dictionary(parameters, self.default_parameters)
        self.search_space = None

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__.get(name)
        elif "parameters" in self.__dict__ and name in self.parameters:
            return self.parameters.get(name)
        else:
            raise AttributeError(name)

    def setup(self, search_space: SearchSpace):
        self.search_space = search_space
        self.parameters["input_dimension"] = self.search_space.input_dimension
    
    def to_device(self, device):
        pass

    def reset(self):
        pass

    def generate_test(self, N: int = 1):
        """Generate N random tests.

        Args:
            N (int): Number of tests to be generated.

        Returns:
            output (np.ndarray): Array of shape (N, self.search_space.input_dimension)."""

        raise NotImplementedError()

    def predict_objective(self, test):
        """Predicts the objective function value of the given tests.

        Args:
            test (np.ndarray): Array of shape (N, self.search_space.input_dimension).

        Returns:
            output (np.ndarray): Array of shape (N, 1)."""

        raise NotImplementedError()

    def train_with_batch(self, dataX, dataY):
        pass
