import pytest

from excavator.coordinates import CoordinateConverter


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