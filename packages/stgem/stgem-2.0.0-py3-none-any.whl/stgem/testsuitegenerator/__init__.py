import copy
import gc
import os

import dill as pickle
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from stgem import merge_dictionary, RandomNumberGenerator, SearchSpace, logging
from stgem.limit import Limit
from stgem.monitor import Monitor
from stgem.sut import SystemUnderTest
from stgem.testgenerator import TestGenerator


class _CheckpointRecorder:
    """Utility class for managing checkpoints.
    """

    def __init__(self, filename: str, th):
        self._filename = filename
        self._tsg = th

    def record(self, data):
        with open(self._filename, 'wb') as file:
            # save the data file
            pickle.dump(data, file)
            # save the generator
            try:
                # sut cannnot serialized
                sut = self._tsg.sut
                self._tsg.sut = None
                pickle.dump(self._tsg, file)
            finally:
                self._tsg.sut = sut

    def resume(self):
        """Restore state of TestSuiteGenerator to a previous exeuction
                """
        # sut cannot be serialized
        sut = self._tsg.sut

        with open(self._filename, 'rb') as file:
            data = pickle.load(file)
            new_tsg = pickle.load(file)

        new_tsg.sut = sut
        # move everything to the existing TestSuiteGenerator
        self._tsg.__dict__.update(copy.copy(new_tsg.__dict__))

        return (self._tsg, data)

    def done(self, save: str | None = None):
        """Called when recording is done and file should be finalised

        Args:
            save (str | None, optional): Whether the final data should be kept, if given, should be the name of the destination file. Defaults to None.
        """
        if save:
            os.rename(self._filename, save)
        else:
            os.remove(self._filename)


