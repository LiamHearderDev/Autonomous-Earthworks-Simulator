import select
import sys
import termios
import time
import tty

import rclpy    # Python library for ROS 2
from rclpy.node import Node as RosNode

from std_msgs.msg import Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from geometry_msgs.msg import Twist

from sensor_msgs.msg import JointState  # For receiving data from the Joints

HELP = """
Keyboard teleop for the bulldozer.

Movement Controls:
    W - Forward
    A - Left
    S - Back
    D - Right
    X - Stop
    
Blade Controls:
    6 - Raise blade
    5 - Stop
    4 - Lower blade

Other Controls:
    Q - quit
    Ctrl-C - quit

Hold a movement key to keep driving.
"""
class JointTrajectoryPublisher(RosNode):
    """Command a joint toward an endpoint until a new target is sent."""

    def __init__(self, name: str, joint_name: str, topic: str, key_bindings: dict):
        super().__init__(name)
        self.publisher = self.create_publisher(JointTrajectory, topic, 10)
        self.joint_name = joint_name
        self.key_bindings = key_bindings
        self.lower_limit = -0.30
        self.upper_limit = 0.30
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

        # Blade - Position
        blade_node = JointTrajectoryPublisher(
            name='blade_teleop',
            joint_name='blade_joint',
            topic='/arm_controller/joint_trajectory',
            key_bindings={'6':-0.1, '4':0.1, '5': 0.0 }  # Up, Down, Stop
        )
        Nodes.append(blade_node)


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
    print(HELP)

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

"""
class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__("keyboard_teleop")

        self.declare_parameter("linear_speed", 1.5)
        self.declare_parameter("angular_speed", 0.8)
        self.declare_parameter("command_timeout", 0.5)
        self.declare_parameter("blade_step", 0.05)
        self.declare_parameter("blade_min", -0.3)
        self.declare_parameter("blade_max", 0.3)

        self.linear_speed = float(self.get_parameter("linear_speed").value)
        self.angular_speed = float(self.get_parameter("angular_speed").value)
        self.command_timeout = float(self.get_parameter("command_timeout").value)
        self.blade_step = float(self.get_parameter("blade_step").value)
        self.blade_min = float(self.get_parameter("blade_min").value)
        self.blade_max = float(self.get_parameter("blade_max").value)

        self.velocity_publisher = self.create_publisher(Twist, "cmd_vel", 10)
        self.blade_publisher = self.create_publisher(
            Float64, "/bulldozer/blade/cmd_pos", 10
        )

        self.velocity = Twist()
        self.blade_position = 0.0
        self.last_motion_key = time.monotonic()

    def handle_key(self, key):
        key = key.lower()
        motion_command = True

        if key == "w":
            self.set_velocity(self.linear_speed, 0.0)
        elif key == "s":
            self.set_velocity(-self.linear_speed, 0.0)
        elif key == "a":
            self.set_velocity(0.0, self.angular_speed)
        elif key == "d":
            self.set_velocity(0.0, -self.angular_speed)
        elif key in (" ", "x"):
            self.set_velocity(0.0, 0.0)
        elif key == "r":
            motion_command = False
            self.move_blade(self.blade_step)
        elif key == "f":
            motion_command = False
            self.move_blade(-self.blade_step)
        else:
            return

        if motion_command:
            self.last_motion_key = time.monotonic()

    def set_velocity(self, linear, angular):
        self.velocity.linear.x = linear
        self.velocity.angular.z = angular
        self.velocity_publisher.publish(self.velocity)

    def move_blade(self, change):
        self.blade_position = min(
            self.blade_max,
            max(self.blade_min, self.blade_position + change),
        )
        message = Float64()
        message.data = self.blade_position
        self.blade_publisher.publish(message)
        print(f"\rBlade position: {self.blade_position:+.2f} m", end="", flush=True)

    def publish_periodic_velocity(self):
        moving = self.velocity.linear.x != 0.0 or self.velocity.angular.z != 0.0
        if moving and time.monotonic() - self.last_motion_key > self.command_timeout:
            self.set_velocity(0.0, 0.0)
        else:
            self.velocity_publisher.publish(self.velocity)

    def stop(self):
        self.set_velocity(0.0, 0.0)


def read_key(timeout=0.05):
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    return sys.stdin.read(1) if ready else ""


def main(args=None):
    if not sys.stdin.isatty():
        print("Keyboard teleop must be run from an interactive terminal.")
        return

    rclpy.init(args=args)
    node = KeyboardTeleop()
    terminal_settings = termios.tcgetattr(sys.stdin)

    print(HELP)
    tty.setraw(sys.stdin.fileno())

    try:
        while rclpy.ok():
            key = read_key()
            if key.lower() == "q" or key == "\x03":
                break
            if key:
                node.handle_key(key)
            node.publish_periodic_velocity()
            rclpy.spin_once(node, timeout_sec=0.0)
    finally:
        node.stop()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, terminal_settings)
        print("\nBulldozer stopped.")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()"""
