import numpy as np
import pytest

from orbital_ring.evidence import (
    force_closure_table,
    node_count_l1_table,
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
    assert row["l1_guide_length_per_node_m"] == pytest.approx(598.87, abs=0.1)
    assert row["average_node_reaction_force_n"] == pytest.approx(130_381.0, abs=1.0)


def test_element_mass_changes_individual_burden_not_total_force(reference_scenario):
    frame = rotor_element_scaling_table(reference_scenario)
    assert list(frame["element_mass_g"]) == [1000, 500, 100, 50, 20, 10, 5, 1]
    assert np.all(np.diff(frame["kinetic_energy_per_element_j"]) < 0.0)
    assert np.all(np.diff(frame["force_per_individual_element_n"]) < 0.0)
    total_forces = frame["total_mean_node_force_n"].to_numpy()
    assert np.ptp(total_forces) / total_forces[0] < 1.0e-12
