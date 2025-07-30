import numpy as np

class Sampler:
    """Base class for samplers."""

    default_parameters = {}

    def __init__(self, parameters=None):
        if parameters is None:
            parameters = {}

        # Merge default_parameters and parameters. The latter takes priority if
        # a key appears in both dictionaries.
        # We would like to write the following but this is not supported in Python 3.7.
        # self.parameters = self.default_parameters | parameters
        for key in self.default_parameters:
            if not key in parameters:
                parameters[key] = self.default_parameters[key]

        self.parameters = parameters
        self.search_space = None
        self.first_call = True
    
    def setup(self, search_space):
        self.search_space = search_space

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__.get(name)
        elif "parameters" in self.__dict__ and name in self.parameters:
            return self.parameters.get(name)
        else:
            raise AttributeError(name)

    def __call__(self, N, objectives, remaining, new=None):
        """A function that returns N indices to objectives which represent a
        sample of tests based on their one-dimensional objective values. The
        variable remaining indicates how much resources, time, etc. are left as
        a number in the interval [0, 1] (0 = nothing left, 1 = full resources
        available). The list new contains indices to objectives that indicate
        which objective values correspond to new tests."""

        raise NotImplementedError


class SBST_Sampler(Sampler):
    """The default WOGAN sampler that was proposed in the paper 'Wasserstein
    generative adversarial networks for online test generation for cyber
    physical systems'. The idea is briefly that the objective range [0,1] is
    split into B bins of equal width and the tests are placed into those bins.
    Each bin is weighted according to a sigmoid function in such a way that the
    initial bins having low objective have higher weight. First a sample of bin
    indices is obtained by a random sampling using these weights. The final
    sample is obtained by selecting tests uniformly randomly from the bins
    according to the bin index sample."""

    default_parameters = {
        "bins": 10,
        "sample_with_replacement": False,
        "omit_initial_empty": True,
        "quantile_start": 0.5,
        "quantile_end": 0.1,
        "zero_minimum": True,
        "shift_function": "linear",
        "shift_function_parameters": {"initial": 0, "final": 3}
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)

        if not self.shift_function in ["linear"]:
            raise Exception("Unknown shift function '{}'.".format(self.shift_function))

        # Function for computing the bin weights.
        self.bin_weight = lambda x: 1 - 1 / (1 + np.exp(-1 * x))
        # Shift function for shifting the weights. This is set up on first call
        # to training_sample.
        self.shift = None
        # Quantile function. This is set up on first call to training_sample.
        self.quantile = None

    def _setup_first_call(self, remaining):
        if self.first_call:
            # We increase the shift linearly according to the given initial and
            # given final value.
            if self.shift is None:
                alpha1 = (self.shift_function_parameters["initial"] - self.shift_function_parameters["final"]) / remaining
                beta1 = self.shift_function_parameters["final"]
                self.shift = lambda x: alpha1 * x + beta1

            # We decrease the quantile linearly according to the given initial
            # and given final value.
            if self.quantile is None:
                alpha2 = (self.quantile_start - self.quantile_end) / remaining
                beta2 = self.quantile_end
                self.quantile = lambda x: alpha2 * x + beta2

            self.first_call = False

    def get_bin(self, x, M=1.0, m=0.0):
        """Function for obtaining the test bin based on its objective."""

        if not (0 <= x <= 1):
            raise Exception("WOGAN expects objectives to be scaled to [0,1]. Got objective with value {}.".format(x))

        # Notice that if the maximum M is incorrect, tests whose objective
        # exceeds M go to the highest bin.
        if x <= M:
            if x < M:
                return int( (self.bins)/(M - m) * (x - m) )
            else:
                return self.bins - 1
        else:
            return self.bins

    def bin_weights(self, shift):
        """Get unnormalized weights for bins."""

        """
        The distribution on the bin indices is defined as follows. Suppose that
        S is a non-negative and decreasing function satisfying S(-x) = 1 - S(x)
        for all x. Consider the middle points of the bins. We map the middle
        point of the middle bin to 0 and the remaining middle points
        symmetrically around 0 with first middle point corresponding to -1 and
        the final to 1. We then shift these mapped middle points to the left by
        the given amount. The weight of the bin is S(x) where x is the mapped
        and shifted middle point. We use the function self.bin_weight for S.
        """

        # If the number of bins is odd, then the middle point of the middle bin
        # interval is mapped to 0 and otherwise the point common to the two
        # middle bin intervals is mapped to 0.
        if self.bins % 2 == 0:
            h = lambda x: x - (int(self.bins / 2) + 0.0) * (1 / self.bins)
        else:
            h = lambda x: x - (int(self.bins / 2) + 0.5) * (1 / self.bins)

        # We basically take the middle point of a bin interval, map it to
        # [-1, 1] and apply S on the resulting point to find the unnormalized
        # bin weight. The sink bin has weight 0.
        weights = np.zeros(shape=(self.bins + 1))
        for n in range(self.bins):
            weights[n] = self.bin_weight(h((n + 0.5) * (1 / self.bins)) + shift)

        return weights

    def bin_sample(self, N, bins):
        """Samples N bin indices."""

        shift = self.current_shift_value

        if N == 0:
            return []

        weights = self.bin_weights(shift)

        # If any number of initial bins are empty, then the first nonempty bin
        # is automatically sampled by the code below. We remove the initial
        # empty bins if requested.
        if self.omit_initial_empty:
            for L in range(len(weights)):
                if len(bins[L]) > 0:
                    break
            weights = weights[L:]
        else:
            L = 0

        # Normalize weights.
        weights = weights / np.sum(weights)

        rng = self.search_space.get_rng("numpy")
        idx = rng.choice(list(range(L, self.bins + 1)), N, p=weights)

        return idx

    def __call__(self, N, objectives, remaining, new=None):
        """Samples N test indices corresponding to the given test objectives.
        The sampling is done by picking a bin and uniformly randomly selecting
        a test from the bin. The probability of picking each bin is computed
        via the function bin_sample."""

        if len(objectives) == 1:
            return np.array([0])

        if new is None:
            new = []

        self._setup_first_call(remaining)

        rng = self.search_space.get_rng("numpy")
        self.current_shift_value = self.shift(remaining)

        # Find the objective value E such that proportion Q of the observed
        # objective mass is below E.
        # ---------------------------------------------------------------------
        Q = self.quantile(remaining)
        O = np.sort(objectives)
        K = len(O)
        M = O[:max(1, int(Q*len(objectives)))][-1]
        m = O[0]
        # Make M slightly bigger based on the number of tests. This comes from
        # the unbiased estimate for the support of uniform random variable. We
        # do analogously for the minimum.
        M = min(1, ((K + 1) / K) * M)
        m = max(0, ((K - 1) / K) * m)
        if self.zero_minimum:
            m = 0.0

        # Put the tests into bins. 
        # ---------------------------------------------------------------------
        test_bins = {i: [] for i in range(self.bins + 1)}
        for n, o in enumerate(objectives):
            test_bins[self.get_bin(o, M, m)].append(n)

        # Sample the bins.
        # ---------------------------------------------------------------------
        sample = np.zeros(N, dtype=int)
        # First include the new tests with high probability if and only if they
        # have low objective.
        K = min(len(new), N)
        C = self.bin_sample(K, test_bins)
        c = 0
        for n in range(K):
            if self.get_bin(objectives[new[n]], M, m) <= C[n]:
                sample[c] = new[n]
                c += 1
        # Then sample the remaining tests.
        available = {n: v.copy() for n, v in test_bins.items()}
        for n, bin_idx in enumerate(self.bin_sample(max(0, N - c), test_bins)):
            # If a bin is empty, try one greater bin. Eventually the sink bin
            # is sampled.
            while len(available[bin_idx]) == 0:
                bin_idx += 1
                bin_idx = bin_idx % (self.bins + 1)
            # Select a test from a bin uniformly randomly.
            idx = rng.choice(available[bin_idx])
            # Remove the test from the set of available tests if the same test
            # cannot be sampled multiple times.
            if not self.sample_with_replacement:
                available[bin_idx].remove(idx)
            sample[c + n] = idx

        return sample


