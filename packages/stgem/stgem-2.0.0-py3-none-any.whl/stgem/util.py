import copy

import inspect


def filter_arguments(dictionary, target):
    """Returns a dictionary where all keys that are not target's attributes are
    removed."""

    allowed_keys = [param.name for param in inspect.signature(target).parameters.values() if
                    param.kind == param.POSITIONAL_OR_KEYWORD]
    return {key: dictionary[key] for key in dictionary if key in allowed_keys}


def merge_dictionary(d1, d2):
    """Merges two dictionaries so that they have common keys. Keys from d1 take
    preference."""

    d1 = copy.deepcopy(d1)
    for key in d2:
        if key not in d1:
            d1[key] = copy.deepcopy(d2[key])

    return d1
