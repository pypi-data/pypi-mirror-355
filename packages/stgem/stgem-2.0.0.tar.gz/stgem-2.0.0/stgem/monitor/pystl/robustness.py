from math import log10

import numpy as np


class Window:
    """A class for sliding a varying-length window along a signal and for
    finding the minimum or maximum over the window."""

    def __init__(self, sequence, find_min=True):
        self.sequence = sequence
        self.find_min = find_min

        self.argminmax = np.argmin if find_min else np.argmax
        self.better = lambda x, y: x < y if find_min else lambda x, y: x > y

        self.prev_best_idx = len(self.sequence)
        self.prev_best = float("inf") if self.find_min else float("-inf")

        self.prev_start_pos = len(self.sequence)
        self.prev_end_pos = len(self.sequence)

    def update(self, start_pos, end_pos):
        """Update the window location, and return the best value (minimum or
        maximum) in the updated window."""

        start = start_pos
        end = end_pos

        # If the window is outside of the sequence, return -1.
        if start >= len(self.sequence) or end < 0:
            return -1

        # Adjust the beginning and end if out of scope.
        end = min(end, len(self.sequence))
        start = max(start, 0)

        if start >= end:
            raise Exception("Window start position {} before its end position {}.".format(start, end))

        # We have three areas we need to care about: an overlap, for which we
        # hopefully know the answer, and two areas to the left and right of the
        # overlap. Each of these three areas can be empty.
        if start < self.prev_start_pos:
            if end <= self.prev_start_pos:
                # Disjoint and to the left.
                l_s = start
                l_e = end
                o_s = -1
                o_e = -1
                r_s = -1
                r_e = -1
            else:
                if end <= self.prev_end_pos:
                    # Intersects from left but does not extend over to the right.
                    l_s = start
                    l_e = self.prev_start_pos
                    o_s = self.prev_start_pos
                    o_e = end
                    r_s = -1
                    r_e = -1
                else:
                    # Contains the previous completely and has left and right areas nonempty.
                    l_s = start
                    l_e = self.prev_start_pos
                    o_s = self.prev_start_pos
                    o_e = self.prev_end_pos
                    r_s = self.prev_end_pos
                    r_e = end
        else:
            if start >= self.prev_end_pos:
                # Disjoint and to the right.
                l_s = -1
                l_e = -1
                o_s = -1
                o_e = -1
                r_s = start
                r_e = end
            else:
                if end <= self.prev_end_pos:
                    # Is contained completely in the previous.
                    l_s = -1
                    l_e = -1
                    o_s = start
                    o_e = end
                    r_s = -1
                    r_e = -1
                else:
                    # Intersects from the right but does not extend over to the left.
                    l_s = -1
                    l_e = -1
                    o_s = start
                    o_e = self.prev_end_pos
                    r_s = self.prev_end_pos
                    r_e = end

        # Find the minimums from each area. If the previous best value is not
        # in the overlap, we need to search the whole overlap.
        best_idx = -1
        if o_s < o_e:
            if o_s <= self.prev_best_idx < o_e:
                best_idx = self.prev_best_idx
            else:
                best_idx = o_s + self.argminmax(self.sequence[o_s:o_e])
                self.prev_best = self.sequence[best_idx]
        if l_s < l_e:
            left_idx = l_s + self.argminmax(self.sequence[l_s:l_e])
            if best_idx == -1 or self.better(self.sequence[left_idx], self.prev_best):
                best_idx = left_idx
                self.prev_best = self.sequence[best_idx]
        if r_s < r_e:
            right_idx = r_s + self.argminmax(self.sequence[r_s:r_e])
            if best_idx == -1 or self.better(self.sequence[right_idx], self.prev_best):
                best_idx = right_idx
                self.prev_best = self.sequence[best_idx]

        self.prev_best_idx = best_idx
        self.prev_start_pos = start_pos
        self.prev_end_pos = end_pos

        return self.prev_best_idx

