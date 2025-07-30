# 内置库 
import math
import os
import sys
import copy
from itertools import combinations
from typing import Tuple,Optional
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')) )
from typing import Dict,List,Tuple,Optional,Union
# 第三方库
import json
import numpy as np
from shapely.geometry import Polygon

# 自定义库
import common.utils as utils
from map_expansion.map_api import TgScenesMap
from map_expansion.bit_map import BitMap
from dynamic_scenes.lookup import CollisionLookup,VehicleType
from dynamic_scenes.observation import Observation
from dynamic_scenes.socket_module import Client




class ReplayInfo():
    """用于存储回放测试中用以控制背景车辆的所有数据
        背景车轨迹信息 vehicle_traj
        vehicle_traj = {
            "vehicle_id_0":{
                "shape":{
                    "vehicle_type":"PickupTruck",
                    "length":5.416,
                    "width":1.947,
                    "height":1.886,
                    "locationPoint2Head":2.708,
                    "locationPoint2Rear":2.708
                },
                "t_0":{
                    "x":0,
                    "y":0,
                    "v_mps":0,
                    "acc_mpss":0,
                    "yaw_rad":0,
                    "yawrate_radps":0,
                },
                "t_1":{...},
                ...
            },
            "vehicle_id_1":{...},
            ...
        }
        主车轨迹信息,只包含当前帧信息
        ego_info = {
            "shape":{
                        "vehicle_type":"MineTruck_NTE200",
                        "length":13.4,
                        "width":6.7,
                        "height":6.9,
                        "min_turn_radius":14.2,
                        "locationPoint2Head":2.708,
                        "locationPoint2Rear":2.708
                    },
            "x":[],
            "y":[],
            "v_mps":[],
            "acc_mpss":[],
            "yaw_rad":[],
            "yawrate_radps":[]
        }
        地图相关信息,具体介绍地图解析工作的教程 markdown 文档待编写
        self.hdmaps = {
            'image_mask':bitmap的ndarray,
            'tgsc_map':语义地图
            }
        测试环境相关信息 test_setting
        test_setting = {
            "t":,
            "dt":,
            "max_t",
            "goal":{
                "x":[-1,-1,-1,-1],
                "y":[-1,-1,-1,-1]
            },
            "end":,
            "scenario_type":,
            "enter_loading_flag":,
            "enter_loading_time":,
            "scenario_name":,
            "map_type":,
            "start_ego_info" 
        }

    """


    def __init__(self):
        self.vehicle_traj = {}  # 背景车轨迹
        self.car_num = 1
        self.ego_info = {
            "shape":{
                        "vehicle_type":"MineTruck_NTE200",
                        "length":13.4,
                        "width":6.7,
                        "height":6.9,
                        "min_turn_radius":14.2,
                        "locationPoint2Head":2.708,
                        "locationPoint2Rear":2.708
                    },
            "x":[],
            "y":[],
            "v_mps":[],
            "acc_mpss":[],
            "yaw_rad":[],
            "yawrate_radps":[],
            "exist_time":[]
        }
        self.hdmaps = {}
        self.test_setting = {
            "t":0,
            "dt":0.1,
            "max_t":10,
            "work_position":[],
            "work_time": 10,
            "cusp_region":[],
            "goal":{
                "x":[1,2,3,4 ],
                "y":[1,2,3,4 ],
                "heading": None
            },# goal box:4 points [x1,x2,x3,x4],[y1,y2,y3,y4]
            "end":-1,
            "scenario_name":None,
            "scenario_type":None,
            "enter_loading_flag":False,
            "enter_loading_time":0.00,
            "x_min":None,
            "x_max":None,
            "y_min":None,
            "y_max":None,
            "start_ego_info":None, # 用不到，不会读取
            "generate_cusp_region": False,
            "cusp_type": "left",   
        } #同 Observation.test_setting


    def _add_vehicle_shape(self, id: int, traj_info: dict = None):
        """ 
        该函数实现向vehicle_trajectiry中添加背景车轨迹信息的功能——增加车辆形状
        """
        if id not in self.vehicle_traj.keys():
            self.vehicle_traj[id] = {}
            self.vehicle_traj[id]['shape'] = {}
        self.vehicle_traj[id]['shape']= traj_info['VehicleShapeInfo']
     
            
    def _add_vehicle_traj(self,id: int, traj_info: dict = None):
        """ 
        该函数实现向vehicle_trajectiry中添加背景车轨迹信息的功能-增加车辆状态、轨迹
        """
        for index,_ in enumerate(traj_info['states']['x']):
            t = traj_info['StartTimeInScene']+ index * self.test_setting['dt']
            str_t = str(round(float(t),2))  # 注意这里的key为时间，是str
            if str_t not in self.vehicle_traj[id].keys(): 
                self.vehicle_traj[id][str_t]={}
            for key,value in zip(['x','y','yaw_rad','v_mps','yawrate_radps','acc_mpss'],
                                  [traj_info['states']['x'][index][0],traj_info['states']['y'][index][0],
                                   traj_info['states']['yaw_rad'][index][0],traj_info['states']['v_mps'][index][0],
                                   traj_info['states']['yawrate_radps'][index][0],traj_info['states']['acc_mpss'][index][0]]):
                if value is not None:
                    self.vehicle_traj[id][str_t][key] = (np.around(value,5))  # 轨迹保留5位小数

    @staticmethod
    def normalize_angle(angle):
        normalized_angle = angle % (2 * math.pi)
        return normalized_angle

    def _init_battlefield_vehicle_ego_info(self,one_scenario: dict = None):
        self.ego_info['shape'] = one_scenario['ego_info']['VehicleShapeInfo']
        for i in range(one_scenario['car_num']):
            self.ego_info['exist_time'].append(one_scenario['exist_time'][i])
            self.ego_info['x'].append(one_scenario['ego_info']['initial_state']['x'])
            self.ego_info['y'].append(one_scenario['ego_info']['initial_state']['y'])
            self.ego_info['yaw_rad'].append(one_scenario['ego_info']['initial_state']['yaw_rad'])
            self.ego_info['v_mps'].append(one_scenario['ego_info']['initial_state']['v_mps'])
            self.ego_info['acc_mpss'].append(one_scenario['ego_info']['initial_state']['yawrate_radps'])
            self.ego_info['yawrate_radps'].append(one_scenario['ego_info']['initial_state']['acc_mpss'])


    def _get_dt_maxt(self,one_scenario: dict = None):
        """
        该函数实现得到最大仿真时长阈值以及采样率的功能,最大最小xy范围
        """
        self.test_setting['max_t']= one_scenario['max_t']
        self.test_setting['dt']= one_scenario['dt']
        self.test_setting['x_min']= one_scenario['x_min']
        self.test_setting['x_max']= one_scenario['x_max']
        self.test_setting['y_min']= one_scenario['y_min']
        self.test_setting['y_max']= one_scenario['y_max']

    def _get_goal(self,one_scenario: dict = None):
        x_A1 = one_scenario['goal']['x'][0]
        x_A2 = one_scenario['goal']['x'][1]
        x_A3 = one_scenario['goal']['x'][2]
        x_A4 = one_scenario['goal']['x'][3]

        y_A1 = one_scenario['goal']['y'][0]
        y_A2 = one_scenario['goal']['y'][1]
        y_A3 = one_scenario['goal']['y'][2]
        y_A4 = one_scenario['goal']['y'][3]
        self.test_setting['goal'] = {
                                        "x": [x_A1,x_A2,x_A3,x_A4],
                                        "y": [y_A1,y_A2,y_A3,y_A4],
                                        "heading": one_scenario['goal']['heading']
                                    }
        
        x = np.mean(self.test_setting['goal']["x"])
        y = np.mean(self.test_setting['goal']["y"])
        self.test_setting['point_goal'] = [x,y,np.mean(self.test_setting['goal']["heading"][0])]
        for x,y,yaw in zip(one_scenario['work_position']['x'], 
                           one_scenario['work_position']['y'],
                           one_scenario['work_position']['yaw_rad']):
            half_width = one_scenario['ego_info']['VehicleShapeInfo']['width']/2
            half_length = one_scenario['ego_info']['VehicleShapeInfo']['length']/2
            # 定义四个顶点的局部坐标（相对于车辆中心）
            local_points = [
                (half_length, half_width),   # 前右
                (half_length, -half_width),  # 前左
                (-half_length, -half_width), # 后左
                (-half_length, half_width)   # 后右
            ]

            x_list, y_list = [], []
            for x_local, y_local in local_points:
                # 应用旋转矩阵
                x_rot = x_local * math.cos(yaw) - y_local * math.sin(yaw)
                y_rot = x_local * math.sin(yaw) + y_local * math.cos(yaw)
                
                # 转换为全局坐标
                x_list.append(x + x_rot)
                y_list.append(y + y_rot)
            tmp_work_area = {
                "x": x_list,
                "y": y_list,
                "yaw_rad": [yaw]
            }
            self.test_setting['work_position'].append(tmp_work_area)


