from PepperPepper.environment import gym, Box, transforms, np


class ResizeObservation(gym.ObservationWrapper):
    def __init__(self, env, shape):
        super().__init__(env)
        if isinstance(shape, int):
            self.shape = (shape, shape)
        else:
            self.shape = tuple(shape)

        obs_shape = self.shape + self.observation_space.shape[2:]
        self.observation_space = Box(low=0, high=255, shape=obs_shape, dtype=np.uint8)

    def observation(self, observation):
        transforms = transforms.Compose(
            [transforms.Resize(self.shape, antialias=True), transforms.Normalize(0, 255)]
        )
        observation = transforms(observation).squeeze(0)
        return observation