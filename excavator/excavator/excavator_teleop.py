#!/usr/bin/env python3
"""
Keyboard teleop for the excavator. Designed to be operated using the 
numpad.

Movement Controls:
    W - Forward
    A - Left
    S - Back
    D - Right
    X - Stop

Upper Arm Controls:
    8 - Pitch up
    5 - Stop
    2 - Pitch down

Lower Arm Controls:
    7 - Pitch up
    5 - Stop
    1 - Pitch down

Chassis Controls:
    4 - Rotate left
    5 - Stop
    6 - Rotate right

BLASTDOG Probe Controls:
    9 - Raise probe
    5 - Stop
    3 - Lower probe

Other Controls:
    q - quit
    Ctrl-C - quit

Publishes Float64MultiArray velocity commands for the chassis and
JointTrajectory position commands for the upper arm.
"""

import select   # For non-blocked I/O
import time     # For waiting 0.01s during I/O
import sys      # For reading keyboard input
import termios  # POSIX terminal control library
import tty      # POSIX terminal control library

import rclpy    # Python library for ROS 2
from rclpy.node import Node as RosNode

from std_msgs.msg import Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from geometry_msgs.msg import Twist

from sensor_msgs.msg import JointState  # For receiving data from the Joints



class Float64Publisher(RosNode):
    """A ROS2 node for teleoperating one joint with a velocity command.
    Originally designed to affect an axis for a joint's rotation. """

    def __init__(self, name: str, joint_name: str, link_name: str, topic: str, key_bindings: dict):
        super().__init__(name)
        self.name = name
        self.publisher = self.create_publisher(Float64MultiArray, topic, 10)

        self.key_bindings = key_bindings
        self.joint_name = joint_name
        self.link_name = link_name

        # Begin listening to the Joint States
        self.joint_position = None
        self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            10
        )

    def publish(self, value):
        """ Used to publish messages on a topic. """
        if not rclpy.ok():
            return

        msg = Float64MultiArray()
        msg.data = [value]
        self.publisher.publish(msg)

    def joint_state_callback(self, message):
        """ Update this node based on the joint/link information. """
        if self.joint_name not in message.name:
            return
        index = message.name.index(self.joint_name)
        self.joint_position = message.position[index]
### Float64Publisher ###


class JointTrajectoryPublisher(RosNode):
    """Command a joint toward an endpoint until a new target is sent."""

    def __init__(self, name: str, joint_name: str, topic: str, key_bindings: dict, lower_limit: float, upper_limit: float):
        super().__init__(name)
        self.name = name
        self.publisher = self.create_publisher(JointTrajectory, topic, 10)
        self.joint_name = joint_name
        self.key_bindings = key_bindings
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.joint_position = None
        self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            10,
        )

    def joint_state_callback(self, message):
        if self.joint_name in message.name:
            self.joint_position = message.position[message.name.index(self.joint_name)]
        else:
            print(f"did NOT find in joint state callback. Received message: \n---\n{message}\n---")

    def publish(self, direction):
        if not rclpy.ok() or self.joint_position is None:
            return

        trajectory = JointTrajectory()
        trajectory.joint_names = [self.joint_name]

        point = JointTrajectoryPoint()
        if direction > 0.0:
            target_position = self.upper_limit
        elif direction < 0.0:
            target_position = self.lower_limit
        else:
            target_position = self.joint_position

        point.positions = [target_position]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 100000000
        trajectory.points = [point]
        self.publisher.publish(trajectory)
### JointTrajectoryPublisher ###


class TwistPublisher(RosNode):
    def __init__(self, name: str, topic: str, key_bindings: dict):
        super().__init__(name)
        self.name = name
        self.publisher = self.create_publisher(Twist, topic, 10)
        self.key_bindings = key_bindings

    def publish(self, value):
        """Publish a (linear_x, angular_z) differential-drive command."""
        if not rclpy.ok():
            return

        msg = Twist()
        if isinstance(value, (int, float)):
            linear_x, angular_z = 0.0, 0.0
        else:
            linear_x, angular_z = value

        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher.publish(msg)
