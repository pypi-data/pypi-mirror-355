import gymnasium as gym
import cv2

env = gym.make("CartPole-v1", render_mode="rgb_array")
env.reset()

for _ in range(1000):
    img = env.render()
    action = env.action_space.sample()
    observation, reward, done, info, _ = env.step(action)

    # 显示图像
    cv2.imshow('CartPole', img)
    cv2.waitKey(1)  # 等待1毫秒

    if done:
        env.reset()

env.close()
cv2.destroyAllWindows()