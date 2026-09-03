#!/usr/bin/env python3
"""
Simple keyboard teleop for a single arm joint (e.g. excavator boom).

Controls:
  + - move arm up   (positive velocity)
  - - move arm down (negative velocity)
  0 - stop
  q - quit
  Ctrl-C - quit

Publishes std_msgs/Float64 on 'arm/boom_cmd', which ros_gz_bridge
forwards to the JointController plugin's command topic.
"""

import sys      # For reading keyboard input
import termios  # POSIX terminal control library
import tty      # POSIX terminal control library

import rclpy    # Python library for ROS 2
from rclpy.node import Node
from std_msgs.msg import Float64

ARM_SPEED = 0.5  # rad/s, tune to your joint's <limit velocity="...">

KEY_BINDINGS = {
    '+': ARM_SPEED,
    '-': -ARM_SPEED,
    '0': 0.0,
    # Potentially add more keys for other actions
}


def get_key(settings):
    """ Get a single keypress from the terminal. """
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class ArmTeleop(Node):
    """ ROS2 node for teleoperating a single arm joint. """

    def __init__(self):
        super().__init__('arm_teleop')
        self.publisher = self.create_publisher(Float64, 'arm/boom_cmd', 10)

    def send_velocity(self, value: float):
        msg = Float64()
        msg.data = value
        self.publisher.publish(msg)


def main():
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = ArmTeleop()

    print(__doc__)

    try:
        while True:
            key = get_key(settings)
            if key == 'q' or key == '\x03':
                break
            elif key in KEY_BINDINGS:
                velocity = KEY_BINDINGS[key]
                node.send_velocity(velocity)
            # Unrecognized keys are ignored
    except Exception as e:
        print(e)
    finally:
        # Always stop the arm on exit, don't leave it moving
        node.send_velocity(0.0)
        node.destroy_node()
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == '__main__':
    main()