### TwistPublisher ###


def get_key():
    """ Get a single keypress from the terminal. """
    readable, _, _ = select.select([sys.stdin], [], [], 0)
    if readable:
        return sys.stdin.read(1)
    return None


def main():
    settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())
        rclpy.init()

        # ====== Set up all publishing nodes ====== #
        Nodes: list[RosNode] = []

        # Differential Drive - Twist
        drive_node = TwistPublisher(
            name='drive_teleop',
            topic='/cmd_vel',
            key_bindings={
                'w': (0.5, 0.0),
                'a': (0.0, 0.5),
                's': (-0.5, 0.0),
                'd': (0.0, -0.5),
                'x': (0.0, 0.0),
            },
        )
        Nodes.append(drive_node)

        # Upper arm - Position
        upper_arm_node = JointTrajectoryPublisher(
            name='upper_arm_teleop',
            joint_name='upper_arm_joint',
            topic='/upper_arm_controller/joint_trajectory',
            key_bindings={'8':-0.5, '2':0.5, '5': 0.0 },  # Up, Down, Stop
            lower_limit=-0.8,
            upper_limit=0.8
        )
        Nodes.append(upper_arm_node)

        # Lower arm - Position
        lower_arm_node = JointTrajectoryPublisher(
            name='lower_arm_teleop',
            joint_name='lower_arm_joint',
            topic='/lower_arm_controller/joint_trajectory',
            key_bindings={'7':-0.5, '1':0.5, '5': 0.0 },  # Up, Down, Stop
            lower_limit=-1.6,
            upper_limit=0.0
        )
        Nodes.append(lower_arm_node)

        # Chassis - Yaw
        chassis_node = Float64Publisher(
            name='chassis_teleop',
            link_name='chassis',
            joint_name='chassis_joint',
            topic='/chassis_controller/commands',
            key_bindings={'4':0.5, '6':-0.5, '5':0.0 }  # Left, Right, Stop
        )
        Nodes.append(chassis_node)

        
        # blastdog_probe_node = Float64Publisher(
        #     name='blastdog_probe_teleop',
        #     link_name='blastdog_probe',
        #     joint_name='blastdog_probe_joint',
        #     topic='/blastdog_probe_controller/commands',
        #     key_bindings={'9': 0.25, '3': -0.25, '5': 0.0},  # Up, Down, Stop
        # )

        # BLASTDOG probe - vertical prismatic joint velocity
        blastdog_probe_node = JointTrajectoryPublisher(
            name='blastdog_probe_teleop',
            joint_name='blastdog_probe_joint',
            topic="/blastdog_probe_controller/joint_trajectory",
            key_bindings={'9': -0.25, '3': 0.25, '5': 0.0},
            lower_limit=0.0,
            upper_limit=1.5
        )
        Nodes.append(blastdog_probe_node)

    except Exception as e:
        print("Exeception occurred... Exiting teleop.")
        print(e)
        print("-"*20)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

        for node in Nodes:
            node.publish(0.0)
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

    # ====== Prints the explanation / controls to the terminal ====== #
    print(__doc__)

    # ====== MAIN LOOP ====== #
    try:
        while True:

            for node in Nodes:
                rclpy.spin_once(node, timeout_sec=0.001)

            key = get_key()
            if (key is None):
                time.sleep(0.01)
                continue

            # Check if should exit
            if key == 'q' or key == '\x03':
                break

            # If the key matches one of our nodes, publish the value
            for node in Nodes:
                if key in node.key_bindings:
                    node.publish(node.key_bindings[key])
    except KeyboardInterrupt as e:
        print("Keyboard Interrupt... Exiting teleop.")
        print("-"*20)
    except Exception as e:
        print("Exeception occurred... Exiting teleop.")
        print(e)
        print("-"*20)
    finally:

        # Resets the terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

        # Always stop joints on exit, don't leave them moving
        for node in Nodes:
            node.publish(0.0)
            node.destroy_node()

        # Safely shuts down rclpy
        if rclpy.ok():
            rclpy.shutdown()
        
        
if __name__ == '__main__':
    main()
