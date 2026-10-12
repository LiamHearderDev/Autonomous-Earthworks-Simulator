from math import atan2, degrees, isfinite, sqrt


def quaternion_to_heading(
    x: float,
    y: float,
    z: float,
    w: float,
) -> float:
    values = (x, y, z, w)

    if not all(isfinite(value) for value in values):
        raise ValueError("Quaternion values must be finite")

    magnitude = sqrt(x * x + y * y + z * z + w * w)

    if magnitude < 1e-12:
        raise ValueError("Quaternion magnitude cannot be zero")

    x /= magnitude
    y /= magnitude
    z /= magnitude
    w /= magnitude

    sin_yaw = 2.0 * (w * z + x * y)
    cos_yaw = 1.0 - 2.0 * (y * y + z * z)

    yaw_degrees = degrees(atan2(sin_yaw, cos_yaw))

    return (90.0 - yaw_degrees) % 360.0