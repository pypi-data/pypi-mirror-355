import numpy as np
from gymnasium.spaces.box import Box
from gymnasium.spaces.discrete import Discrete

from stgem.features import FeatureVector, PiecewiseConstantSignal, Signal
from stgem.sut import SystemUnderTest


class GYM(SystemUnderTest):
    """Class for testing Gymnasium environments.

        Args:
            env: The name of the Gymnasium environment.
            inputs (FeatureVector): A FeatureVector describing the inputs to the model.
            outputs (FeatureVector): A FeatureVector describing the outputs from the model.

        Raises:
            Exception: Environment name not a string or not a valid Gymnasium environment.
            TypeError: Inputs and outputs not of the type FeatureVector.
    """

    def __init__(self, env, inputs: FeatureVector, outputs: FeatureVector) -> None:
        super().__init__()

        if not isinstance(inputs, FeatureVector) or not isinstance(outputs, FeatureVector):
            raise TypeError('Inputs and outputs must be of type FeatureVector')

        self.env = env

        if not hasattr(self.env, 'reset') or not hasattr(self.env, 'step'):
            raise Exception(f"The environment {self.env} is not a valid Gymnasium environment.")

        self.inputs = inputs
        self.outputs = outputs

    def reset(self):
        return self.env.reset()

    def close(self):
        return self.env.close()

    def new_ifv(self) -> FeatureVector:
        return self.inputs

    def new_ofv(self) -> FeatureVector:
        return self.outputs

    def from_ifv_to_testinput(self, input_fv: FeatureVector):
        inputs = []
        for feature in input_fv:
            inputs.append(feature.synthesize_signal())

        timestamps = inputs[0][0]
        if type(self.env.action_space) == Discrete:
            values = np.int64([np.round(input[1], 0) for input in inputs])
        else:
            values = [input[1] for input in inputs]

        return timestamps, np.array(values)

    def from_testouput_to_ofv(self, output) -> FeatureVector:
        fv = self.new_ofv()
        timestamps = output[0]
        values = output[1:]

        to_set = []
        for entry in values:
            to_set.append([timestamps, entry])

        fv.set(to_set)
        return fv

    def execute_test(self, test_input):
        results = []
        idx = 0

        timestamps, inputs = test_input
        start_time = timestamps[0]
        stop_time = timestamps[-1]
        step = 1
        time = start_time

        observation, info = self.reset()
        results.append((time, *observation))

        if type(self.env.action_space) == Box:
            inputs = inputs[..., np.newaxis]

        while time < stop_time:

            action = ([i[idx] for i in inputs]) if inputs.shape[0] > 1 else ([i[idx] for i in inputs])[0]

            observation, reward, terminated, truncated, info = self.env.step(action)

            time += step
            idx += 1

            results.append((time, *observation))

            if terminated or truncated:
                break

        if time < stop_time - 1:
            time_remaining = stop_time - time
            results += [(time + i, *observation) for i in range(time_remaining)]

        return np.asarray(results).T, {}


def extract_gym_features(env, time_steps: int) -> FeatureVector:
    """Creates feature vectors for the Gymnasium environment based on the action and observation space.

    Args:
        env: The Gymnasium environment.
        time_steps (int): Amount of time steps that the agent can take through the environment.

    Raises:
        Exception: If the environment doesn't exist.

    Allowed action spaces:
        Discrete:
            This class represents a finite subset of integers, more specifically a set of the form.
            {a, a+1,...,a+n-1}
        Box:
            Box represents the Cartesian product of n closed intervals. Each interval has the form of one of
            [a,b], (-inf, b], [a, inf) or (-inf, inf)

    Allowed Observation spaces:
        Box:
            Box represents the Cartesian product of n closed intervals. Each interval has the form of one of
            [a,b], (-inf, b], [a, inf) or (-inf, inf)

    Returns:
        FeatureVector: input and output feature vectors, in that order.
    """

    # Check if the environment has the parameter "continuous" (some have both discrete and continuous action spaces.)

    input_features = []
    output_features = []

    # Input is usually of the type Discrete or Box
    if type(env.action_space) == Discrete:
        input_features.append(PiecewiseConstantSignal(name=f'action',
                                                      piece_durations=[1] * time_steps,
                                                      min_value=0,
                                                      max_value=env.action_space.n - 1))

    elif type(env.action_space) == Box:
        for i in range(env.action_space.shape[0]):
            input_features.append(PiecewiseConstantSignal(name=f'action_{i}',
                                                          piece_durations=[1] * time_steps,
                                                          min_value=env.action_space.low[i],
                                                          max_value=env.action_space.high[i]))

    # Output is usually of the type Box
    for i in range(env.observation_space.shape[0]):
        output_features.append(Signal(name=f'observation_{i}',
                                      min_value=env.observation_space.low[i],
                                      max_value=env.observation_space.high[i]))

    input_fv = FeatureVector(name='inputs', features=input_features)
    output_fv = FeatureVector(name='outputs', features=output_features)

    return input_fv, output_fv
