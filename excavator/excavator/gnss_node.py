from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import Float64

from excavator.coordinates import CoordinateConverter
from excavator.orientation import quaternion_to_heading


class GnssNode(Node):
    def __init__(self) -> None:
        super().__init__("gnss_node")

        self.declare_parameter("origin_latitude", 48.08028)
        self.declare_parameter("origin_longitude", 11.63806)
        self.declare_parameter("origin_altitude", 553.0)
        self.declare_parameter("origin_x", 0.0)
        self.declare_parameter("origin_y", 0.0)
        self.declare_parameter("angle_degrees", 0.0)
        self.declare_parameter("frame_id", "")

        self.origin_latitude = self.get_parameter("origin_latitude").value
        self.origin_longitude = self.get_parameter("origin_longitude").value
        self.origin_altitude = self.get_parameter("origin_altitude").value
        self.frame_id = self.get_parameter("frame_id").value

        self.converter = CoordinateConverter(
            origin_x=self.get_parameter("origin_x").value,
            origin_y=self.get_parameter("origin_y").value,
            angle_degrees=self.get_parameter("angle_degrees").value,
        )

        self.fix_publisher = self.create_publisher(NavSatFix, "/fix", 10)
        self.pose_publisher = self.create_publisher(
            PoseStamped,
            "/gnss/pose",
            10,
        )
        self.heading_publisher = self.create_publisher(
            Float64,
            "/gnss/heading",
            10,
        )
        self.odom_subscription = self.create_subscription(
            Odometry,
            "/odom",
            self.odom_callback,
            10,
        )

    def odom_callback(self, odometry: Odometry) -> None:
        position = odometry.pose.pose.position
        orientation = odometry.pose.pose.orientation

        try:
            geographic = self.converter.world_to_geographic(
                x=position.x,
                y=position.y,
                z=position.z,
                origin_latitude=self.origin_latitude,
                origin_longitude=self.origin_longitude,
                origin_altitude=self.origin_altitude,
            )
            heading = quaternion_to_heading(
                x=orientation.x,
                y=orientation.y,
                z=orientation.z,
                w=orientation.w,
            )
        except (TypeError, ValueError, OverflowError) as error:
            self.get_logger().warning(
                f"Ignoring invalid odometry sample: {error}",
                throttle_duration_sec=5.0,
            )
            return

        fix = NavSatFix()
        fix.header.stamp = odometry.header.stamp
        fix.header.frame_id = (
            self.frame_id
            or odometry.child_frame_id
            or odometry.header.frame_id
        )
        fix.status.status = NavSatStatus.STATUS_FIX
        fix.status.service = NavSatStatus.SERVICE_GPS
        fix.latitude = geographic.latitude
        fix.longitude = geographic.longitude
        fix.altitude = geographic.altitude
        fix.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN

        pose = PoseStamped()
        pose.header.stamp = odometry.header.stamp
        pose.header.frame_id = odometry.header.frame_id
        pose.pose.position.x = position.x
        pose.pose.position.y = position.y
        pose.pose.position.z = position.z
        pose.pose.orientation = orientation

        heading_message = Float64()
        heading_message.data = heading

        self.fix_publisher.publish(fix)
        self.pose_publisher.publish(pose)
        self.heading_publisher.publish(heading_message)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = GnssNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
