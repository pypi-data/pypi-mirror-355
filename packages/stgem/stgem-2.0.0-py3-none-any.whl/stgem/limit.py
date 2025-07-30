import math
import time

from stgem import config


class Limit:
    """Class for keeping track of quantities that represent available resources
    or achievement of goals. The assumption is that each quantity is initially
    0 and it has a positive upper limit. A quantity is updated by adding to its
    value by an external call or it is updated automatically. The remaining
    quantity is reported as a number in [0,1] scaled according to the specified
    limits. The overall remaining quantity is the minimum remaining quantity
    value."""

    default_quantities = []

    def __init__(self, limits: dict[str, float | int] = None):
        """
        Initialize the Limit object.

        Args:
            limits (dict[str, float | int], optional): A dictionary specifying the upper limits for each quantity.
                The keys are quantity names and the values are the corresponding upper limits. Default is None.
        """
        # Setup the quantities and their initial values.
        self.quantities = {q: 0 for q in self.default_quantities}
        # Setup default quantity limits to be from 0 to infinity.
        self.limits = {q: math.inf for q in self.quantities}

        # Setup default reporting functions. These functions can be used to
        # compute more complex relations than just returning the quantity
        # value. This is mainly used for implementing the wall time quantity.
        def make_func(q):
            # This is to work around Python variable scoping.
            return lambda quantities: quantities[q]

        self.report = {q:make_func(q) for q in self.quantities}

        # Set up the limits if available.
        if limits is not None:
            self.update_limits(limits)
    
    def __str__(self):
        # Here we define some shorthand identifier for various possible quantities.
        short = {
            "executed_tests": "E",
            "critical_test_count": "C",
            "wall_time": "WT",
        }
        s = ""
        for quantity in self.quantities:
            if self.limits[quantity] != math.inf:
                short = short[quantity] if quantity in short else quantity
                value = self.report[quantity](self.quantities)
                if isinstance(value, float):
                    value = round(value, 1)
                s += "{}:{}/{} ".format(short, value, self.limits[quantity])
            
        return s[:-1]

    def __and__(self, other):
        """
        Combines the current Limit instance with another Limit instance to create a CombinedLimit.

        Args:
            other (Limit or CombinedLimit): Another Limit instance to combine with.

        Returns:
            CombinedLimit: A new CombinedLimit instance combining the two limits.

        Raises:
            ValueError: If the other object is not a Limit or CombinedLimit instance.
        """
        if isinstance(other, CombinedLimit):
            limits = [self] + other.get_limits()
        elif isinstance(other, Limit):
            limits = [self] + [other]
        else:
            raise ValueError("Unsupported type '{}' to be combined with a Limit.".format(type(other)))

        return CombinedLimit(limits)

    def start(self):
        """ Placeholder method to be overridden by subclasses"""
        pass

    def update_limits(self, limits: dict[str, float | int]):
        """
        Updates the limits for the quantities.

        Args:
            limits (dict[str, float | int]): A dictionary specifying the new upper limits for each quantity.
                The keys are quantity names and the values are the corresponding upper limits.

        Raises:
            ValueError: If the new limit is below the current value.
        """
        # Force a configured upper limit if configured. This is useful for
        # faster debunning.
        if __debug__ and config.force_maximum_limit > 0:
            for k, v in limits.items():
                if v > config.force_maximum_limit:
                    limits[k] = config.force_maximum_limit

        for quantity, limit in limits.items():
            if quantity in self.quantities and limit < self.quantities[quantity]:
                raise ValueError(
                    "Cannot update quantity limit from '{}' to '{}' since it is below the current value '{}'.".format(
                        quantity, limit, self.quantities[quantity]))

            # If the quantity does not exist, we add it here. This can thus be
            # used to add new quantities on top of the default ones.
            if quantity not in self.quantities:
                self.quantities[quantity] = 0

            self.limits[quantity] = limit

    def add(self, quantity: str, amount: float | int = 1):
        """
        Adds an amount to the specified quantity.

        Args:
            quantity (str): The name of the quantity to be updated.
            amount (float | int, optional): The amount to be added to the quantity. Default is 1.

        Raises:
            ValueError: If the addition makes the quantity value negative.
        """
        # We do not want to check here that amount is positive as decrementing
        # by allowing the addition of a negative allows some flexibility for
        # the user. The method used returns reasonable values even in the
        # prosence of nonpositive value.
        if quantity in self.quantities:
            new_value = self.quantities[quantity] + amount
            if new_value < 0:
                raise ValueError("Adding a value to a quantity cannot make it negative.")
            self.quantities[quantity] = new_value

    def used(self):
        """
        Return the usage ratio of each quantity as a number in [0,1].

        Returns:
            dict: A dictionary with quantity names as keys and their used ratio as values.
        """

        result = {}
        for quantity in self.quantities:
            start = 0
            end = self.limits[quantity]
            value = self.report[quantity](self.quantities)
            if value >= start:
                used = min(1, (value - start) / (end - start))
            else:
                used = 0.0

            result[quantity] = used

        return result

    def get_limit(self, limit):
        return self.limits[limit]

    def remaining(self):
        """
        Return the minimum remaining quantity among all quantities as a number in [0,1].

        Returns:
            float: The minimum remaining quantity.
        """

        return 1 - max(self.used().values())

    def resources_remaining(self):
        """
        Placeholder method to return the remaining resources. To be overridden by subclasses.

        Returns:
            float: Default is 1.0.
        """
        return 1.0

    def goals_remaining(self):
        """
        Placeholder method to return the remaining goals. To be overridden by subclasses.

        Returns:
            float: Default is 1.0.
        """
        return 1.0

    def finished(self):
        """
        Check if any of the quantities is used up.

        Returns:
            bool: True if any quantity is used up, otherwise False.
        """

        return self.remaining() == 0


