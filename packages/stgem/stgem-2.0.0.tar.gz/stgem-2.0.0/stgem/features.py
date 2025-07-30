import copy

import numpy as np

from stgem.exceptions import FeatureNotFoundError


class Feature:
    """Base class for the feature."""

    def __init__(self, name=""):
        """Initialize a Feature object.

        Args:
            name (str, optional): The name of the feature. Default is an empty string.
        """

        self._name = name
        self._value = None

    @property
    def dimension(self):
        """Return the dimension of the feature. This can be extended in more specific subclasses."""
        return 1

    @property
    def range(self):
        """Return the range of the feature. This can be extended in more specific subclasses."""
        return None

    def pack(self):
        """
        Pack self into a vector of length self.dimension of reals in the interval [-1, 1].

        Raises:
            NotImplementedError: This method should be implemented by subclasses.
        """

        raise NotImplementedError

    def unpack(self, value):
        """
        Unpack an array of length self.dimension of reals in the interval [-1, 1] and set the unpacked values as feature values.

        Args:
            value (array-like): The array of values to unpack.

        Raises:
            NotImplementedError: This method should be implemented by subclasses.
        """

        raise NotImplementedError

    def set(self, value):
        """
        Set the value of the feature.

        This method must be specifically implemented in more concrete subclasses depending on the structure of the feature.

        Args:
            value (any): The value to set for the feature.

        Raises:
            NotImplementedError: This method should be implemented by subclasses.
        """
        raise NotImplementedError

    def get(self):
        """
        Get the value of the feature.

        Returns:
            any: The value of the feature.
        """
        return self._value

    @property
    def name(self):
        """Return the name of the feature."""
        return self._name


