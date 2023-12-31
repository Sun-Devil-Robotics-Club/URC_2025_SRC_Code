import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_path


def generate_launch_description():
    zed2_launch = os.path.join(
        get_package_share_path("zed_wrapper"), "launch", "zed2.launch.py"
    )

    zed2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(zed2_launch),
    )

    return LaunchDescription([zed2])
