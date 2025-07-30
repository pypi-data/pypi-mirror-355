import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'
import gym_super_mario_bros
from gym_super_mario_bros.actions import COMPLEX_MOVEMENT
from nes_py.wrappers import JoypadSpace
from PepperPepper.RL.mario.callbacks import get_MARIOtrain_config
from PepperPepper.RL.mario.tools import MetricLogger
from PepperPepper.RL.mario.model import Mario

from gym.wrappers import FrameStack, GrayScaleObservation, TransformObservation
from PepperPepper.RL.mario.wrappers import SkipFrame, ResizeObservation
from pathlib import Path
import datetime



class MARIOTrainer:
    def __init__(self, config, model=None, device=None):
        self.config = config
        self.epochs = config.epochs
        # self.net = IRSTDNet(config.model_name, model)



        env = gym_super_mario_bros.make(config.env_name)
        env = JoypadSpace(env, COMPLEX_MOVEMENT)
        env = SkipFrame(env, config.skip_frame)

        env = GrayScaleObservation(env)
        env = ResizeObservation(env, shape=84)
        env = TransformObservation(env, f=lambda x: x / 255.)
        env = FrameStack(env, num_stack=4)
        self.env = env
        self.epoch = 0
        self.save_dir = Path('./checkpoints') / config.title / datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        self.save_dir.mkdir(parents=True,  exist_ok=True)

        checkpoint = config.checkpoint # Path('checkpoints/2020-10-21T18-25-27/mario.chkpt')


        # state = env.reset()
        self.net = Mario(state_dim=(4, 84, 84), action_dim=env.action_space.n, save_dir=save_dir, checkpoint=config.checkpoint)

        # logger = MetricLogger(save_dir)


    def train(self, epochs = None):
        # setting epoch
        logger = MetricLogger(self.save_dir)

        if epochs is None:
            try:
                epochs = self.config.epochs
            except:
                epochs = 600

        print('MARIO Net:{} ENV:{} Start training...'.format(self.config.model_name, self.config.env_name))
        print(self.config)
        start_epoch = self.epoch
        ### for Loop that train the model num_episodes times by playing the game
        for idx_epoch in range(start_epoch, epochs):
            state = env.reset()

            # Play the game!
            while True:
                # 3. Show environment (the visual) [WIP]
                if self.config.render == True:
                    env.render()

                # 4. Run agent on the state
                action = mario.act(state)

                # 5. Agent performs action
                next_state, reward, done, info = env.step(action)

                # 6. Remember
                mario.cache(state, next_state, action, reward, done)

                # 7. Learn
                q, loss = mario.learn()

                # 8. Logging
                self.logger.log_step(reward, loss, q)

                # 9. Update state
                state = next_state

                # 10. Check if end of game
                if done or info['flag_get']:
                    break
            logger.log_episode()

            if idx_epoch % self.config.iter_print == 0:
                logger.record(
                    episode=e,
                    epsilon=mario.exploration_rate,
                    step=mario.curr_step
                )

