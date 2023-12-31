import os
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    port_arg = DeclareLaunchArgument(
        "port", default_value="9090", description="Port for ROS Bridge Server"
    )

    ros_bridge_server_launch_path = os.path.join(
        get_package_share_directory("rosbridge_server"),
        "launch",
        "rosbridge_websocket_launch.xml",
    )

    ros_bridge_server_node = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(ros_bridge_server_launch_path),
        launch_arguments={"port": LaunchConfiguration("port")}.items(),
    )

    return LaunchDescription([port_arg, ros_bridge_server_node])
