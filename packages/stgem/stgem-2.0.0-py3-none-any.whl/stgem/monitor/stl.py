from typing import Union

import numpy as np

import stgem.monitor.pystl.robustness as STL
from stgem.features import FeatureVector, Signal, SignalRepresentation, find_min_sampling_period
from stgem.monitor import Monitor
from stgem.monitor.pystl.parser import parse


class STLRobustness(Monitor):
    """Provides scaled and unscaled STL robustness for an STL formula.

    The scaling is done according to the effective range as described in J.
    Peltomäki, I. Porres: Requirement falsification for cyber-physical systems
    using generative models (2023)."""

    """
    By default the robustness is not scaled, but if scale is True and variable
    ranges have been specified for the signals, then the robustness is scaled to
    [0, 1].

    The parameter strict_horizon_check controls if an exception is raised if
    the signal is too short to determine the truth value of the formula.
    If False and the signal is too short, then the best estimate for the
    robustness is returned, but this value might be incorrect if the signal is
    augmented with appropriate values.

    The parameter epsilon is a value which is added to positive robustness
    values. A positive epsilon value thus makes falsification harder. This is
    sometimes useful if the observed values are very close to 0 but positive
    and the machine learning models consider such a value to be 0. Raising the
    bar a bit can encourage the models to work harder and eventually produce
    robustness which is nonpositive."""

    def __init__(self, formula: str | STL.STL, default_sampling_period: float | None = None, default_strict_horizon_check=True, scale=False):
        super().__init__()

        self.default_sampling_period = default_sampling_period
        self.default_scale = scale
        self.default_strict_horizon_check = default_strict_horizon_check

        if isinstance(formula, STL.STL):
            self.formula = formula
            self.formula_str = "<STL Tree>"
        else:
            self.formula = parse(formula)
            self.formula_str = formula

        self._setup_formula()

    def __str__(self):
        return self.formula_str

    def _setup_formula(self):
        self.horizon = self.formula.horizon

        # Find out variables of the formula and time bounded formulas.
        self.formula_variables = []
        self.time_bounded = []
        for node in self.formula:
            if isinstance(node, STL.Signal) and node.name not in self.formula_variables:
                self.formula_variables.append(node.name)

            if isinstance(node, (STL.Global, STL.Until)):
                self.time_bounded.append(node)
            if isinstance(node, STL.Finally):
                self.time_bounded.append(node)
                self.time_bounded.append(node.formula_robustness.formulas[0])

        """
        One problem with STL usage is that the differences between timestamps
        of different signals can be very small and variable. We cannot simply
        take the minimum difference and use this as a sampling step because
        this can lead into very small time steps and thus to very long
        augmented signals. Very small time steps could be unnecessary too as
        the STL formula might only refer to relatively big time steps.

        Our solution to the above is to figure out the smallest timestep
        referred to in the STL formula and divide this into K equal pieces
        (currently K = 10). This determines a sampling period and we sample all
        signals according to this sampling period (if an even lower sampling
        period was requested, we use this). This can mean discarding signal
        values or augmenting a signal. Currently we augment a signal by
        assuming a constant value.
        """

        K = 10
        smallest = 1
        for x in self.time_bounded:
            if x.lower_time_bound > 0 and x.lower_time_bound < smallest:
                smallest = x.lower_time_bound
            if x.upper_time_bound > 0 and x.upper_time_bound < smallest:
                smallest = x.upper_time_bound
        smallest /= K
        if self.default_sampling_period is not None:
            self.default_sampling_period = min(smallest, self.default_sampling_period)
        else:
            self.default_sampling_period = smallest

    def _adjust_time_bounds(self, horizon, sampling_period=None):
        sampling_period = sampling_period if sampling_period is not None else self.default_sampling_period
        for x in self.time_bounded:
            x.old_lower_time_bound = x.lower_time_bound
            x.old_upper_time_bound = x.upper_time_bound
            x.lower_time_bound = int(x.lower_time_bound / sampling_period)
            x.upper_time_bound = int(x.upper_time_bound / sampling_period)
        return int(horizon / sampling_period)

    def _reset_time_bounds(self):
        for x in self.time_bounded:
            x.lower_time_bound = x.old_lower_time_bound
            x.upper_time_bound = x.old_upper_time_bound

    def _evaluate_signal_fv(self, fv: FeatureVector, sampling_period: float | None = None,
                            strict_horizon_check: bool = True, scale: bool = False) -> float:
        ranges = fv.ranges

        # Create a suitable dictionary to be passed to _evaluate_signal_dict.
        args = {}
        for var in self.formula_variables:
            if not var in fv:
                raise ValueError("Variable '{}' not found in the given feature vector.".format(var))
            if scale and ranges[var] is None:
                raise ValueError(
                    "STL robustness scaling is enabled but no range is provided for variable '{}'.".format(var))

            if isinstance(fv.feature(var), Signal):
                timestamps = fv[var][0, :]
                values = fv[var][1, :]
            elif isinstance(fv.feature(var), SignalRepresentation):
                timestamps, values = fv.feature(var).synthesize_signal()
            elif np.isscalar(fv[var]):
                # For a scalar, fake a signal with single timestamp 0.
                timestamps = [0]
                values = [fv[var]]
            else:
                raise ValueError("Unsupported feature vector feature value.")

            args[var] = [timestamps, values, ranges[var]]

        return self._evaluate_signal_dict(args, sampling_period=sampling_period,
                                          strict_horizon_check=strict_horizon_check, scale=scale)

    def _evaluate_signal_dict(self, d, sampling_period: float, strict_horizon_check: bool = True,
                              scale: bool = False) -> float:
        """
        Here we find the robustness at time 0.

        We assume that the user guarantees that time is increasing. Floating
        point numbers and timestamp search do not go well together: we have 0.1
        != 0.1000000001 etc. This can lead to erroneous results. The solution
        is to use integer timestamps. Using integer timestamps then requires
        scaling the time intervals occurring in the formula formulas.
        """

        signal_ranges = {} if scale else None
        # Create ranges and trajectories with common timestamps for all signals.
        args = []
        for k, v in d.items():
            args.append(k)
            if np.isscalar(v):
                # The variable value is a single scalar. We transform it to a
                # signal with one timestamp 0.
                v = [[0], [v], None]
                # We cannot scale when converting from a scalar as there is no
                # range information.
                if scale:
                    raise Exception("Scaling of robustness values requested but no scale available.")
            elif len(v) == 2:
                if np.isscalar(v[0]):
                    # The variable value is a single scalar with range
                    # information. We transform it to a signal with one
                    # timestamp 0.
                    v = [[0], [v[0]], v[1]]
                else:
                    # The variable contains a proper signal with timestamps but
                    # without range information. We just add undefined ranges.
                    v = [v[0], v[1], None]
                    if scale:
                        raise Exception("Scaling of robustness values requested but no scale available.")
            elif len(v) != 3:
                raise ValueError("Unsupported data for variable '{}'.".format(k))

            args.append(v[0])
            args.append(v[1])
            if scale:
                signal_ranges[k] = v[2]

        trajectories = STL.Traces.from_mixed_signals(*args, sampling_period=sampling_period)
        robustness_timestamps = trajectories.timestamps

        # Use integer timestamps.
        trajectories.timestamps = np.arange(len(trajectories.timestamps))

        # Adjust time bounds and the horizon.
        horizon = self._adjust_time_bounds(self.horizon)

        # Allow slight inaccuracy in horizon check.
        if strict_horizon_check and horizon - 1e-2 > trajectories.timestamps[-1]:
            adjusted_max_time = int(trajectories.timestamps[-1] * sampling_period)
            self._reset_time_bounds()
            raise Exception(
                "The horizon {} of the formula is too long compared to the final signal timestamp {}. The robustness cannot be computed.".format(
                    self.horizon, adjusted_max_time))

        robustness_signal, robustness_range, effective_range_signal = self.formula.eval(trajectories,
                                                                                        signal_ranges=signal_ranges)

        # Reset time bounds. This allows reusing the formulas.
        self._reset_time_bounds()

        return robustness_timestamps, robustness_signal, robustness_range, effective_range_signal

    def robustness(self, obj: FeatureVector | dict, sampling_period: float = None, strict_horizon_check: bool = None,
                   scale: bool = None):
        """Compute the (traditional) STL robustness signal."""

        if strict_horizon_check is None:
            strict_horizon_check = self.default_strict_horizon_check
        if sampling_period is None:
            sampling_period = self.default_sampling_period
        if scale is None:
            scale = self.default_scale

        if isinstance(obj, FeatureVector):
            return self._evaluate_signal_fv(obj, sampling_period=sampling_period,
                                            strict_horizon_check=strict_horizon_check, scale=scale)
        else:
            return self._evaluate_signal_dict(obj, sampling_period=sampling_period,
                                              strict_horizon_check=strict_horizon_check, scale=scale)

    def __call__(self, obj: FeatureVector | dict, sampling_period: float = None, strict_horizon_check: bool = None,
                 scale: bool = None) -> float:
        """Return a possibly scaled robustness at time 0."""

        _, robustness_signal, _, effective_range_signal = self.robustness(obj, sampling_period=sampling_period,
                                                                          strict_horizon_check=strict_horizon_check,
                                                                          scale=scale)

        # Robustness at 0.
        robustness = robustness_signal[0]

        # Scale the robustness to [0,1] if required.
        if scale is None:
            scale = self.default_scale
        if scale:
            if effective_range_signal is None:
                raise Exception("Scaling of robustness values requested but no scale available.")

            if robustness <= 0:
                robustness = 0
            else:
                robustness *= 1 / effective_range_signal[0][1]
                robustness = min(1, robustness)

        return robustness


