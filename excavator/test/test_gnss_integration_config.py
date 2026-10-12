from pathlib import Path
from xml.etree import ElementTree

import yaml


PACKAGE_ROOT = Path(__file__).parents[1]


def test_bridge_subscribes_to_diff_drive_odometry():
    robot = ElementTree.parse(PACKAGE_ROOT / "urdf" / "excavator.urdf.xacro")
    drive = robot.find(".//plugin[@name='gz::sim::systems::DiffDrive']")
    bridges = yaml.safe_load(
        (PACKAGE_ROOT / "config" / "excavator_bridge.yaml").read_text()
    )
    odometry = next(
        bridge for bridge in bridges if bridge["ros_topic_name"] == "/odom"
    )

    assert odometry["gz_topic_name"] == drive.findtext("odom_topic")
    assert odometry["ros_type_name"] == "nav_msgs/msg/Odometry"
    assert odometry["gz_type_name"] == "gz.msgs.Odometry"
    assert odometry["direction"] == "GZ_TO_ROS"
    assert float(drive.findtext("odom_publish_frequency")) >= 10.0
