import math

import pytest

from excavator.coordinate_converter import (
    EARTH_RADIUS_M,
    GeographicCoordinate,
    local_to_geographic,
)

# Representative GOOSE dataset location (Neubiberg, Germany). Defined here for
# the tests only; the converter itself takes the origin as arguments.
NEUBIBERG = {
    'origin_latitude': 48.08028,
    'origin_longitude': 11.63806,
    'origin_altitude': 553.0,
}


def convert(x, y, z, **origin):
    return local_to_geographic(x, y, z, **{**NEUBIBERG, **origin})


def haversine_m(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def test_origin_maps_to_neubiberg():
    result = convert(0.0, 0.0, 0.0)
    assert result == GeographicCoordinate(48.08028, 11.63806, 553.0)


def test_positive_x_increases_longitude():
    result = convert(5.0, 0.0, 0.0)
    assert result.longitude > NEUBIBERG['origin_longitude']
    assert result.latitude == pytest.approx(NEUBIBERG['origin_latitude'])


def test_negative_x_decreases_longitude():
    result = convert(-5.0, 0.0, 0.0)
    assert result.longitude < NEUBIBERG['origin_longitude']
    assert result.latitude == pytest.approx(NEUBIBERG['origin_latitude'])


def test_positive_y_increases_latitude():
    result = convert(0.0, 5.0, 0.0)
    assert result.latitude > NEUBIBERG['origin_latitude']
    assert result.longitude == pytest.approx(NEUBIBERG['origin_longitude'])


def test_negative_y_decreases_latitude():
    result = convert(0.0, -5.0, 0.0)
    assert result.latitude < NEUBIBERG['origin_latitude']
    assert result.longitude == pytest.approx(NEUBIBERG['origin_longitude'])


def test_positive_z_increases_altitude():
    result = convert(0.0, 0.0, 2.5)
    assert result.altitude == pytest.approx(555.5)
    assert result.latitude == NEUBIBERG['origin_latitude']
    assert result.longitude == NEUBIBERG['origin_longitude']


def test_ten_metres_east_and_north():
    result = convert(10.0, 10.0, 0.0)

    # ~1.11e5 m per degree of latitude; ~7.43e4 m per degree of longitude at 48.08 N.
    assert result.latitude == pytest.approx(48.08028 + 8.9932e-5, abs=1e-8)
    assert result.longitude == pytest.approx(11.63806 + 1.346109e-4, abs=1e-8)

    # Independent check: great-circle distance should be ~sqrt(200) m.
    distance = haversine_m(
        NEUBIBERG['origin_latitude'], NEUBIBERG['origin_longitude'],
        result.latitude, result.longitude,
    )
    assert distance == pytest.approx(math.sqrt(200.0), abs=1e-3)


@pytest.mark.parametrize('latitude', [-90.1, 90.1, 180.0, -1000.0])
def test_invalid_latitude_rejected(latitude):
    with pytest.raises(ValueError, match='origin_latitude'):
        convert(0.0, 0.0, 0.0, origin_latitude=latitude)


@pytest.mark.parametrize('longitude', [-180.1, 180.1, 360.0])
def test_invalid_longitude_rejected(longitude):
    with pytest.raises(ValueError, match='origin_longitude'):
        convert(0.0, 0.0, 0.0, origin_longitude=longitude)


@pytest.mark.parametrize('bad', [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize(
    'field', ['x', 'y', 'z', 'origin_latitude', 'origin_longitude', 'origin_altitude']
)
def test_non_finite_values_rejected(field, bad):
    kwargs = {'x': 0.0, 'y': 0.0, 'z': 0.0, **NEUBIBERG, field: bad}
    with pytest.raises(ValueError, match=field):
        local_to_geographic(**kwargs)


@pytest.mark.parametrize('bad', ['1.0', None, True, [1.0]])
def test_non_numeric_values_rejected(bad):
    with pytest.raises(ValueError, match='x'):
        convert(bad, 0.0, 0.0)


@pytest.mark.parametrize('latitude', [90.0, -90.0, 89.5, -89.999])
def test_origin_near_pole_rejected(latitude):
    with pytest.raises(ValueError, match='pole'):
        convert(1.0, 0.0, 0.0, origin_latitude=latitude)


def test_origin_at_pole_limit_is_finite():
    result = convert(1.0, 0.0, 0.0, origin_latitude=89.0)
    assert math.isfinite(result.longitude)


def test_displacement_past_pole_rejected():
    with pytest.raises(ValueError, match='pole'):
        convert(0.0, 2.0e5, 0.0, origin_latitude=89.0)


def test_longitude_wraps_at_antimeridian():
    result = convert(1000.0, 0.0, 0.0, origin_latitude=0.0, origin_longitude=180.0)
    assert -180.0 <= result.longitude < -179.99


def test_inputs_not_mutated():
    position = [10.0, -20.0, 3.0]
    origin = dict(NEUBIBERG)
    position_before = list(position)
    origin_before = dict(origin)

    local_to_geographic(*position, **origin)

    assert position == position_before
    assert origin == origin_before


def test_integer_inputs_accepted():
    result = local_to_geographic(0, 0, 0, 48, 11, 553)
    assert result == GeographicCoordinate(48.0, 11.0, 553.0)