class Traces:

    def __init__(self, timestamps, signals):
        self.timestamps = timestamps
        self.signals = signals

        # Check that all signals have correct length.
        for s in signals.values():
            if len(s) != len(timestamps):
                raise ValueError("All signals must have exactly as many samples as there are timestamps.")

    @classmethod
    def from_mixed_signals(C, *args, sampling_period=None):
        """Instantiate the class from signals that have different timestamps
        (with 0 as a first timestamp) and different lengths. This is done by
        finding the maximum signal length and using that as a signal length,
        dividing this length into pieces according to the sampling period
        (smallest observed difference between timestamps if None), and filling
        values by assuming constant value. If no sampling period is defined, we
        use the minimum average timestamp gap rounded to the nearest power of
        10.

        The input is expected to be of the form
        name1, timestamps1, signal1, name2, timestamps2, signal2, ..."""

        """
        Currently the code does not work reliably with time steps lower than
        1e-4, but this should be enough.
        """

        # Find the minimum average gap and round it to closest power of 10.
        m = float("inf")
        for i in range(0, len(args), 3):
            if len(args[i+1]) > 1:
                m = min(m, np.mean(np.diff(args[i+1])))
            else:
                m = min(m, 1)
        default_sampling_period = 10**(round(log10(m), 0))

        if sampling_period is None:
            sampling_period = default_sampling_period

        if 10**(round(log10(sampling_period), 0)) > default_sampling_period:
            raise Exception("The specified sampling period {} differs significantly from the average timestamp gap {}.".format(sampling_period, default_sampling_period))

        # Check that all timestamps begin with 0. Otherwise the code below is
        # not valid.
        for i in range(0, len(args), 3):
            if args[i+1][0] != 0:
                raise Exception("The first timestamp should be 0 in all signals.")

        # Maximum signal length.
        T = max(args[i+1][-1] for i in range(0, len(args), 3))

        # New timestamps.
        timestamps = [i*sampling_period for i in range(0, int(T/sampling_period) + 1)]

        # Fill the signals by assuming constant value.
        signals = {}
        eps = 1e-5
        for i in range(0, len(args), 3):
            name = args[i]
            signal_timestamps = args[i+1]
            signal_values = args[i+2]

            assert len(signal_timestamps) == len(signal_values), "Signal must have equally many timestamps and values."

            signals[name] = np.empty(shape=(len(timestamps)))
            pos = 0
            for n, t in enumerate(timestamps):
                while pos < len(signal_timestamps) and signal_timestamps[pos] <= t + eps:
                    pos += 1

                value = signal_values[pos - 1]
                signals[name][n] = value

        return C(timestamps, signals)

    def search_time_index(self, t, start=0):
        """Finds the index of the time t in the timestamps using binary
        search."""

        lower_idx = start
        upper_idx = len(self.timestamps) - 1
        middle = (lower_idx + upper_idx)//2
        while lower_idx <= upper_idx:
            if self.timestamps[middle] < t:
                lower_idx = middle + 1
            elif self.timestamps[middle] > t:
                upper_idx = middle - 1
            else:
                break

            middle = (lower_idx + upper_idx)//2

        if self.timestamps[middle] == t:
            return middle
        else:
            return -1

class TreeIterator:

    def __init__(self, node):
        self.nodes = [node]

    def __next__(self):
        try:
            node = self.nodes.pop(0)
            self.nodes += node.formulas

            return node
        except IndexError:
            raise StopIteration

class STL:
    """Base class for all logical operations and atoms."""

    def __iter__(self):
        return TreeIterator(self)

class Atom(STL):
    """Base class for atoms."""

class Signal(Atom):

    def __init__(self, name):
        self.formulas = []
        self.name = name
        self.horizon = 0

    def eval(self, traces, signal_ranges=None):
        if signal_ranges is None:
            _range = None
            effective_range_signal = None
        else:
            _range = signal_ranges[self.name]
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)
        # We return a copy so that subsequent robustness computations can
        # safely reuse arrays. We also enforce floats in order to avoid errors.
        return np.array(traces.signals[self.name], copy=True, dtype="float64"), _range, effective_range_signal

