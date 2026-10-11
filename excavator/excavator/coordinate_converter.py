"""Convert Gazebo local coordinates into geographic coordinates.

This module is ROS-independent so it can be unit tested on its own and reused
by the simulated GNSS node.

Coordinate convention for the local (Gazebo) frame:

* +X is east, in metres
* +Y is north, in metres
* +Z is up, in metres

The geographic origin (the coordinate corresponding to Gazebo ``(0, 0, 0)``)
is always supplied by the caller so that it can be loaded from configuration.

The conversion uses a local equirectangular (flat-Earth) approximation on a
spherical Earth, which is accurate to well under a metre for displacements of
a few kilometres around the origin.
"""

import math
from dataclasses import dataclass
from numbers import Real

# IUGG mean Earth radius in metres.
EARTH_RADIUS_M = 6_371_008.8

# Origins closer to a pole than this are rejected, since cos(latitude) tends to
# zero there and longitude offsets become unstable.
MAX_ORIGIN_ABS_LATITUDE_DEG = 89.0

# Quaternions shorter than this are treated as zero-length (no orientation).
_MIN_QUATERNION_NORM = 1e-9


@dataclass(frozen=True)
class GeographicCoordinate:
    """A geographic position in degrees and metres."""

    latitude: float
    longitude: float
    altitude: float


def _require_finite(name: str, value: object) -> float:
    """Return ``value`` as a float, raising ``ValueError`` if not finite numeric."""
    # bool is a subclass of int, but True/False are never valid coordinates.
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(
            f'{name} must be a finite number, got {type(value).__name__}: {value!r}'
        )
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f'{name} must be a finite number, got {result}')
    return result


def local_to_geographic(
    x: float,
    y: float,
    z: float,
    origin_latitude: float,
    origin_longitude: float,
    origin_altitude: float,
) -> GeographicCoordinate:
    """Convert a local ENU position to latitude, longitude and altitude.

    Args:
        x: Displacement east of the origin, in metres.
        y: Displacement north of the origin, in metres.
        z: Displacement above the origin, in metres.
        origin_latitude: Latitude of local ``(0, 0, 0)``, in degrees.
        origin_longitude: Longitude of local ``(0, 0, 0)``, in degrees.
        origin_altitude: Altitude of local ``(0, 0, 0)``, in metres.

    Returns:
        The geographic coordinate of the local position. Longitude is wrapped
        into ``[-180, 180]``.

    Raises:
        ValueError: If any input is non-numeric or not finite, the origin is
            outside valid latitude/longitude ranges, the origin is within
            ``90 - MAX_ORIGIN_ABS_LATITUDE_DEG`` degrees of a pole, or the
            resulting latitude would pass a pole.
    """
    x = _require_finite('x', x)
    y = _require_finite('y', y)
    z = _require_finite('z', z)
    origin_latitude = _require_finite('origin_latitude', origin_latitude)
    origin_longitude = _require_finite('origin_longitude', origin_longitude)
    origin_altitude = _require_finite('origin_altitude', origin_altitude)

    if not -90.0 <= origin_latitude <= 90.0:
        raise ValueError(
            f'origin_latitude must be between -90 and 90 degrees, got {origin_latitude}'
        )
    if not -180.0 <= origin_longitude <= 180.0:
        raise ValueError(
            f'origin_longitude must be between -180 and 180 degrees, '
            f'got {origin_longitude}'
        )
    if abs(origin_latitude) > MAX_ORIGIN_ABS_LATITUDE_DEG:
        raise ValueError(
            f'origin_latitude {origin_latitude} is too close to a pole; '
            f'|latitude| must not exceed {MAX_ORIGIN_ABS_LATITUDE_DEG} degrees'
        )

    origin_latitude_rad = math.radians(origin_latitude)

    latitude = origin_latitude + math.degrees(y / EARTH_RADIUS_M)
    longitude = origin_longitude + math.degrees(
        x / (EARTH_RADIUS_M * math.cos(origin_latitude_rad))
    )
    altitude = origin_altitude + z

    if not -90.0 <= latitude <= 90.0:
        raise ValueError(
            f'y = {y} m moves the position past a pole (latitude {latitude})'
        )
    if not -180.0 <= longitude <= 180.0:
        longitude = (longitude + 180.0) % 360.0 - 180.0

    return GeographicCoordinate(latitude, longitude, altitude)


def quaternion_to_heading_degrees(x: float, y: float, z: float, w: float) -> float:
    """Convert an ENU orientation quaternion to a compass heading.

    ROS yaw is measured anticlockwise from east (+X). Compass heading is
    measured clockwise from north, so ``heading = (90 - yaw) % 360``:
    north = 0, east = 90, south = 180, west = 270.

    Non-unit quaternions are normalised before use.

    Returns:
        Heading in degrees, in the range ``[0, 360)``.

    Raises:
        ValueError: If any component is non-numeric or not finite, or the
            quaternion has (near) zero length.
    """
    x = _require_finite('quaternion x', x)
    y = _require_finite('quaternion y', y)
    z = _require_finite('quaternion z', z)
    w = _require_finite('quaternion w', w)

    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm < _MIN_QUATERNION_NORM:
        raise ValueError(f'quaternion has near-zero length ({norm}); cannot compute heading')
    x, y, z, w = x / norm, y / norm, z / norm, w / norm

    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    heading = (90.0 - math.degrees(yaw)) % 360.0
    # Float modulo of a tiny negative number can round up to exactly 360.
    return 0.0 if heading >= 360.0 else heading
