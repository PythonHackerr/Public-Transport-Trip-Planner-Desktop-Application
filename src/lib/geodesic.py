import math
from functools import lru_cache
from src.core.custom_types import Geopoint_t

EARTH_RADIUS = 6371000.0


def rotate_vec(vec: list, axis: int, angle: float):
    a_old = vec[axis - 1]
    b_old = vec[(axis + 1) % 3]

    vec[axis - 1] = a_old * math.cos(angle) - b_old * math.sin(angle)
    vec[(axis + 1) % 3] = a_old * math.sin(angle) + b_old * math.cos(angle)


def angle_between_normalized_vectors(vec_a: list, vec_b: list):
    return vec_a[0] * vec_b[0] + vec_a[1] * vec_b[1] + vec_a[2] * vec_b[2]


@lru_cache(2000, False)  # Now that i think about it, 2000 spaces in the cache will do just fine
def ground_distance(geopoint_a: Geopoint_t, geopoint_b: Geopoint_t):
    """
    Returns the distance in meters between the 2 points
    :param geopoint_a: lat lng float tuple
    :param geopoint_b: lat lng float tuple
    :return: ground distance in meters
    """
    if geopoint_a == geopoint_b:
        return 0

    lat_a, lng_a = geopoint_a
    lat_b, lng_b = geopoint_b
    lat_a = lat_a / 360.0 * math.pi * 2
    lat_b = lat_b / 360.0 * math.pi * 2
    lng_a = lng_a / 360.0 * math.pi * 2
    lng_b = lng_b / 360.0 * math.pi * 2

    vec_a = [1, 0, 0]
    vec_b = [1, 0, 0]

    rotate_vec(vec_a, 1, lat_a)
    rotate_vec(vec_a, 2, lng_a)

    rotate_vec(vec_b, 1, lat_b)
    rotate_vec(vec_b, 2, lng_b)

    final_angle = math.acos(angle_between_normalized_vectors(vec_a, vec_b))
    return EARTH_RADIUS * final_angle
