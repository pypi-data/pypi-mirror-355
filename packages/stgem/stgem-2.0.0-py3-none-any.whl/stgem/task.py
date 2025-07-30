import time

import pandas as pd

from stgem.features import PiecewiseConstantSignal
from stgem.limit import CriticalTestCount, ExecutionCount, TestCount, Limit
from stgem.monitor.stl import STLRobustness, as_robustness_monitor
from stgem.sut import SystemUnderTest, as_SystemUnderTest
from stgem.testgenerator import TestGenerator
from stgem.testgenerator.random import RandomGenerator, Uniform, LHS, Halton
from stgem.testsuitegenerator import TestSuiteGenerator, run, OfflineTestGeneration, ExploreExploitOneGoal
from stgem.testsuitegenerator.diffusion import Diffusion, Diffusion_Model
from stgem.testsuitegenerator.diffusion import get_parameters as get_DIFFUSION_parameters
from stgem.testsuitegenerator.ogan import OGAN, OGAN_Model
from stgem.testsuitegenerator.ogan import get_parameters as get_OGAN_parameters
from stgem.testsuitegenerator.wogan import WOGAN, WOGAN_Model
from stgem.testsuitegenerator.wogan import get_parameters as get_WOGAN_parameters

def as_Generator(generator: str | None, sut: SystemUnderTest | None = None) -> TestGenerator:
    """Converts a string into a test generator based on some default settings.
    Otherwise returns the generator as is.

    Parameters:
        generator (str, | None): The type of generator to be used. Can be None,
            "Random", "OGAN", "WOGAN", "Diffusion, or an actual TestGenerator
            instance.
        sut (SystemUnderTest | None, optional): The system under test (only
            used when generator is a string). Defaults to None.

    Returns:
        TestGenerator: The corresponding generator object or None if generator
            is None.

    Raises:
        ValueError: If an unknown generator string is provided.
    """

    if not isinstance(generator, str):
        return generator

    has_signal_input = False
    if sut is not None:
        for feature in sut.new_ifv().flatten_to_list():
            if isinstance(feature, PiecewiseConstantSignal):
                has_signal_input = True
                break

    match generator.upper() if generator is not None else None:
        case None:
            generator = None
        case "RANDOM":
            generator = RandomGenerator()
        case "DIFFUSION":
            network_type = "convolution" if has_signal_input else "dense"
            parameters = get_DIFFUSION_parameters("default", 1500)
            generator_parameters = parameters["generator_parameters"]
            model_parameters = parameters["model_parameters"]
            generator = Diffusion(parameters=generator_parameters, models=Diffusion_Model(model_parameters))
        case "OGAN":
            network_type = "convolution" if has_signal_input else "dense"
            parameters = get_OGAN_parameters("default", 1500, network_type=network_type)
            generator_parameters = parameters["generator_parameters"]
            model_parameters = parameters["model_parameters"]
            generator = OGAN(parameters=generator_parameters, models=OGAN_Model(model_parameters))
        case "WOGAN":
            network_type = "convolution" if has_signal_input else "dense"
            parameters = get_WOGAN_parameters("default", network_type=network_type)
            generator_parameters = parameters["generator_parameters"]
            model_parameters = parameters["model_parameters"]
            generator = WOGAN(parameters=generator_parameters, models=WOGAN_Model(model_parameters))
        case _:
            raise ValueError("Unknown generator '{}'.".format(generator))

    return generator