class FeatureVector(Feature):
    """A collection of features"""

    def __init__(self, name="", values=None, features=None):
        """
        Initialize the FeatureVector feature.

        Args:
            name (str, optional): The name of the feature vector. Default is an empty string.
            values (iterable, optional): The initial values for the features. Default is None.
            features (list of Feature): A list of Feature objects to be included in the feature vector. Must not be None.

        Raises:
            AssertionError: If features are not provided or are not instances of Feature, or if feature names are not unique.
        """

        super().__init__(name)

        # Ensure features are provided and they are instances of Feature class
        assert features is not None
        assert all([isinstance(f, Feature) for f in features]), "Incorrect feature type"
        assert len(features) == len(set([f._name for f in features])), "Feature names should be unique"

        self._features = features

        if values is not None:
            # Set feature values based on the given values.
            self.set(values)

    @property
    def features(self):
        """
        Return a list of feature objects from self.

        Returns:
            list: The list of feature objects.
        """
        return self._features

    @property
    def names(self):
        """
        Return the feature names in order.

        Returns:
            list: The list of feature names.
        """

        return [f._name for f in self._features]

    def feature(self, name: str) -> Feature:
        """
        Returns the feature with the given name.

        Args:
            name (str): The name of the feature to retrieve.

        Returns:
            Feature: The feature object with the specified name.

        Raises:
            ValueError: If the feature name is not a string.
            FeatureNotFoundError: If the feature with the given name is not found.
        """

        if not isinstance(name, str):
            raise ValueError("Feature names should be strings.")

        ns = name.split(".")
        try:
            idx = self.names.index(ns[0])
            if len(ns) > 1:
                return self._features[idx].feature(".".join(ns[1:]))
            else:
                return self._features[idx]
        except ValueError:
            raise FeatureNotFoundError(name)

    @property
    def ranges(self):
        """Return the ranges of all features as a dictionary."""
        return {f._name: f.range for f in self._features}

    @property
    def dimension(self):
        """Return the dimension of self which is the dimension of the corresponding flattened vector."""

        return sum([c.dimension for c in self._features])

    def __len__(self):
        """Return the number of features."""
        return len(self._features)

    def __iter__(self):
        """Return an iterator over the features."""
        return iter(self._features)

    def __str__(self):
        """Return a string representation of the feature vector."""
        return "FeatureVector(\'{}\', ".format(self._name) + ", ".join(str(f) for f in self._features) + ")"

    def __call__(self, name=""):
        """Return a copy of the current feature vector"""

        return FeatureVector(name=name, features=copy.deepcopy(self._features))

    def __contains__(self, key):
        """
        Checks if a feature with the given name exists in the feature vector.

        Args:
            key (str): The name of the feature to check.

        Returns:
            bool: True if the feature exists, False otherwise.

        Raises:
            ValueError: If the feature name is not a string.
        """

        if not isinstance(key, str):
            raise ValueError("Feature names should be strings.")

        ns = key.split(".")
        try:
            idx = self.names.index(ns[0])
            if len(ns) > 1:
                return self._features[idx][".".join(ns[1:])]
            else:
                return True
        except ValueError:
            return False

    def __getattr__(self, key):
        """
        Support accessing feature values using the dot notation.

        Args:
            key (str): The name of the feature to access.

        Returns:
            any: The value of the feature.

        Raises:
            AttributeError: If the feature is not found.
        """

        try:
            return self.__getattribute__(key)
        except AttributeError:
            try:
                names = [c._name for c in self.__dict__["_features"]]
                idx = names.index(key)
            except (ValueError, KeyError):
                raise AttributeError(key)

            if isinstance(self._features[idx], FeatureVector):
                return self._features[idx]
            else:
                return self._features[idx]._value

    def __setattr__(self, key, value):
        """
        Support setting feature values using the dot notation.

        Args:
            key (str): The name of the feature to set.
            value (any): The value to set for the feature.

        Raises:
            AttributeError: If the feature is not found.
        """

        if key in ["_value", "_features", "_name"]:
            self.__dict__[key] = value
        else:
            try:
                idx = self.names.index(key)
            except ValueError:
                raise AttributeError(key)
            self._features[idx].set(value)

    def __getitem__(self, key):
        """
        Support accessing feature values using the bracket notation. This also supports accessing feature values by their index.

        Args:
            key (int or str): The index or name of the feature to access.

        Returns:
            any: The value of the feature.

        Raises:
            AssertionError: If the index is out of bounds.
            FeatureNotFoundError: If the feature is not found.
            KeyError: If the key is not an int or str.
        """

        if isinstance(key, int):
            assert key >= 0 and key <= len(self._features)
            if isinstance(self._features[key], FeatureVector):
                return self._features[key]
            else:
                return self._features[key]._value

        elif isinstance(key, str):
            ns = key.split(".")
            try:
                idx = self.names.index(ns[0])
            except ValueError:
                raise FeatureNotFoundError(ns[0])
            if len(ns) > 1:
                return self._features[idx].__getitem__(".".join(ns[1:]))
            else:
                if isinstance(self._features[idx], FeatureVector):
                    return self._features[idx]
                else:
                    return self._features[idx]._value
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """
        Support setting feature values using the bracket notation. This also supports setting feature values by their index.

        Args:
            key (int or str): The index or name of the feature to set.
            value (any): The value to set for the feature.

        Raises:
            AssertionError: If the index is out of bounds.
            FeatureNotFoundError: If the feature is not found.
            KeyError: If the key is not an int or str.
        """

        if isinstance(key, int):
            assert key >= 0 and key <= len(self._features)
            self._features[key].set(value)
        elif isinstance(key, str):
            ns = key.split(".")
            try:
                idx = self.names.index(ns[0])
            except ValueError:
                raise FeatureNotFoundError(ns[0])
            if len(ns) > 1:
                return self._features[idx].__setitem__(".".join(ns[1:]), value)
            else:
                self._features[idx].set(value)
        else:
            raise KeyError(key)

    def set(self, values):
        """
        Set the values for each feature in the feature vector.

        Args:
            values (iterable): The values to set for the features.

        Returns:
            self: The updated FeatureVector object.

        Raises:
            ValueError: If the values are not iterable or if the number of values does not match the number of features.
        """
        try:
            iter(values)
        except TypeError:
            raise ValueError("Values to be set must be iterable.")

        if len(values) != len(self._features):
            raise ValueError("Cannot set {} features with {} values.".format(len(self._features), len(values)))

        for v, f in zip(values, self._features):
            f.set(v)

        return self

    def get(self):
        """Get features in list format."""
        return self.to_list()

    def set_packed(self, values):
        """
        Set the packed values for the feature vector.

        Args:
            values (iterable): The packed values to set.
        """
        self.unpack(values)

    def to_dict(self):
        """Return a dictionary with the feature vector values."""

        r = {}
        for f in self._features:
            if isinstance(f, FeatureVector):
                r[f._name] = f.to_dict()
            else:
                r[f._name] = f._value
        return r

    def to_list(self):
        """Return a list with the feature vector values."""

        r = []
        for f in self._features:
            if isinstance(f, FeatureVector):
                r.append(f.to_list())
            else:
                r.append(f._value)
        return r

    def __or__(self, other):
        """
        Merge the feature vector with another feature vector to obtain a new feature vector.

        Args:
            other (FeatureVector): The other feature vector to merge with.

        Returns:
            FeatureVector: A new feature vector that combines both feature vectors.
        """

        d = {}
        for f in self:
            d[f._name] = copy.deepcopy(f)
        for f in other:
            d[f._name] = copy.deepcopy(f)

        features = list(d.values())
        
        return FeatureVector(name=self._name, features=features)

    def pack(self):
        """
        Pack the feature vector into a single flattened array of values, with each value from the original ones normalized to [-1, 1].

        Returns:
            np.ndarray: A flattened array of packed values.
        """
        r = np.zeros(self.dimension)
        i = 0
        for f in self._features:
            n = f.pack()
            r[i:i + f.dimension] = n
            i += f.dimension
        return r

    def unpack(self, nv):
        """
        Unpack the feature vector into a single flattened array of values, with each value from the normalized one [-1, 1] to the original ones.

        Args:
            nv (iterable): The flattened array of packed values.

        Returns:
            self: The updated FeatureVector object.
        """
        i = 0
        for f in self._features:
            if f.dimension == 1:
                v = nv[i]
            else:
                v = nv[i:i + f.dimension]
            f.unpack(v)
            i += f.dimension
        return self

    def flatten_to_list(self):
        """Return a flattened list of all Feature objects, including nested ones."""
        features = []
        self._flatten_helper(self, features)
        return features

    @staticmethod
    def _flatten_helper(fv, features):
        """Helper function to flatten the features of a FeatureVector."""
        for f in fv.features:
            if isinstance(f, FeatureVector):
                FeatureVector._flatten_helper(f, features)
            else:
                features.append(f)