class Quantile_Sampler(SBST_Sampler):
    """The quantile sampler is based on similar ideas as the SBST sampler. The
    differences are in bin weights selection and in the placing of tests into
    the bins. The bin weights are here simply linear: the bins from lowest to
    highest objective get respectively the weights B, B - 1, ..., 1 where B is
    the number of bins. If no test has been placed into a bin, its weight is
    set to 0. The tests are placed into the bins as follows. First the interval
    [m, M] is computed. The number m is the minimum objective multiplied by
    (N-1)/N where N is the number of tests. The number M equals (N+1)/N * O
    where O is the objective value such that proportion Q of the objective
    values are less than O. The interval [m, M] is split into B bins, and the
    tests are placed into the bins according to their objective. Tests with
    objective not in the interval [m, M] go to a special sink bin which is only
    sampled when no other bin can be sampled. The number Q is decreased
    linearly from the given start value to the given end value according to the
    variable remaining."""

    default_parameters = {
        "bins": 10,
        "sample_with_replacement": False,
        "omit_initial_empty": True,
        "quantile_start": 0.5,
        "quantile_end": 0.1,
        "zero_minimum": True
    }

    def __init__(self, parameters=None):
        # Fake some parameters, so we can inherit.
        parameters["shift_function"] = "linear"
        parameters["shift_function_parameters"] = {"initial": 0, "final": 3}
        super().__init__(parameters)

    def bin_sample(self, N, bins):
        """Samples N bin indices."""

        if N == 0: return []

        # Initial unnormalized weights. The weights are 1, 2, ..., self.bins in
        # reverse order. The sink bin has weight 0.
        weights = list(range(self.bins, 0, -1)) + [0]
        """
        # If a bin has no tests, we set its sampling probability to 0.
        for n in range(self.bins):
            if len(bins[n]) == 0:
                weights[n] = 0.0
        """

        # Normalize weights.
        weights = weights / np.sum(weights)

        # Select bin indices based on the weights.
        rng = self.search_space.get_rng("numpy")
        idx = rng.choice(list(range(self.bins + 1)), N, p=weights)

        return idx


