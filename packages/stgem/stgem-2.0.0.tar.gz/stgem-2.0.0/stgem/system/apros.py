import os
import time
from importlib import resources

import numpy as np
from grpc import RpcError, insecure_channel
from grpc_tools import protoc

from stgem.features import FeatureVector, PiecewiseConstantSignal
from stgem.sut import SystemUnderTest

# If these modules are missing, run
# python -m grpc_tools.protoc -Istgem/systems --python_out=stgem/systems --grpc_python_out=stgem/systems stgem/systems/apros.proto
try:
    from stgem.system import apros_pb2_grpc
    from stgem.system import apros_pb2 as sc
except:
    print('Compiling gRPC components as they are missing')
    # Library includes for compiling
    proto_include = str((resources.files('grpc_tools') / '_proto').resolve())
    protoc.main(
        ['-Istgem/systems', f'I{proto_include}', '--python_out=stgem/systems', '--grpc_python_out=stgem/systems',
         'stgem/systems/apros.py'])
    from stgem.system import apros_pb2_grpc
    from stgem.system import apros_pb2 as sc


class _AprosError(Exception):
    pass


# Keys for property names used in gRPC with Apros
_DataTypeDouble = 'double'
_DataTypeFloat = 'float'
_DataTypeInteger = 'integer'
_DataTypeBoolean = 'boolean'
_DataKeyName = 'name'
_DataKeyType = 'dataType'
_DataKeyValue = 'value'


def _asValuePair(name, dataType, value):
    if name is None or dataType is None or value is None:
        print("Invalid name, dataType or value! Cannot handle None values.")
        return

    if dataType == _DataTypeDouble:
        yield sc.ValuePair(name=name, valueDouble=float(value))
    if dataType == _DataTypeFloat:
        yield sc.ValuePair(name=name, valueFloat=float(value))
    elif dataType == _DataTypeInteger:
        yield sc.ValuePair(name=name, valueInt=int(value))
    elif dataType == _DataTypeBoolean:
        yield sc.ValuePair(name=name, valueBoolean=bool(value))
    else:
        pass


def _createInputEntry(name, dataType, value):
    return {_DataKeyName: name, _DataKeyType: dataType, _DataKeyValue: value}


