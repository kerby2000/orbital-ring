"""Rotor-stream population, energy, guide occupancy, and force scaling."""

from __future__ import annotations

import math

from orbital_ring.guide import evaluate_guide_kinematics
from orbital_ring.results import RotorStreamResult


def evaluate_rotor_stream(
    *,
    total_rotor_mass_kg: float,
    element_mass_kg: float,
    rotor_velocity_m_s: float,
    node_count: int,
    node_stride: int,
    flight_time_s: float,
    incoming_local_velocity_m_s: tuple[float, float],
    outgoing_local_velocity_m_s: tuple[float, float],
    guide_tangential_speed_m_s: float,
    allowed_lateral_acceleration_m_s2: float,
) -> RotorStreamResult:
    """Evaluate a uniformly populated periodic stream.

    This homogeneous-stride scaling is valid only when the complete regular
    stream uses ``node_stride``. A local failed-node bypass must not use this
    function to redefine global passage frequency.
    The summed-force check accounts for the rotating lateral-force direction
    through a finite-angle guide; it is therefore a vector sum, not a sum of
    force magnitudes.
    """

    number_of_elements = total_rotor_mass_kg / element_mass_kg
    guide = evaluate_guide_kinematics(
        incoming_local_velocity_m_s=incoming_local_velocity_m_s,
        outgoing_local_velocity_m_s=outgoing_local_velocity_m_s,
        guide_tangential_speed_m_s=guide_tangential_speed_m_s,
        allowed_lateral_acceleration_m_s2=allowed_lateral_acceleration_m_s2,
    )
    circulation_period_s = flight_time_s * node_count / node_stride
    interactions_per_element_per_circulation = node_count / node_stride
    passage_frequency = (
        number_of_elements
        * interactions_per_element_per_circulation
        / (node_count * circulation_period_s)
    )
    mean_inertial_spacing = (
        rotor_velocity_m_s * circulation_period_s / number_of_elements
    )
    mean_guide_spacing = (
        guide.representative_guide_relative_speed_m_s / passage_frequency
    )
    kinetic_energy = 0.5 * element_mass_kg * rotor_velocity_m_s**2
    simultaneous_elements = passage_frequency * guide.ideal_interaction_time_s
    mass_flow = passage_frequency * element_mass_kg
    force_mdot = mass_flow * guide.required_delta_v_m_s

    if guide.inertial_turn_angle_rad == 0.0:
        vector_projection_factor = 1.0
    else:
        vector_projection_factor = (
            2.0
            * math.sin(guide.inertial_turn_angle_rad / 2.0)
            / guide.inertial_turn_angle_rad
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
        inertial_rotor_speed_m_s=guide.inertial_rotor_speed_m_s,
        earth_fixed_guide_relative_entry_speed_m_s=(
            guide.guide_relative_entry_speed_m_s
        ),
        earth_fixed_guide_relative_exit_speed_m_s=(
            guide.guide_relative_exit_speed_m_s
        ),
        ideal_interaction_time_s=guide.ideal_interaction_time_s,
        inertial_turn_angle_rad=guide.inertial_turn_angle_rad,
        required_delta_v_m_s=guide.required_delta_v_m_s,
        physical_guide_length_estimate_m=guide.physical_guide_length_estimate_m,
        inertial_turn_path_length_m=guide.inertial_turn_path_length_m,
        number_of_elements=number_of_elements,
        circulation_period_s=circulation_period_s,
        element_passage_frequency_per_node_hz=passage_frequency,
        mean_inertial_element_spacing_m=mean_inertial_spacing,
        mean_guide_frame_element_spacing_m=mean_guide_spacing,
        elements_simultaneously_in_guide=simultaneous_elements,
        kinetic_energy_per_element_j=kinetic_energy,
        mass_flow_per_node_kg_s=mass_flow,
        average_node_reaction_force_mdot_n=force_mdot,
        average_node_reaction_force_summed_n=force_summed,
        force_consistency_relative_error=relative_error,
    )