def falsify(sut,
            formula: str | STLRobustness,
            limit: int | Limit = None,
            exploit_generator: str | TestGenerator = None,
            test_suite_generator: TestSuiteGenerator = None,
            robustness_thresshold: float = 0.0,
            seed: int = None,
            rng: RandomGenerator | None = None,
            checkpoint_name: str | None = None,
            strict_horizon_check: bool | None = None,
            sampling_period: float | None = None):
    """Attempts to falsify an STL formula for a given system under test. Uses
    either a provided test suite generator or a test generator. The default
    test generator used is OGAN.

    Args:
        sut (SystemUnderTest): The system under test.
        formula (str | STLRobustness): The STL formula to be falsified.
        limit (Limit | int): A Limit object defining how many tests are
            generated. Optionally an integer n can be given to stand for
            TestCount(n).
        exploit_generator (str | TestGenerator | None, optional): The generator
            to be used for exploitation phase. Default is None.
        test_suite_generator (TestSuiteGenerator | None, optional): The test
            suite generator to be used for test generator. Defaults to None.
        robustness_threshold (float, optional): Threshold for determining
            objective. Default is 0.0.
        seed (int | None, optional): Random number generator seed. Defaults to
            None.
        rng (RandomNumberGenerator | None, optional): The random number
            generator used in the falsification.
        checkpoint_name (str | None, optional). The checkpoint name. Defaults
            to None.
        strict_horizon_check (bool | None, optional): Specifies if strict
            horizon check is used when the STL formula is given as a string.
            Defaults to None.
        sampling_period (float | None, optional): Specifies the sampling period
            when the STL formula is given as a string. Defaults to None.

    Returns:
        Results of generate_critical_tests() with limit = 1, i.e., one critical
        test result.

    Raises:
        ValueError: If both a test generator and a test suite generator have
            been specified.
    """

    if isinstance(limit, int):
        limit = ExecutionCount(limit)
    
    if exploit_generator is not None and test_suite_generator is not None:
        raise ValueError("Specify either an exploit generator or a test suite generator.")

    # We stop when the first critical test has been found.
    limit = limit & CriticalTestCount(1)

    if exploit_generator is None and test_suite_generator is None:
        exploit_generator = "OGAN"

    return generate_critical_tests(
        sut=sut,
        formula=formula,
        limit=limit,
        generator=exploit_generator,
        test_suite_generator=test_suite_generator,
        robustness_threshold=robustness_thresshold,
        seed=seed,
        rng=rng,
        checkpoint_name=checkpoint_name,
        strict_horizon_check=strict_horizon_check,
        sampling_period=sampling_period
    )