class RealVector(Feature):
    """A feature that is a vector of real numbers."""

    def __init__(self, dimension, min_value=None, max_value=None, name="", clip=False):
        """
        Initialize the RealVector feature.

        Args:
            dimension (int): The dimension of the real vector.
            min_value (float, optional): The minimum value for the elements of the vector. Default is None.
            max_value (float, optional): The maximum value for the elements of the vector. Default is None.
            name (str, optional): The name of the feature. Default is an empty string.
            clip (bool, optional): Whether to clip the values to the range [min_value, max_value]. Default is False.

        Raises:
            AssertionError: If dimension is not an integer.
            ValueError: If the minimum value exceeds the maximum value.
        """
        super().__init__(name)

        assert isinstance(dimension, int), "Dimension must be an integer"

        self._dimension = dimension
        self._min_value = min_value
        self._max_value = max_value
        self._has_range = self._min_value is not None and self._max_value is not None
        self._clip = clip
        if self._has_range and self._min_value > self._max_value:
            raise ValueError(
                "The minimum value {} cannot exceed the maximum value {}.".format(self._min_value, self._max_value))

    def __str__(self):
        """Return a string representation of the real vector."""
        return "RealVector(\'{}\', {}, [{}, {}])".format(self._name, self.__dimension, self._min_value, self._max_value)

    @property
    def dimension(self):
        """Return the dimension of the real vector."""
        return self._dimension

    @property
    def range(self):
        """Return the range of the real vector."""
        if self._has_range:
            return [self._min_value, self._max_value]
        else:
            return None

    def pack(self):
        """
        Pack the real vector into a flattened array of values in the interval [-1, 1].

        Returns:
            np.ndarray: A flattened array of packed values.

        Raises:
            Exception: If value range information is not set or no value is set.
        """

        if not self._has_range:
            raise Exception("Cannot pack without value range information.")

        if self._value is None:
            raise ValueError("Cannot pack as no value has been set.")

        x = np.array(self._value)
        M = self._max_value
        m = self._min_value
        return 2 * ((x - m) / (M - m)) - 1

    def unpack(self, x):
        """
        Unpack a flattened array of values in the interval [-1, 1] into the real vector.

        Args:
            x (iterable): The array of packed values.

        Raises:
            Exception: If value range information is not set.
        """
        if not self._has_range:
            raise Exception("Cannot unpack without value range information.")

        if np.isscalar(x):
            x = [x]
        x = np.array(x)
        M = self._max_value
        m = self._min_value
        self._value = 0.5 * ((M - m) * x + M + m)

    def set(self, value):
        """Set the value of the real vector, by default, clip is false and it
        will make sure the values are in the range of the real vector.

        Args:
            value (iterable): The values to set for the real vector.

        Raises:
            ValueError: If values are not iterable or do not match the dimension of the vector.
        """

        try:
            iter(value)
        except TypeError:
            raise ValueError("Values must be iterable.")
        v = np.array(value)
        if len(v) != self.dimension:
            raise ValueError("Expected a value of dimension {} got {}.".format(self.dimension, len(v)))
        if self._has_range and self._clip:
            np.clip(v, self._min_value, self._max_value, out=v)

        self._value = v