default = None


def robustness(obj, formula, strict_horizon_check=True, scale=default):
    """
    Evaluate the robustness of an STL formula on a feature vector or dictionary.

    Args:
        obj (FeatureVector | dict): The input feature vector or dictionary.
        formula (str): The STL formula as a string.
        strict_horizon_check (bool, optional): Whether to strictly check the horizon. Default is True.
        scale (bool, optional): Whether to scale the robustness value. Default is None.

    Returns:
        float: The evaluated robustness value.

    Raises:
        ValueError: If the input object type is unknown.
    """
    if isinstance(obj, FeatureVector):
        if scale is default:
            scale = True
        m = STLRobustness(formula)
        return m(obj, scale=scale)
    elif type(obj) is dict:
        if scale is default:
            scale = False
        assert not scale, "Dictionary has no scale information."
        m = STLRobustness(formula)
        return m(obj, scale=scale)
    else:
        raise ValueError("Unknown object type.")


robustness_monitor = STLRobustness


def as_robustness_monitor(formula: Union[str, STLRobustness],
                          input_fv: FeatureVector | None = None,
                          sampling_period: float | None = None,
                          scale: bool = True,
                          strict_horizon_check: bool | None = True) -> STLRobustness:
    """Create an STLRobustness monitor from a formula.

    Args:
        formula (Union[str, STLRobustness]): The STL formula as a string or STLRobustness object.
        input_fv (FeatureVector, optional): An input feature vector for a SUT to determine signal sampling period.
        sampling_period (float, optional): A sampling period for signals.
        scale (bool, optional): Whether to scale the robustness value. Default is True.
        strict_horizon_check (bool, optional): Whether to strictly check the horizon. Default is True.

    Returns:
        STLRobustness: The STLRobustness monitor.
    """

    if input_fv is not None:
        if sampling_period is None:
            sampling_period = find_min_sampling_period(input_fv)
        else:
            m = find_min_sampling_period(input_fv)
            sampling_period = min(sampling_period, m) if m is not None else None

    if type(formula) is str:
        return STLRobustness(formula, default_sampling_period=sampling_period, scale=scale, default_strict_horizon_check=strict_horizon_check)
    else:
        return formula
