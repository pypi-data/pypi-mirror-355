# Copyright (C) [2025] [DingGuohua]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import gymnasium as gym
import numpy as np
from stable_baselines3 import HerReplayBuffer, DDPG, DQN, SAC, TD3
from stable_baselines3 import  PPO,A2C
import os
from DHGym import DHgym,DHgym_VecEnv

class myEnv(DHgym) :
    """用户自己写的代码"""
    def init(self):
        self.num_envs = 1
        self.render_fps = 20
        
        print('Env nums', self.num_envs)
        self.action_space = gym.spaces.Discrete(5) # 0, 1, 2，3，4:

        # x,z,vx,vz
        low = [-10 , -10 ,-200,-200]
        high = [10 , 10, 200, 200]
        self.observation_space = gym.spaces.Box(
            low  = np.array(low ,dtype=np.float32),
            high = np.array(high,dtype=np.float32)
            )# 确定上下界
        
        add_obj = {}
        # add_obj['Ground'] = {'size':[20,20] ,'position':[0,0,0]}
        add_obj['Heightground'] = {'size':[30,30,1],'position':[0,0,0],'path': '/models/heightground.jpeg', 'detail': 100 }
        add_obj['urdf'] = [
                            {'scale':1,'position':[0,1,0],'path': '/models/T12/urdf/T12.URDF','debug':False }, # dae 文件需要 root 路径 eg. 'root':'models'
                            {'scale':1,'position':[2,1,0],'path': '/models/ball.urdf','debug':False }
                          ]

        obs_target = []
        obs_target.append('Link.ball') # (x,y,z,vx,vy,vz)
        # obs_target.append('Joint.RL_calf_joint')

        return add_obj, obs_target
        
    def explain_obs(self,obs):
        state = np.zeros((self.num_envs,4),dtype=np.float32)
        for i in range( self.num_envs):
            x,_,y,vx,_,vy = obs[i]
            state[i][0] = x  
            state[i][1] = y  
            state[i][2] = vx  
            state[i][3] = vy  
        return state
    
    def explain_action(self,action):
        explain = []
        for i in range(self.num_envs):
            force = {}
            if action[i]==0:
                force['Impulse.ball'] = [10,0,0]
            elif action[i]==1:
                force['Impulse.ball'] = [-10,0,0]
            elif action[i]==2:
                force['Impulse.ball'] = [0,0,10]
            elif action[i]==3:
                force['Impulse.ball'] = [0,0,-10]
            elif action[i]==4:
                force['Impulse.ball'] = [0,0,0]
            explain.append(force)

        # for i in range(self.num_envs):
        #     force = {}
        #     force['Joint.KP1'] = action[i]/3
        #     force['Joint.KP2'] = action[i]/3
        #     force['Joint.KP4'] = action[i]/3
        #     force['Joint.KP5'] = action[i]/3
            explain.append(force)
        return explain

    
    def reward(self,state):
        reward_array  = np.full(self.num_envs,0,dtype=np.float32)
        terminated = np.full(self.num_envs,False,dtype=bool)
        truncated  = np.full(self.num_envs,False,dtype=bool)
        reset_array = np.full(self.num_envs,False,dtype=bool)
        
        for i in range( self.num_envs):
            info = self.info_array[i] # 引用

            x,y,vx,vy = state[i]
            info["counts"] += 1 
            
            distance = np.abs(np.array([x, y])).sum()
            Done = (distance<=1) or (distance >= 20) 
            if not Done:
                reward =  -1*distance
                info["is_success"] = False
            else:
                if distance<=1:
                    reward = 10
                    info["is_success"] = True
                else:
                    reward = -40 # 超界扣大分 或 超步数
                    info["is_success"] = False
            if Done:
                info["TimeLimit.truncated"]= False # PPO等ReplayBuffer算法专属
                info["terminal_observation"]= state[i]
                reset_array[i] = True
                info["counts"] = 0
            
            terminated[i] = Done 
            reward_array[i] = reward
        return  reward_array, terminated, truncated, reset_array
    
    def explain_reset(self,reset_array):
        position = {}
        random_uniform: np.ndarray = np.random.uniform(size=(self.num_envs, 3))* 2 * 10 - 10
        random_uniform.astype(int)
        random_uniform[:,1] = 1
        position['ball'] = random_uniform

        angle = {}
        angle['KP1'] = np.zeros(self.num_envs).fill(1.5)
        angle['KP3'] = np.zeros(self.num_envs).fill(1.5)
        angle['KP5'] = np.zeros(self.num_envs).fill(1.5)
        return position, angle

# ------------------------------------------------------------------------------从下面多个func中选一个
# def func():
#     env = Car2DEnv(render_mode='human')
#     # env = myVecEnv( [lambda : Car2DEnv(render_mode="human")])
#     obs, info = env.reset()
#     T1 = time.time()
#     for i in range(10):
#         obs, reward, done, truncated , _  = env.step(env.action_space.sample())
#         if done:
#             obs, info = env.reset()
#     T2 = time.time()
#     print('程序运行时间:%s毫秒' % ((T2 - T1)*1000))
#     os._exit(0)

# def func():
#     env = Car2DEnv(render_mode='human')
#     # env = myVecEnv( [lambda : Car2DEnv(render_mode="human")])
#     print(env.reset())
#     # T1 = time.time()
#     # print(env.step([env.action_space.sample().tolist() for i in range(2)]))
#     print(env.step(env.action_space.sample() )) # num_envs 是 1 的时候
#     # T2 = time.time()
#     # print('程序运行时间:%s毫秒' % ((T2 - T1)*1000))
#     os._exit(0)

# def func():
#     '''正式的训练代码
#     '''
#     # env = Car2DEnv(render_mode='human') #成功率0.56
#     env = myVecEnv( [lambda : Car2DEnv(render_mode="human")])
#     # check_env(env)

#     model = DQN.load("./model/Game2.zip",env)
#     model.load_replay_buffer("./model/Game2buffer")
#     model.set_env(env, force_reset=True)

#     model.learn(total_timesteps=5000 ,log_interval=10,progress_bar=True)
#     # model.save("./model/Game2.zip")
#     # model.save_replay_buffer("./model/Game2buffer")# DQN需要
#     print('Finish!')
#     os._exit(0)


'''正式的训练代码
DQN 仅支持Discrete，DDPG、SAC、TD3仅支持Box，PPO、A2C支持广泛
'''
env = DHgym_VecEnv( [lambda : myEnv()]) # 自建并行化————待重写

tensorboard_log = os.path.abspath("./tensorboard/")

# model = A2C("MlpPolicy", env=env, verbose=1)
# model = PPO("MlpPolicy", env=env, verbose=1, device="cpu") 

model = DQN(
    "MlpPolicy", 
    env=env, 
    learning_rate=1e-3,
    # batch_size=128,
    # buffer_size=50000,
    learning_starts=0, # how many steps of the model to collect transitions for before learning starts 
    target_update_interval=40,
    policy_kwargs={"net_arch" : [64, 32]},
    verbose=1,
    # tensorboard_log=tensorboard_log
    )
    # log_interval默认是4,
    # progress_bar

model.learn(total_timesteps=10000 ,log_interval=10,progress_bar=True)
# model.save("./model/Game2.zip")
# model.save_replay_buffer("./model/Game2buffer")# DQN需要
print('Finish!')


