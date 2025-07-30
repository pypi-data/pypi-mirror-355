class Observation():
    """
    vehicle_info={
        "ego":{
            "x":,
            "y":,
            "yaw_rad":,
            "v_mps":,
            "yawrate_radps":,
            "acc_mpss":,
            "shape":{
				"vehicle_type":"MineTruck_NTE200",
				"length":13.4,
				"width":6.7,
				"height":6.9,
				"min_turn_radius":14.2,
				"locationPoint2Head":9.8,
				"locationPoint2Rear":3.8
			}
        },
        "0":{...},
        ...
    }
    test_setting = {
            "t":,
            "dt":,
            "max_t",
            "goal":{
                "x":[-1,-1,-1,-1],
                "y":[-1,-1,-1,-1]
            },
            "work_position":[
                {
                    "x":[],四个数代表四个角点的x
                    "y":[],四个数代表四个角点的y
                    "yaw_rad":[] 一个数代表headign
                },
                ...
            ],
            "cusp_region":[
                {
                "cusp_point": (x,y,yaw_rad),
                "cusp_region_radius": 0,
                },
                ...
            ],
            "end":
        }
    """

    def __init__(self):
        self.car_num = 1
        self.collision_car_index = []
        self.complete_flag = []
        self.vehicle_info = {
            "ego":{
                "x":[],
                "y":[],
                "v_mps":[],
                "acc_mpss":[],
                "yaw_rad":[],
                "yawrate_radps":[],
                "exist_time":[],
                "shape":{
                    "vehicle_type":"MineTruck_NTE200",
                    "length":13.4,
                    "width":6.7,
                    "height":6.9,
                    "min_turn_radius":14.2,
                    "locationPoint2Head":9.8,
                    "locationPoint2Rear":3.8
			    }
            },
        }
        self.hdmaps = {}
        self.test_setting = {
            "scenario_name":"name",
            "scenario_type":"intersection",
            "enter_loading_flag":False,
            "enter_loading_time":0.00,
            "t":0.0,
            "dt":0.1,
            "max_t":-1,
            "work_position":[],
            "work_time": 10,
            "cusp_region":[],
            "goal":{
                "x":[-1,-1,-1,-1],
                "y":[-1,-1,-1,-1],
                "heading":None
            },
            "end":-1,
            "x_min":None,
            "x_max":None,
            "y_min":None,
            "y_max":None,
            "start_ego_info":None,
            "generate_cusp_region": False,
            "cusp_type": "left", # 往左前方伸展出去获得人字尖点也就是逆时针伸展
        }
        
    def format(self):
        return {
            "car_num":self.car_num,
            "collision_car_index":self.collision_car_index,
            "vehicle_info":self.vehicle_info,
            "test_setting":self.test_setting,
            "hdmaps_info":self.hdmaps,
            "complete_flag":self.complete_flag
        }

if __name__ == "__main__":
    pass
