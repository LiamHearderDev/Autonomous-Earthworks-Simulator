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

import select   # For non-blocked I/O
import time     # 

import sys      # For reading keyboard input
import termios  # POSIX terminal control library
import tty      # POSIX terminal control library

import rclpy    # Python library for ROS 2
from rclpy.node import Node
from std_msgs.msg import Float64

from sensor_msgs.msg import JointState  # For receiving data from the Joints (for margins)


class Float64Publisher(Node):
    """ A ROS2 node for teleoperating a joint using a Float64.
    Originally designed to affect an axis for a joint's rotation. """

    def __init__(self, name: str, joint_name: str, topic: str, key_bindings: dict):
        super().__init__(name)
        self.publisher = self.create_publisher(Float64, topic, 10)

        self.key_bindings = key_bindings
        self.joint_name = joint_name

        # Begin listening to the Joint States
        self.joint_position = None
        self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            10
        )

        # Margins are used to dampen, so the joint never reaches the real limit.
        self.adhere_to_margins = False
        self.lower_margin = -1.5708
        self.upper_margin = 1.5708

        self.current_velocity = 0.0


    def publish(self, velocity):
        """ Used to publish messages on a topic. """
        if not rclpy.ok():
            return

        if (self.joint_position is not None) and (self.adhere_to_margins == True):
            if (self.joint_position >= self.upper_margin) and (velocity > 0):
                print("APPROACHING UPPER LIMIT")
                velocity = 0.0
            if (self.joint_position <= self.lower_margin) and (velocity < 0):
                velocity = 0.0
                print("APPROACHING LOWER LIMIT")

        self.current_velocity = velocity

        msg = Float64()
        msg.data = velocity
        self.publisher.publish(msg)


    def set_margins(self, lower: float, upper: float):
        """ Used to define soft limits for joints. """
        self.adhere_to_margins = True
        self.lower_margin = lower
        self.upper_margin = upper


    def joint_state_callback(self, message):
        """ Used to learn the joint positions. Useful for soft limits on joints. """
        if self.joint_name not in message.name:
            return
        index = message.name.index(self.joint_name)
        self.joint_position = message.position[index]

        if (self.joint_position is not None) and (self.adhere_to_margins == True):
            if (self.joint_position >= self.upper_margin) and (self.current_velocity > 0):
                print("APPROACHING UPPER LIMIT")
                self.publish(0.0)
            if (self.joint_position <= self.lower_margin) and (self.current_velocity < 0):
                print("APPROACHING LOWER LIMIT")
                self.publish(0.0)
### Float64Publisher ###


def get_key():
    """ Get a single keypress from the terminal. """

    readable, _, _ = select.select([sys.stdin], [], [], 0)
    if readable:
        return sys.stdin.read(1)
    
    return None


def main():
    settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    rclpy.init()

    # ====== Set up all publishing nodes ====== #
    Nodes: list[Node] = []

    # Upper arm - Pitch
    upper_arm_node = Float64Publisher(      
        name='arm_teleop',
        joint_name='upper_arm_joint',
        topic='arm/boom_cmd',
        key_bindings={'8':-0.5, '2':0.5, '5': 0.0 }  # Up, Down, Stop
    )
    upper_arm_node.set_margins(lower=-1.0, upper=1.0)
    Nodes.append(upper_arm_node)

    # Chassis - Yaw
    chassis_node = Float64Publisher(      
        name='chassis_teleop',
        joint_name='chassis_joint',
        topic='chassis/yaw_cmd',
        key_bindings={'4':0.5, '6':-0.5, '5':0.0 }  # Left, Right, Stop
    )
    Nodes.append(chassis_node)


    # ====== Prints the explanation / controls to the terminal ====== #
    print(__doc__)


    # ====== MAIN LOOP ====== #
    try:
        while True:

            for node in Nodes:
                rclpy.spin_once(node, timeout_sec=0.0)

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
                    node.publish(velocity=node.key_bindings[key])
    except KeyboardInterrupt as e:
        print("Keyboard Interrupt... Exiting teleop.")
        print("-"*20)
    except Exception as e:
        print("Exeception occurred... Exiting teleop.")
        print(e)
        print("-"*20)
    finally:

        # Always stop joints on exit, don't leave them moving
        for node in Nodes:
            node.publish(0.0)
            node.destroy_node()


        if rclpy.ok():
            rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        


if __name__ == '__main__':
    main()