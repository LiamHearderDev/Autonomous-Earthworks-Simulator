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
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import Command


def generate_launch_description():
    pkg_name = "excavator"          # TODO: change this, if this isn't an excavator
    robot_name = "excavator"        # TODO: change this, if this isn't an excavator

    pkg_share = get_package_share_directory(pkg_name)
    gz_resource_path = os.pathsep.join(
        path
        for path in [
            os.path.dirname(pkg_share),
            os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
        ]
        if path
    )

    # ---- Launch arguments -------------------------------------------------
    world_arg = DeclareLaunchArgument(
        "world",
        default_value="worlds/aarp_goose_demo_v2.sdf",
        description="Gazebo world file to load",
    )
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation clock",
    )
    gnss_enabled_arg = DeclareLaunchArgument(
        "gnss_enabled",
        default_value="true",
    )

    world = LaunchConfiguration("world")
    use_sim_time = LaunchConfiguration("use_sim_time")
    gnss_enabled = LaunchConfiguration("gnss_enabled")

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

    # ---- Activating ROS2 controllers ---------------------------------------
    joint_state_broadcaster = Node(
    package="controller_manager",
    executable="spawner",
    arguments=[
        "joint_state_broadcaster",
        "--controller-manager",
        "/controller_manager",
    ],
    output="screen",
)

    upper_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "upper_arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    lower_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "lower_arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    chassis_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "chassis_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    # ---- Start Gazebo (gz sim) via ros_gz_sim's launch file ----------------
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={"gz_args": ["-r -v4 ", world], 'on_exit_shutdown': 'true'}.items(),
    )

    # ---- Spawn the robot from /robot_description into Gazebo ---------------
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", robot_name,
            "-x", "0.5", "-y", "0.0", "-z", "5.4",
        ],
        output="screen",
    )
    
    # ---- ROS <-> Gazebo Camera ----------------------------------------------
    camera_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=["/cam1/rgbd_camera/image", "/cam2/rgbd_camera/image"],
            output="screen",
            parameters=[{"use_sim_time": use_sim_time}],
        )
    
    camera_view1 = Node(
        package="rqt_image_view",
        executable="rqt_image_view",
        name="camera_view1",
        arguments=["/cam1/rgbd_camera/image"],
        output="screen"
    )
    
    camera_view2 = Node(
            package="rqt_image_view",
            executable="rqt_image_view",
            name="camera_view2",
            arguments=["/cam2/rgbd_camera/image"],
            output="screen"
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

    gnss_node = Node(
        package=pkg_name,
        executable="gnss_node",
        name="gnss_node",
        output="screen",
        parameters=[
            os.path.join(pkg_share, "config", "gnss.yaml"),
            {"use_sim_time": use_sim_time},
        ],
        condition=IfCondition(gnss_enabled),
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable(
                name="GZ_SIM_RESOURCE_PATH",
                value=gz_resource_path,
            ),
            world_arg,
            use_sim_time_arg,
            gnss_enabled_arg,
            robot_state_publisher,
            gz_sim,
            spawn_robot,
            bridge,
            gnss_node,
            joint_state_broadcaster,
            upper_arm_controller,
            lower_arm_controller,
            chassis_controller,
            camera_bridge,
            camera_view1,
            camera_view2
        ]
    )