class Constant(Atom):

    def __init__(self, val):
        self.formulas = []
        self.val = val
        self.horizon = 0

    def eval(self, traces, signal_ranges=None):
        if signal_ranges is None:
            _range = [self.val, self.val]
            effective_range_signal = None
        else:
            _range = [self.val, self.val]
            effective_range_signal = np.full(shape=(len(traces.timestamps), 2), fill_value=self.val)
        # We must always produce a new array because subsequent robustness
        # computations can reuse arrays.
        return np.full(len(traces.timestamps), self.val), _range, effective_range_signal

class Sum(Atom):

    def __init__(self, left_formula, right_formula):
        self.formulas = [left_formula, right_formula]
        self.horizon = 0

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            A = left_range[0] + right_range[0]
            B = left_range[1] + right_range[1]
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, _ = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, _ = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.add(left_formula_robustness, right_formula_robustness, out=left_formula_robustness), _range, effective_range_signal

class Subtract(Atom):

    def __init__(self, left_formula, right_formula):
        self.formulas = [left_formula, right_formula]
        self.horizon = 0

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            A = left_range[0] - right_range[1]
            B = left_range[1] - right_range[0]
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, _ = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, _ = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.subtract(left_formula_robustness, right_formula_robustness, out=left_formula_robustness), _range, effective_range_signal

class Multiply(Atom):

    def __init__(self, left_formula, right_formula):
        self.formulas = [left_formula, right_formula]
        self.horizon = 0

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            A = left_range[0] * right_range[0]
            B = left_range[1] * right_range[1]
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, _ = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, _ = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.multiply(left_formula_robustness, right_formula_robustness, out=left_formula_robustness), _range, effective_range_signal

class Divide(Atom):

    def __init__(self, left_formula, right_formula):
        self.formulas = [left_formula, right_formula]
        self.horizon = 0

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            if right_range[1] == 0:
                raise Exception("Cannot determine a finite range for division as the right formula upper bound is 0.")
            if right_range[0] == 0:
                raise Exception("Cannot determine a finite range for division as the right formula lower bound is 0.")
            A = left_range[0] / right_range[1]
            B = left_range[1] / right_range[0]
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, _ = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, _ = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.divide(left_formula_robustness, right_formula_robustness, out=left_formula_robustness), _range, effective_range_signal

class GreaterThan(Atom):

    def __init__(self, left_formula, right_formula):
        if isinstance(left_formula, (int, float)):
            left_formula = Constant(left_formula)
        if isinstance(right_formula, (int, float)):
            right_formula = Constant(right_formula)
        self.formulas = [left_formula, right_formula]
        self.horizon = 0

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            A = left_range[0] - right_range[1]
            B = left_range[1] - right_range[0]
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, _ = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, _ = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.subtract(left_formula_robustness, right_formula_robustness, out=left_formula_robustness), _range, effective_range_signal

class LessThan(Atom):

    def __init__(self, left_formula, right_formula):
        if isinstance(left_formula, (int, float)):
            left_formula = Constant(left_formula)
        if isinstance(right_formula, (int, float)):
            right_formula = Constant(right_formula)
        self.formulas = [left_formula, right_formula]
        self.horizon = 0

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            A = right_range[0] - left_range[1]
            B = right_range[1] - left_range[0]
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, _ = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, _ = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.subtract(right_formula_robustness, left_formula_robustness, out=right_formula_robustness), _range, effective_range_signal