class ReplayParser():
    """
    解析场景文件
    """
    def __init__(self):
        self.replay_info = ReplayInfo()


    def parse(self,map_path, setting_path, scene_type, generate_tmp_map=False) -> ReplayInfo:

        # 场景名称与测试类型
        self.scene_type = scene_type
        if scene_type == "B":
            self._parse_battlefield_scenario(setting_path)
            self._parse_battle_field_hdmaps(map_path,generate_tmp_map) # 解析 地图文件
        
        return self.replay_info
    
    def _parse_battlefield_scenario(self, setting_path):
        with open(setting_path,'r') as f:
            one_scenario = json.load(f)
        self.replay_info.car_num = one_scenario.setdefault("car_num", 1)
        self.replay_info.test_setting['generate_cusp_region'] = one_scenario.setdefault("generate_cusp_region", False)
        self.replay_info.test_setting['cusp_type'] = one_scenario.setdefault("cusp_type", 'left')
        self.replay_info.test_setting['work_time'] = one_scenario.setdefault("work_time", 10)
        # 1) 获取ego车辆的目标区域,goal box
        self.replay_info._get_goal(one_scenario)
        # 2) 步长,最大时间,最大最小xy范围
        self.replay_info._get_dt_maxt(one_scenario)
        
        # 3) 读取ego车初始信息
        self.replay_info._init_battlefield_vehicle_ego_info(one_scenario)

        # 读取背景车信息，包括：车辆形状信息以及轨迹信息
        for idex,value_traj_segment in enumerate(one_scenario['TrajSegmentInfo']):
            # if value_traj_segment['TrajSetToken'] != "ego":
            num_vehicle = idex
            # 4) 读取车辆长度与宽度等形状信息,录入replay_info.id从1开始
            self.replay_info._add_vehicle_shape(
                id=num_vehicle,
                traj_info=value_traj_segment)
            # 5) 以下读取背景车相关信息,车辆编号从1号开始,轨迹信息记录在vehicle_traj中
            self.replay_info._add_vehicle_traj(
                id=num_vehicle,
                traj_info=value_traj_segment)

        return self.replay_info
    
    def _parse_battle_field_hdmaps(self,map_path:str, generate_tmp_map=False) -> None:
        
        # 获取mask图信息并确定最大方形区域
        self._load_battlefied_mask_and_calculate_square_region(map_path, generate_tmp_map)
    
    def _load_battlefied_mask_and_calculate_square_region(self,map_path:str, generate_tmp_map=False) -> None:
        self.replay_info.hdmaps['image_mask'] = BitMap(map_path,'bitmap_mask', scene_type=self.scene_type, generate_tmp_map=generate_tmp_map)  # 得到整个二进制图的ndarray
        
        # 整合所有的坐标点
        x_coords = (
            [self.replay_info.ego_info['x']] + 
            self.replay_info.test_setting['goal']['x'] +
            [self.replay_info.test_setting['x_min'],self.replay_info.test_setting['x_max']]
        )  # 包括主车初始横坐标、目标区域横坐标、以及整张地图横坐标
        y_coords = (
            [self.replay_info.ego_info['y']] + 
            self.replay_info.test_setting['goal']['y'] +
            [self.replay_info.test_setting['y_min'],self.replay_info.test_setting['y_max']]
        )
        
        # 根据坐标确定最大的方形框
        x_min,x_max = self.replay_info.test_setting['x_min'], self.replay_info.test_setting['x_max']
        y_min,y_max = self.replay_info.test_setting['y_min'], self.replay_info.test_setting['y_max']
        utm_local_range = (
            x_min,y_min,
            x_max,y_max
        )  # 确定坐标范围
        self.replay_info.hdmaps['image_mask'].load_bitmap_using_utm_local_range(utm_local_range,0,0, is_battle=True)
   
        
          
        
        

