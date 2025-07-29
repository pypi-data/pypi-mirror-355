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
from .Free import Free_Pal_st,upload

from abc import  abstractmethod

import gymnasium as gym
import numpy as np
from threading import Thread

from collections import OrderedDict
from collections.abc import Sequence
from copy import deepcopy

from typing import Any, Callable, Optional

from stable_baselines3.common.vec_env.base_vec_env import VecEnv, VecEnvIndices, VecEnvObs, VecEnvStepReturn
from stable_baselines3.common.vec_env.patch_gym import _patch_env
from stable_baselines3.common.vec_env.util import dict_to_obs, obs_space_info
    
import os
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


class DHgym(Free_Pal_st):
    """
        补充说明, step() 和 reset() 基于下面的函数不需要额外编写：

        Usage:

            # step 基于 self.reward、self.explain_obs
            def step(self, action):
               self.state = self.explain_obs(...)
               reward_array, terminated, truncated ,self.info_array = self.reward(...)
               return self.state, reward_array, terminated, truncated ,self.info_array 

            # reset 基于 self.explain_obs, 获取全局info请使用 self.info_array
            def reset(self, seed=None):
                self.state = self.explain_obs(...)
                return self.state, reset_info
            

    """
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 20}
    def __init__(self, render_mode=None):
        self.state = None
        self.action_space = None
        self.observation_space = None
        self.render_mode = render_mode
        self.render_fps = self.metadata["render_fps"]
        self.num_envs = 1

        self.add_obj, self.obs_target = self.init()

        self.info_array = [{"counts":0} for _ in range(self.num_envs)] # 全局 info 列表
        self.reset_array : np.ndarray = np.full(self.num_envs,True,dtype=bool) # 全局 reset 列表

        super().__init__()

    @abstractmethod
    def init(self)-> tuple[dict, list]:
        """初始函数，设置 action_space、 observation_space 返回 添加内容、观察目标

        需要用户自行编写

        Usage:

            def init(self)-> tuple[dict, list]:
                self.num_envs : = ...
                self.action_space = ... # NotOptional
                self.observation_space  = ... # NotOptional
                ...
                add_obj = {} # NotOptional
                add_obj['Ground'] = {'size':[20,20] }
                add_obj['Heightground'] = {'size':[30,30,1],'path': '/models/heightground.jpeg', 'detail': 100 }
                add_obj['urdf'] = {'scale':[1,1,1],'position':[0,0,0],'path': '/models/T12/urdf/T12.URDF','debug':False }
                ...
                return add_obj, ['Link.somelink','Joint.somejoint']
        """
        raise NotImplementedError()
        
    @abstractmethod
    def explain_reset(self, reset_array: np.ndarray):
        """设置初始位置、初始约束角度

        需要用户自行编写

        :param reset_array: 复位 bool array

        Usage:

            def explain_reset(self,reset_array):
                position = {link: np.ndarray | list}
                angle = {joint: np.ndarray | list}
                ...
                return  position, angle
        """
        raise NotImplementedError()

    @abstractmethod
    def explain_action(self, action: np.ndarray):
        """解释具体动作， 格式：'Joint.KP1' 角度 'Impulse.ball' 力

        需要用户自行编写

        Usage:

            def explain_action(self,action)-> list:
                ...
                return  [{},{},...]
        """
        raise NotImplementedError()
    
    @abstractmethod
    def explain_obs(self, obs: list):
        """将观察内容 state 适配 observation_space

        需要用户自行编写

        Usage:

            def explain_obs(self,action)-> np.ndarray|list:
                ...
                return  state
        """
        raise NotImplementedError()
    
    @abstractmethod
    def reward(self,state : np.ndarray):
        """奖励函数

        需要用户自行编写

        Usage:

            def reward(self,state):
                for i in range( self.num_envs):
                    state : np.ndarray = state[i]
                    reset_array[i] = True # NotOptional
                    terminated[i] = True
                    truncated[i] = True
                ...
                return  reward_array, terminated, truncated, reset_array
        """
        raise NotImplementedError()

    def connect(self,connect_func):
        t1 = Thread(target=connect_func) 
        print('waiting for connection...')
        t1.daemon = True # 守护线程，自动退出
        t1.start()




