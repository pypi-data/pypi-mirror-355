#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author： Wentao Zheng
# datetime： 2024/3/4 21:13 
# ide： PyCharm
import os
import sys
import shlex
import platform
import subprocess
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

# 自定义库
from dynamic_scenes.socket_module import Client
from dynamic_scenes.observation import Observation
import VehicleModel_dll.VehicleModel as vml

class KineticsModelStarter():
    def __init__(self, observation: Observation):
        # 四个列表存储所有智能体的状态
        self.step_time = observation.test_setting['dt']
        self.multi_x, self.multi_y, self.multi_yaw, self.multi_v = self._get_init_state_of_ego(observation)
        abs_dll_path = os.path.abspath(os.path.join((os.path.dirname(__file__)),'../VehicleModel_dll', "VehicleModelPython.dll"))
        abs_so_path = os.path.abspath(os.path.join((os.path.dirname(__file__)),'../VehicleModel_dll', "libcombined.so"))
        if self._judge_platform() == 'win':
            self.model_dll = vml.load_VehicleModel_dll(abs_dll_path)
        elif self._judge_platform() == 'linux':
            self.model_dll = vml.load_VehicleModel_so(abs_so_path)
        if self.model_dll == None:
            print("加载库文件失败")
            sys.exit(1)
        # 虽然理论上一个车辆模型可以作为了一个黑盒用于串行地推演多个车辆的状态变化，
        # 但测试发现，车辆模型内部有隐形的状态变量,除了初始状态外，后续再通过车辆模型推演状态时输入的状态量将无效，系统自动读取每个模型内部隐性存储地状态量
        self.car_list = []
        for i in range(observation.car_num):
            car = vml.CreateVehicleModel(self.model_dll)
            self.car_list.append(car)
    def reset(self, observation):
        self.kinetic_terminate()
        self.car_list = []
        for i in range(observation.car_num):
            car = vml.CreateVehicleModel(self.model_dll)
            self.car_list.append(car)
    
    def kinetic_step(self, action, state, car_index):
        car = self.car_list[car_index]
        new_state, _ = vml.VehicleModel_step(self.model_dll, car, action, state, self.step_time)
        return new_state
    
    def kinetic_terminate(self):
        for car in self.car_list:
            vml.DeleteVehicleModel(self.model_dll, car)
            

    @property
    def get_client(self):
        return self.client

    def _get_init_state_of_ego(self, observation:Observation):
        x = observation.vehicle_info['ego']['x']
        y = observation.vehicle_info['ego']['y']
        yaw = observation.vehicle_info['ego']['yaw_rad']
        v0 = observation.vehicle_info['ego']['v_mps']
        return x,y,yaw,v0

    def _write_temp_script(self, x:float, y:float, yaw:float, v0:float):
        # 编写一个tempScript.m脚本用于存储初始化信息
        current_path = Path(__file__).parent
        os_type = self._judge_platform()
        tempscript = current_path.parent / 'kinetic_model' / f'{os_type}'/'tempScript.m'
        with open(tempscript, 'w') as f:
            f.write(f"currentDir = pwd;\n")
            f.write(f"cd ..\n")
            f.write(f"cd(currentDir);\n")
            f.write(f"x0={x};\n")
            f.write(f"y0={y};\n")
            f.write(f"yaw={yaw};\n")
            #f.write(f"head={yaw};\n")
            f.write(f"v0={v0};\n")
            f.write("acc=0.0;\n")  # 初始加速度
            f.write("gear=2;\n")  # 初始档位：1-前进档；2-驻车档；3-倒车档
            f.write("steer=0.0;\n")  # 初始前轮转角
            # f.write("slope=getGradient(x0, y0, head, grid, vx, vy);\n")  # 初始坡度值
            f.write("slope=-0.2;\n")
            f.write("load('a_brake.mat');\n")
            f.write("load('a_thr.mat');\n")
            f.write("load('brake.mat');\n")
            f.write("load('thr.mat');\n")
            #f.write("modelName='VehicleModel';\n")
            f.write("modelName='VehicleModel_SJTU';\n")
            f.write("run('control_simulink.m');\n")

        command = f"matlab -r \"run('{tempscript.as_posix()}')\""
        result = subprocess.Popen(shlex.split(command))


        return result

    def _check_completed(self):
        # Check whether the initialization is complete
        data, _ = self.client.client_receive_sock.recvfrom(1024)  # 假设信号很小，不需要大缓冲区
        if data.decode() == 'ready':
            print("MATLAB就绪，继续执行")

    def _judge_platform(self):
        os_type = platform.system()
        if os_type == "Windows":
            return 'win'
        elif os_type == "Linux" or os_type == "Darwin":
            return 'linux'
        else:
            print(f"不支持的操作系统: {os_type}")