import math

import pytest

from orbital_ring.magnetic_field import (
    MU_0_H_M,
    evaluate_aligned_dipole,
    evaluate_maxwell_pressure_bound,
    evaluate_quadrupole,
    magnetic_pressure_pa,
    quadrupole_aperture_energy_numerical_j_m,
    quadrupole_field_xy_t,
    required_gradient_t_m,
)


def test_synthetic_dipole_force_and_mass_cancellation():
    gradient = required_gradient_t_m(5000.0, 100.0)
    assert gradient == pytest.approx(50.0)

    first = evaluate_aligned_dipole(
        magnetic_moment_a_m2=10.0, element_mass_kg=0.1, gradient_t_m=gradient
    )
    second = evaluate_aligned_dipole(
        magnetic_moment_a_m2=0.1, element_mass_kg=0.001, gradient_t_m=gradient
    )
    assert first.force_n == pytest.approx(500.0)
    assert second.force_n == pytest.approx(5.0)
    assert first.acceleration_m_s2 == pytest.approx(5000.0)
    assert second.acceleration_m_s2 == pytest.approx(5000.0)
    assert first.specific_magnetic_moment_a_m2_kg == pytest.approx(
        second.specific_magnetic_moment_a_m2_kg
    )


def test_quadrupole_pole_tip_and_energy_integral():
    field_xy = quadrupole_field_xy_t(x_m=0.03, y_m=0.04, gradient_t_m=132.6)
    assert math.hypot(*field_xy) == pytest.approx(132.6 * 0.05)
    result = evaluate_quadrupole(
        gradient_t_m=132.6,
        aperture_radius_m=0.075,
        operating_offset_m=0.02,
    )
    assert result.aperture_edge_field_t == pytest.approx(132.6 * 0.075)
    expected = math.pi * 132.6**2 * 0.075**4 / (4.0 * MU_0_H_M)
    assert result.aperture_field_energy_per_length_j_m == pytest.approx(expected)
    assert quadrupole_aperture_energy_numerical_j_m(132.6, 0.075) == pytest.approx(
        expected, rel=1e-11
    )


def test_maxwell_pressure_bound():
    assert magnetic_pressure_pa(2.0) == pytest.approx(4.0 / (2.0 * MU_0_H_M))
    result = evaluate_maxwell_pressure_bound(field_t=2.0, requested_force_n=400.0)
    assert result.field_energy_density_j_m3 == pytest.approx(
        result.magnetic_pressure_pa
    )
    assert result.ideal_interaction_area_m2 == pytest.approx(
        400.0 / result.magnetic_pressure_pa
    )
    assert result.fidelity == "M0-PRESSURE"
