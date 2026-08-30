"""Earth-fixed equatorial node geometry."""

from __future__ import annotations

import math

import numpy as np

from orbital_ring.constants import TAU


def node_angular_spacing(node_count: int, skip_nodes: int = 1) -> float:
    return TAU * skip_nodes / node_count


def node_arc_separation(radius_m: float, node_count: int, skip_nodes: int = 1) -> float:
    return radius_m * node_angular_spacing(node_count, skip_nodes)


def node_chord_separation(radius_m: float, node_count: int, skip_nodes: int = 1) -> float:
    angle = node_angular_spacing(node_count, skip_nodes)
    return 2.0 * radius_m * math.sin(angle / 2.0)


def target_node_position(
    radius_m: float,
    node_count: int,
    skip_nodes: int,
    earth_rotation_rad_s: float,
    flight_time_s: float,
) -> np.ndarray:
    angle = node_angular_spacing(node_count, skip_nodes) + earth_rotation_rad_s * flight_time_s
    return radius_m * np.array([math.cos(angle), math.sin(angle)], dtype=float)


def rotate_vector(vector: np.ndarray, angle_rad: float) -> np.ndarray:
    cosine = math.cos(angle_rad)
    sine = math.sin(angle_rad)
    rotation = np.array([[cosine, -sine], [sine, cosine]])
    return rotation @ vector

