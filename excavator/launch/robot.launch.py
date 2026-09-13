"""
Launch file for a differential-drive robot in Gazebo Harmonic + ROS 2 Jazzy.

Starts:
  1. Gazebo (gz sim) with a given world
  2. robot_state_publisher (publishes TF from your URDF/xacro)
  3. Spawns the robot into Gazebo from the /robot_description topic
  4. ros_gz_bridge (cmd_vel, odom, tf, clock, etc.)

Usage:
  ros2 launch excavator robot.launch.py
  ros2 launch excavator robot.launch.py world:=my_world.sdf
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import Command


def generate_launch_description():
    pkg_name = "excavator"          # TODO: change this, if this isn't an excavator
    robot_name = "excavator"        # TODO: change this, if this isn't an excavator

    pkg_share = get_package_share_directory(pkg_name)

    # Set the world path, through the package share directory
    world_path = PathJoinSubstitution(
        [ FindPackageShare(pkg_name), "worlds", "excavator_empty.sdf" ]
    )

    # ---- Launch arguments -------------------------------------------------
    world_arg = DeclareLaunchArgument(
        "world",
        default_value="worlds/excavator_empty.sdf",
        description="Gazebo world file to load",
    )
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation clock",
    )

    world = LaunchConfiguration("world")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # ---- Process the xacro/URDF into robot_description ---------------------
    xacro_file = os.path.join(pkg_share, "urdf", robot_name + ".urdf.xacro")
    robot_description = {
        "robot_description": Command(["xacro ", xacro_file])
    }

    # ---- robot_state_publisher ---------------------------------------------
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # ---- Start Gazebo (gz sim) via ros_gz_sim's launch file ----------------
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={"gz_args": ["-r ", world]}.items(),
    )

    # ---- Spawn the robot from /robot_description into Gazebo ---------------
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", robot_name,
            "-x", "0.5", "-y", "0.0", "-z", "0.4",
        ],
        output="screen",
    )

    # ---- ROS <-> Gazebo bridge ----------------------------------------------
    bridge_config = PathJoinSubstitution(
        [FindPackageShare(pkg_name), "config", robot_name + "_bridge.yaml"]
    )
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {"config_file": bridge_config, "use_sim_time": use_sim_time}
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            world_arg,
            use_sim_time_arg,
            robot_state_publisher,
            gz_sim,
            spawn_robot,
            bridge,
        ]
    )