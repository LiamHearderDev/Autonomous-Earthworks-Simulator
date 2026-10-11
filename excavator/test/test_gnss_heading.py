import math

import pytest

from excavator.coordinate_converter import quaternion_to_heading_degrees


def yaw_quaternion(yaw_degrees, scale=1.0):
    """Quaternion (x, y, z, w) for a pure rotation about +Z."""
    half = math.radians(yaw_degrees) / 2.0
    return (0.0, 0.0, scale * math.sin(half), scale * math.cos(half))


def heading_for_yaw(yaw_degrees, scale=1.0):
    return quaternion_to_heading_degrees(*yaw_quaternion(yaw_degrees, scale))


def test_yaw_90_is_north():
    assert heading_for_yaw(90.0) == pytest.approx(0.0, abs=1e-9)


def test_yaw_0_is_east():
    assert heading_for_yaw(0.0) == pytest.approx(90.0)


def test_yaw_minus_90_is_south():
    assert heading_for_yaw(-90.0) == pytest.approx(180.0)


def test_yaw_180_is_west():
    assert heading_for_yaw(180.0) == pytest.approx(270.0)


def test_identity_quaternion_is_east():
    assert quaternion_to_heading_degrees(0.0, 0.0, 0.0, 1.0) == 90.0


@pytest.mark.parametrize('yaw', [step * 7.5 for step in range(-96, 97)] + [0.1, -0.1, 89.999999])
def test_heading_in_range(yaw):
    heading = heading_for_yaw(yaw)
    assert 0.0 <= heading < 360.0
    # Compare on the circle so 0 and 359.999... count as equal.
    error = (heading - (90.0 - yaw) + 180.0) % 360.0 - 180.0
    assert error == pytest.approx(0.0, abs=1e-6)


def test_tiny_rounding_never_returns_360():
    # Yaw just above 90 degrees gives (90 - yaw) slightly negative.
    assert 0.0 <= heading_for_yaw(90.0 + 1e-13) < 360.0


@pytest.mark.parametrize('scale', [0.001, 0.5, 2.0, 1000.0])
def test_non_unit_quaternion_is_normalised(scale):
    assert heading_for_yaw(30.0, scale) == pytest.approx(heading_for_yaw(30.0))
    assert heading_for_yaw(30.0, scale) == pytest.approx(60.0)


def test_negated_quaternion_gives_same_heading():
    x, y, z, w = yaw_quaternion(-45.0)
    assert quaternion_to_heading_degrees(-x, -y, -z, -w) == pytest.approx(135.0)


@pytest.mark.parametrize('quaternion', [(0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1e-12, 0.0)])
def test_zero_length_quaternion_rejected(quaternion):
    with pytest.raises(ValueError, match='zero length'):
        quaternion_to_heading_degrees(*quaternion)


@pytest.mark.parametrize('bad', [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize('index', range(4))
def test_non_finite_components_rejected(index, bad):
    quaternion = [0.0, 0.0, 0.0, 1.0]
    quaternion[index] = bad
    with pytest.raises(ValueError, match='finite'):
        quaternion_to_heading_degrees(*quaternion)


def test_non_numeric_component_rejected():
    with pytest.raises(ValueError, match='finite'):
        quaternion_to_heading_degrees(0.0, 0.0, '0', 1.0)