class TestSuiteGenerator:
    """
    Abstract base class for test suite generators. Defines the basic interface and common functionality
    for a test suite generator with a limit on resources or test executions.
    Parameters:
        limit (Limit): The limit object defining the resource or execution limits.
    """
    __test__ = False # Prevent pytest from considering this class a test class

    default_parameters = {}

    def __init__(self,
                 *,
                 sut: SystemUnderTest | None = None,
                 goal: Monitor | None = None,
                 limit: Limit | None = None,
                 parameters: dict = None):
        self.parameters = parameters if parameters is not None else {}
        self.parameters = merge_dictionary(self.parameters, self.default_parameters)

        self.sut = None
        self.goal = None
        self.limit = None
        self.rng = None
        self.search_space = None
        self.has_been_initialized = False

        self.min_robustness = 1
        
        if sut is not None or limit is not None or goal is not None:
            self.setup(sut=sut, goal=goal, limit=limit)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__.get(name)
        elif "parameters" in self.__dict__ and name in self.parameters:
            return self.parameters.get(name)
        else:
            raise AttributeError(name)

    def setup(self,
              sut: SystemUnderTest | None = None,
              goal: Monitor | None = None,
              limit: Limit | None = None,
              seed: int | None = None,
              rng: RandomNumberGenerator | None = None):
        """Set up the test suite generator for the creation of a new test
        suite. Only the provided arguments are actually updated."""
        
        if sut is not None:
            self.sut = sut
            self.search_space = SearchSpace(input_vector=self.sut.new_ifv(), rng=self.rng)
        if goal is not None:
            self.goal = goal
        if limit is not None:
            self.limit = limit
            # Start the limit tracking (in case of wall time etc.).
            self.limit.start()

        # Set up the random number generator. Either use the provided RNG or
        # create a new one using the given seed (if seed is None, then a random
        # seed will be used).
        if seed is not None and rng is not None:
            raise ValueError("Specify either a random seed or a random number generator but not both.")

        if rng is not None:
            self.rng = rng
            if self.search_space is not None:
                self.search_space.rng = self.rng
        elif seed is not None:
            self.rng = RandomNumberGenerator(seed=seed)
            if self.search_space is not None:
                self.search_space.rng = self.rng
    
    def initialize(self):
        """An abstract method to let the test suite generator initialize itself."""
        
        self.has_been_initialized = True

    def step(self) -> dict:
        """
        Abstract method to perform a single step of the heuristic.

        Returns:
            dict: The result of the step.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

        raise NotImplementedError("TestSuiteGenerator step not implemented.")

    def finalize_step(self, data: pd.DataFrame, step_result: dict):
        pass

    def finalize_run(self, data: pd.DataFrame):
        pass

    def _append_data(self, data: pd.DataFrame, step_result: dict):
        """Appends the results of a step to the collected data.
        Parameters:
        data (pd.DataFrame): The dataframe containing all collected data.
        step_result (dict): The results of the current step.

        Returns:
        pd.DataFrame: Updated dataframe with the new step results.
        """

        i = data.shape[0] + 1
        new_data = pd.DataFrame(columns=["idx"] + list(step_result.keys()))
        new_data.loc[i, "idx"] = i
        # convert columns containing numpy arrays to object
        for k, v in step_result.items():
            if not np.isscalar(v):
                new_data[k].astype(object)
        for k in step_result:
            if np.isscalar(step_result[k]):
                new_data.loc[i, k] = step_result[k]
            else:
                # If we do not enclose step_result[k] in brackets and
                # step_result[k] is a Numpy array of length 1, it will be
                # converted to a scalar, and we do not want this.
                new_data.loc[i, k] = [step_result[k]]
        data = pd.concat([data, new_data])
        return data


def run(tsg: TestSuiteGenerator,
        seed=None,
        quiet=False,
        checkpoint_name: str | None = None):
    """
    Run the test heuristic by calling the method step repeatedly until
    the stopping condition defined by a Limit object is satisfied.

    Args:
        tsg: TestSuiteGenerator to run
        seed: Seed to run the test heuristic.
        quiet (bool, optional): If True, suppresses logging output. Defaults to False.
        checkpoint_name (str | None, optional): Name for checkpoint file, checkpoints not used if None

    Returns:
        pd.DataFrame: Collected data as a dataframe.
    """

    assert tsg is not None

    data = pd.DataFrame()

    tsg.setup(seed=seed)
    tsg.initialize()

    checkpoints = None
    if checkpoint_name:
        exists = os.path.exists(checkpoint_name)
        checkpoints = _CheckpointRecorder(checkpoint_name, tsg)
        if exists:
            tsg, data = checkpoints.resume()

    def get_bar_text(limit, step_result):
        if step_result is None or "robustness" not in step_result:
            return str(limit)
        else:
            if "estimated_robustness" in step_result:
                return str(limit) + " O:{:.3f} ({:.3f})".format(step_result["robustness"],
                                                                step_result["estimated_robustness"])
            else:
                return str(limit) + " O:{:.3f}".format(step_result["robustness"])

    # This loops forever if the step method does not ensure that the
    # stopping condition is eventually satisfied.
    logging_display = logging.info_bar(manual=True) if not quiet else lambda x: None
    step_result = None
    with logging_display as bar:
        while not tsg.limit.finished():
            step_result = tsg.step()
            tsg.limit.add("generated_tests")
            data = tsg._append_data(data, step_result)
            tsg.finalize_step(data, step_result)
            bar.text(get_bar_text(tsg.limit, step_result))
            bar(1 - tsg.limit.remaining())

            if checkpoints:
                checkpoints.record(data)

        bar.text(get_bar_text(tsg.limit, step_result))
        bar(1)

    if checkpoints:
        checkpoints.done()

    tsg.finalize_run(data)
    data = data.infer_objects()
    return data


def run_n_replicas(cls, n_replicas: int, seed_generator=None, done=None, n_workers=1):
    """
    Runs multiple replicas of the test heuristic in parallel.

    Parameters:
    cls: A TestSuiteGenerator class
    n_replicas (int): Number of replicas to run.
    seed_factory (callable, optional): A callable that generates seeds for the replicas. Default is None.
    done (list, optional): A list of completed replicas. Default is None.
    n_workers (int, optional): Number of parallel workers. Default is 1 (no multiprocessing).

    Returns:
    tuple: A tuple containing the results dataframe and the list of completed replicas.

    Raises:
        SystemExit: If the number of workers is less than 1.
    """
    if seed_generator is None:
        seed_iterator = iter(range(1, n_replicas + 1))
        seed_generator = (lambda: next(seed_iterator))
    else:
        seed_generator = seed_generator

    # This is because the CI pipeline gets a segmentation fault for calling
    # garbage collection for some reason.
    garbage_collect = True

    def run_one_replica(idx, done):
        results = pd.DataFrame()
        if done is None:
            done = []

        seed = seed_generator()
        if not idx in done:
            tsg = cls()
            tsg.setup(seed=seed)
            result = run(tsg)

            result.insert(0, "Replica", idx)
            result.insert(1, "Seed", seed)
            results = pd.concat([results, result], ignore_index=True)

            done.append(idx)

        # Delete generator and force garbage collection. This is
        # especially important when using Matleb SUTs as several
        # Matlab instances take quite a lot of memory.
        del tsg
        if garbage_collect:
            gc.collect()

        return results, done

    if done is None:
        done = []

    if n_workers < 1:
        raise SystemExit("The number of workers must be positive.")
    elif n_workers == 1:
        # Do not use multiprocessing.
        replicas = []
        for idx in range(n_replicas):
            replicas.append(run_one_replica(idx, done))
    else:
        # Use multiprocessing
        indexes = range(n_replicas)
        replicas = Parallel(n_jobs=n_workers)(delayed(run_one_replica)(i, done) for i in indexes)

    results = pd.DataFrame()

    for r in replicas:
        results = pd.concat([results, r[0]], ignore_index=True)
        done.append(r[1])

    return results, done


def save_to_file(filename: str,
                 data: dict | pd.DataFrame
                 ):
    """Saves dataframe to file as a csv.

    Args:
        filename (str): Name of file to write
        data (pd.DataFrame): The data to be written.
    """

    if isinstance(data, dict):
        header, content = _dict_to_csv(data)
    elif isinstance(data, pd.DataFrame):
        header, content = _df_to_csv(data)
    else:
        raise Exception('Unknown data type')

    f = open(filename, 'w+')
    first = f.readline()
    # Prepend the header to content if this is a fresh file
    if first != header:
        content = f'{header}\n{content}'

    f.write(content)
    f.close()


def _df_to_csv(data: pd.DataFrame):
    # Pandas to_csv is a lossy function when the dataframe
    # contains structures like numpy arrays
    # content = data.to_csv(filename, index=False)

    header = ','.join(data.columns.tolist())
    content = ''
    for i in data.index:
        data_row = data.loc[i]

        row = []
        for entry in data_row:
            # Numpy arrays have to be converted to lists as otherwise they
            # get truncated in the middle when converted to a string and we lose data
            if isinstance(entry, np.ndarray):
                entry = entry.tolist()

            # Values and timestamps arrays
            if isinstance(entry, list) and len(entry) == 2:
                if isinstance(entry[0], np.ndarray):
                    entry[0] = entry[0].tolist()
                if isinstance(entry[1], np.ndarray):
                    entry[1] = entry[1].tolist()

            # Wrap arrays in quotes so pandas can take care of parsing them
            row.append(f'"{str(entry)}"' if isinstance(entry, list) else str(entry))

        content += ','.join(row) + '\n'

    return header, content


def _dict_to_csv(data: dict):
    row = []
    header = ','.join(data.keys())
    content = ''
    for i in data:
        entry = data[i]
        # Numpy arrays have to be converted to lists as otherwise they
        # get truncated in the middle when converted to a string and we lose data
        if isinstance(entry, np.ndarray):
            entry = entry.tolist()

        # Values and timestamps arrays
        if isinstance(entry, list) and len(entry) == 2:
            if isinstance(entry[0], np.ndarray):
                entry[0] = entry[0].tolist()
            if isinstance(entry[1], np.ndarray):
                entry[1] = entry[1].tolist()

        # Wrap arrays in quotes so pandas can take care of parsing them
        row.append(f'"{str(entry)}"' if isinstance(entry, list) else str(entry))

    content += ','.join(row) + '\n'
    return header, content


class OfflineTestGeneration(TestSuiteGenerator):
    """
    Implements a test heuristic for offline test generation using a specified generator.

    Parameters:
        sut (SystemUnderTest): The system under test.
        generator (TestGenerator): The generator used for test generation.
        ss (SearchSpace, optional): The search space. Defaults to None.
    """

    def __init__(self,
                 generator: TestGenerator,
                 sut: SystemUnderTest | None = None,
                 goal: Monitor | None = None,
                 limit: Limit | None = None
                 ):
        """
        Initializes the OfflineTestGeneration with a system under test, generator, and limit.

        Args:
            generator (TestGenerator): The generator used for test generation.
        """

        super().__init__(sut=sut, goal=goal, limit=limit)
        self.generator = generator

    def initialize(self):
        if self.search_space is None:
            raise Exception("Search space not set up when initializing the test suite generator.")

        self.generator.setup(search_space=self.search_space)

    def step(self):
        """
        Performs a single step of offline test generation.

        Returns:
            dict: The generated input feature vector as a dictionary.
        """
        # This assumes that the user has set a limit to test generation.
        # Otherwise an infinite loop might be encountered.
        input_fv, _, _ = self.generator.generate_next(remaining=self.limit.remaining())
        return input_fv.to_dict()


class ExploreExploitOneGoal(TestSuiteGenerator):
    """
    Implements a test heuristic that explores and exploits to achieve a single goal.

    Parameters:
        explore_generator (TestGenerator): The generator used for exploration.
        exploit_generator (TestGenerator): The generator used for exploitation.
        resources_for_exploration (float): Proportion of resources allocated for exploration.
        resources_for_training (float): Proportion of resources allocated for training.
        robustness_threshold (float): Threshold for robustness to be considered critical.
    """

    def __init__(self,
                 explore_generator: TestGenerator,
                 exploit_generator: TestGenerator,
                 resources_for_exploration: float = 0.2,
                 resources_for_training: float = 0.8,
                 robustness_threshold: float = 0.0,
                 sut: SystemUnderTest | None = None,
                 goal: Monitor | None = None,
                 limit: Limit | None = None
                 ):
        """
        Initializes the ExploreExploitOneGoal with system under test, generators, goal, and limits.

        Args:
            sut (SystemUnderTest): The system under test.
            explore_generator (TestGenerator): The generator used for exploration.
            exploit_generator (TestGenerator): The generator used for exploitation.
            goal (Monitor): The monitor defining the goal.
            limit (Limit): The limit object to define resource or execution limits.
            resources_for_exploration (float, optional): Proportion of resources allocated for exploration. Defaults to 0.2.
            resources_for_training (float, optional): Proportion of resources allocated for training. Defaults to 0.8.
            robustness_threshold (float, optional): Threshold for robustness to be considered critical. Defaults to 0.0.
        """
        super().__init__(sut=sut, goal=goal, limit=limit)

        self.explore_generator = explore_generator
        self.exploit_generator = exploit_generator

        self.resources_for_exploration = resources_for_exploration
        self.resources_for_training = resources_for_training

        self.min_robustness = 1.0
        self.robustness_threshold = robustness_threshold

    def __str__(self):
        return self.__class__.__name__ + "(" + str(self.explore_generator) + "," + str(self.exploit_generator) + ")"

    def initialize(self):
        if self.has_been_initialized: return
        super().initialize()
        
        if self.search_space is None:
            raise Exception("Search space not set up when initializing the test suite generator.")

        # Set up the generators.
        self.explore_generator.setup(search_space=self.search_space)
        if self.exploit_generator:
            self.exploit_generator.setup(search_space=self.search_space)

    def select_generator(self):
        """Selects an appropriate generator based on the used resources.

        Returns:
            TestGenerator: The selected generator.
        """

        resources_remaining = self.limit.resources_remaining()
        use_explore_generator = resources_remaining > 1 - self.resources_for_exploration

        if use_explore_generator:
            return self.explore_generator
        else:
            return self.exploit_generator

    def train_generator(self, generator):
        """Trains the given generator if training resources allow it."""

        resources_remaining = self.limit.resources_remaining()
        train_generator = resources_remaining > 1 - self.resources_for_training
        if train_generator:
            training_performance = generator.train_on_search_space(remaining=resources_remaining)
        else:
            training_performance = {}

        return training_performance

    def step(self):
        """
        Performs a single step of the explore-exploit heuristic.

        Returns:
            dict: The result of the step, including generator used, robustness, input and output feature vectors.
        """

        # Select the generator to be trained and which is to be used to
        # generate a test with.
        generator = self.select_generator()

        # Train the generator.
        training_performance = self.train_generator(generator)
        if "training_time" in training_performance:
            self.limit.add("training_time", training_performance["training_time"])

        # Generate a test.
        resources_remaining = self.limit.remaining()
        input_fv, robustness_estimate, generation_performance = generator.generate_next(remaining=resources_remaining)
        if "generation_time" in generation_performance:
            self.limit.add("generation_time", generation_performance["generation_time"])

        # Execute a test.
        output_fv, output_features = self.sut.execute_test_fv(input_fv)
        self.limit.add("executed_tests")
        if "execution_time" in output_features:
            self.limit.add("execution_time", output_features["execution_time"])

        # Find robustness for the system trace.
        robustness = self.goal(input_fv | output_fv)
        if robustness <= self.robustness_threshold:
            self.limit.add("critical_test_count")
        self.min_robustness = min(robustness, self.min_robustness)

        self.search_space.record(input_fv, robustness)

        r = {
            "generator": generator.__class__.__name__,
            "robustness": robustness,
            "estimated_robustness": robustness_estimate
        }
        r = r | input_fv.to_dict() | output_fv.to_dict()
        return r


class ProbabilisticExploreExploitOneGoal(ExploreExploitOneGoal):
    """
    Extends ExploreExploitOneGoal by introducing a probabilistic selection mechanism for the generator.
    """

    def select_and_train_generator(self):
        """
        Selects and trains the appropriate generator based on a probabilistic mechanism.

        Returns:
            TestGenerator: The selected generator (explore or exploit).
        """
        if self.search_space.rng.rand() < self.min_robustness + 0.05:
            generator = self.explore_generator
        else:
            generator = self.exploit_generator
            generator.train_on_search_space(remaining=self.limit.resources_remaining())

        return generator
