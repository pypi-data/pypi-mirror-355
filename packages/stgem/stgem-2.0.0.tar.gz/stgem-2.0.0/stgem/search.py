from copy import deepcopy
from typing import Union

import numpy as np

from stgem.features import FeatureVector
from stgem.rng import RandomNumberGenerator


class SearchSpace:
    """
    Represents an n-dimensional search space
    Every input (decision variable) is normalized in the interval [-1,1]
    The output (objective) is normalized in the interval [0,1]"""

    def __init__(self,
                 input_vector: FeatureVector = None,
                 input_dimension: int = 0,
                 output_dimension: int = 1,
                 constraint=None,
                 rng: RandomNumberGenerator = None):
        """
        Initializes the SearchSpace object.

        Parameters:
        input_vector (FeatureVector): The input feature vector.
        input_dimension (int): The dimension of the input space.
        output_dimension (int): The dimension of the output space.
        constraint (function): A function to constrain valid inputs.
        rng (RandomNumberGenerator): A random number generator.
        """

        assert not (input_vector and input_dimension > 0)

        if input_vector:
            input_dimension = input_vector.dimension

        self.input_vector = input_vector
        self.input_dimension = input_dimension
        self.I = np.empty((0, self.input_dimension))

        self.output_dimension = output_dimension
        self.O = np.empty((0, self.output_dimension))

        self.rng = rng if rng is not None else RandomNumberGenerator(seed=None)

        self.constraint = constraint
    
    def __deepcopy__(self, memo=None):
        # We never expect to have independent copies of exactly the same search
        # space.
        if memo is not None and id(self) in memo:
            return memo[id(self)]
        input_vector = self.input_vector
        input_dimension = self.input_dimension if input_vector is None else 0
        ss = SearchSpace(
            input_vector=input_vector,
            input_dimension=input_dimension,
            output_dimension=self.output_dimension,
            constraint=self.constraint,
            rng=self.rng
        )
        ss.I = np.copy(self.I)
        ss.O = np.copy(self.O)
        memo[id(self)] = ss
        return ss

    def get_rng(self, rng_id):
        return self.rng.get_rng(rng_id)

    def new_ifv(self):
        """
        Creates a new input feature vector with the same features as the current one.

        Returns:
        FeatureVector: A new feature vector with the same features.
        """
        assert self.input_vector, "Input vector is not defined"
        return self.input_vector(name=self.input_vector.name)

    def is_valid(self, input: np.array) -> bool:
        """
        Checks if a given input is valid according to the constraint function.

        Parameters:
        input (np.array): The input to check.

        Returns:
        bool: True if the input is valid, False otherwise.
        """
        # This is here until valid tests are changed to preconditions. This
        # line ensures that model-based SUTs work and can be pickled.
        if self.constraint is None:
            return True
        else:
            return self.constraint(input)

    def sample_input_vector(self, max_trials=10000) -> FeatureVector:
        ifv = self.new_ifv()
        ifv.set_packed(self.sample_input_space(max_trials))
        return ifv

    def sample_input_space(self, max_trials=10000) -> np.array:
        """
        Samples a valid input from the input space.

        Parameters:
        max_trials (int): The maximum number of trials to find a valid input.

        Returns:
        np.array: A valid input.

        Raises:
        Exception: If a valid input cannot be found within max_trials.
        """

        rng = self.rng.get_rng("numpy")
        for _ in range(max_trials):
            candidate = rng.uniform(-1, 1, size=self.input_dimension)
            if self.is_valid(candidate):
                return candidate

        raise Exception("sample_input_space: max_trials exceeded")

    def record_normalized(self, input: np.array, output: Union[np.array, float]):
        """
        Records a normalized input-output pair.

        Parameters:
        input (np.array): The normalized input.
        output (Union[np.array, float]): The normalized output.
        
        Raises:
        AssertionError: If the inputs are not in the range [-1, 1] or outputs are not in the range [0, 1].
        """
        if __debug__:
            def _min(x):
                return min(x) if not np.isscalar(x) else x

            def _max(x):
                return max(x) if not np.isscalar(x) else x

            assert _min(input) >= -1 and _max(input) <= 1 and \
                   _min(output) >= 0 and _max(output <= 1)
        self.I = np.append(self.I, [input], axis=0)
        if np.isscalar(output):
            self.O = np.append(self.O, [[output]], axis=0)
        else:
            self.O = np.append(self.O, [output], axis=0)

    def record(self, ifv: FeatureVector, output: Union[np.array, float]):
        """
        Records an input-output pair by normalizing the input feature vector.

        Parameters:
        ifv (FeatureVector): The input feature vector.
        output (Union[np.array, float]): The output.
        """
        self.record_normalized(ifv.pack(), output)

    @property
    def recorded_inputs(self):
        return len(self.I)

    def known_inputs(self):
        """
        Returns the known inputs recorded so far.

        Returns:
        np.array: The recorded inputs.
        """
        return self.I

    def known_outputs(self):
        """
        Returns the known outputs recorded so far.

        Returns:
        np.array: The recorded outputs.
        """
        return self.O
