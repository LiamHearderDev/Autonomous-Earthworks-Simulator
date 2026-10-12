from math import cos, radians, sin

import pytest

from excavator.orientation import quaternion_to_heading


def yaw_quaternion(yaw_degrees: float) -> tuple[float, float, float, float]:
    half_yaw = radians(yaw_degrees) / 2.0

    return (
        0.0,
        0.0,
        sin(half_yaw),
        cos(half_yaw),
    )


@pytest.mark.parametrize(
    ("yaw", "expected_heading"),
    [
        (90.0, 0.0),
        (0.0, 90.0),
        (-90.0, 180.0),
        (180.0, 270.0),
    ],
)
def test_quaternion_to_heading(yaw, expected_heading):
    quaternion = yaw_quaternion(yaw)

    heading = quaternion_to_heading(*quaternion)

    assert heading == pytest.approx(expected_heading)


def test_non_unit_quaternion_is_normalized():
    heading = quaternion_to_heading(
        x=0.0,
        y=0.0,
        z=2.0,
        w=2.0,
    )

    assert heading == pytest.approx(0.0)


def test_zero_quaternion_is_rejected():
    with pytest.raises(ValueError):
        quaternion_to_heading(0.0, 0.0, 0.0, 0.0)
