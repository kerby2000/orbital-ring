"""L0 closed-form orbital and magnetic-support relationships."""

from __future__ import annotations

import math

from orbital_ring.constants import TAU
from orbital_ring.results import ClosedFormResult


def gravity_acceleration(mu_m3_s2: float, radius_m: float) -> float:
    return mu_m3_s2 / radius_m**2


def circular_orbital_velocity(mu_m3_s2: float, radius_m: float) -> float:
    return math.sqrt(mu_m3_s2 / radius_m)


def escape_velocity(mu_m3_s2: float, radius_m: float) -> float:
    return math.sqrt(2.0 * mu_m3_s2 / radius_m)


def continuous_magnetic_support_acceleration(
    rotor_velocity_m_s: float, mu_m3_s2: float, radius_m: float
) -> float:
    return rotor_velocity_m_s**2 / radius_m - gravity_acceleration(mu_m3_s2, radius_m)


def magnetic_turning_angle_many_node(
    rotor_velocity_m_s: float, circular_velocity_m_s: float
) -> float:
    return TAU * (1.0 - (circular_velocity_m_s / rotor_velocity_m_s) ** 2)


def magnetic_curvature_radius(
    rotor_velocity_m_s: float, allowed_lateral_acceleration_m_s2: float
) -> float:
    return rotor_velocity_m_s**2 / allowed_lateral_acceleration_m_s2


def evaluate_closed_form(
    *,
    mu_m3_s2: float,
    radius_m: float,
    rotor_velocity_m_s: float,
    allowed_lateral_acceleration_m_s2: float,
    node_count: int,
) -> ClosedFormResult:
    """Evaluate all requested L0 equations.

    Guide-length values are explicitly large-N scaling approximations.
    """

    gravity = gravity_acceleration(mu_m3_s2, radius_m)
    circular = circular_orbital_velocity(mu_m3_s2, radius_m)
    escape = escape_velocity(mu_m3_s2, radius_m)
    support = continuous_magnetic_support_acceleration(
        rotor_velocity_m_s, mu_m3_s2, radius_m
    )
    turning = magnetic_turning_angle_many_node(rotor_velocity_m_s, circular)
    curvature_radius = magnetic_curvature_radius(
        rotor_velocity_m_s, allowed_lateral_acceleration_m_s2
    )
    total_length = curvature_radius * turning
    return ClosedFormResult(
        gravity_m_s2=gravity,
        circular_velocity_m_s=circular,
        escape_velocity_m_s=escape,
        continuous_support_acceleration_m_s2=support,
        magnetic_turning_angle_rad=turning,
        magnetic_curvature_radius_m=curvature_radius,
        total_guide_length_m=total_length,
        guide_length_per_node_m=total_length / node_count,
        approximation="large-N L0 scaling",
    )