class ReplayController():
    def __init__(self, kinetics_mode):
        self.control_info = ReplayInfo()
        self.collision_lookup = None
        self.kinetics_mode = kinetics_mode
        self.step_count = None  # 添加一个类属性来存储step_count


    def init(self,control_info:ReplayInfo) -> Observation:
        self.control_info = control_info
        # self.collision_lookup = collision_lookup
        return self._get_initial_observation()

    def step(self, env, action_list, observation_last:Observation, traj_future=100, traj=100, 
             ha_path=None, slope=0, last_height=None, vis_cir_open=False) -> Observation:
        """
        进行一步更新
        new_observation:限制范围内观测值
        new_observation_all:全部观测值用于可视化
        """
        if self.kinetics_mode == 'complex':
            action_list = self._action_cheaker_kinetics(action_list)
            new_observation = self._update_kinetics(env, action_list, observation_last, 
                                                                        traj_future, traj, ha_path, 
                                                                        slope, last_height, vis_cir_open)
            #print("完成一次更新与记录")
        else:
            print("请勿选择除complex之外的kinetics模式")

        return new_observation

    def _action_cheaker_kinetics(self,action_list):
        new_action_list = []
        for action in action_list:
            a = np.clip(action[0],-4,2)
            rad = np.clip(action[1],-math.pi/4,math.pi/4)
            gear = action[2]
            if gear not in [1, 2, 3]:
                raise ValueError("不支持{0}档位，请选择合适档位".format(gear))
            new_action_list.append((a,rad,gear))
        return new_action_list
    def _create_cusp_region(self):
        for i in range(len(self.control_info.test_setting['work_position'])):
            x = np.mean(self.control_info.test_setting['work_position'][i]['x'])
            y = np.mean(self.control_info.test_setting['work_position'][i]['y'])
            yaw_rad = np.mean(self.control_info.test_setting['work_position'][i]['yaw_rad'])

            clock_wise = False if self.control_info.test_setting['cusp_type'] == 'left' else True
            move_radius = 1.7*self.control_info.ego_info['shape']['min_turn_radius']
            cusp_region_radius = 0.6*self.control_info.ego_info['shape']['min_turn_radius']
            move_yaw_rad = 75*math.pi/180
            delta_yaw_rad = 5*math.pi/180
            while True:
                # 返回一个(x,y,yaw_rad)的元组
                cusp_point = utils.generate_cusp_point((x,y,yaw_rad), move_radius, move_yaw_rad, clock_wise)
                if not self.collision_lookup.collision_detection(cusp_point[0],cusp_point[1],cusp_point[2],
                                                             self.control_info.hdmaps['image_mask'].image_ndarray):
                    cusp_point_region = {
                        "cusp_point": cusp_point,
                        "cusp_region_radius": cusp_region_radius
                    }
                    self.control_info.test_setting['cusp_region'].append(cusp_point_region)
                    break
                move_yaw_rad -= delta_yaw_rad
                if move_yaw_rad < 50*math.pi/180:
                    move_yaw_rad = 75*math.pi/180
                    move_radius += 0.1*self.control_info.ego_info['shape']['min_turn_radius']
                

    def _get_initial_observation(self) -> Observation:
        observation = Observation()
        observation.car_num = self.control_info.car_num
        for _ in range(observation.car_num):
            observation.complete_flag.append(False)
        # vehicle_info
        ego_vehicle = self.control_info.ego_info
        observation.vehicle_info["ego"] = ego_vehicle  # 初始化主车信息
        # 更新自车与边界碰撞查询表
        if ego_vehicle["shape"]["length"] >= 8.5 and ego_vehicle["shape"]["width"] <= 9.5:
            self.collision_lookup = CollisionLookup(type=VehicleType.MineTruck_XG90G)
        elif ego_vehicle["shape"]["length"] >= 12.5 and ego_vehicle["shape"]["width"] <= 13.6:
            self.collision_lookup = CollisionLookup(type=VehicleType.MineTruck_NTE200)
        else:
            self.collision_lookup = CollisionLookup(type=VehicleType.MineTruck_XG90G)
        # 人为构建人字尖点区域引导车辆行驶
        if self.control_info.test_setting['generate_cusp_region']:
            self._create_cusp_region()
        # hdmaps info
        observation.hdmaps = self.control_info.hdmaps
        # test_setting
        observation.test_setting = self.control_info.test_setting
        # observation,observation_all = self._update_other_vehicles(observation)  # 初始化背景车信息

        observation = self._update_end_status(observation)
        # observation_all = self._update_end_status(observation_all)
    
        return observation


    def _update_ego_and_t(self,action:tuple,old_observation:Observation) -> Observation:
        # 拷贝一份旧观察值
        new_observation = copy.copy(old_observation)
        # 首先修改时间,新时间=t+dt
        new_observation.test_setting['t'] = float(
            old_observation.test_setting['t'] +
            old_observation.test_setting['dt']
        )
        # 修改本车的位置,方式是前向欧拉更新,1.根据旧速度更新位置;2.然后更新速度.
        # 速度和位置的更新基于自行车模型.
        # 首先分别取出加速度和方向盘转角
        a,rot,gear = action
        # 取出步长
        dt = old_observation.test_setting['dt']
        # 取出本车的各类信息
        x,y,v,yaw,= [float(old_observation.vehicle_info['ego'][key]) for key in ['x','y','v_mps','yaw_rad']]
        width,length  = old_observation.vehicle_info['ego']['shape']['width'],old_observation.vehicle_info['ego']['shape']['length']

        # 首先根据旧速度更新本车位置
        new_observation.vehicle_info['ego']['x'] = x + \
                                                   v * np.cos(yaw) * dt  # 更新X坐标

        new_observation.vehicle_info['ego']['y'] = y + \
                                                   v * np.sin(yaw) * dt  # 更新y坐标

        new_observation.vehicle_info['ego']['yaw_rad'] = yaw + \
                                                     v / length * 1.7 * np.tan(rot) * dt  # 更新偏航角

        new_observation.vehicle_info['ego']['v_mps'] = v + a * dt  # 更新速度
        if new_observation.vehicle_info['ego']['v_mps'] < -10/3.6:
            new_observation.vehicle_info['ego']['v_mps'] = -10/3.6

        new_observation.vehicle_info['ego']['acc_mpss'] = a  # 更新加速度
        return new_observation

    def _judge_gear(self, a, rot):
        # TODO 完成人字形节点判断，进而判断档位
        return 1
    
    def _get_slope_value(self,x, y):
        """
        根据车辆的位置 x, y 检索坡度值
        """
        return 0
    
    def _update_ego(self,unpacked_data,i,a,old_observation:Observation) -> Observation:
        "更新本车信息"
        new_observation = copy.copy(old_observation)
        new_observation.test_setting['t'] = float(
            old_observation.test_setting['t'] +
            old_observation.test_setting['dt']
            )
        new_observation.vehicle_info['ego']['x'] = unpacked_data[i*4+2]
        new_observation.vehicle_info['ego']['y'] = unpacked_data[i*4+3]
        # 更新航向角
        new_observation.vehicle_info['ego']['yaw_rad'] = unpacked_data[i*4+1]
        # 更新速度
        new_observation.vehicle_info['ego']['v_mps'] = unpacked_data[i*4+0]
        if new_observation.vehicle_info['ego']['v_mps'] < -10/3.6:
            new_observation.vehicle_info['ego']['v_mps'] = -10/3.6
        # 更新加速度
        new_observation.vehicle_info['ego']['acc_mpss'] = a
        return new_observation
    
    
    def _update_kinetics(self, env, action_list, observation_last:Observation, traj_future=100,
                         traj=100, ha_path=None, slope=0, last_height=None, vis_cir_open=False) -> Observation:
        """
        使用动力学模型更新状态值
        """
        new_observation = copy.deepcopy(observation_last)
        dt = observation_last.test_setting['dt']

        # 更新自车状态量        
        for i in range(observation_last.car_num):
            if not self._check_car_available(observation_last, i):
                continue
            a,rot,gear = action_list[i]
            action = (a, gear, rot, 0)
            state = (observation_last.vehicle_info['ego']['x'][i], 
                     observation_last.vehicle_info['ego']['y'][i],
                     observation_last.vehicle_info['ego']['yaw_rad'][i],
                     observation_last.vehicle_info['ego']['v_mps'][i])
            new_state = env.kinetic_step(action, state, i)
            new_observation.vehicle_info['ego']['x'][i] = new_state[0]
            new_observation.vehicle_info['ego']['y'][i] = new_state[1]
            new_observation.vehicle_info['ego']['yaw_rad'][i] = new_state[2]
            new_observation.vehicle_info['ego']['v_mps'][i] = new_state[3]
            new_observation.vehicle_info['ego']['acc_mpss'][i] = a
            new_observation.vehicle_info['ego']['yawrate_radps'][i] = rot

        # 更新障碍车信息（暂不需要）

        # 更新时间
        new_observation.test_setting['t'] = float(
            observation_last.test_setting['t'] +
            observation_last.test_setting['dt']
            )
        
        # 更新交互环境终止状态
        new_observation = self._update_end_status(new_observation)

        #记录轨迹与可视化
        env.recorder.record(new_observation, action_list)
        env.visualizer.update(new_observation,traj_future,observation_last,traj,ha_path, last_height, vis_cir_open)
          
        return new_observation

    def _update_other_vehicles(self,old_observation:Observation) -> Observation:
        """已知仿真时刻，把背景车信息更新至对应时刻(只返回30m内的车辆信息)"""
        # 删除除了ego之外的车辆观察值
        new_observation = copy.copy(old_observation)  # 复制一份旧观察值
        new_observation.vehicle_info = {}
        # 将本车信息添加回来
        new_observation.vehicle_info['ego'] = old_observation.vehicle_info['ego']
        new_observation_all = copy.deepcopy(new_observation)  # 包含所有车辆信息的观测值
        # 根据时间t,查询control_info,赋予新值
        t = old_observation.test_setting['t']
        t = str(np.around(t,2))  # t保留3位小数,与生成control_info时相吻合
        # 获取 ego 车辆的位置信息
        ego_x = old_observation.vehicle_info['ego']['x']
        ego_y = old_observation.vehicle_info['ego']['y']

        for vehi in self.control_info.vehicle_traj.items():
            id = vehi[0]  # 车辆id
            info = vehi[1]  # 车辆的轨迹信息
            if t in info.keys():
                new_observation_all.vehicle_info[id] = {}
                for key in ['x','y','yaw_rad','v_mps','yawrate_radps','acc_mpss']:
                    new_observation_all.vehicle_info[id][key] = info[t][key]
                new_observation_all.vehicle_info[id]['shape'] = info['shape']
                # 获取车辆在当前时刻的位置信息
                veh_x = info[t]['x']
                veh_y = info[t]['y']
                # 计算与 ego 车辆的距离
                distance = np.sqrt((veh_x - ego_x) ** 2 + (veh_y - ego_y) ** 2)
                #print("dis:",distance)
                if distance <= 40:
                    new_observation.vehicle_info[id] = {}
                    for key in ['x','y','yaw_rad','v_mps','yawrate_radps','acc_mpss']:
                        new_observation.vehicle_info[id][key] = info[t][key]
                    new_observation.vehicle_info[id]['shape'] = info['shape']

        return new_observation,new_observation_all

    def _update_end_status(self,observation:Observation) -> Observation:
        """计算T时刻,测试是否终止,更新observation.test_setting中的end值
            end=
                -1:回放测试正常进行; 
                1:回放测试运行完毕;
                2:ego车与其它车辆发生碰撞;
                3:ego车与道路边界发生碰撞(驶出道路边界);
                4:ego车到达目标区域               
        """
        status_list = [-1]
        observation.collision_car_index.clear()
        # 检查多智能体之间是否发生碰撞
        car_collision_flag, car_collision_index=self._collision_detect(observation)
        if car_collision_flag:
            status_list += [2]  # 添加状态
            observation.collision_car_index += car_collision_index
            collision_indices = ", ".join(map(str, car_collision_index))
            print(f"###log### 车辆发生碰撞，涉及车辆索引：{collision_indices}")
            

        # 检查是否已到达场景终止时间max_t
        if observation.test_setting['t'] >= observation.test_setting['max_t']:
            status_list += [1]
            print("###log### 已到达场景终止时间max_t")
            
    
        # 检查是否与道路边界碰撞
        local_x_range = observation.hdmaps['image_mask'].bitmap_info['bitmap_mask_PNG']['UTM_info']['local_x_range']
        local_y_range = observation.hdmaps['image_mask'].bitmap_info['bitmap_mask_PNG']['UTM_info']['local_y_range']
        # index 从0开始
        for index, (x,y,yaw_rad) in enumerate(zip(observation.vehicle_info['ego']['x'],
                               observation.vehicle_info['ego']['y'],
                               observation.vehicle_info['ego']['yaw_rad'])):
            collision_flag = self.collision_lookup.collision_detection(x-local_x_range[0], y-local_y_range[0], yaw_rad,
                                                    observation.hdmaps['image_mask'].image_ndarray)
            if collision_flag == True:
                status_list += [3]
                observation.collision_car_index.append(index)
                print(f"###log### {index}号车与道路边界碰撞")
                break
            
        # check target area
        for car_idx in range(observation.car_num):
            availabe = self._check_car_available(observation, car_idx)
            if not availabe:
                continue
            if utils.is_inside_polygon(observation.vehicle_info['ego']['x'][car_idx],observation.vehicle_info['ego']['y'][car_idx],observation.test_setting['goal']):
                observation.complete_flag[car_idx] = True
        # 如果全为True
        if all(observation.complete_flag):
            status_list += [4]
            print("###log### 主车均已到达终点区域")
        # 从所有status中取最大的那个作为end.
        observation.test_setting['end'] = max(status_list)
        if observation.test_setting['end'] != -1:
            print(f"end_status:{observation.test_setting['end']}")
        return observation
    
    def _check_car_available(self, observation:Observation, car_idx) -> bool:
        """检查车辆是否可用,即是否在场景中
        """
        if observation.vehicle_info['ego']['exist_time'][car_idx] > observation.test_setting['t']:
            return False
        if observation.complete_flag[car_idx]==True:
            return False
        return True


    def _collision_detect(self,observation:Observation) -> bool:
        poly_zip = []
        shape = observation.vehicle_info['ego']['shape']
        for x, y, yaw_rad in zip(observation.vehicle_info['ego']['x'], 
                                 observation.vehicle_info['ego']['y'], 
                                 observation.vehicle_info['ego']['yaw_rad']):
            poly_zip += [self._get_poly(shape, x, y, yaw_rad)]

        # 检测车辆之间是否碰撞
        for (aidx,a),(bidx,b) in combinations(enumerate(poly_zip),2):
            a_vail = self._check_car_available(observation, aidx)
            b_vail = self._check_car_available(observation, bidx)
            if a_vail and b_vail:
                if a.intersects(b):
                    return True,[aidx, bidx]
        return False,[]


    def _get_poly(self,shape:dict, x, y, yaw_rad) -> Polygon:
        """根据车辆信息,通过shapely库绘制矩形.这是为了方便地使用shapely库判断场景中的车辆是否发生碰撞
        """
        # 提取车辆shape中的属性
        length = shape['length']
        width = shape['width']
        locationPoint2Head = shape['locationPoint2Head']
        locationPoint2Rear = shape['locationPoint2Rear']
    
        front_left_corner,front_right_corner,rear_left_corner,rear_right_corner = utils.calculate_vehicle_corners(
            length,width,locationPoint2Head,locationPoint2Rear,x,y,yaw_rad)

        # 通过车辆矩形的4个顶点,可以绘制出对应的长方形
        poly = Polygon([
            (front_left_corner[0],front_left_corner[1]),
            (front_right_corner[0],front_right_corner[1]),
            (rear_right_corner[0],rear_right_corner[1]),
            (rear_left_corner[0],rear_left_corner[1]),
            (front_left_corner[0],front_left_corner[1])
        ]).convex_hull
        return poly