class Random_Bin_Sampler(SBST_Sampler):
    """A sampler that has uniformly random weights on bins. Used for
    establishing baseline results. The settings work as in SBST_Sampler."""

    default_parameters = {
        "bins": 10,
        "sample_with_replacement": False,
        "omit_initial_empty": True,
        "quantile_start": 0.5,
        "quantile_end": 0.1,
        "zero_minimum": True
    }

    def __init__(self, parameters=None):
        if parameters is None: parameters = {}
        # Fake some parameters, so we can inherit.
        parameters["shift_function"] = "linear"
        parameters["shift_function_parameters"] = {"initial": 0, "final": 3}
        super().__init__(parameters)

    def bin_sample(self, N, bins):
        """Samples N bin indices."""

        if N == 0: return []

        # Equal weights on all bins except the sink bin that has weight 0.
        weights = [1] * self.bins + [0]
        # If a bin has no tests, we set its sampling probability to 0.
        for n in range(self.bins):
            if len(bins[n]) == 0:
                weights[n] = 0.0

        # Normalize weights.
        weights = weights / np.sum(weights)

        # Select bin indices based on the weights.
        rng = self.search_space.get_rng("numpy")
        idx = rng.choice(list(range(self.bins + 1)), N, p=weights)

        return idx


class Random_Sampler(Sampler):
    """A sampler that samples the given tests uniformly randomly, that is, the
    tests are not binned as in Random_Sampler."""

    default_parameters = {}

    def __call__(self, N, objectives, remaining, new=None):
        rng = self.search_space.get_rng("numpy")
        return rng.choice(list(range(len(objectives))), N)

