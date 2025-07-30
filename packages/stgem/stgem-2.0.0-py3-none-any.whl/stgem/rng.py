import os
import random

import numpy as np
import torch


class RandomNumberGenerator:
    """For consistent results, wrap Python's, Numpy's, and Torch's random
    number generators into a single class that is initializable with a single
    integer seed. Supports setting the random number generator state for
    returning to a previous state."""

    def __init__(self, seed=None):
        if seed is None:
            # Select a random seed.
            seed = random.randint(0, 2 ** 15)

        self.seed = seed
        self.reset()

    def reset(self):
        self.rng_python = random.Random(self.seed)
        self.rng_numpy = np.random.RandomState(self.seed)
        self.rng_torch = torch.Generator()
        self.rng_torch.manual_seed(self.seed)

        # Notice that making Pytorch deterministic makes it slower.
        torch.use_deterministic_algorithms(mode=True)
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

    def get_rng(self, rng_id):
        match rng_id.lower():
            case "python":
                rng = self.rng_python
            case "numpy":
                rng = self.rng_numpy
            case "torch":
                rng = self.rng_torch
            case _:
                raise ValueError("Unknown random number generator id '{}'.".format(rng_id))

        return rng

    def __getstate__(self):
        # This method is used for serialization
        return {
            "seed": self.seed,
            "state_python": self.rng_python.getstate(),
            "state_numpy": self.rng_numpy.__getstate__(),
            "state_torch": self.rng_torch.get_state(),
        }

    def get_state(self):
        state_python = self.rng_python.getstate()
        state_numpy = self.rng_numpy.__getstate__()
        state_torch = self.rng_torch.get_state()

        return (state_python, state_numpy, state_torch)

    def __setstate__(self, state):
        # This method is used for de-serialization
        self.seed = state["seed"]
        self.reset()
        self.rng_python.setstate(state["state_python"])
        self.rng_numpy.__setstate__(state["state_numpy"])
        self.rng_torch.set_state(state["state_torch"])

    def set_state(self, state):
        self.rng_python.setstate(state[0])
        self.rng_numpy.__setstate__(state[1])
        self.rng_torch.set_state(state[2])

    def set_torch_global_rng_from(self):
        """Save the current Pytorch global RNG state and set the global RNG
        state to match the state of this RNG. This is useful when using
        Pytorch's functions that do not allow to pass an RNG as a parameter."""

        state_torch_global = torch.get_rng_state()
        torch.set_rng_state(self.get_state()[2])

        return state_torch_global

    def set_from_torch_global_rng(self, prev_state_torch_global=None):
        """Set this RNG Pytorch state to match the current state of Pytorch's
        global RNG and restore the Pytorch global RNG to the given state (if
        given)."""
        state_torch_global = torch.get_rng_state()
        self.rng_torch.set_state(state_torch_global)
        if prev_state_torch_global is not None:
            torch.set_rng_state(prev_state_torch_global)