class Signal(Feature):
    """A feature that represents a raw signal (real-valued function of time)
    that can have arbitrary many samples. A signal cannot be packed or
    unpacked."""

    def __init__(self, name="", min_value=None, max_value=None, sampling_period=1, clip=False):
        """Initialize a Signal feature.

        Args:
            name (str, optional): Name of the signal. Defaults to empty.
            min_value (Union[int,float], optional): Minimum value of signal. Defaults to Non.
            max_value (Union[int,float], optional): Maximum value of signal. Defaults to None.
            sampling_period (Union[int,float], optional): How frequently to sample the signal. Defaults to 1.
            clip (bool, optional): Indicates if canonized values should be clipped to range. Defaults to False."""

        super().__init__(name)
        self._min_value = min_value
        self._max_value = max_value
        self._has_range = self._min_value is not None and self._max_value is not None
        self._clip = clip
        self._sampling_period = sampling_period

    def __str__(self):
        """Return a string representation of the signal."""

        return "Signal(\'{}\', [{}, {}])".format(self._name, self._min_value, self._max_value)

    @property
    def dimension(self):
        """Return the dimension of the signal, which is 1 (single 2D-array of
        timestamps and values)."""

        return 1

    @property
    def range(self):
        """Return the range of the signal."""

        if self._has_range:
            return [self._min_value, self._max_value]
        else:
            return None

    def pack(self):
        """
        Pack the signal.

        Raises:
            Exception: A signal cannot be packed.
        """

        # We could in principle pack a signal (the only problem for unpacking
        # is the unspecified length), but we do not see a current use for this
        # feature, so we skip implementing it.
        raise Exception("A signal cannot be packed.")

    def unpack(self, x):
        """
        Unpack the signal.

        Raises:
            Exception: A signal cannot be unpacked.
        """

        raise Exception("A signal cannot be unpacked.")

    def set(self, values):
        """
        Set the value of the signal.

        Args:
            values (list or list of lists): The values to set. Can be a single list of values or a list of timestamps and values.

        Raises:
            ValueError: If the values do not match the expected format.
        """
        # Convert timestamps.
        if np.isscalar(values[0]):

            # A single list of numbers. We interpret it as the samples and
            # create timestamps automatically according to the sampling period.
            t = self._sampling_period * np.arange(len(values))
            v = np.array(values)
        else:
            t = np.array(values[0])
            v = np.array(values[1])

        # Convert values.
        # We truncate the samples to timestamp length.
        v = v[:len(t)]
        if self._has_range and self._clip:
            np.clip(v, self._min_value, self._max_value, out=v)

        self._value = np.empty(shape=(2, len(t)))
        self._value[0, :] = t
        self._value[1, :] = v

    def synthesize_signal(self):
        return self._value


