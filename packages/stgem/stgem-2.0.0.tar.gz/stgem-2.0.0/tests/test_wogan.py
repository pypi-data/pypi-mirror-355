from stgem.limit import ExecutionCount
from stgem.system.mo3d import MO3D
from stgem.task import falsify, generate_critical_tests
from stgem.testsuitegenerator.wogan import WOGAN_TestSuiteGenerator


def test_falsify_WOGAN():
    # Test falsify with a WOGAN generator.
    falsify(MO3D(), "y1 > 10", 30, exploit_generator="WOGAN")


def test_WOGAN():
    # Test falsify with the WOGAN test suite generator.
    falsify(
        sut=MO3D(),
        formula="y1 > 10",
        limit=ExecutionCount(30),
        test_suite_generator=WOGAN_TestSuiteGenerator()
    )

def test_WOGAN_generator_transfer():
    # Test transfering a WOGAN generator to a new instance of WOGAN.
    sut = MO3D()
    formula = "y1 > 10"
    _, _, tester = generate_critical_tests(
        sut=sut,
        formula=formula,
        limit=ExecutionCount(30),
        test_suite_generator=WOGAN_TestSuiteGenerator()
    )

    generator = tester.generator
    tsg = WOGAN_TestSuiteGenerator()
    tsg.setup(sut=sut)
    tsg.set_generator(random_generator=generator)
    tsg.set_generator(generator=generator)
    generate_critical_tests(
        sut=sut,
        formula=formula,
        limit=ExecutionCount(30),
        test_suite_generator=tsg
    )

if __name__ == "__main__":
    test_WOGAN_generator_transfer()
