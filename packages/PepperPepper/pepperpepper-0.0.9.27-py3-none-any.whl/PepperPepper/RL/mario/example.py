import torch
from torch import nn
from torchvision import transforms as T
from PIL import Image
import numpy as np
from pathlib import Path
from collections import deque
import random, datetime, os

# Gym is an OpenAI toolkit for RL
import gym
from gym.spaces import Box
from gym.wrappers import FrameStack

# NES Emulator for OpenAI Gym
from nes_py.wrappers import JoypadSpace

# Super Mario environment for OpenAI Gym
import gym_super_mario_bros

from tensordict import TensorDict
from torchrl.data import TensorDictReplayBuffer, LazyMemmapStorage
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT

# env = gym_super_mario_bros.make("SuperMarioBros-1-1-v0")

# Initialize Super Mario environment (in v0.26 change render mode to 'human' to see results on the screen)
if gym.__version__ < '0.26':
    env = gym_super_mario_bros.make("SuperMarioBros-1-1-v0", new_step_api=True)
else:
    env = gym_super_mario_bros.make("SuperMarioBros-1-1-v0", render_mode='rgb', apply_api_compatibility=True)

# Limit the action-space to
#   0. walk right
#   1. jump right
env = JoypadSpace(env, SIMPLE_MOVEMENT)

env.reset()
# next_state, reward, done, trunc, info = env.step(action=0)
# print(f"{next_state.shape},\n {reward},\n {done},\n {info}")

for _ in range(1000):
    env.render()
    action = env.action_space.sample()
    env.step(action)
env.close()
