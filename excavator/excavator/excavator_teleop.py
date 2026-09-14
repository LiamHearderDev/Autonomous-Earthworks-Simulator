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
import time     # For waiting 0.01s during I/O
import sys      # For reading keyboard input
import termios  # POSIX terminal control library
import tty      # POSIX terminal control library

import rclpy    # Python library for ROS 2
from rclpy.node import Node as RosNode
from std_msgs.msg import Float64

from sensor_msgs.msg import JointState  # For receiving data from the Joints (for margins)



class Float64Publisher(RosNode):
    """ A ROS2 node for teleoperating a joint using a Float64.
    Originally designed to affect an axis for a joint's rotation. """

    def __init__(self, name: str, joint_name: str, link_name: str, topic: str, key_bindings: dict):
        super().__init__(name)
        self.publisher = self.create_publisher(Float64, topic, 10)

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

        # Margins are used to dampen, so the joint never reaches the real limit.
        self.adhere_to_margins = False
        self.lower_margin = -1.5708
        self.upper_margin = 1.5708

        # The joint's current velocity
        self.current_velocity = 0.0

        # Set Gravity Compensator to None, so we don't use it
        self.gravity_compensator = None


    def start_gravity_compensator(self, link_mass: float, r_com: float):
        self.gravity_compensator = GravityCompensator(
            self.link_name,
            self.joint_name,
            link_mass,
            r_com
        )

    def publish(self, velocity):
        """ Used to publish messages on a topic. """
        if not rclpy.ok():
            return

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
        """ Update this node based on the joint/link information. """
        if self.joint_name not in message.name:
            return
        index = message.name.index(self.joint_name)
        self.joint_position = message.position[index]

        if (self.gravity_compensator is not None):
            self.gravity_compensator.joint_state_callback(message)
### Float64Publisher ###


# === Imports for GravityCompensator === #
import math
from gz.transport13 import Node as GzNode
from gz.msgs10.entity_wrench_pb2 import EntityWrench

class GravityCompensator:
    """ This class calculates gravity's torque about a joint, and applies
    a compensating force. Originally designed to stop the excavator arm
    from being slowly pulled to the ground. 
    
    This is only important for boom joints.

    Formula:
        τ_gravity ≈ m * g * r_com * cos(θ)

        m       =   The link's mass. 
        g       =   Gravity.
        r_com   =   Distance from the joint to its center of mass.
        θ       =   The angle measured from horizontal.
    """

    def __init__(self, link_name: str, joint_name: str, link_mass: float, r_com: float):
        self.mass = link_mass
        self.r_com = r_com
        self.link_name = link_name
        self.joint_name = joint_name

        self.gravity = 9.8

        self.gz_node = GzNode()
        self.publisher = self.gz_node.advertise(
            "/world/excavator/wrench/persistent",
            EntityWrench,
        )
        
        # Used to find the index of the target joint in /joint_states
        self.message_index = None

    def gravity_torque(self, theta_rad: float):
        return self.mass * self.gravity * self.r_com * math.cos(theta_rad)

    def joint_state_callback(self, msg):
        theta: float = self.get_angle(msg)
        torque = self.gravity_torque(theta)

        wrench = EntityWrench()
        wrench.entity.name = self.link_name
        wrench.entity.type = 3                  # TODO: try 2 and 3
        wrench.wrench.torque.y = torque
        self.publisher.publish(wrench)

    def get_angle(self, msg) -> float:
        """ This is only really relevant for boom joints. """
        if self.message_index is None:
            try:
                self.message_index = msg.name.index(self.joint_name)
            except ValueError:
                raise RuntimeError(
                    f"'{self.joint_name}' not found in /joint_states."
                    "Check that JointStatePublisher is attached and the bridge is configured."
                )
        return msg.position[self.message_index]
### GravityCompensator ###



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

        # Upper arm - Pitch
        upper_arm_node = Float64Publisher(
            name='arm_teleop',
            link_name='upper_arm',
            joint_name='upper_arm_joint',
            topic='arm/boom_cmd',
            key_bindings={'8':-0.5, '2':0.5, '5': 0.0 }  # Up, Down, Stop
        )
        upper_arm_node.set_margins(lower=-1.0, upper=1.0)
        upper_arm_node.start_gravity_compensator(link_mass=1.0, r_com=1.0)
        Nodes.append(upper_arm_node)

        # Chassis - Yaw
        chassis_node = Float64Publisher(
            name='chassis_teleop',
            link_name='chassis',
            joint_name='chassis_joint',
            topic='chassis/yaw_cmd',
            key_bindings={'4':0.5, '6':-0.5, '5':0.0 }  # Left, Right, Stop
        )
        Nodes.append(chassis_node)
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