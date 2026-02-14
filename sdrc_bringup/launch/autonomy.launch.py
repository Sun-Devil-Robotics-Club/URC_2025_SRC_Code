from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Include full simulation stack
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("sdrc_bringup"),
                "launch",
                "sdrc_gazebo.launch.py",
            )
        )
    )

    # Perception pipeline
    detect_ar = Node(
        package="sdrc_autonomy",
        executable="detect_ar_tag",
        name="ar_tag_detector",
        parameters=[{"use_sim_time": True}],
    )

    detect_obj = Node(
        package="sdrc_autonomy",
        executable="detect_object",
        name="object_detector",
        parameters=[
            {
                "use_sim_time": True,
                "yolo_model_path": os.path.expanduser("~/Downloads/best.onnx"),
                "conf_threshold": 0.5,
                "nms_threshold": 0.4,
            }
        ],
    )

    localizer = Node(
        package="sdrc_autonomy",
        executable="semantic_localizer",
        name="semantic_localizer",
        parameters=[{"use_sim_time": True}],
    )

    # Behavior tree executor
    bt_exec = Node(
        package="sdrc_autonomy",
        executable="bt_runner",
        name="bt_executor",
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription(
        [
            sim_launch,
            detect_ar,
            detect_obj,
            localizer,
            bt_exec,
        ]
    )
