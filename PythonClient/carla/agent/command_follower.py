


from carla.agent.agent import Agent
from carla.agent.modules import ObstacleAvoidance, Controller, Waypointer
from carla.agent.modules.utils import get_angle, get_vec_dist



class CommandFollower(Agent):
    """
    The Command Follower agent. It follows the high level commands proposed by the player.
    """
    def __init__(self, town_name):

        # The necessary parameters for the obstacle avoidance module.
        param_obstacles = {
            'stop4TL': False,  # Stop for traffic lights
            'stop4P': True,  # Stop for pedestrians
            'stop4V': True,  # Stop for vehicles
            'coast_factor': 2,  # Factor to control coasting
            'tl_dist_thres': 15,  # Distance Threshold Traffic Light
            'tl_angle_thres': 0.5,  # Angle Threshold Traffic Light
            'p_dist_thres': 10,  # Distance Threshold Pedestrian
            'p_angle_thres': 0.3,  # Angle Threshold Pedestrian
            'v_dist_thres': 15,  # Distance Threshold Vehicle
            'v_angle_thres': 0.35  # Angle Threshold Vehicle

        }
        # The used parameters for the controller.
        param_controller = {
            'default_throttle': 0.5,  # Default Throttle
            'default_brake': 0.0,  # Default Brake
            'steer_gain': 0.7,  # Gain on computed steering angle
            'brake_strength': 1,  # Strength for applying brake - Value between 0 and 1
            'pid_p': 0.2,  # PID speed controller parameters
            'pid_i': 0.08,
            'pid_d': 0.0,
            'target_speed': 35,  # Target speed - could be controlled by speed limit
            'throttle_max': 0.75,
        }


        self.wp_num_steer = 0.8  # Select WP - Reverse Order: 1 - closest, 0 - furthest
        self.wp_num_speed = 0.5  # Select WP - Reverse Order: 1 - closest, 0 - furthest
        self.waypointer = Waypointer(town_name)
        self.obstacle_avoider = ObstacleAvoidance(param_obstacles)
        self.controller = Controller(param_controller)




    def run_step(self, measurements, sensor_data, direction, target):
        """

        Args:
            measurements: carla measurements for all vehicles
            sensor_data: the sensor that attached to this vehicle
            waypoints: waypoints produced by the local planner
            target: the transform of the target.

        Returns:

        """

        player = measurements.player_measurements
        agents = measurements.non_player_agents
        # print ' it has  ',len(agents),' agents'
        loc_x_player = player.transform.location.x
        loc_y_player = player.transform.location.y
        ori_x_player = player.transform.orientation.x
        ori_y_player = player.transform.orientation.y
        ori_z_player = player.transform.orientation.z

        waypoints_world, waypoints = self.waypointer.get_next_waypoints(
            (loc_x_player, loc_y_player, 0.22), (ori_x_player, ori_y_player, ori_z_player),
            (target.location.x, target.location.y, target.location.z),
            (target.orientation.x, target.orientation.y, target.orientation.z)
        )

        #  TODO This go inside the waypoints
        if waypoints_world == []:
            waypoints_world = [[loc_x_player, loc_y_player, 0.22]]


        # Make a function, maybe util function to get the magnitues

        wp = [waypoints_world[int(self.wp_num_steer * len(waypoints_world))][0],
              waypoints_world[int(self.wp_num_steer * len(waypoints_world))][1]]

        wp_vector, wp_mag = get_vec_dist(wp[0], wp[1], loc_x_player, loc_y_player)

        if wp_mag > 0:
            wp_angle = get_angle(wp_vector, [ori_x_player, ori_y_player])
        else:
            wp_angle = 0

        # WP Look Ahead for steering
        wp_speed = [waypoints[int(self.wp_num_speed * len(waypoints))][0],
                         waypoints[int(self.wp_num_speed * len(waypoints))][1]]
        wp_vector_speed, wp_mag_speed = get_vec_dist(wp_speed[0], wp_speed[1],
                                                     loc_x_player,
                                                     loc_y_player)
        wp_angle_speed = get_angle(wp_vector_speed, [ori_x_player, ori_y_player])

        # print ('Next Waypoint (Steer): ', waypoints[self.wp_num_steer][0], waypoints[self.wp_num_steer][1])
        # print ('Car Position: ', player.transform.location.x, player.transform.location.y)
        # print ('Waypoint Vector: ', wp_vector[0]/wp_mag, wp_vector[1]/wp_mag)
        # print ('Car Vector: ', player.transform.orientation.x, player.transform.orientation.y)
        # print ('Waypoint Angle: ', wp_angle, ' Magnitude: ', wp_mag)

        speed_factor = self.obstacle_avoider.stop_for_agents(player.transform.location, wp_angle,
                                                             wp_vector, agents)



        # We should run some state machine around here
        control = self.controller.get_control(wp_angle, wp_angle_speed, speed_factor,
                                              player.forward_speed*3.6)

        return control