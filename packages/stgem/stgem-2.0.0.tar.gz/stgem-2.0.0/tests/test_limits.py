from time import sleep

from stgem.limit import *

eps = 1e-5


def test_resources():
    # Test resources.
    resource = ExecutionCount(5)
    resource.start()
    assert not resource.finished()
    resource.add("executed_tests")
    assert not resource.finished()
    assert abs(resource.remaining() - 0.8) < eps
    resource.add("executed_tests", 3)
    assert abs(resource.remaining() - 0.2) < eps
    resource.add("executed_tests", 1)
    assert resource.finished()

    limits = {
        "training_time": 5
    }
    resource = ResourceLimit(limits)
    resource.start()
    assert not resource.finished()
    resource.add("training_time", 2.5)
    assert (resource.remaining() - 0.5) < eps
    resource.add("executed_tests", 1000)
    assert (resource.remaining() - 0.5) < eps

    resource = WallTime(3)
    assert resource.initial_wall_time is None
    assert resource.report["wall_time"]({"wall_time": 1}) == 0.0
    resource.start()
    assert not resource.finished()
    sleep(3)
    assert resource.finished()


def test_goals():
    # Test goals.
    goal = CriticalTestCount(5)
    goal.start()
    assert not goal.finished()
    goal.add("critical_test_count")
    assert not goal.finished()
    assert abs(goal.remaining() - 0.8) < eps
    goal.add("critical_test_count", 3)
    assert abs(goal.remaining() - 0.2) < eps
    goal.add("training_time")
    assert abs(goal.remaining() - 0.2) < eps
    goal.add("critical_test_count", 1)
    assert goal.finished()


def test_limits():
    # Test limits.
    resource = ExecutionCount(5)
    resource.start()
    new_limits = {
        "executed_tests": 8
    }
    resource.update_limits(new_limits)
    resource.add("executed_tests", 5)
    assert not resource.finished()
    new_limits = {
        "executed_tests": 4
    }
    try:
        resource.update_limits(new_limits)
        assert False
    except ValueError:
        pass
    resource.add("executed_tests", 3)
    assert resource.finished()


def test_combined_limits():
    # Test combined limits.
    resource = ExecutionCount(5)
    goal = CriticalTestCount(2)
    limit = resource & goal
    limit.start()

    assert isinstance(limit, CombinedLimit)

    limit.add("executed_tests", 1)
    limit.add("critical_test_count", 1)
    assert not limit.finished()
    assert abs(limit.remaining() - 0.5) < eps
    assert abs(limit.resources_remaining() - 0.8) < eps
    assert abs(limit.goals_remaining() - 0.5) < eps

    limit = WallTime(10) & ExecutionCount(2)
    limit.start()
    assert not limit.finished()
    limit.add("executed_tests")
    assert not limit.finished()
    limit.add("executed_tests")
    assert limit.finished()
