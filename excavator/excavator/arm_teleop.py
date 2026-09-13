#!/usr/bin/env python3
"""
Keyboard teleop for the excavator. Designed to be operated using the 
numpad.

Arm Controls:
    8 - Pitch up
    5 - Stop
    2 - Pitch down

Chassis Controls:
    4 - Rotate left
    5 - Stop
    6 - Rotate right

Other Controls:
    q - quit
    Ctrl-C - quit

Publishes std_msgs/Float64 on 'arm/boom_cmd' and 'chassis/yaw_cmd', 
which ros_gz_bridge forwards to the JointController plugin's command topic.
"""

import sys      # For reading keyboard input
import termios  # POSIX terminal control library
import tty      # POSIX terminal control library

import rclpy    # Python library for ROS 2
from rclpy.node import Node
from std_msgs.msg import Float64


# ====== ARM CONFIG ====== #

ARM_SPEED = 0.5  # rad/s, tune to revolute joint's <limit velocity="...">
ARM_KEY_BINDINGS = {
    '8': -ARM_SPEED,        # Up
    '2': ARM_SPEED,         # Down
    '5': 0.0,               # Stop
}

# ====== CHASSIS CONFIG ====== #

CHASSIS_SPEED = 10.5
CHASSIS_KEY_BINDINGS = {
    '4': CHASSIS_SPEED,     # Left
    '6': -CHASSIS_SPEED,    # Right
    '5': 0.0,               # Stop
}


def get_key(settings):
    """ Get a single keypress from the terminal. """
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class ArmTeleop(Node):
    """ ROS2 node for teleoperating a single arm joint.
    Designed to affect pitch. """

    def __init__(self):
        super().__init__('arm_teleop')
        self.publisher = self.create_publisher(Float64, 'arm/boom_cmd', 10)

    def publish(self, value):
        msg = Float64()
        msg.data = value
        self.publisher.publish(msg)
### ArmTeleop

class ChassisTeleop(Node):
    """ ROS2 node for teleoperating a chasiss joint. 
    Designed to affect yaw. """

    def __init__(self):
        super().__init__('chassis_teleop')
        self.publisher = self.create_publisher(Float64, 'chassis/yaw_cmd', 10)

    def publish(self, value):
        msg = Float64()
        msg.data = value
        self.publisher.publish(msg)
### ChassisTeleop

def main():
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()

    # Set up a dictionary for all publishing nodes
    # TODO: Probably should refactor this to be a list, where nodes store their own key bindings and we iterate over all nodes
    Nodes: dict[str, Node] = {}

    Nodes["arm"] = ArmTeleop()
    Nodes["chassis"] = ChassisTeleop()

    # Prints the explanation to the consol
    print(__doc__)

    # ====== MAIN LOOP ====== #
    try:
        while True:
            key = get_key(settings)

            # Check if should exit
            if key == 'q' or key == '\x03':
                break

            # Check if moving arm
            if key in ARM_KEY_BINDINGS:
                velocity = ARM_KEY_BINDINGS[key]
                Nodes["arm"].publish(velocity)

            # Check if moving Chassis
            if key in CHASSIS_KEY_BINDINGS:
                velocity = CHASSIS_KEY_BINDINGS[key]
                Nodes["chassis"].publish(velocity)

            # Unrecognized keys are ignored
    except Exception as e:
        print(e)
    finally:
        # Always stop the arm on exit, don't leave it moving

        Nodes["arm"].publish(0.0)
        Nodes["arm"].destroy_node()

        Nodes["chassis"].publish(0.0)
        Nodes['chassis'].destroy_node()

        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == '__main__':
    main()