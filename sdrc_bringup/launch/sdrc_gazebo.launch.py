import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import (
    get_package_share_path,
    get_package_share_directory,
)


def generate_launch_description():
    use_ros2_control = LaunchConfiguration("use_ros2_control")
    use_sim_time = LaunchConfiguration("use_sim_time")

    urdf_path = os.path.join(
        get_package_share_path("sdrc_description"), "urdf", "my_robot.urdf.xacro"
    )
    gazebo_ros_launch_path = os.path.join(
        get_package_share_path("gazebo_ros"), "launch", "gazebo.launch.py"
    )
    rviz_config_path = os.path.join(
        get_package_share_path("sdrc_bringup"), "rviz", "urdf_config.rviz"
    )
    world_path = os.path.join(
        get_package_share_path("sdrc_bringup"), "worlds", "nav_world.world"
    )
    gazebo_params_file = os.path.join(
        get_package_share_path("sdrc_bringup"), "config", "gazebo_params.yaml"
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            {
                "robot_description": Command(
                    ["xacro ", urdf_path, " use_ros2_control:=", use_ros2_control]
                ),
                "use_sim_time": use_sim_time,
            }
        ],
    )

    twist_mux_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("sdrc_bringup"),
                    "launch",
                    "twist_mux.launch.py",
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_ros_launch_path),
        launch_arguments={
            "world": world_path,
            "extra_gazebo_args": "--ros-args --params-file " + gazebo_params_file,
        }.items(),
    )

    gazebo_ros_node = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "my_robot"],
        output="screen",
    )

    rviz2_node = Node(
        package="rviz2", executable="rviz2", arguments=["-d", rviz_config_path]
    )

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="uses simulation time if true",
            ),
            DeclareLaunchArgument(
                "use_ros2_control",
                default_value="true",
                description="use ros2 control if true",
            ),
            robot_state_publisher_node,
            twist_mux_node,
            gazebo,
            gazebo_ros_node,
            rviz2_node,
            diff_drive_spawner,
            joint_broad_spawner,
        ]
    )
