import pytest

from orbital_ring.rotor import evaluate_rotor_stream


def test_rotor_scaling_and_force_consistency():
    velocity = 12_000.0
    angle = 0.04
    delta_v = 2.0 * velocity * __import__("math").sin(angle / 2.0)
    result = evaluate_rotor_stream(
        total_rotor_mass_kg=1_000_000.0,
        element_mass_kg=0.05,
        rotor_velocity_m_s=velocity,
        node_count=96,
        skip_nodes=1,
        flight_time_s=39.0,
        active_deflection_angle_rad=angle,
        required_delta_v_m_s=delta_v,
        allowed_lateral_acceleration_m_s2=9_806.65,
    )
    assert result.number_of_elements == 20_000_000
    assert result.circulation_period_s == pytest.approx(3744.0)
    assert result.kinetic_energy_per_element_j == pytest.approx(3_600_000.0)
    assert result.average_node_reaction_force_mdot_n == pytest.approx(
        result.average_node_reaction_force_summed_n, rel=2e-15
    )
    assert result.force_consistency_relative_error < 2e-15

