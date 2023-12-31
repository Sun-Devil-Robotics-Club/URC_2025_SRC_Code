import os
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_path
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch import LaunchDescription


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    slam_params = os.path.join(
        get_package_share_path("sdrc_bringup"),
        "config",
        "mapper_params_online_async.yaml",
    )

    async_slam_toolbox_node = Node(
        parameters=[slam_params, {"use_sim_time": use_sim_time}],
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use simulation/Gazebo clock",
            ),
            async_slam_toolbox_node,
        ]
    )
