import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from excavator.coordinates import CoordinateConverter


class PoseStamped:
    def __init__(self):
        self.header = SimpleNamespace(stamp=None, frame_id="")
        self.pose = SimpleNamespace(position=SimpleNamespace(), orientation=None)


class NavSatFix:
    COVARIANCE_TYPE_UNKNOWN = 0

    def __init__(self):
        self.header = SimpleNamespace(stamp=None, frame_id="")
        self.status = SimpleNamespace()


@pytest.fixture
def node(monkeypatch):
    modules = {
        "geometry_msgs.msg": {"PoseStamped": PoseStamped},
        "nav_msgs.msg": {"Odometry": SimpleNamespace},
        "rclpy": {},
        "rclpy.node": {"Node": object},
        "sensor_msgs.msg": {
            "NavSatFix": NavSatFix,
            "NavSatStatus": SimpleNamespace(STATUS_FIX=0, SERVICE_GPS=1),
        },
        "std_msgs.msg": {"Float64": SimpleNamespace},
    }
    for name, attributes in modules.items():
        module = ModuleType(name)
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, module)

    path = Path(__file__).parents[1] / "excavator" / "gnss_node.py"
    spec = importlib.util.spec_from_file_location("gnss_node_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instance = module.GnssNode.__new__(module.GnssNode)
    instance.converter = CoordinateConverter()
    instance.origin_latitude = 48.08028
    instance.origin_longitude = 11.63806
    instance.origin_altitude = 553.0
    instance.frame_id = ""
    instance.fix_publisher = Mock()
    instance.pose_publisher = Mock()
    instance.heading_publisher = Mock()
    instance.get_logger = Mock(return_value=Mock())
    return instance


@pytest.fixture
def odometry():
    return SimpleNamespace(
        header=SimpleNamespace(
            stamp=SimpleNamespace(sec=42, nanosec=123456789), frame_id="odom"
        ),
        child_frame_id="excavator/root",
        pose=SimpleNamespace(pose=SimpleNamespace(
            position=SimpleNamespace(x=0.0, y=0.0, z=5.0),
            orientation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
        )),
    )


def test_publishes_origin_pose_heading_and_timestamp(node, odometry):
    node.odom_callback(odometry)

    node.fix_publisher.publish.assert_called_once()
    node.pose_publisher.publish.assert_called_once()
    node.heading_publisher.publish.assert_called_once()
    fix = node.fix_publisher.publish.call_args.args[0]
    pose = node.pose_publisher.publish.call_args.args[0]
    heading = node.heading_publisher.publish.call_args.args[0]

    assert fix.latitude == pytest.approx(48.08028)
    assert fix.longitude == pytest.approx(11.63806)
    assert fix.altitude == pytest.approx(558.0)
    assert fix.status.status == 0
    assert fix.status.service == 1
    assert fix.position_covariance_type == 0
    assert fix.header.stamp == odometry.header.stamp
    assert pose.header.stamp == odometry.header.stamp
    assert fix.header.frame_id == "excavator/root"
    assert pose.header.frame_id == "odom"
    assert vars(pose.pose.position) == vars(odometry.pose.pose.position)
    assert pose.pose.orientation == odometry.pose.pose.orientation
    assert heading.data == pytest.approx(90.0)


@pytest.mark.parametrize("frame,child,expected", [
    ("antenna", "excavator/root", "antenna"),
    ("", "excavator/root", "excavator/root"),
    ("", "", "odom"),
])
def test_fix_frame_selection(node, odometry, frame, child, expected):
    node.frame_id = frame
    odometry.child_frame_id = child
    node.odom_callback(odometry)
    assert node.fix_publisher.publish.call_args.args[0].header.frame_id == expected
    assert node.pose_publisher.publish.call_args.args[0].header.frame_id == "odom"


@pytest.mark.parametrize("part,field,value", [
    ("position", axis, value)
    for axis in ("x", "y", "z")
    for value in (float("nan"), float("inf"), -float("inf"))
] + [
    ("orientation", axis, value)
    for axis in ("x", "y", "z", "w")
    for value in (float("nan"), float("inf"), -float("inf"))
] + [("orientation", "w", 0.0)])
def test_invalid_sample_is_dropped_and_next_valid_sample_publishes(
    node, odometry, part, field, value
):
    component = getattr(odometry.pose.pose, part)
    original = getattr(component, field)
    setattr(component, field, value)
    node.odom_callback(odometry)

    for publisher in (node.fix_publisher, node.pose_publisher, node.heading_publisher):
        publisher.publish.assert_not_called()
    node.get_logger.return_value.warning.assert_called_once()
    assert node.get_logger.return_value.warning.call_args.kwargs == {
        "throttle_duration_sec": 5.0
    }

    setattr(component, field, original)
    node.odom_callback(odometry)
    for publisher in (node.fix_publisher, node.pose_publisher, node.heading_publisher):
        publisher.publish.assert_called_once()
