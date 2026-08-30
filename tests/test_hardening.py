import numpy as np
import pytest

from orbital_ring.evidence import (
    bypass_leg_table,
    failure_transition_table,
    force_closure_table,
    node_count_l1_table,
    physical_guide_convergence_table,
    rotor_element_scaling_table,
)


def test_global_force_closure_converges_monotonically(reference_scenario):
    frame = force_closure_table(reference_scenario)
    assert list(frame["node_count"]) == [48, 96, 192, 480, 960, 1920]
    errors = frame["absolute_relative_error"].to_numpy()
    assert np.all(np.diff(errors) < 0.0)
    assert errors[-1] < 1.0e-6


def test_reference_guide_and_node_force_remain_accepted(reference_scenario):
    row = node_count_l1_table(reference_scenario, [96]).iloc[0]
    assert row["l1_physical_guide_length_per_node_m"] == pytest.approx(573.86, abs=0.1)
    assert row["ideal_interaction_time_s"] == pytest.approx(0.0499056, abs=1.0e-6)
    assert row["guide_relative_entry_speed_m_s"] == pytest.approx(11_499.07, abs=0.1)
    assert row["guide_relative_exit_speed_m_s"] == pytest.approx(11_499.07, abs=0.1)
    assert row["inertial_turn_path_length_m"] == pytest.approx(598.867, abs=0.01)
    assert row["average_node_reaction_force_n"] == pytest.approx(130_381.0, abs=1.0)


def test_physical_guide_length_converges_to_l0_earth_fixed_limit(reference_scenario):
    frame = physical_guide_convergence_table(reference_scenario)
    errors = frame["absolute_relative_error"].to_numpy()
    assert np.all(np.diff(errors) < 0.0)
    assert errors[-1] < 1.0e-6
    assert frame.iloc[-1]["l0_large_n_physical_guide_length_m"] == pytest.approx(
        55_093.079443, abs=1.0e-5
    )


def test_element_mass_changes_individual_burden_not_total_force(reference_scenario):
    frame = rotor_element_scaling_table(reference_scenario)
    assert list(frame["element_mass_g"]) == [1000, 500, 100, 50, 20, 10, 5, 1]
    assert np.all(np.diff(frame["kinetic_energy_per_element_j"]) < 0.0)
    assert np.all(np.diff(frame["force_per_individual_element_n"]) < 0.0)
    total_forces = frame["total_mean_node_force_n"].to_numpy()
    assert np.ptp(total_forces) / total_forces[0] < 1.0e-12
    assert "mean_guide_frame_element_spacing_m" in frame.columns
    assert "ideal_interaction_time_s" in frame.columns


def test_failure_evidence_separates_free_flight_from_node_transition(reference_scenario):
    legs = bypass_leg_table(reference_scenario, [96])
    transitions = failure_transition_table(reference_scenario, [96])
    assert "local_bypass_deflection_angle_rad" not in legs.columns
    assert "local_bypass_guide_length_m" not in legs.columns
    assert len(legs) == 2
    assert len(transitions) == 4
    assert set(transitions["incoming_leg_stride"]) == {1, 2, 3}
    assert set(transitions["outgoing_leg_stride"]) == {1, 2, 3}
