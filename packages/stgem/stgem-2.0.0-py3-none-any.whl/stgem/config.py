import os

# Device to be used by torch
device = "cpu"

# Enforce maximum limit on resources and goals. This is enforced only if
# __debug__ is True and force_maximum_limit > 0.
force_maximum_limit = 0

# Enforce faster falsification parameters for testing. This is enforced only if
# __debug__ is True and environment variable is set.
faster_parameters = os.getenv("CICD") is not None
