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
    7 - Pitch ip
    5 - Stop
    1 - Pitch down

Chassis Controls:
    4 - Rotate left
    5 - Stop
    6 - Rotate right

Other Controls:
    q - quit
    Ctrl-C - quit

Publishes Float64MultiArray velocity commands for the chassis and
JointTrajectory position commands for the upper arm.
"""

import math
import select   # For non-blocked I/O
import sys      # For reading keyboard input
import time     # For waiting 0.01s during I/O
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
    """Command a joint toward an endpoint, optionally limiting its trajectory speed."""

    def __init__(
        self,
        name: str,
        joint_name: str,
        topic: str,
        key_bindings: dict,
        lower_limit: float,
        upper_limit: float,
        rad_per_sec: float,
    ):
        super().__init__(name)
        self.name = name
        self.publisher = self.create_publisher(JointTrajectory, topic, 10)
        self.joint_name = joint_name
        self.key_bindings = key_bindings
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        if lower_limit > upper_limit:
            raise ValueError("lower_limit must not exceed upper_limit")
        if not math.isfinite(rad_per_sec) or rad_per_sec <= 0.0:
            raise ValueError("rad_per_sec must be a finite positive value")
        self.rad_per_sec = rad_per_sec
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
            print(f"did NOT find in joint state callback. Here it is: \n---\n{message}\n---")

    def publish(self, direction):
        if not rclpy.ok():
            print("rclpy not ok")
            return
        if self.joint_position is None:
            print("Joint position is None")
            return

        trajectory = self.generate_trajectory(direction, self.joint_position)
        

        self.publisher.publish(trajectory)

    def generate_trajectory(self, direction, current_position=None):
        """ Generates a series of points for a JointTrajectory message based on the current joint position, 
        the direction of movement, and the limits of the joint. Each point will be spaced out in time 
        based on the rad_per_sec parameter, which defines how fast the joint should move, with a maximum of
        0.1 rads/second. """
        trajectory = JointTrajectory()

        if current_position is None:
            current_position = self.joint_position

        trajectory.joint_names = [self.joint_name]
        step_duration_sec = 0.1
        step_duration_ns = 100_000_000

        if direction == 0.0:
            point = JointTrajectoryPoint()
            point.positions = [current_position]
            point.velocities = [0.0]
            point.time_from_start.nanosec = step_duration_ns
            trajectory.points = [point]
        else:
            end_goal = self.upper_limit if direction > 0.0 else self.lower_limit
            end_goal = min(max(end_goal, self.lower_limit), self.upper_limit)
            distance = abs(end_goal - current_position)
            steps = max(
                1,
                math.ceil(distance / (self.rad_per_sec * step_duration_sec)),
            )

            for step in range(1, steps + 1):
                point = JointTrajectoryPoint()
                fraction = step / steps
                point.positions = [
                    current_position + (end_goal - current_position) * fraction
                ]
                elapsed_ns = step * step_duration_ns
                point.time_from_start.sec, point.time_from_start.nanosec = divmod(
                    elapsed_ns,
                    1_000_000_000,
                )
                trajectory.points.append(point)
        return trajectory

    def test_generate_trajectory(self):
        """Test the generate_trajectory method with various inputs."""
        test_cases = [
            ("No movement", 0.0, -0.2, 0.2, 0.1, 0.0),
            ("Move to upper limit", 0.5, -0.2, 0.2, 0.1, 0.0),
            ("Move to lower limit", -0.5, -0.2, 0.2, 0.1, 0.0),
            ("Exceed upper limit", 1.5, -0.2, 0.2, 0.1, 0.0),
            ("Exceed lower limit", -1.5, -0.2, 0.2, 0.1, 0.0),
            ("Move to upper limit from mid position", 0.5, -0.2, 0.2, 0.1, 0.1),
            ("Move to lower limit from mid position", -0.5, -0.2, 0.2, 0.1, -0.1),
            ("Already at upper limit", 0.5, -0.2, 0.2, 0.1, 0.2),
            ("Already at lower limit", -0.5, -0.2, 0.2, 0.1, -0.2),
            ("Start above upper limit", 0.5, -0.2, 0.2, 0.1, 0.25),
            ("Start below lower limit", -0.5, -0.2, 0.2, 0.1, -0.25),
        ]

        for name, direction, lower_limit, upper_limit, rad_per_sec, joint_position in test_cases:
            self.joint_position = joint_position
            self.lower_limit = lower_limit
            self.upper_limit = upper_limit
            self.rad_per_sec = rad_per_sec

            print(f"Test Case: {name}")
            trajectory = self.generate_trajectory(direction)
            print(f"Direction: {direction}, Trajectory Points: {len(trajectory.points)}")
            print(f"points: {[trajectory.points[i].positions[0] for i in range(len(trajectory.points))]}")
            print("\n" + "-" * 20)

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
            lower_limit=-0.2,
            upper_limit=0.2,
            rad_per_sec=0.2,
        )
        Nodes.append(upper_arm_node)
        # upper_arm_node.test_generate_trajectory()  # Run the test for trajectory generation

        # Lower arm - Position
        lower_arm_node = JointTrajectoryPublisher(
            name='lower_arm_teleop',
            joint_name='lower_arm_joint',
            topic='/lower_arm_controller/joint_trajectory',
            key_bindings={'7':-0.5, '1':0.5, '5': 0.0 },  # Up, Down, Stop
            lower_limit=-0.2,
            upper_limit=0.2,
            rad_per_sec=0.2,
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