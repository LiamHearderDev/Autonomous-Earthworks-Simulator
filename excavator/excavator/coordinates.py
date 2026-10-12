"""Conversions between simulator, local and geographic coordinates."""

from dataclasses import dataclass
from math import cos, degrees, isfinite, radians, sin


EARTH_RADIUS_METRES = 6_378_137.0


@dataclass(frozen=True)
class Coordinate:
    x: float
    y: float


@dataclass(frozen=True)
class GeographicCoordinate:
    latitude: float
    longitude: float
    altitude: float


class CoordinateConverter:
    """Convert simulator coordinates into a local ENU frame and GNSS position."""

    def __init__(
        self,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
        angle_degrees: float = 0.0,
    ):
        values = (origin_x, origin_y, angle_degrees)

        if not all(isfinite(value) for value in values):
            raise ValueError("Coordinate-converter values must be finite")

        self.origin_x = origin_x
        self.origin_y = origin_y
        self.angle = radians(angle_degrees)

    def local_to_world(self, x: float, y: float) -> Coordinate:
        """Convert a point in the local frame to the simulator world frame."""
        world_x = self.origin_x + x * cos(self.angle) - y * sin(self.angle)
        world_y = self.origin_y + x * sin(self.angle) + y * cos(self.angle)
        return Coordinate(world_x, world_y)

    def world_to_local(self, x: float, y: float) -> Coordinate:
        """Convert a simulator world point into the local ENU frame."""
        translated_x = x - self.origin_x
        translated_y = y - self.origin_y

        local_x = (
            translated_x * cos(self.angle)
            + translated_y * sin(self.angle)
        )

        local_y = (
            -translated_x * sin(self.angle)
            + translated_y * cos(self.angle)
        )

        return Coordinate(local_x, local_y)

    def world_to_geographic(
        self,
        x: float,
        y: float,
        z: float,
        origin_latitude: float,
        origin_longitude: float,
        origin_altitude: float,
    ) -> GeographicCoordinate:
        """Convert a simulator world position to a geographic coordinate."""

        values = (
            x,
            y,
            z,
            origin_latitude,
            origin_longitude,
            origin_altitude,
        )

        if not all(isfinite(value) for value in values):
            raise ValueError("All coordinate values must be finite")

        if not -90.0 <= origin_latitude <= 90.0:
            raise ValueError("Origin latitude must be between -90 and 90 degrees")

        if not -180.0 <= origin_longitude <= 180.0:
            raise ValueError(
                "Origin longitude must be between -180 and 180 degrees"
            )

        local = self.world_to_local(x, y)

        latitude_radians = radians(origin_latitude)
        longitude_scale = cos(latitude_radians)

        if abs(longitude_scale) < 1e-8:
            raise ValueError("Origin is too close to a pole")

        latitude = origin_latitude + degrees(
            local.y / EARTH_RADIUS_METRES
        )

        longitude = origin_longitude + degrees(
            local.x / (EARTH_RADIUS_METRES * longitude_scale)
        )

        altitude = origin_altitude + z

        return GeographicCoordinate(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
        )