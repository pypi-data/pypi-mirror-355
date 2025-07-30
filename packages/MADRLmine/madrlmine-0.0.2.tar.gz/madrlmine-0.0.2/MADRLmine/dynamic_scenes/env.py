# 内置库 
import os
import sys
import shlex
import subprocess
import numpy as np
from PIL import Image
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
import importlib
import json
# 第三方库
from typing import Dict,List,Tuple,Optional,Union

# 自定义库
from dynamic_scenes.observation import Observation
from dynamic_scenes.controller import Controller
from dynamic_scenes.recorder import Recorder
from dynamic_scenes.visualizer import Visualizer
from dynamic_scenes.lookup import CollisionLookup
from dynamic_scenes.kinetics_model import KineticsModelStarter

class Env():
    """仿真环境读取及迭代过程,simulation"""
    def __init__(self):
        self.controller = Controller()
        self.recorder = Recorder()
        self.visualizer = Visualizer()
        self.scene_type = "intersection"
    
    def kinetic_step(self, action, state, car_index):
        return self.kineticModel.kinetic_step(action, state, car_index)
    
    # 用于强化学习交互环境的重置，只重置车辆动力学模型以及车辆的位姿状态
    #     car_state_dict = {
    #     'x': [240,240, 240],
    #     'y': [50,50,50],
    #     'yaw_rad': [3.14,3.14,3.14],
    #     'v_mps': [0,0,0],
    #     'acc_mpss': [0,0,0]
    # }
    def reset(self, manual_set_car_state=False, car_state_dict = None):
        # print("+++++reset_env+++++")
        observation = self.controller.reset(manual_set_car_state, car_state_dict)
        self.kineticModel.reset(observation)
        self.recorder.reset(observation)
        
        return observation.format()
    
    def make(self, map_path, setting_path, generate_tmp_map=False, flag_vis=False, flag_vis_without_show=False, need_record=False, dir_outputs='',kinetics_mode='complex', scene_type = "B") -> Tuple:

        self.scene_type = scene_type
        self.need_record = need_record

        observation = self.controller.init(map_path, setting_path, kinetics_mode, self.scene_type, generate_tmp_map)
        if kinetics_mode == "complex":
            self.kineticModel = KineticsModelStarter(observation)
            print("using complex kinetics model")
        else:
            raise ValueError("不提供这种动力学模式，请选择complex！")

        self.recorder.init(observation, dir_outputs, need_record=need_record)
        if self.scene_type == "B":
            self.visualizer.battle_init(observation,
                            flag_visilize=flag_vis,
                            flag_save_fig_whitout_show=flag_vis_without_show,
                            dir_outputs=dir_outputs) # 此处通过查看配置参数,True,设置运行过程中可视化打开;
        
        return observation.format()
    

        

    def step(self, action_list) -> Observation:
        """迭代过程"""
        observation = self.controller.step(self, action_list)  # 使用车辆运动学模型单步更新场景;

        return observation.format()
    
    def stop_car_model(self):
        if hasattr(self, 'kineticModel'):
            self.kineticModel.kinetic_terminate()




if __name__ == "__main__":
    import time
    dir_current_file = os.path.dirname(__file__)  
    dir_parent_1 = os.path.dirname(dir_current_file) 
    height_data_path = os.path.abspath(os.path.join(dir_parent_1, 'data'))
    print(dir_parent_1)
    