# Backend code modified from example implementation file provided by Semantum OY, with permission
class _AprosBackend():
    def __init__(self, stub):
        self.stub = stub
        self.ioset_filename = None

    # def upload_model(self, model_chunks):
    #     result = self.stub.UploadModel(model_chunks)
    #     print('UploadModel result: {}'.format(result))
    #     if result.reply != 'Upload completed':
    #         raise _AprosError('Uploading model failed: {}'.format(result))

    # def set_ioset_filename(self, filename):
    #     self.ioset_filename = filename

    def poll_until_wakeup(self, n: int):
        success = False
        count = 0
        while not success and count < n:
            try:
                result = self.stub.HealthCheck(sc.RequestMsg(request=''))
                success = True
            except RpcError:
                time.sleep(0.5)
                count += 1

        if not success:
            raise _AprosError(f'HealthCheck got no response in {n} tries')

    def check_experiment_health(self):
        # Kludge to avoid receiving the state of the previous experiment
        time.sleep(0.5)

        # Poll HealthCheck until it returns a zero instead of 1
        result = self.stub.HealthCheck(sc.RequestMsg(request=''))
        count = 1
        while result.statusCode == 1 and count < 20:
            count += 1
            time.sleep(0.5)
            result = self.stub.HealthCheck(sc.RequestMsg(request=''))

        if result.statusCode != 0:
            raise _AprosError('HealthCheck returned error code {}: {}'
                              .format(result.statusCode, result.reply))

    def load_ic(self, ic_name):
        try:
            self.stub.LoadExistingICByName(sc.ICNameRequestMsg(icName=ic_name))
        except RpcError as err:
            raise _AprosError(f'gRPC error in LoadExistingICByName {str(err)}') from err

    # modelName: String
    # icName: String
    # initCommands: List of commands (Strings)
    def initialize(self, modelName, icName):
        result = self.stub.ListExistingModels(sc.RequestMsg(request=''))
        if modelName in result.names:
            result = self.stub.ActivateModel(sc.ActivateModelMsg(name=modelName))
            if result.reply.startswith('Activated model'):
                msg = "Model activated successfully."
            else:
                return False, "Model failed to be activated."
        else:
            return False, "Apros does not contain a model with the provided name!"

        # Make sure that experiment is activated and healthy
        self.check_experiment_health()

        try:
            self.stub.LoadExistingICByName(sc.ICNameRequestMsg(icName=icName))
        except RpcError as err:
            raise _AprosError(f'gRPC error in LoadExistingICByName {str(err)}') from err

        return True, msg

    # Provide a list of strings with commands
    def runCommands(self, commands):
        if not commands:
            raise _AprosError('Missing commands')
        for command in commands:
            try:
                self.stub.Execute(sc.ExecuteRequestMsg(
                    request='', aproscommand=command))
            except RpcError as err:
                raise _AprosError(
                    'gRPC error in Execute("{}"): {}'.format(command, str(err))) from err

    # def monitor_simulation_time(self, future):
    #     '''Monitor the simulation time until the future is done.'''
    #     def monitor_till_completion():
    #         while not future.done():
    #             time.sleep(0.1)
    #             yield sc.Empty()
    #     for msg in self.stub.MonitorSimulationTime(monitor_till_completion()):
    #         print("Simulation time: {}".format(msg.timestamp))
    #     print("Finished monitoring simulation time")

    def simulate(self, duration):
        try:
            fut = self.stub.DoStep.future(
                sc.DoStepRequestMsg(request='', stepSize=duration))
            return fut
        except RpcError as err:
            raise _AprosError(f'gRPC error in DoStep: {str(err)}') from err

    def send_inputs(self, inputs):
        if not inputs:
            raise _AprosError('Missing inputs')
        try:
            inputsAsValuePairs = [
                v
                for entry in inputs
                for v in _asValuePair(entry[_DataKeyName], entry[_DataKeyType], entry[_DataKeyValue])
            ]

            self.stub.Write(sc.WriteMsg(
                values=inputsAsValuePairs))
        except RpcError as err:
            raise _AprosError(f'gRPC error in Write: {str(err)}') from err

    # Provide a list of strings as outputs parameter
    def get_outputs(self, outputs):
        if not outputs:
            raise _AprosError('Missing output names')
        try:
            read_reply = self.stub.Read(sc.ReadMsg(names=outputs))
            return read_reply.values
        except RpcError as err:
            raise _AprosError(f'gRPC error in Write: {str(err)}') from err

    def clean_up(self, exitCommands):
        try:
            if exitCommands:
                for command in exitCommands:
                    self.stub.Execute(sc.ExecuteRequestMsg(
                        request='', aproscommand=command))
        except RpcError as err:
            raise _AprosError(f'gRPC error in Execute: {str(err)}') from err

        try:
            self.stub.FlushExperiment(sc.RequestMsg(request=''))
        except RpcError as err:
            raise _AprosError(f'gRPC error in FlushExperiment {str(err)}') from err


_sep = '#'


