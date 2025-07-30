import gymnasium as gym
import numpy as np
import torch

from stgem.limit import ExecutionCount
from stgem.system.gym import GYM, extract_gym_features
from stgem.task import generate_critical_tests


def set_seed(n):
    np.random.seed(n)
    torch.manual_seed(n)


def test_gym(seed=0):
    env = gym.make('MountainCarContinuous-v0', render_mode=None)
    time_steps = 100

    inputs, outputs = extract_gym_features(env=env, time_steps=time_steps)

    sut = GYM(
        env=env,
        inputs=inputs,
        outputs=outputs,
    )

    # observation_0 is the position of the car along the x-axis where >= 0.45 is the goal position
    critical_tests, all_tests, tester = generate_critical_tests(
        sut=sut,
        formula=f'always[0, {str(time_steps - 2)}] (eventually[0, 1] (observation_0 <= 0.45) )',
        limit=ExecutionCount(10),
        generator='OGAN'
    )


if __name__ == '__main__':
    for replica in range(50):
        set_seed(replica)
        print(f'Seed: {replica}')
        test_gym(replica)