class ResourceLimit(Limit):
    """Class for keeping track of available resources for test heuristics. A
    resource must either be consumed by an external call or it is consumed
    automatically.

    The following resources need to be consumed by an external call:

    generated_tests: How many tests have been generated?
    executed_tests: How many tests have been executed?
    execution_time: How much execution time has passed?
    generation_time: How much generation time has passed?
    training_time: How much training time has passed?

    The following quantity is automatically consumed:

    wall_time: How much wall time has passed since the method start was called"""

    default_quantities = ["generated_tests", "executed_tests", "execution_time", "generation_time", "training_time", "wall_time"]

    def __init__(self, limits: dict[str, float | int] = None):
        super().__init__(limits)
        """
        Initialize the ResourceLimit object.

        Args:
            limits (dict[str, float | int], optional): A dictionary specifying the upper limits for each resource. Default is None.
        """

        # Set up (automatic) wall time reporting. We start automatic wall time
        # consumption only when the start method has been called.
        self.initial_wall_time = None
        self.report["wall_time"] = lambda quantities: time.perf_counter() - self.initial_wall_time if self.initial_wall_time is not None else 0

    def start(self):
        """Starts the wall time measurement"""
        if self.initial_wall_time is None:
            self.initial_wall_time = time.perf_counter()

    def resources_remaining(self):
        """
        Returns the remaining resources as a fraction of the limit.

        Returns:
            float: The remaining resources.
        """
        return self.remaining()


class GoalLimit(Limit):
    """
    Class for keeping track if goals have been achieved or not.

    The following goals need to be tracked by an external call:
    - critical_test_count: How many critical tests have been encountered so far
    """
    default_quantities = ["critical_test_count"]

    def goals_remaining(self):
        return self.remaining()