class Controller():
    """控制车辆运行
    """
    def __init__(self) -> None:
        self.observation = Observation()
        self.parser = None
        self.control_info = None
        self.controller = None
        self.mode = 'replay'


    def init(self,map_path, setting_path, kinetics_mode:str, scene_type, generate_tmp_map=False) -> Tuple:
        """初始化运行场景,给定初始时刻的观察值

        Parameters
        ----------
        input_dir :str
            测试输入文件所在位置
                回放测试:包含ScenariosResultes、TrajDataResultes、other目录,存放场景信息,轨迹片段集合、车辆配置信息等
                交互测试:
        mode :str
            指定测试模式
                回放测试:replay
                交互测试:interact
        Returns
        -------
        observation :Observation
            初始时刻的观察值信息,以Observation类的对象返回.
        """
        self.mode = 'replay'
        if self.mode == 'replay':
            self.parser = ReplayParser()
            self.controller = ReplayController(kinetics_mode)
            self.control_info = self.parser.parse(map_path, setting_path, scene_type,generate_tmp_map)
            # 不会被其他东西所改变，只是对最初状态做个备份用于reset的时候快速恢复
            self.init_control_info = copy.deepcopy(self.control_info)
            observation = self.controller.init(self.control_info)
            self.observation = observation
            self.traj = self.control_info.vehicle_traj
        return observation
    
    def reset(self, manual_set_car_state=False, car_state_dict = None):
        self.control_info = copy.deepcopy(self.init_control_info)
        if manual_set_car_state:
            self.control_info.ego_info['x'] = car_state_dict['x']
            self.control_info.ego_info['y'] = car_state_dict['y']
            self.control_info.ego_info['yaw_rad'] = car_state_dict['yaw_rad']
            self.control_info.ego_info['v_mps'] = car_state_dict['v_mps']
            self.control_info.ego_info['acc_mpss'] = car_state_dict['acc_mpss']
        observation = self.controller.init(self.control_info)
        self.observation = observation
        return observation



    def step(self, env, action_list, traj_future=100, traj=100, ha_path=None, slope=0, last_height=None, vis_cir_open=False):
        # replayController需要的上一时刻observation不在需要通过使用者输入，而是直接调用Controller成员变量的self.observation
        # 即交互环境内部的状态量变化自成一体，自己变化自己维护，不再受外部使用者干扰，使用者只能获取观测值，不能直接修改状态量
        self.observation = self.controller.step(env, action_list, self.observation, traj_future, traj, ha_path, slope, last_height, vis_cir_open)
        return self.observation




if __name__ == "__main__":
    input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '/home/czf/project_czf/20231010_onsite_mine/devkit/inputs'))
    scenes_file = os.path.join(input_dir,'ScenariosResultes','Scenario-jiangtong_intersection_1_1_2.json')

    with open(scenes_file,'r') as f:
        jsondata = json.load(f)
            
    pass