class SignalRepresentation(RealVector):
    """Base class for signal representations that can be synthesized to signals."""

    def __init__(self, N_control_points=0, sampling_period=1, min_value=None, max_value=None, name="", clip=False):
        """
        Initialize the SignalRepresentation object.

        Args:
            N_control_points (int): Number of control points.
            min_value (float, optional): Minimum value the signal can take at any point. Defaults to None.
            max_value (float, optional): Maximum value the signal can take at any point. Defaults to None.
            name (str, optional): Name of the signal. Defaults to "".
            clip (bool, optional): Indicates if canonized values should be clipped to range. Defaults to False.
        """
        super().__init__(dimension=N_control_points, min_value=min_value, max_value=max_value, name=name, clip=clip)
        self._sampling_period = sampling_period
        self._N_control_points = N_control_points

    def __str__(self):
        return "SignalRepresentation(\'{}\', {}, [{}, {}])".format(self._name, self.__dimension, self._min_value,
                                                                   self._max_value)

    def synthesize_signal(self):
        """
        Synthesize the signal from the control points.

        Raises:
            NotImplementedError: This method should be implemented by subclasses.
        """
        raise NotImplementedError()


class PiecewiseConstantSignal(SignalRepresentation):
    """Represents a piecewise constant signal."""

    # We assume that the signal begins from time 0.

    def __init__(self, piece_durations, sampling_period=1, min_value=None, max_value=None, name="", clip=False,
                 round_duration=True):
        """
        Initialize the PiecewiseConstantSignal object.

        Args:
            piece_durations (list[int]): A list of how long each piece of the signal is.
            sampling_period (float): Duration between time samples.
            min_value (float, optional): Minimum value the signal can take at any point. Defaults to None.
            max_value (float, optional): Maximum value the signal can take at any point. Defaults to None.
            name (str, optional): Name of the signal. Defaults to "".
            clip (bool, optional): Indicates if control points should be clipped to range. Defaults to False.
            round_duration (bool, optional): Indicates if the summed durations should be rounded to the nearest integer. Defaults to True.
        """
        super().__init__(N_control_points=len(piece_durations), sampling_period=sampling_period, min_value=min_value,
                         max_value=max_value, name=name, clip=clip)
        self._piece_durations = piece_durations
        self._round_duration = round_duration

    def __str__(self):
        """Return a string representation of the piecewise constant signal."""

        duration = sum(self._piece_durations)
        if self._round_duration:
            duration = round(duration, 0)
        return "PiecewiseConstantSignal(\'{}\', [{}, {}], control_points={}, duration={}, piece_durations={}, sampling_period={})".format(
            self._name, self._min_value, self._max_value, self._N_control_points, duration, self._piece_durations,
            self._sampling_period)

    def synthesize_signal(self):
        """
        Synthesize a piecewise constant signal (timestamps and values) from the control points.

        Returns:
            list: A list containing two numpy arrays:
                - Timestamps: Array of timestamps corresponding to the start of each piece.
                - Values: Array of values for each piece in the signal.

        Raises:
            ValueError: If the number of control points does not match the expected number.
        """

        control_points = self._value

        if len(control_points) != self._N_control_points:
            raise ValueError(
                "Expected {} control points instead of {}.".format(self._N_control_points, len(control_points)))

        total_duration = sum(self._piece_durations)
        # We round to the nearest integer to avoid problems when the piece
        # lengths do not exactly sum to an integer.
        if self._round_duration:
            total_duration = round(total_duration, 0)
        N_samples = int(total_duration / self._sampling_period) + 1

        # Timestamps.
        timestamps = self._sampling_period * np.arange(N_samples)

        # Values.
        values = np.zeros(N_samples)
        i = 0
        offset = 0
        for t in range(N_samples):
            if self._sampling_period * t - offset >= self._piece_durations[i]:
                offset += self._piece_durations[i]
                i += 1
            if t < N_samples - 1:
                values[t] = control_points[i]
            else:
                values[t] = control_points[-1]

        return [timestamps, values]