class Apros(SystemUnderTest):
    """Test adapter for Apros Thermal using gRPC for communication

    Args:
        inputs (FeatureVector, optional): A FeatureVector describing the inputs to the model.. Defaults to None.
        outputs (FeatureVector, optional): A FeatureVector describing the outputs from the model.. Defaults to None.
        apros_grpc_address (str, optional): Address to the Apros instance. Defaults to os.getenv('APROS_GRPC_ADDRESS', 'localhost:11111').
        model (str, optional): Model name, must match the name of the model in Apros. Defaults to 'Model'.
        initial_condition (str, optional): Name of the Initial Condition used for testing. Defaults to 'Initial Condition'.

    Raises:
        Exception: Raised if any necessary arguments are missing or if the model failed to initialise.
    """

    def __init__(self,
                 inputs: FeatureVector = None,
                 outputs: FeatureVector = None,
                 apros_grpc_address=os.getenv('APROS_GRPC_ADDRESS', 'localhost:11111'),
                 model: str = 'Model',
                 initial_condition='Initial Condition',
                 ) -> None:
        super().__init__()

        if not inputs or not outputs:
            raise Exception('Missing input and/or output FeatureVectors')

        self.inputs = inputs
        self.outputs = outputs

        # Keys for fetching component data
        # Input names should be in the format <COMPONENT_NAME>#<ATTRIBUTE_NAME>
        # e.g. PO07#PO11_TEMPERATURE will fetch the temperature reading from Point 07
        self.output_keys = [' '.join(output.name.split(_sep)) for output in outputs]

        # GRPC communication channel
        self.channel = insecure_channel(apros_grpc_address)

        grpc_client = apros_pb2_grpc.SimulationStepManagerStub(self.channel)
        self.apros = _AprosBackend(grpc_client)
        # Try polling max 20 times, throws an error if unable to communicate
        self.apros.poll_until_wakeup(20)

        self.initial_condition = initial_condition
        self.model = model

        # Load the model with the given initial condition
        ok, message = self.apros.initialize(model, initial_condition)
        if not ok:
            raise Exception(f'Failed to initialise model: {message}')

    def __del__(self):
        if hasattr(self, 'apros'):
            self.apros.clean_up(None)

    def from_ifv_to_testinput(self, input_fv: FeatureVector):
        inputs = {}
        timestamps = None
        for feature in input_fv:
            name = ' '.join(feature.name.split(_sep))
            if isinstance(feature, PiecewiseConstantSignal):
                synth = feature.synthesize_signal()
                inputs[name] = list(synth[1])
                timestamps = synth[0]
            else:
                inputs[name] = feature.get()
        return (timestamps, inputs)

    def from_testouput_to_ofv(self, output) -> FeatureVector:
        fv = self.new_ofv()
        timestamps = output[0]
        values = output[1:]

        toSet = []
        for entry in values:
            toSet.append([timestamps, entry])

        fv.set(toSet)
        return fv

    def new_ifv(self) -> FeatureVector:
        return self.inputs()

    def new_ofv(self) -> FeatureVector:
        return self.outputs()

    def execute_test(self, test_input: dict):
        """Runs the simulation on Apros step by step.
        The simulation runs in real-time, i.e. a second in the simulation is a real-world second.
        Even though Apros supports speeding up the simulation, there is no guarantee that it
        runs at the given speed, especially for more complex models.
        """
        results = []
        idx = 0

        timestamps, inputs = test_input
        start_time = timestamps[0]
        stop_time = timestamps[-1]
        step = timestamps[1] - start_time
        current_time = start_time

        self.reset()

        outputs = self.apros.get_outputs(self.output_keys)
        values = [o.valueFloat for o in outputs]
        results.append((current_time, *values))

        while current_time < stop_time:
            values = [
                _createInputEntry(
                    key,
                    _DataTypeFloat,
                    inputs[key][idx] if type(inputs[key]) == list else inputs[key]
                )
                for key in inputs
            ]
            self.apros.send_inputs(values)
            future = self.apros.simulate(step)
            # Simulations are real-time on apros
            # Even though there's an option to increase the simulation speed,
            # there is no guarantee that the simulation will run at that speed
            time.sleep(step)

            # Sometimes the simulation will not be done exactly in time,
            # could be due to overhead or speed, so we wait a bit more
            while not future.done():
                time.sleep(0.1)

            current_time += step
            idx += 1

            outputs = self.apros.get_outputs(self.output_keys)
            values = [o.valueFloat for o in outputs]
            results.append((current_time, *values))

        return np.asarray(results).T, {}

    def reset(self):
        self.apros.load_ic(self.initial_condition)
