import math

import pytest

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.magnetic_demand import (
    build_guide_demand,
    solve_acceleration_for_guide_length,
    solve_guide_length_for_acceleration,
    solve_guide_length_for_force,
)


def test_guide_demand_preserves_accepted_or11_reference(reference_scenario):
    result = evaluate_scenario(reference_scenario)
    demand = build_guide_demand(reference_scenario, result)

    assert demand.inertial_turn_angle_rad == pytest.approx(0.0407838915646583)
    assert demand.required_delta_v_m_s == pytest.approx(489.372781031356)
    assert demand.legacy_interaction_time_s == pytest.approx(0.0499055945481795)
    assert demand.legacy_physical_guide_length_m == pytest.approx(573.86418294666)
    assert demand.representative_guide_relative_speed_m_s == pytest.approx(
        demand.legacy_physical_guide_length_m / demand.legacy_interaction_time_s
    )
    assert demand.net_impulse_per_element_n_s == pytest.approx(
        reference_scenario.rotor.element_mass_kg * demand.required_delta_v_m_s
    )


def test_length_and_capability_modes_are_inverse(reference_scenario):
    demand = build_guide_demand(
        reference_scenario, evaluate_scenario(reference_scenario)
    )
    doubled_length = 2.0 * demand.legacy_physical_guide_length_m
    length_driven = solve_acceleration_for_guide_length(demand, doubled_length)
    assert length_driven.required_lateral_acceleration_m_s2 == pytest.approx(
        0.5 * demand.legacy_acceleration_m_s2
    )
    capability = solve_guide_length_for_acceleration(
        demand, length_driven.required_lateral_acceleration_m_s2
    )
    assert capability.physical_guide_length_m == pytest.approx(doubled_length)

    force_driven = solve_guide_length_for_force(
        demand,
        demand.rotor_element_mass_kg * demand.legacy_acceleration_m_s2,
    )
    assert force_driven.physical_guide_length_m == pytest.approx(
        demand.legacy_physical_guide_length_m
    )
    assert force_driven.node_mean_force_relative_error == pytest.approx(0.0, abs=1e-12)
    assert math.isclose(
        force_driven.node_mean_force_from_impulse_n,
        demand.total_mean_node_reaction_force_n,
        rel_tol=1e-12,
    )
