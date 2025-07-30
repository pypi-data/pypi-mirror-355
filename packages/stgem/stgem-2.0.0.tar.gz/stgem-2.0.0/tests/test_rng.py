import random
import numpy as np
import torch

from stgem.rng import RandomNumberGenerator

def test_rng():
    rng = RandomNumberGenerator(seed=25321)

    rng_python = rng.get_rng("python")
    rng_numpy = rng.get_rng("numpy")
    rng_torch = rng.get_rng("torch")
    try:
        rng.get_rng("foo")
        assert False
    except ValueError:
        pass
    
    def get_normal_noise(rng):
        rng_python = rng.get_rng("python")
        rng_numpy = rng.get_rng("numpy")
        rng_torch = rng.get_rng("torch")
        X = [rng_python.gauss() for _ in range(5)]
        Y = rng_numpy.normal(size=5)
        Z = torch.randn(5, generator=rng_torch)
        return X, Y, Z
    
    get_normal_noise(rng)
    state = rng.get_state()
    X1, Y1, Z1 = get_normal_noise(rng)
    rng.set_state(state)
    X2, Y2, Z2 = get_normal_noise(rng)
    
    assert X1 == X2
    assert (Y1 == Y2).all()
    assert (Z1 == Z2).all()
