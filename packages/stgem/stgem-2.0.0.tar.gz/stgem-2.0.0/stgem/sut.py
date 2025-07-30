import time
import types
from inspect import signature
from typing import Union

import numpy as np

from stgem.features import Feature, FeatureVector, Real

import asyncio
import inspect

def sync(future):
    """
    If the input is an awaitable, runs it until complete and returns the result.
    Otherwise, returns the input directly.
    
    Parameters:
    future: An awaitable object or a direct value.
    
    Returns:
    The result of the future if it's awaitable, or the input value itself.
    """
    if not inspect.isawaitable(future):
        return future
    return asyncio.get_event_loop().run_until_complete(future)

class SystemUnderTest:
    """
        Abstract class to be implemented as an interface between the system being tested
        and the testing framework.
    """

    def new_ifv(self) -> FeatureVector:
        """
        Creates a new input feature vector which contains the same features as the calling instance.
        
        Returns:
            FeatureVector: A new input feature vector.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

        raise NotImplementedError

    def new_ofv(self) -> FeatureVector:
        """
        Creates a new output feature vector which contains the same features as the calling instance.
        
        Returns:
            FeatureVector: A new output feature vector.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

        raise NotImplementedError

    def from_ifv_to_testinput(self, input_fv: FeatureVector):
        """
        Converts an input feature vector to a test input.
        
        Parameters:
            input_fv (FeatureVector): The input feature vector.
        
        Returns:
            The converted test input.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

        raise NotImplementedError

    def from_testouput_to_ofv(self, output) -> FeatureVector:
        """
        Converts a test output to an output feature vector.
        
        Parameters:
        output: The test output.
        
        Returns:
            FeatureVector: The output feature vector.
        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

        raise NotImplementedError

    def execute_test_fv(self, input_fv: FeatureVector) -> FeatureVector:
        """
        Executes a test using the input feature vector and returns the output feature vector.
        
        Parameters:
        input_fv (FeatureVector): The input feature vector.
        
        Returns:
        FeatureVector: The output feature vector.
        """

        test_input = self.from_ifv_to_testinput(input_fv)
        test_output, features = sync(self.execute_test(test_input))
        output_fv = self.from_testouput_to_ofv(test_output)
        return output_fv, features

    def execute_test(self, test_input):
        """
        Executes the test with the given input.
        
        Parameters:
        test_input: The test input.
        
        Returns:
        The test output.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

        raise NotImplementedError



class PythonFunctionSystemUnderTest(SystemUnderTest):
    """
    SystemUnderTest implementation for a Python function.
    """

    def __init__(self, function: types.FunctionType):
        """
        Convert a Python function into a standardized SystemUnderTest (SUT) 
        by mapping the function's annotations to input and output features. 
        This allows the function to be used within a testing framework 
        that expects a specific interface.

        Args:
            function (types.FunctionType): The Python function to be tested. The function's annotations are used 
                to determine the input and output features.

        Raises:
            AssertionError: If an input annotation is not a Feature or if a return value is not a Feature or a list/tuple of Features.
            ValueError: If not all input values are annotated or if no annotation is specified for the return value.
        """
        SystemUnderTest.__init__(self)

        self.input_features = []
        self.output_features = []

        self.function = function

        for k, v in self.function.__annotations__.items():
            if k != "return":
                add_to = self.input_features
            else:
                if isinstance(v, FeatureVector):
                    self.output_features = v._features
                    continue
                else:
                    add_to = self.output_features

            if type(v) is list or type(v) is tuple:
                # multiple return parameters as list
                assert k == "return", "Only return values can be defined as a sequence of features"
                for f in v:
                    assert f._name != "", "Feature should have a name"
                    add_to.append(f)
            else:
                assert isinstance(v, Feature), "Type annotation should be a Feature if it is not a list or a tuple."
                # We set the feature name to match the Python variable name
                # except for the output.
                if k != "return":
                    v._name = k
                add_to.append(v)

        if len(signature(self.function).parameters) != len(self.input_features):
            raise ValueError("No annotation for all input values.")
        if len(self.output_features) == 0:
            raise ValueError("No annotation specified for the return value.")

    def execute_test(self, test_input):
        start_time = time.perf_counter()
        v = self.function(*test_input)
        return v, {"execution_time": time.perf_counter() - start_time}

    def new_ifv(self) -> FeatureVector:
        return FeatureVector(features=self.input_features)

    def new_ofv(self) -> FeatureVector:
        return FeatureVector(features=self.output_features)

    def from_ifv_to_testinput(self, input_fv: FeatureVector):
        return input_fv.to_list()

    def from_testouput_to_ofv(self, output) -> FeatureVector:
        if len(self.output_features) == 1 and isinstance(self.output_features[0], Real):
            if np.isscalar(output):
                output = [output]
            else:
                raise ValueError("From the signature it is expected that the function returns a scalar value.")

        output_fv = FeatureVector(values=output, features=self.output_features)
        return output_fv


def as_SystemUnderTest(sut_or_function: Union[SystemUnderTest, types.FunctionType]) -> SystemUnderTest:
    """Given a System Under Test, returns the same object unchanged. Given a
    Python function, returns a SystemUnderTest object that wraps this
    function."""

    if isinstance(sut_or_function, SystemUnderTest):
        return sut_or_function
    elif isinstance(sut_or_function, types.FunctionType):
        # check if it is an actual Python function.
        # We should *not* use callable for this
        return PythonFunctionSystemUnderTest(sut_or_function)
    else:
        raise ValueError("Unknown type.")
