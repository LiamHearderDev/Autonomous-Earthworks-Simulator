import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float64


HELP = """
Bulldozer keyboard controls
---------------------------
W / S       drive forward / backward
A / D       turn left / right
Space or X  stop
R / F       raise / lower blade
Q           quit

Hold a movement key to keep driving.
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
    main()
