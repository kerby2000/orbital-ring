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
        node_stride=1,
        flight_time_s=39.0,
        incoming_local_velocity_m_s=(
            velocity * __import__("math").sin(angle / 2.0),
            velocity * __import__("math").cos(angle / 2.0),
        ),
        outgoing_local_velocity_m_s=(
            -velocity * __import__("math").sin(angle / 2.0),
            velocity * __import__("math").cos(angle / 2.0),
        ),
        guide_tangential_speed_m_s=501.0,
        allowed_lateral_acceleration_m_s2=9_806.65,
    )
    assert result.number_of_elements == 20_000_000
    assert result.circulation_period_s == pytest.approx(3744.0)
    assert result.kinetic_energy_per_element_j == pytest.approx(3_600_000.0)
    assert result.ideal_interaction_time_s == pytest.approx(velocity * angle / 9_806.65)
    assert result.inertial_turn_path_length_m > result.physical_guide_length_estimate_m
    assert result.average_node_reaction_force_mdot_n == pytest.approx(
        result.average_node_reaction_force_summed_n, rel=2e-15
    )
    assert result.force_consistency_relative_error < 2e-15