class Abs(Atom):

    def __init__(self, formula):
        self.formulas = [formula]
        self.horizon = 0

    def _compute_range(self, _range):
        if _range is None:
            return None
        else:
            A = _range[0]
            B = _range[1]
            if A <= 0:
                if B > 0:
                    return [0, B]
                else:
                    return [-B, -A]
            else:
                return [A, B]

    def eval(self, traces, signal_ranges=None):
        formula_robustness, _range, _ = self.formulas[0].eval(traces, signal_ranges)
        _range = self._compute_range(_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.abs(formula_robustness, out=formula_robustness), _range, effective_range_signal

class Equals(Atom):

    def __init__(self, left_formula, right_formula):
        self.formulas = [left_formula, right_formula]
        self.formula_robustness = Not(Abs(Subtract(self.formulas[0], self.formulas[1])))
        self.horizon = 0

    def _compute_range(self, _range):
        if _range is None:
            return None
        else:
            # Make sure that 1 is included in the interval.
            _range = _range.copy()
            if _range[0] > 1:
                _range[0] = 1
            elif _range[1] < 1:
                _range[1] = 1
            return _range

    def eval(self, traces, signal_ranges=None):
        robustness, _range, _ = self.formula_robustness.eval(traces, signal_ranges)
        _range = self._compute_range(_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.empty(shape=(len(traces.timestamps), 2))
            effective_range_signal[:] = np.array([_range[0], _range[1]]).reshape(1, 2)

        return np.where(robustness == 0, 1, robustness), _range, effective_range_signal

class Next(STL):

    def __init__(self, formula):
        self.formulas = [formula]
        self.horizon = 1 + self.formulas[0].horizon

    def _compute_range(self, _range):
        return _range.copy() if _range is not None else None

    def eval(self, traces, signal_ranges=None):
        formula_robustness, _range, formula_effective_range_signal = self.formulas[0].eval(traces, signal_ranges)
        _range = self._compute_range(_range)
        robustness = np.roll(formula_robustness, -1)[:-1]

        if signal_ranges is None:
            effective_range_signal = None
        else:
            effective_range_signal = np.roll(formula_effective_range_signal, -1)[:-1]

        return robustness, _range, effective_range_signal

class Until(STL):

    def __init__(self, lower_time_bound, upper_time_bound, left_formula, right_formula):
        self.upper_time_bound = upper_time_bound
        self.lower_time_bound = lower_time_bound
        self.formulas = [left_formula, right_formula]
        self.horizon = self.upper_time_bound +  max(self.formulas[0].horizon, self.formulas[1].horizon)

    def _compute_range(self, left_range, right_range):
        if left_range is None or right_range is None:
            return None
        else:
            A = max(left_range[1], right_range[1])
            B = min(left_range[0], right_range[0])
            return [A, B]

    def eval(self, traces, signal_ranges=None):
        left_formula_robustness, left_range, left_formula_effective_range_signal = self.formulas[0].eval(traces, signal_ranges)
        right_formula_robustness, right_range, right_formula_effective_range_signal = self.formulas[1].eval(traces, signal_ranges)
        _range = self._compute_range(left_range, right_range)

        robustness = np.empty(shape=(len(left_formula_robustness)))
        if signal_ranges is not None:
            effective_range_signal = np.empty(shape=(len(left_formula_effective_range_signal), 2))
            
        # We save the previously found positions; see the corresponding comment
        # in eval of Global.
        prev_lower_bound_pos = len(traces.timestamps) - 1
        prev_upper_bound_pos = len(traces.timestamps) - 1
        window = Window(left_formula_robustness)
        alternation = 0
        for current_time_pos in range(len(traces.timestamps) - 1, -1, -1):
            # Lower and upper times for the current time.
            lower_bound = traces.timestamps[current_time_pos] + self.lower_time_bound
            upper_bound = traces.timestamps[current_time_pos] + self.upper_time_bound

            # Find the corresponding positions in timestamps.
            # Lower bound.
            if lower_bound > traces.timestamps[-1]:
                # If the lower bound is out of scope, then the right robustness
                # term in the min clause does not exist, so it is reasonable to
                # compute the inf term to the end of the signal and use that as
                # the robustness.
                inf_min_idx = window.update(current_time_pos, len(traces.timestamps))
                robustness[current_time_pos] = left_formula_robustness[inf_min_idx]
                if signal_ranges is not None:
                    effective_range_signal[current_time_pos] = left_formula_effective_range_signal[inf_min_idx]

                continue
            else:
                if traces.timestamps[prev_lower_bound_pos - 1] == lower_bound:
                    lower_bound_pos = prev_lower_bound_pos - 1
                else:
                    lower_bound_pos = traces.search_time_index(lower_bound, start=current_time_pos)

                    if lower_bound_pos < 0:
                        raise Exception("No timestamp '{}' found even though it should exist.".format(lower_bound))
            # Upper bound.
            if upper_bound > traces.timestamps[-1]:
                upper_bound_pos = len(traces.timestamps) - 1
            else:
                if traces.timestamps[prev_upper_bound_pos - 1] == upper_bound:
                    upper_bound_pos = prev_upper_bound_pos - 1
                else:
                    upper_bound_pos = traces.search_time_index(upper_bound, start=lower_bound_pos)
                    # See above.
                    if upper_bound_pos < 0:
                        raise Exception("No timestamp '{}' found even though it should exist.".format(upper_bound))

            # Move a window with start position current_time_pos and end
            # position in the interval determined by lower_bound_pos and
            # upper_bound_pos.
            maximum = float("-inf")
            maximum_idx = None
            maximum_robustness = None
            # Alternating the reading direction speeds up the computations.
            R = range(lower_bound_pos, upper_bound_pos + 1) if alternation == 0 else range(upper_bound_pos, lower_bound_pos - 1, -1)
            alternation = (alternation + 1) % 2
            for window_end_pos in R:
                # This is the infimum term.
                if current_time_pos == window_end_pos:
                    # This is a special case where the infimum term is taken
                    # over an empty interval. We return an infinite value to
                    # always select other robustness value.
                    inf_min_idx = window_end_pos
                    L = float("inf")
                else:
                    inf_min_idx = window.update(current_time_pos, window_end_pos)
                    if inf_min_idx == -1:
                        # The window was out of scope. This happens only in
                        # exceptional circumstances. We guess the value then to be
                        # the final robustness value observed.
                        inf_min_idx = len(traces.timestamps) - 1
                    L = left_formula_robustness[inf_min_idx]

                # Compute the minimum of the right robustness and the inf term.
                R = right_formula_robustness[window_end_pos]
                if R < L:
                    minimum_idx = window_end_pos
                    minimum_robustness = 1
                    v = R
                else:
                    minimum_idx = inf_min_idx
                    minimum_robustness = 0
                    v = L

                # Update the maximum if needed.
                if v > maximum:
                    maximum = v
                    maximum_idx = minimum_idx
                    maximum_robustness = minimum_robustness

            if maximum_robustness == 0:
                robustness[current_time_pos] = left_formula_robustness[maximum_idx]
                if signal_ranges is not None:
                    effective_range_signal[current_time_pos] = left_formula_effective_range_signal[maximum_idx]
            else:
                robustness[current_time_pos] = right_formula_robustness[maximum_idx]
                if signal_ranges is not None:
                    effective_range_signal[current_time_pos] = right_formula_effective_range_signal[maximum_idx]

            prev_lower_bound_pos = lower_bound_pos
            prev_upper_bound_pos = upper_bound_pos

        return robustness, _range, effective_range_signal if signal_ranges is not None else None

class Global(STL):

    def __init__(self, lower_time_bound, upper_time_bound, formula):
        self.upper_time_bound = upper_time_bound
        self.lower_time_bound = lower_time_bound
        self.formulas = [formula]
        self.horizon = self.upper_time_bound + self.formulas[0].horizon

    def _compute_range(self, _range):
        return _range.copy() if _range is not None else None

    def eval(self, traces, signal_ranges=None):
        formula_robustness, _range, formula_effective_range_signal = self.formulas[0].eval(traces, signal_ranges)
        _range = self._compute_range(_range)
        robustness = np.empty(shape=(len(formula_robustness)))
        if signal_ranges is not None:
            effective_range_signal = np.empty(shape=(len(formula_effective_range_signal), 2))

        # We save the previously found positions as most often we use integer
        # timestamps and evenly sampled signals, so the correct answer is
        # directly previous position - 1. This has a huge speed benefit.
        prev_lower_bound_pos = len(traces.timestamps) - 1
        prev_upper_bound_pos = len(traces.timestamps) - 1
        window = Window(formula_robustness)
        for current_time_pos in range(len(traces.timestamps) - 1, -1, -1):
            # Lower and upper times for the current time.
            lower_bound = traces.timestamps[current_time_pos] + self.lower_time_bound
            upper_bound = traces.timestamps[current_time_pos] + self.upper_time_bound

            # Find the corresponding positions in timestamps.
            # Lower bound.
            if lower_bound > traces.timestamps[-1]:
                lower_bound_pos = len(traces.timestamps)
            else:
                if traces.timestamps[prev_lower_bound_pos - 1] == lower_bound:
                    lower_bound_pos = prev_lower_bound_pos - 1
                else:
                    lower_bound_pos = traces.search_time_index(lower_bound, start=current_time_pos)

                    if lower_bound_pos < 0:
                        raise Exception("No timestamp '{}' found even though it should exist.".format(lower_bound))
            # Upper bound.
            if upper_bound > traces.timestamps[-1]:
                upper_bound_pos = len(traces.timestamps) - 1
            else:
                if traces.timestamps[prev_upper_bound_pos - 1] == upper_bound:
                    upper_bound_pos = prev_upper_bound_pos - 1
                else:
                    upper_bound_pos = traces.search_time_index(upper_bound, start=lower_bound_pos)
                    # See above.
                    if upper_bound_pos < 0:
                        raise Exception("No timestamp '{}' found even though it should exist.".format(upper_bound))

            # Slide a window corresponding to the indices and find the index of
            # the minimum. The value -1 signifies that the window was out of
            # scope.
            min_idx = window.update(lower_bound_pos, upper_bound_pos + 1)
            if min_idx == -1:
                # The window was out of scope. We guess here that the
                # robustness is the final robustness value observed. We don't
                # know the future, but this is our last observation.
                min_idx = len(traces.timestamps) - 1

            robustness[current_time_pos] = formula_robustness[min_idx]
            if signal_ranges is not None:
                effective_range_signal[current_time_pos] = formula_effective_range_signal[min_idx]

            prev_lower_bound_pos = lower_bound_pos
            prev_upper_bound_pos = upper_bound_pos

        return robustness, _range, effective_range_signal if signal_ranges is not None else None

class Finally(STL):

    def __init__(self, lower_time_bound, upper_time_bound, formula):
        self.upper_time_bound = upper_time_bound
        self.lower_time_bound = lower_time_bound
        self.formulas = [formula]
        self.formula_robustness = Not(Global(self.lower_time_bound, self.upper_time_bound, Not(self.formulas[0])))
        self.horizon = self.upper_time_bound + self.formulas[0].horizon

    def eval(self, traces, signal_ranges=None):
        return self.formula_robustness.eval(traces, signal_ranges)

class Not(STL):

    def __init__(self, formula):
        self.formulas = [formula]
        self.horizon = self.formulas[0].horizon

    def _compute_range(self, _range):
        if _range is None:
            return None
        else:
            return [-1*_range[1], -1*_range[0]]

    def eval(self, traces, signal_ranges=None):
        formula_robustness, _range, formula_effective_range_signal = self.formulas[0].eval(traces, signal_ranges)
        _range = self._compute_range(_range)

        if signal_ranges is None:
            effective_range_signal = None
        else:
            np.multiply(-1, formula_effective_range_signal, out=formula_effective_range_signal)
            effective_range_signal = np.roll(formula_effective_range_signal, -1, axis=1)

        return np.multiply(-1, formula_robustness, out=formula_robustness), _range, effective_range_signal

class Implication(STL):

    def __init__(self, left_formula, right_formula):
        self.formulas = [left_formula, right_formula]
        self.formula_robustness = Or(Not(self.formulas[0]), self.formulas[1])
        self.horizon = max(self.formulas[0].horizon, self.formulas[1].horizon)

    def eval(self, traces, signal_ranges=None):
        return self.formula_robustness.eval(traces, signal_ranges)

class Or(STL):

    def __init__(self, *args):
        self.formulas = list(args)
        self.formula_robustness = Not(And(*[Not(f) for f in self.formulas]))
        self.horizon = self.formula_robustness.horizon

    def eval(self, traces, signal_ranges=None):
        return self.formula_robustness.eval(traces, signal_ranges)

class And(STL):

    def __init__(self, *args):
        self.formulas = list(args)
        self.horizon = max(f.horizon for f in self.formulas)

    def eval(self, traces, signal_ranges=None):
        _range = [float("inf"), float("inf")] if signal_ranges is not None else None
        # Evaluate the robustness of all subformulas and save the robustness
        # signals into one 2D array.
        M = len(self.formulas)
        ranges_available = False
        for i in range(M):
            formula_robustness, formula_range, formula_effective_range_signal = self.formulas[i].eval(traces, signal_ranges)
            if _range is not None:
                if formula_range is None:
                    _range = None
                else:
                    _range[0] = min(_range[0], formula_range[0])
                    _range[1] = min(_range[1], formula_range[1])
            if i == 0:
                rho = np.empty(shape=(M, len(formula_robustness)))
                if signal_ranges is not None:
                    bounds = np.empty(shape=(M, formula_effective_range_signal.shape[0], 2))
                    ranges_available = True

            rho[i,:] = formula_robustness
            if ranges_available:
                if signal_ranges is not None:
                    bounds[i,:] = formula_effective_range_signal
                else:
                    del bounds
                    ranges_available = False

        if ranges_available:
            min_idx = np.argmin(rho, axis=0)
            return rho[min_idx,np.arange(len(min_idx))], _range, bounds[min_idx,np.arange(len(min_idx))]

            """
            The below commented code implements a proportional approach to And.
            It is commented out for now, but saved for possible future use.

            
            Traditionally the robustness of several conjunctions is the minimum
            of the robustness values. If, however, we have scale information
            for each robustness value, we can select the robustness that is
            proportionally smallest. Say we have robustness values F_1, ...,
            F_n with ranges [A_1, B_1], ..., [A_n, B_n]. Then instead of
            considering F_i, we can consider in its place F_i / B_i (when F_i
            >= 0) or F_i / -A_i (when F_i < 0). Then we select the i for which
            the scaled robustness is smallest and return F_i as the robustness
            (so we do not scale the resulting value but scaling is involved in
            the selection of i). Similarly we set the effective range to be
            [A_i, B_i]. This results in a new robustness value and at the very
            end it can be scaled to [0, 1] (or to [-1, 1] for that matter)
            according to the effective range.
            """

            """
            idx_n = rho < 0
            idx_p = ~idx_n
            d = np.empty_like(rho)
            d[idx_n] = rho[idx_n] / -bounds[idx_n,0]
            d[idx_p] = rho[idx_p] / bounds[idx_p,1]
            min_idx = np.argmin(d, axis=0)
            return rho[min_idx,np.arange(len(min_idx))], _range, bounds[min_idx,np.arange(len(min_idx))]
            """
        else:
            return np.min(rho, axis=0), _range, None

StrictlyLessThan = LessThan
StrictlyGreaterThan = GreaterThan