class CombinedLimit(Limit):
    """
    This class combines several Limit objects that result when the & operation is used.
    This class ensures that ResourceLimit objects and GoalLimit objects are kept separate so that their remaining quantities can separately be queried using the methods resources_remaining and goals_remaining.
    """

    def __init__(self, limits: list):
        """
        Initialize the CombinedLimit object.

        Args:
            limits (list): A list of Limit objects to combine. The list must contain at least one Limit object.

        Raises:
            ValueError: If no Limit objects are specified or if an object in the list is not a ResourceLimit or GoalLimit.
        """
        if len(limits) == 0:
            raise ValueError("No Limit objects specified.")

        self.resources = []
        self.goals = []
        for limit in limits:
            if isinstance(limit, ResourceLimit):
                self.resources.append(limit)
            elif isinstance(limit, GoalLimit):
                self.goals.append(limit)
            else:
                raise ValueError("Combined limits can only be Resource objects or Goal objects.")
    
    def __str__(self):
        return " ".join(str(q) for q in self.resources) + " " + " ".join(str(q) for q in self.goals)

    def __and__(self, other):
        """
        Combines the current CombinedLimit instance with another Limit or CombinedLimit instance.

        Args:
            other (Limit or CombinedLimit): Another Limit or CombinedLimit instance to combine with.

        Returns:
            CombinedLimit: A new CombinedLimit instance combining the two limits.

        Raises:
            ValueError: If the other object is not a Limit or CombinedLimit instance.
        """
        if isinstance(other, CombinedLimit):
            limits = self.get_limits() + other.get_limits()
        elif isinstance(other, Limit):
            limits = self.get_limits() + [other]
        else:
            raise ValueError("Unsupported type '{}' to be combined with a Limit.".format(type(other)))

        return CombinedLimit(limits)

    def start(self):
        """ Starts all the limits in resources and goals."""
        for limit in self.resources + self.goals:
            limit.start()

    def update_limits(self, limits: dict[str, float | int]):
        """
        Updates the limits for all the Limit objects in resources and goals.

        Args:
            limits (dict[str, float | int]): A dictionary specifying the new upper limits for each quantity.
        """
        for limit in self.resources + self.goals:
            limit.update_limits(limits)

    def get_limits(self):
        """
        Returns the combined list of ResourceLimit and GoalLimit objects.

        Returns:
            list: The combined list of Limit objects.
        """
        return self.resources + self.goals

    def add(self, quantity: str, amount: float | int = 1):
        """Adds an amount to a specified quantity in all the Limit objects."""
        for limit in self.resources + self.goals:
            limit.add(quantity, amount)

    def _used(self, limits):
        """
        Returns the used quantities for all the specified Limit objects.

        Args:
            limits (list): The list of Limit objects.

        Returns:
            dict: A dictionary with quantity names as keys and their used ratio as values.
        """
        result = {}
        for limit in limits:
            u = limit.used()
            for q in u:
                if q in result:
                    result[q] = max(result[q], u[q])
                else:
                    result[q] = u[q]
        return result

    def used(self):
        """ Returns the used quantities for all the Limit objects."""
        return self._used(self.resources + self.goals)

    def remaining(self):
        """ Returns the minimum remaining quantity among all the Limit objects."""
        return 1 - max(self.used().values())

    def resources_remaining(self):
        """resources_remaining(self): Returns the minimum remaining resource quantity."""
        return 1 - max(self._used(self.resources).values())

    def goals_remaining(self):
        """ Returns the minimum remaining goal quantity."""
        return 1 - max(self._used(self.goals).values())


def ExecutionCount(n: int) -> ResourceLimit:
    assert n > 0
    return ResourceLimit({"executed_tests": n})


def TestCount(n: int) -> ResourceLimit:
    assert n > 0
    return ResourceLimit({"generated_tests": n})


def CriticalTestCount(n: int) -> GoalLimit:
    assert n > 0
    return GoalLimit({"critical_test_count": n})


def WallTime(seconds: float) -> ResourceLimit:
    assert seconds > 0
    return ResourceLimit({"wall_time": seconds})