def generate_critical_tests(sut: SystemUnderTest,
                            formula: str | STLRobustness,
                            limit: int | Limit,
                            generator: TestGenerator | str | None = None,
                            test_suite_generator: TestSuiteGenerator | None = None,
                            robustness_threshold: float = 0,
                            seed: int = None,
                            rng: RandomGenerator | None = None,
                            checkpoint_name: str | None = None,
                            strict_horizon_check: bool | None = None,
                            sampling_period: float | None = None):
    """Generates critical tests for a given system under test and STL formula.
    Uses either a provided test suite generator or a test generator. The
    default test generator used is OGAN.

    Args:
        sut (SystemUnderTest): The system under test.
        formula (str | STLRobustness): The STL formula to be tested.
        limit (Limit | int): A Limit object defining how many tests are
            generated. Optionally an integer n can be given to stand for
            TestCount(n).
        generator (TestGenerator | str | None, optional): The generator to be
            used for test generation either as a TestGenerator object or as a
            string signifying one of the default test generators. Default is
            None.
        test_suite_generator (TestSuiteGenerator | None, optional): The test
            suite generator to be used for test generator. Defaults to None.
        robustness_threshold (float, optional): Threshold for determining
            objective. Default is 0.0.
        seed (int | None, optional): Random number generator seed. Defaults to
            None.
        rng (RandomNumberGenerator | None, optional): The random number
            generator used in the falsification.
        checkpoint_name (str | None, optional). The checkpoint name. Defaults
            to None.
        strict_horizon_check (bool | None, optional): Specifies if strict
            horizon check is used when the STL formula is given as a string.
            Defaults to None.
        sampling_period (float | None, optional): Specifies the sampling period
            when the STL formula is given as a string. Defaults to None.

    Returns:
        Tuple containing critical results, all results, and the tester object.

    Raises:
        ValueError: If both a test generator and a test suite generator have
            been specified.
    """

    if isinstance(limit, int):
        limit = ExecutionCount(limit)

    if generator is not None and test_suite_generator is not None:
        raise ValueError("Specify either a generator or a test suite generator.")

    if generator is None and test_suite_generator is None:
        exploit_generator = "OGAN"
    
    strict_horizon_check = strict_horizon_check if strict_horizon_check is not None else True

    sut = as_SystemUnderTest(sut)
    if test_suite_generator is None:
        exploit_generator = as_Generator(generator, sut)
        resources_for_exploration = 0.2 if exploit_generator else 1
        tsg = ExploreExploitOneGoal(
            explore_generator=RandomGenerator(),
            exploit_generator=exploit_generator,
            resources_for_exploration=resources_for_exploration,
            resources_for_training=1.0,
            robustness_threshold=robustness_threshold
        )
    else:
        tsg = test_suite_generator

    tsg.setup(sut=sut,
              goal=as_robustness_monitor(formula, input_fv=sut.new_ifv(), strict_horizon_check=strict_horizon_check, sampling_period=sampling_period),
              limit=limit,
              seed=seed,
              rng=rng
    )

    start = time.time()
    print("\nAttempting to falsify {} using {} ".format(formula, tsg))
    results = run(tsg, checkpoint_name=checkpoint_name)
    end = time.time()

    print("{} tests generated and executed in {:.2f} seconds, {:.2f} tests/s.".format(len(results), end - start, len(results) / (end - start)))

    critical_results = results[results["robustness"] <= robustness_threshold]
    if robustness_threshold == 0:
        what = "counterexample"
    else:
        what = "critical test"
    if len(critical_results) == 1:
        print("Found 1 {} for formula {}.".format(what, formula))
    else:
        what = what + "s"
        print("Found {} {} for formula {}, {:.2f}% of all executed tests".format(len(critical_results), what, formula, 100*len(critical_results) / len(results)))
    pd.option_context("display.max_cols", None)
    pd.option_context("display.max_rows", None)
    pd.set_option("display.width", None)

    if len(critical_results) > 0:
        if robustness_threshold > 0:
            print()
            print(critical_results.sort_values(by="robustness", ascending=True).to_string(index=False))
        else:
            print()
            print(critical_results.to_string(index=False))

    return critical_results, results, tsg


def generate_tests_offline(sut, limit: int | Limit, generator: str = "Uniform"):
    """Generates tests offline for a given system under test (SUT).

    Args:
        sut (SystemUnderTest): The system under test.
        limit (Limit | int): A Limit object defining how many tests are
            generated. Optionally an integer n can be given to stand for
            TestCount(n).
        generator (TestGenerator | str, optional): The generator to be used for
            test generation either as a TestGenerator object or as a string
            signifying one of the default test generators. Default is
            "Uniform".

    Returns:
        pd.DataFrame: DataFrame containing the results of the test generation process.

    Raises:
        ValueError:
            - If LHS sampling plan is used without specifying the number of tests.
            - If the string generator is not recognized.
    """

    if isinstance(limit, int):
        limit = TestCount(limit)

    if not isinstance(generator, TestGenerator):
        match generator:
            case "Uniform":
                mo = Uniform()
            case "LHS":
                n = limit.get_limit("generated_tests")
                if n == float("inf"): 
                    raise ValueError("LHS test generator requires to know the number of tests in advance.")
                mo = LHS({"samples": n})
            case "Halton":
                mo = Halton()
            case _:
                raise ValueError("Unknown generator '{}'".format(generator))
        generator = RandomGenerator(models=mo)

    print("\nGenerating tests using {}".format(generator.__class__.__name__))
    start = time.time()
    tester = OfflineTestGeneration(generator=generator)
    tester.setup(sut=as_SystemUnderTest(sut), limit=limit)
    results = run(tester)
    end = time.time()

    print("{} tests generated in {:.2f} seconds, {:.2f} tests/s.".format(len(results), end - start, len(results) / (end - start)))

    pd.option_context("display.max_cols", None)
    pd.option_context("display.max_rows", None)
    pd.set_option("display.width", None)

    print("All tests:")
    print(results)
    return results
