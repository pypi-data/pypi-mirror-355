class AlgorithmException(Exception):
    pass


class GenerationException(Exception):
    pass


class FeatureNotFoundError(Exception):

    def __init__(self, name):
        super().__init__(name)
        self.name = name

    def __str__(self):
        return "No feature with name '{}' exists.".format(self.name)


