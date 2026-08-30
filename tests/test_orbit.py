import math

import pytest

from orbital_ring.constants import STANDARD_GRAVITY_M_S2
from orbital_ring.orbit import (
    circular_orbital_velocity,
    continuous_magnetic_support_acceleration,
    escape_velocity,
    evaluate_closed_form,
    gravity_acceleration,
)


MU = 3.986_004_418e14
RADIUS = 6_871_000.0
VELOCITY = 12_000.0


def test_direct_orbit_equations():
    assert gravity_acceleration(MU, RADIUS) == pytest.approx(MU / RADIUS**2)
    assert circular_orbital_velocity(MU, RADIUS) == pytest.approx(math.sqrt(MU / RADIUS))
    assert escape_velocity(MU, RADIUS) == pytest.approx(math.sqrt(2.0 * MU / RADIUS))
    assert continuous_magnetic_support_acceleration(VELOCITY, MU, RADIUS) == pytest.approx(
        VELOCITY**2 / RADIUS - MU / RADIUS**2
    )


def test_reference_closed_form_values():
    result = evaluate_closed_form(
        mu_m3_s2=MU,
        radius_m=RADIUS,
        rotor_velocity_m_s=VELOCITY,
        allowed_lateral_acceleration_m_s2=1000.0 * STANDARD_GRAVITY_M_S2,
        node_count=96,
        earth_rotation_rad_s=7.292_115_0e-5,
    )
    assert result.circular_velocity_m_s / 1000.0 == pytest.approx(7.62, abs=0.01)
    assert result.magnetic_turning_angle_inertial_period_rad == pytest.approx(
        3.75193436, abs=1.0e-8
    )
    assert result.earth_fixed_magnetic_turning_angle_rad == pytest.approx(
        3.91541644, abs=1.0e-8
    )
    assert result.magnetic_curvature_radius_m / 1000.0 == pytest.approx(14.7, abs=0.1)
    assert result.total_physical_guide_length_m / 1000.0 == pytest.approx(
        55.093079, abs=1.0e-6
    )
    assert result.physical_guide_length_per_node_m == pytest.approx(
        result.total_physical_guide_length_m / 96
    )
    assert result.approximation == "large-N L0 Earth-fixed physical-guide scaling"
