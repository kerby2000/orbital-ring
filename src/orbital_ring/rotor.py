"""Rotor-stream population, energy, guide occupancy, and force scaling."""

from __future__ import annotations

import math

from orbital_ring.results import RotorStreamResult


def evaluate_rotor_stream(
    *,
    total_rotor_mass_kg: float,
    element_mass_kg: float,
    rotor_velocity_m_s: float,
    node_count: int,
    skip_nodes: int,
    flight_time_s: float,
    active_deflection_angle_rad: float,
    required_delta_v_m_s: float,
    allowed_lateral_acceleration_m_s2: float,
) -> RotorStreamResult:
    """Evaluate a uniformly populated periodic stream.

    For skip trajectories, each element interacts at one of every
    ``skip_nodes`` nodes. Passage frequency is the uniform average per node.
    The summed-force check accounts for the rotating lateral-force direction
    through a finite-angle guide; it is therefore a vector sum, not a sum of
    force magnitudes.
    """

    number_of_elements = total_rotor_mass_kg / element_mass_kg
    circulation_period_s = flight_time_s * node_count / skip_nodes
    interactions_per_element_per_circulation = node_count / skip_nodes
    passage_frequency = (
        number_of_elements
        * interactions_per_element_per_circulation
        / (node_count * circulation_period_s)
    )
    mean_spacing = rotor_velocity_m_s * circulation_period_s / number_of_elements
    kinetic_energy = 0.5 * element_mass_kg * rotor_velocity_m_s**2
    guide_length = (
        rotor_velocity_m_s**2
        * active_deflection_angle_rad
        / allowed_lateral_acceleration_m_s2
    )
    dwell_time = guide_length / rotor_velocity_m_s
    simultaneous_elements = passage_frequency * dwell_time
    mass_flow = passage_frequency * element_mass_kg
    force_mdot = mass_flow * required_delta_v_m_s

    if active_deflection_angle_rad == 0.0:
        vector_projection_factor = 1.0
    else:
        vector_projection_factor = (
            2.0
            * math.sin(active_deflection_angle_rad / 2.0)
            / active_deflection_angle_rad
        )
    force_summed = (
        simultaneous_elements
        * element_mass_kg
        * allowed_lateral_acceleration_m_s2
        * vector_projection_factor
    )
    denominator = max(abs(force_mdot), abs(force_summed), 1.0)
    relative_error = abs(force_mdot - force_summed) / denominator

    return RotorStreamResult(
        number_of_elements=number_of_elements,
        circulation_period_s=circulation_period_s,
        element_passage_frequency_per_node_hz=passage_frequency,
        mean_element_spacing_m=mean_spacing,
        elements_simultaneously_in_guide=simultaneous_elements,
        kinetic_energy_per_element_j=kinetic_energy,
        active_guide_length_per_node_m=guide_length,
        mass_flow_per_node_kg_s=mass_flow,
        average_node_reaction_force_mdot_n=force_mdot,
        average_node_reaction_force_summed_n=force_summed,
        force_consistency_relative_error=relative_error,
    )

