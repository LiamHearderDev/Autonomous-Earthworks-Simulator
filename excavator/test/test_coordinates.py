import pytest

from excavator.coordinates import CoordinateConverter

ORIGIN_LATITUDE = 48.08028
ORIGIN_LONGITUDE = 11.63806
ORIGIN_ALTITUDE = 553.0

def test_local_world_round_trip():
    converter = CoordinateConverter(
        origin_x=4.0,
        origin_y=-3.0,
        angle_degrees=30.0,
    )

    world = converter.local_to_world(10.0, 20.0)
    local = converter.world_to_local(world.x, world.y)

    assert local.x == pytest.approx(10.0)
    assert local.y == pytest.approx(20.0)

def test_world_origin_returns_neubiberg_origin():
    converter = CoordinateConverter()

    result = converter.world_to_geographic(
        x=0.0,
        y=0.0,
        z=0.0,
        origin_latitude=ORIGIN_LATITUDE,
        origin_longitude=ORIGIN_LONGITUDE,
        origin_altitude=ORIGIN_ALTITUDE,
    )

    assert result.latitude == pytest.approx(ORIGIN_LATITUDE)
    assert result.longitude == pytest.approx(ORIGIN_LONGITUDE)
    assert result.altitude == pytest.approx(ORIGIN_ALTITUDE)


def test_eastward_movement_increases_longitude():
    converter = CoordinateConverter()

    result = converter.world_to_geographic(
        x=10.0,
        y=0.0,
        z=0.0,
        origin_latitude=ORIGIN_LATITUDE,
        origin_longitude=ORIGIN_LONGITUDE,
        origin_altitude=ORIGIN_ALTITUDE,
    )

    assert result.latitude == pytest.approx(ORIGIN_LATITUDE)
    assert result.longitude > ORIGIN_LONGITUDE


def test_northward_movement_increases_latitude():
    converter = CoordinateConverter()

    result = converter.world_to_geographic(
        x=0.0,
        y=10.0,
        z=0.0,
        origin_latitude=ORIGIN_LATITUDE,
        origin_longitude=ORIGIN_LONGITUDE,
        origin_altitude=ORIGIN_ALTITUDE,
    )

    assert result.latitude > ORIGIN_LATITUDE
    assert result.longitude == pytest.approx(ORIGIN_LONGITUDE)


def test_upward_movement_increases_altitude():
    converter = CoordinateConverter()

    result = converter.world_to_geographic(
        x=0.0,
        y=0.0,
        z=5.0,
        origin_latitude=ORIGIN_LATITUDE,
        origin_longitude=ORIGIN_LONGITUDE,
        origin_altitude=ORIGIN_ALTITUDE,
    )

    assert result.altitude == pytest.approx(558.0)