class PiecewiseLinearSignal(SignalRepresentation):
    """Represents a continuous function made up of linear pieces."""

    # We assume that the signal begins from time 0.

    def __init__(self, piece_durations, sampling_period=1, min_value=None, max_value=None, name="", clip=False,
                 round_duration=True):
        super().__init__(N_control_points=len(piece_durations) + 1, sampling_period=sampling_period,
                         min_value=min_value, max_value=max_value, name=name, clip=clip)
        self._piece_durations = piece_durations
        self._round_duration = round_duration

    def __str__(self):
        duration = sum(self._piece_durations)
        if self._round_duration:
            duration = round(duration, 0)
        return "PiecewiseLinearSignal(\'{}\', [{}, {}], control_points={}, duration={}, piece_durations={}, sampling_period={})".format(
            self._name, self._min_value, self._max_value, self._N_control_points, duration, self._piece_durations,
            self._sampling_period)

    def synthesize_signal(self):
        control_points = self._value

        if len(control_points) != self._N_control_points:
            raise ValueError(
                "Expected {} control points instead of {}.".format(self._N_control_points, len(control_points)))

        total_duration = sum(self._piece_durations)
        # We round to the nearest integer to avoid problems when the piece
        # lengths do not exactly sum to an integer.
        if self._round_duration:
            total_duration = round(total_duration, 0)
        N_samples = int(total_duration / self._sampling_period) + 1

        # Timestamps.
        timestamps = self._sampling_period * np.arange(N_samples)

        # Values.
        values = np.zeros(N_samples)
        i = 0
        offset = 0
        a = (control_points[1] - control_points[0]) / self._piece_durations[i]
        b = control_points[0]
        for t in range(N_samples):
            # Update in which segment we are in.
            if self._sampling_period * t - offset >= self._piece_durations[i]:
                offset += self._piece_durations[i]
                i += 1
                if offset < total_duration:
                    a = (control_points[i + 1] - control_points[i]) / self._piece_durations[i]
                    b = control_points[i]
                else:
                    a = (control_points[-2] - control_points[-1]) / self._piece_durations[-1]
                    b = control_points[-1]

            # Relative time in the current segment.
            T = self._sampling_period * t - offset

            # Sample from segment i.
            v = a * T + b
            values[t] = v

        return [timestamps, values]


class Real(Feature):
    """A real number (float)."""

    def __init__(self, name="", min_value=None, max_value=None, clip=False):
        super().__init__(name)
        """
        Initialize the Real object.

        Args:
            name (str, optional): Name of the real. Defaults to empty string.
            min_value (float, optional): Minimum value this real can be. Defaults to None.
            max_value (float, optional): Maximum value this real can be. Defaults to None.
            clip (bool, optional): Whether the set value should be clipped into the range, or raise a ValueError. Defaults to False.

        Raises:
            ValueError: If min_value is greater than max_value.
        """
        self._min_value = min_value
        self._max_value = max_value
        self._has_range = self._min_value is not None and self._max_value is not None
        self._clip = clip
        if self._has_range and self._min_value > self._max_value:
            raise ValueError(
                "The minimum value {} cannot exceed the maximum value {}.".format(self._min_value, self._max_value))

    @property
    def range(self):
        """Return the range of the real value."""

        if self._has_range:
            return [self._min_value, self._max_value]
        else:
            return None

    def __str__(self):
        """Return a string representation of the real value."""

        return "Real(\'{}\', [{}, {}])".format(self._name, self._min_value, self._max_value)

    def pack(self):
        """
        Pack the real value into the interval [-1, 1].

        Returns:
            float: The packed value.

        Raises:
            Exception: If value range information is not set.
            ValueError: If no value is set.
        """

        if not self._has_range:
            raise Exception("Cannot pack without value range information.")

        if self._value is None:
            raise ValueError("Cannot pack as no value has been set.")

        M = self._max_value
        m = self._min_value
        return 2 * ((self._value - m) / (M - m)) - 1

    def unpack(self, x):
        """
        Unpack a value from the interval [-1, 1] to the real value range.

        Args:
            x (float): The value to unpack.

        Raises:
            Exception: If value range information is not set.
        """

        if not self._has_range:
            raise Exception("Cannot unpack without value range information.")

        M = self._max_value
        m = self._min_value
        self._value = 0.5 * ((M - m) * x + M + m)

    def set(self, value):
        """Set the value of the real number."""

        value = float(value)
        if self._has_range and self._clip:
            value = min(self._max_value, max(self._min_value, value))
        if self._has_range and value < self._min_value:
            raise ValueError(
                "Cannot set a value '{}' that is smaller than the minimum value '{}'.".format(value, self._min_value))

        self._value = value


def find_min_sampling_period(fv):
    """Finds the minimum sampling period of the features of the given feature
    vector if it exists. Otherwise return None."""

    m = None
    for feature in fv.flatten_to_list():
        if isinstance(feature, SignalRepresentation):
            if m is None:
                m = feature._sampling_period
            else:
                m = min(m, feature._sampling_period)

    return m
