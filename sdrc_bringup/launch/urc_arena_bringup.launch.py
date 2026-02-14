from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    bringup_pkg = FindPackageShare('sdrc_bringup')
    desc_pkg    = FindPackageShare('sdrc_description')
    gz_pkg      = FindPackageShare('gazebo_ros')

    world      = PathJoinSubstitution([bringup_pkg, 'worlds', 'urc_arena.world'])
    urdf_xacro = PathJoinSubstitution([desc_pkg, 'urdf', 'my_robot.urdf.xacro'])

    declare_x   = DeclareLaunchArgument('x', default_value='0.0')
    declare_y   = DeclareLaunchArgument('y', default_value='0.0')
    declare_z   = DeclareLaunchArgument('z', default_value='0.10')
    declare_Yaw = DeclareLaunchArgument('Y', default_value='0.0')
    x = LaunchConfiguration('x'); y = LaunchConfiguration('y')
    z = LaunchConfiguration('z'); Y = LaunchConfiguration('Y')

    robot_description = Command(['xacro', ' ', urdf_xacro])

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen'
    )

    # Use gazebo_ros' canonical launcher
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([gz_pkg, 'launch', 'gazebo.launch.py'])
        ),
        launch_arguments={'world': world}.items()
    )

    spawner = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'my_robot', '-x', x, '-y', y, '-z', z, '-Y', Y],
        output='screen'
    )

    return LaunchDescription([
        declare_x, declare_y, declare_z, declare_Yaw,
        gazebo_launch,
        rsp,
        spawner,
    ])
