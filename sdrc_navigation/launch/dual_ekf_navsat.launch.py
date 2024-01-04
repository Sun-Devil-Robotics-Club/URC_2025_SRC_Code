from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_ros.actions
import os
import launch.actions


def generate_launch_description():
    nav_dir = get_package_share_directory("sdrc_navigation")
    rl_params_file = os.path.join(nav_dir, "config", "dual_ekf_navsat_params.yaml")

    # This EKF is responsible for taking local data and providing odom -> base link transform
    # Answers how is robot oriented and moving
    ekf_local_node = launch_ros.actions.Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node_odom",
        output="screen",
        parameters=[rl_params_file, {"use_sim_time": True}],
        remappings=[("odometry/filtered", "odometry/local")],
    )

    # This EKF is responsible for global positioning using GPS data provide map -> odom transform
    # Answers where is robot in the world (GPS -> Robot Co-ordinate system)
    ekf_global_node = launch_ros.actions.Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node_map",
        output="screen",
        parameters=[rl_params_file, {"use_sim_time": True}],
        remappings=[("odometry/filtered", "odometry/global")],
    )

    # Converts GNSS data to cartesian frame of robot
    navsat_node = launch_ros.actions.Node(
        package="robot_localization",
        executable="navsat_transform_node",
        name="navsat_transform",
        output="screen",
        parameters=[rl_params_file, {"use_sim_time": True}],
        remappings=[
            ("imu/data", "imu/data"),
            ("gps/fix", "gps/data"),
            ("odometry/filtered", "odometry/global"),
            ("gps/filtered", "gps/filtered"),
            ("odometry/gps", "odometry/gps"),
        ],
    )

    return LaunchDescription(
        [
            ekf_local_node,
            navsat_node,
            ekf_global_node,
        ]
    )