class DHgym_VecEnv(VecEnv):
    """
    参考 dummy_vec_env  适配 stable_baselines3 的算法
    """
    actions: np.ndarray

    def __init__(self, env_fns: list[Callable[[], gym.Env]]):
        self.envs = [_patch_env(fn()) for fn in env_fns]
        if len(set([id(env.unwrapped) for env in self.envs])) != len(self.envs):
            raise ValueError(
                "You tried to create multiple environments, but the function to create them returned the same instance "
                "instead of creating different objects. "
                "You are probably using `make_vec_env(lambda: env)` or `DummyVecEnv([lambda: env] * n_envs)`. "
                "You should replace `lambda: env` by a `make_env` function that "
                "creates a new instance of the environment at every call "
                "(using `gym.make()` for instance). You can take a look at the documentation for an example. "
                "Please read https://github.com/DLR-RM/stable-baselines3/issues/1151 for more information."
            )
        env : DHgym = self.envs[0]
        super().__init__(env.num_envs, env.observation_space, env.action_space)
        obs_space = env.observation_space
        self.keys, shapes, dtypes = obs_space_info(obs_space)

        self.buf_obs = OrderedDict([(k, np.zeros((self.num_envs, *tuple(shapes[k])), dtype=dtypes[k])) for k in self.keys])
        self.buf_dones = np.zeros((self.num_envs,), dtype=bool)
        self.buf_rews = np.zeros((self.num_envs,), dtype=np.float32)
        self.buf_infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]
        self.metadata = env.metadata

    def step_async(self, actions: np.ndarray) -> None:
        if len(actions) != self.num_envs:
            raise ValueError(
            f"Expected actions with length {self.num_envs}, "
            f"but got length {len(actions)}"
        )
        self.actions = actions

    def step_wait(self) -> VecEnvStepReturn:
        obs, self.buf_rews, terminated, truncated, self.buf_infos = self.envs[0].step( self.actions )
        self.buf_dones = terminated | truncated
        self._save_obs(obs) 

        return (self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), deepcopy(self.buf_infos))

    def reset(self) -> VecEnvObs:
        maybe_options = {"options": self._options} if self._options[0] else {}
        obs, self.reset_infos = self.envs[0].reset(seed=self._seeds, **maybe_options)
        self._save_obs( obs)

        # Seeds and options are only used once
        self._reset_seeds()
        self._reset_options()
        return self._obs_from_buf()

    def close(self) -> None:
        for env in self.envs:
            env.close()

    def get_images(self) -> Sequence[Optional[np.ndarray]]:
        '''unused'''
        if self.render_mode != "rgb_array":
            return [None for _ in self.envs]
        return [env.render() for env in self.envs]

    def render(self, mode: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Gym environment rendering. If there are multiple environments then
        they are tiled together in one image via ``BaseVecEnv.render()``.

        :param mode: The rendering type.
        """
        return super().render(mode=mode)

    def _save_obs(self,  obs: VecEnvObs) -> None:
        for key in self.keys:
            if key is None:
                self.buf_obs[key] = obs
            else:
                self.buf_obs[key] = obs[key]

    def _obs_from_buf(self) -> VecEnvObs:
        return dict_to_obs(self.observation_space, deepcopy(self.buf_obs))

    def get_attr(self, attr_name: str, indices: VecEnvIndices = None) -> list[Any]:
        """Return attribute from vectorized environment (see base class)."""
        target_envs = [self.envs[0]]
        return [env_i.get_wrapper_attr(attr_name) for env_i in target_envs]

    def set_attr(self, attr_name: str, value: Any, indices: VecEnvIndices = None) -> None:
        """Set attribute inside vectorized environments (see base class)."""
        target_envs = self._get_target_envs(indices)
        for env_i in target_envs:
            setattr(env_i, attr_name, value)

    def env_method(self, method_name: str, *method_args, indices: VecEnvIndices = None, **method_kwargs) -> list[Any]:
        """Call instance methods of vectorized environments."""
        target_envs = self._get_target_envs(indices)
        return [env_i.get_wrapper_attr(method_name)(*method_args, **method_kwargs) for env_i in target_envs]

    def env_is_wrapped(self, wrapper_class: type[gym.Wrapper], indices: VecEnvIndices = None) -> list[bool]:
        """Check if worker environments are wrapped with a given wrapper"""
        target_envs = self._get_target_envs(indices)
        # Import here to avoid a circular import
        from stable_baselines3.common import env_util

        return [env_util.is_wrapped(env_i, wrapper_class) for env_i in target_envs]

    def _get_target_envs(self, indices: VecEnvIndices) -> list[gym.Env]:
        indices = self._get_indices(indices)
        return [self.envs[i] for i in indices]


def open_browser():
    """Open the default web browser to the specified URL."""
    PORT = 8000
    DIRECTORY = os.path.join(os.path.dirname( os.path.abspath(__file__) ) , "..\\dist")

    os.chdir(DIRECTORY)

    class CustomHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(('localhost', PORT), CustomHandler)
    url = f"http://localhost:{PORT}/index.html"

    print(f"🌐 正在打开浏览器: {url}")
    webbrowser.open_new_tab(url)

    print(f"\n🚀 服务器已启动在 http://localhost:{PORT}")
    print("🛑 按 Ctrl+C 停止服务器\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 正在关闭服务器...")
    finally:
        server.server_close()
        print("✅ 服务器已停止")


def Upload(folder_path: str , folder_name: str):
    """上传模型文件到web端

    :param path: 资源文件夹路径，
    :param folder_name: 上传到web端的文件夹名
    """
    upload(folder_path,folder_name)