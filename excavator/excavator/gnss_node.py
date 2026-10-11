"""Simulated GNSS receiver.

Subscribes to odometry and republishes the local position as a geographic fix,
using the configurable origin that corresponds to local ``(0, 0, 0)``.

Subscribes:
    /odom (nav_msgs/msg/Odometry)

Publishes:
    /fix (sensor_msgs/msg/NavSatFix)
    /gnss/pose (geometry_msgs/msg/PoseStamped)
    /gnss/heading (std_msgs/msg/Float64), compass degrees in [0, 360)

This is a perfect GNSS model: the reported covariance is zero, meaning no
modelled uncertainty. It does not represent the accuracy of a real receiver.

Simulation time is controlled by the standard ``use_sim_time`` parameter,
e.g. ``ros2 run excavator gnss_node --ros-args -p use_sim_time:=true``.
Published stamps are copied from the incoming odometry either way.
"""

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Float64

from excavator.coordinate_converter import (
    local_to_geographic,
    quaternion_to_heading_degrees,
)

# Minimum interval between repeated warnings about bad odometry.
WARN_THROTTLE_SEC = 5.0

# Zero covariance: the simulated fix has no modelled error.
ZERO_COVARIANCE = [0.0] * 9


class GnssNode(Node):
    """Converts odometry into NavSatFix, ENU pose and compass heading."""

    def __init__(self) -> None:
        super().__init__('gnss_node')

        self.declare_parameter('origin_latitude', 48.08028)
        self.declare_parameter('origin_longitude', 11.63806)
        self.declare_parameter('origin_altitude', 553.0)
        self.declare_parameter('input_topic', '/odom')
        self.declare_parameter('fix_topic', '/fix')
        self.declare_parameter('pose_topic', '/gnss/pose')
        self.declare_parameter('heading_topic', '/gnss/heading')
        self.declare_parameter('gnss_frame_id', 'gnss_link')
        self.declare_parameter('enu_frame_id', 'gnss_enu')
        self.declare_parameter('publish_heading', True)

        self._origin_latitude = self._float_param('origin_latitude')
        self._origin_longitude = self._float_param('origin_longitude')
        self._origin_altitude = self._float_param('origin_altitude')
        self._gnss_frame_id = self._str_param('gnss_frame_id')
        self._enu_frame_id = self._str_param('enu_frame_id')
        self._publish_heading = self._bool_param('publish_heading')

        # Fail fast on an invalid origin rather than on the first message.
        local_to_geographic(
            0.0, 0.0, 0.0,
            self._origin_latitude, self._origin_longitude, self._origin_altitude,
        )

        input_topic = self._str_param('input_topic')
        fix_topic = self._str_param('fix_topic')
        pose_topic = self._str_param('pose_topic')
        heading_topic = self._str_param('heading_topic')

        self._fix_pub = self.create_publisher(NavSatFix, fix_topic, 10)
        self._pose_pub = self.create_publisher(PoseStamped, pose_topic, 10)
        self._heading_pub = (
            self.create_publisher(Float64, heading_topic, 10)
            if self._publish_heading else None
        )
        self.create_subscription(Odometry, input_topic, self._on_odometry, 10)

        self._received_first_fix = False
        self.get_logger().info(
            f'GNSS origin lat={self._origin_latitude}, lon={self._origin_longitude}, '
            f'alt={self._origin_altitude}; waiting for odometry on {input_topic}'
        )

    def _float_param(self, name: str) -> float:
        value = self.get_parameter(name).value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'parameter {name} must be a number, got {value!r}')
        return float(value)

    def _str_param(self, name: str) -> str:
        value = self.get_parameter(name).value
        if not isinstance(value, str) or not value:
            raise ValueError(f'parameter {name} must be a non-empty string, got {value!r}')
        return value

    def _bool_param(self, name: str) -> bool:
        value = self.get_parameter(name).value
        if not isinstance(value, bool):
            raise ValueError(f'parameter {name} must be a boolean, got {value!r}')
        return value

    def _on_odometry(self, message: Odometry) -> None:
        position = message.pose.pose.position
        orientation = message.pose.pose.orientation

        try:
            coordinate = local_to_geographic(
                position.x, position.y, position.z,
                self._origin_latitude, self._origin_longitude, self._origin_altitude,
            )
        except ValueError as error:
            self.get_logger().warning(
                f'Ignoring odometry with invalid position: {error}',
                throttle_duration_sec=WARN_THROTTLE_SEC,
            )
            return

        if not self._received_first_fix:
            self._received_first_fix = True
            self.get_logger().info('Received first valid odometry; publishing GNSS')

        fix = NavSatFix()
        fix.header.stamp = message.header.stamp
        fix.header.frame_id = self._gnss_frame_id
        fix.status.status = NavSatStatus.STATUS_FIX
        fix.status.service = NavSatStatus.SERVICE_GPS
        fix.latitude = coordinate.latitude
        fix.longitude = coordinate.longitude
        fix.altitude = coordinate.altitude
        fix.position_covariance = ZERO_COVARIANCE
        fix.position_covariance_type = NavSatFix.COVARIANCE_TYPE_KNOWN
        self._fix_pub.publish(fix)

        # Orientation is needed for both pose and heading, so a bad quaternion
        # suppresses both while the position fix above is still published.
        try:
            heading = quaternion_to_heading_degrees(
                orientation.x, orientation.y, orientation.z, orientation.w
            )
        except ValueError as error:
            self.get_logger().warning(
                f'Ignoring odometry orientation: {error}',
                throttle_duration_sec=WARN_THROTTLE_SEC,
            )
            return

        pose = PoseStamped()
        pose.header.stamp = message.header.stamp
        pose.header.frame_id = self._enu_frame_id
        pose.pose.position = position
        pose.pose.orientation = orientation
        self._pose_pub.publish(pose)

        if self._heading_pub is not None:
            self._heading_pub.publish(Float64(data=heading))


def main(args=None) -> None:
    """Run the GNSS node until shutdown."""
    rclpy.init(args=args)
    node = None
    try:
        node = GnssNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
