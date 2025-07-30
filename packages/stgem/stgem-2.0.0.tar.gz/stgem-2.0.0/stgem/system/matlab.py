import os, time

import numpy as np

from stgem.features import FeatureVector, Real, SignalRepresentation
from stgem.sut import SystemUnderTest

try:
    import matlab
    import matlab.engine
except ImportError:
    raise Exception("Error importing Python Matlab engine.")

class Matlab(SystemUnderTest):
    """Generic class for using Matlab m files or Simulink models.

    Args:
        model_file (str): The path to the model file to be tested. \
        Can be a simulink model or a matlab script that runs the model.

        inputs (FeatureVector): A FeatureVector describing the inputs to the model. \
        Must match the inputs defined in the simulink model or the matlab function in \
        the script.

        outputs (FeatureVector): A FeatureVector describing the outputs of the model. \
        Must match the inputs defined in the simulink model or the matlab function in \
        the script.

        init_model_file (str, optional): Optional script that initialises the model. \
        Defaults to None.

    Raises:
        Exception: If any of the inputs fail their type checks or if the files at the \
        given paths are missing

    Currently we assume the following. The model_file parameter is either a
    Matlab function with the same name (function statement on the first line) or
    the name of a Simulink model.
    
    **In the case of a function:**
    It takes as its input a sequence of floats or signals. This is specified by
    setting the parameter 'input_type' to 'vector' or 'signal'. Similarly the
    output of the Matlab function is specified by setting the parameter
    'output_type' to have value 'vector' or 'signal'.

    Currently we assume that if the Matlab function expects signals as inputs,
    then the Matlab function's argument is U, a data matrix such that its first
    column corresponds to the timestamps, second column to the first signal
    etc.

    **In the case of a Simulink model:**
    Currently, we expect a simulink model to always take a signal input and
    output a signal.

    If an initializer Matlab program needs to be run before calling the actual
    function, this is accomplished by giving the program file (without the
    extension .m) as the parameter 'init_model_file'. This program is called
    with nargout=0 and we assume that it needs to be run only once.
    """

    def __init__(self,
                 model_file: str,
                 inputs: FeatureVector,
                 outputs: FeatureVector,
                 init_model_file: str = None):
        super().__init__()

        if type(model_file) != str:
            raise Exception('Model file must be a string')
        if not isinstance(inputs, FeatureVector) or not isinstance(outputs, FeatureVector):
            raise TypeError('Inputs and outputs must be of type FeatureVector')

        # Expect all features in a given vector to be the same type, as mixing
        # them would currently be undefined behaviour. Use the first feature as
        # the reference type
        inputRef = type(inputs.feature(inputs.names[0]))
        outputRef = type(outputs.feature(outputs.names[0]))
        if not all(inputRef == type(i) for i in inputs) and not all(outputRef == type(o) for o in outputs):
            raise Exception('All inputs/outputs in a given feature vector must be the same.')

        self.inputs = inputs
        self.outputs = outputs

        self.model_file = model_file
        # Model file can be an actual model or a script that runs the model
        if not os.path.exists(self.model_file + ".m") and not os.path.exists(self.model_file + '.mdl') and not os.path.exists(self.model_file + '.slx'):
            raise Exception("The file '{}.(m | mdl | slx)' does not exist.".format(self.model_file))

        self.script = False
        if os.path.exists(self.model_file + '.m'):
            # Indicate that the model file is a script
            self.script = True

        self.init_model_file = init_model_file
        if self.init_model_file and not os.path.exists(self.init_model_file + ".m"):
            raise Exception("The file '{}.m' does not exist.".format(self.init_model_file))

        self.idim = len(self.inputs)
        self.odim = len(self.outputs)

        self._has_been_setup = False

    def setup(self):
        if self._has_been_setup: return

        self.MODEL_NAME = os.path.basename(self.model_file)
        self.INIT_MODEL_NAME = os.path.basename(self.init_model_file) if self.init_model_file else None

        # Initialize the Matlab engine (takes a lot of time).
        self.engine = matlab.engine.start_matlab()
        # The paths for the model files.
        self.engine.addpath(os.path.dirname(self.model_file))
        if self.INIT_MODEL_NAME is not None:
            self.engine.addpath(os.path.dirname(self.init_model_file))

        # If the model is a script, save the function.
        if self.script:
            self.matlab_func = getattr(self.engine, self.MODEL_NAME)
        else:  # Else store the info about the simulation.
            model_opts = self.engine.simget(self.MODEL_NAME)
            self.model_opts = self.engine.simset(model_opts, 'SaveFormat', 'Array')
            self.variable_step = self.model_opts['Solver'].lower().startswith('variablestep')

        # Run the initializer program.
        if self.INIT_MODEL_NAME is not None:
            init = getattr(self.engine, self.INIT_MODEL_NAME)
            init(nargout=0)

        self._has_been_setup = True

    def new_ifv(self):
        # Return a clone of the input FV
        return self.inputs()

    def new_ofv(self) -> FeatureVector:
        # Return a clone of the output FV
        return self.outputs()

    def from_ifv_to_testinput(self, input_fv: FeatureVector):
        inputs = []
        for feature in input_fv.features:
            if isinstance(feature, SignalRepresentation):
                inputs.append(feature.synthesize_signal())
            else:
                inputs.append(feature.get())
        return inputs

    def from_testouput_to_ofv(self, output) -> FeatureVector:
        values, timestamps = output
        fv = self.new_ofv()
        assert len(values) == len(self.outputs), "Output dimension mismatch"

        toSet = []
        for idx in range(len(values)):
            assert len(values[idx]) == len(timestamps), 'Length of values and timestamps do not match'
            toSet.append([timestamps, values[idx]] if timestamps is not None else values[idx])

        fv.set(toSet)
        return fv

    def __del__(self):
        if hasattr(self, "engine"):
            self.engine.quit()

    def _execute_vector_vector(self, inputs):
        """Executes the values from execute_test with vector inputs and vector
        outputs.

        Args:
            inputs (list[list[float]]): List of input vectors

        Returns:
            tuple: A tuple with the results and None, in that order.
        """

        matlab_result = self.matlab_func(*(float(x) for x in inputs), nargout=self.odim)
        matlab_result = np.asarray(matlab_result)

        return matlab_result, None

    def _execute_vector_signal(self, inputs):
        """Executes the values from execute_test with vector inputs and signal
        outputs.

        Args:
            inputs (list[list[float]]): List of input vectors

        Returns:
            tuple: A tuple of signals and timestamps, in that order.
        """

        matlab_result = self.matlab_func(*(float(x) for x in inputs), nargout=self.odim + 1)
        output_timestamps = np.asarray(matlab_result[0]).flatten()
        data = np.asarray(matlab_result[1])

        # Reshape the data.
        output_signals = np.zeros(shape=(self.odim, len(output_timestamps)))
        for i in range(self.odim):
            output_signals[i] = data[:, i]

        return output_signals, output_timestamps

    def _execute_signal_vector(self, timestamps, signals):
        """Executes the values from execute_test with signal inputs and vector
        outputs.

        Args:
            timestamps (list[float]): The timestamps for the input signal samples.
            signals (list[list[float]]): Nested array with signal samples.

        Returns:
            tuple: A tuple with the results and None, in that order.
        """

        model_input = matlab.double(np.column_stack((timestamps, *signals)).tolist())

        matlab_result = self.matlab_func(model_input, nargout=self.odim)

        return matlab_result, None

    def _execute_signal_signal(self, timestamps, signals):
        """Executes the values from execute_test with signal inputs and signal
        outputs.

        Args:
            timestamps (list[float]): The timestamps for the input signal samples.
            signals (list[list[float]]): Nested array with signal samples.

        Returns:
            tuple: A tuple of signals and timestamps, in that order.
        """

        model_input = matlab.double(np.column_stack((timestamps, *signals)).tolist())

        if self.script:
            matlab_result = self.matlab_func(model_input, nargout=2)
            output_timestamps = np.asarray(matlab_result[0]).flatten()
            data = np.asarray(matlab_result[1])

            # Reshape the data.
            output_signals = np.zeros(shape=(self.odim, len(output_timestamps)))
            for i in range(self.odim):
                output_signals[i] = data[:, i]
        else:  # Simulink
            """
            Output formats depends on the solver.

            Fixed-step solver:
            -------------------------------------------------------------------
            Since the simulation steps are known in advance, Matlab can put the
            outputs in a matrix with columns time, output1, output2, ... This
            means that three values are returned timestamps, internal state,
            and the output matrix.

            Variable-step solver:
            -------------------------------------------------------------------
            Since the simulation timesteps are not known in advance, the size
            of the matrix described is not known. Here Matlab returns 2 +
            outputs arrays. The first has the timesteps, the second is the
            internal state, and the remaining are the outputs.
            """

            simulation_time = matlab.double([timestamps[0], timestamps[-1]])
            if self.variable_step:
                matlab_result = self.engine.sim(self.MODEL_NAME, simulation_time, self.model_opts, model_input, nargout=self.odim + 2)
                output_timestamps = matlab_result[0]
                output_signals = np.zeros(shape=(self.odim, len(output_timestamps)))
                for idx in range(self.odim):
                    output_signals[idx] = np.asarray(matlab_result[2 + idx]).flatten()
            else:
                matlab_result = self.engine.sim(self.MODEL_NAME, simulation_time, self.model_opts, model_input, nargout=self.odim)
                output_timestamps = matlab_result[0]
                data = np.asarray(matlab_result[2])
                output_signals = np.zeros(shape=(self.odim, len(output_timestamps)))
                for idx in range(self.odim):
                    output_signals[idx] = data[:, idx]

        output_timestamps = np.array(output_timestamps).flatten()
        return output_signals, output_timestamps

    def execute_test(self, inputs: list[list]):
        """Passes the unpacked values generated by the test generator to the
        Matlab model/script.

        Args:
            inputs (list[list]): Inputs to the matlab call.

        Returns:
            tuple: Outputs from the Matlab call.

        Raises:
            MatlabExecutionError: Function call fails to execute.
            RejectedExecutionError: Matlab engine terminated.
            SyntaxError: Syntax error in function call.
            TypeError: Data type of an input or output argument not supported.
        """

        self.setup()
        
        start_time = time.perf_counter()
        
        if isinstance(self.inputs.features[0], Real):
            if isinstance(self.outputs.features[0], Real):
                output = self._execute_vector_vector(inputs)
            else:
                output = self._execute_vector_signal(inputs)
        else:
            # Assuming all inputs will contain timestamps and that they're
            # always the same for each input (at the time of writing this, this
            # is true).
            timestamps = inputs[0][0]
            signals = [input[1] for input in inputs]

            if isinstance(self.outputs.features[0], Real):
                output = self._execute_signal_vector(timestamps, signals)
            else:
                output = self._execute_signal_signal(timestamps, signals)
        
        return output, {"execution_time": time.perf_counter() - start_time}
