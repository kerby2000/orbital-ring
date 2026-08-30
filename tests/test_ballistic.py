import math

import numpy as np
import pytest

from orbital_ring.ballistic import solve_ballistic_intercept
from orbital_ring.constants import REFERENCE_EARTH_ROTATION_RAD_S
from orbital_ring.geometry import node_angular_spacing
from orbital_ring.orbit import circular_orbital_velocity


EARTH_RADIUS = 6_371_000.0
ALTITUDE = 500_000.0
RADIUS = EARTH_RADIUS + ALTITUDE
MU = 3.986_004_418e14


def test_circular_orbit_rotating_target_limit():
    node_count = 96
    circular = circular_orbital_velocity(MU, RADIUS)
    result = solve_ballistic_intercept(
        earth_radius_m=EARTH_RADIUS,
        altitude_m=ALTITUDE,
        node_count=node_count,
        rotor_velocity_m_s=circular,
        mu_m3_s2=MU,
        earth_rotation_rad_s=REFERENCE_EARTH_ROTATION_RAD_S,
        minimum_safe_altitude_m=100_000.0,
        skip_nodes=1,
    )
    expected_time = node_angular_spacing(node_count) / (
        circular / RADIUS - REFERENCE_EARTH_ROTATION_RAD_S
    )
    assert result.flight_time_s == pytest.approx(expected_time, rel=2e-8)
    assert result.minimum_altitude_m == pytest.approx(ALTITUDE, abs=0.1)
    assert result.required_delta_v_m_s == pytest.approx(0.0, abs=1e-4)
    assert result.terminal_position_error_m < 0.25


@pytest.mark.parametrize("skip_nodes", [1, 2, 3])
def test_reference_direct_and_bypass_transfers(skip_nodes):
    result = solve_ballistic_intercept(
        earth_radius_m=EARTH_RADIUS,
        altitude_m=ALTITUDE,
        node_count=96,
        rotor_velocity_m_s=12_000.0,
        mu_m3_s2=MU,
        earth_rotation_rad_s=REFERENCE_EARTH_ROTATION_RAD_S,
        minimum_safe_altitude_m=100_000.0,
        skip_nodes=skip_nodes,
    )
    assert result.node_angular_spacing_rad == pytest.approx(
        2.0 * math.pi * skip_nodes / 96
    )
    assert np.linalg.norm(result.outgoing_velocity_m_s) == pytest.approx(12_000.0, rel=1e-10)
    assert np.linalg.norm(result.incoming_velocity_m_s) == pytest.approx(12_000.0, rel=1e-8)
    assert result.minimum_altitude_m < ALTITUDE
    assert result.required_active_deflection_angle_rad > 0.0
    assert result.required_delta_v_m_s > 0.0
    assert result.terminal_position_error_m < 0.25


def test_low_node_count_bypass_flags_earth_intersection():
    # skip_nodes=2 advances two node intervals and therefore bypasses one node.
    result = solve_ballistic_intercept(
        earth_radius_m=EARTH_RADIUS,
        altitude_m=ALTITUDE,
        node_count=10,
        rotor_velocity_m_s=12_000.0,
        mu_m3_s2=MU,
        earth_rotation_rad_s=REFERENCE_EARTH_ROTATION_RAD_S,
        minimum_safe_altitude_m=100_000.0,
        skip_nodes=2,
    )
    assert result.minimum_altitude_m < 0.0
    assert result.intersects_earth
    assert result.violates_minimum_safe_altitude


def test_configurable_safe_altitude_flag():
    result = solve_ballistic_intercept(
        earth_radius_m=EARTH_RADIUS,
        altitude_m=ALTITUDE,
        node_count=96,
        rotor_velocity_m_s=12_000.0,
        mu_m3_s2=MU,
        earth_rotation_rad_s=REFERENCE_EARTH_ROTATION_RAD_S,
        minimum_safe_altitude_m=ALTITUDE,
        skip_nodes=1,
    )
    assert result.violates_minimum_safe_altitude
    assert not result.intersects_earth
