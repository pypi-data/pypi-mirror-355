from stgem import SearchSpace
from stgem.limit import ExecutionCount
from stgem.system.mo3d import MO3D
from stgem.task import falsify
from stgem.testgenerator.random import RandomGenerator
from stgem.testgenerator.random.model import Uniform, Halton, LHS


def test_random_generator():
    critical_tests, all_tests, tester = falsify(
        sut=MO3D(),
        formula="y1 > 10",
        limit=ExecutionCount(1),
        exploit_generator=RandomGenerator(),
        seed=0
    )


def test_random_models():
    sut = MO3D()
    search_space = SearchSpace(input_vector=sut.new_ifv())

    # Uniform random search.
    model = Uniform({"minimum_distance": 0.2})
    model.setup(search_space)
    rng = model.search_space.rng
    state = rng.get_state()
    X = model.generate_test().reshape(-1)
    rng.set_state(state)
    Y = model.generate_test().reshape(-1)
    assert (X == Y).all()

    # Halton sequence.
    model = Halton()
    model.setup(search_space)
    X = model.generate_test().reshape(-1)

    # LHS.
    try:
        model = LHS()
        model.setup(search_space)
        assert False
    except ValueError:
        pass
    model = Halton({"samples": 5})
    model.setup(search_space)
    X = model.generate_test().reshape(-1)
    try:
        model.generate_test(5)
        assert False
    except:
        pass
