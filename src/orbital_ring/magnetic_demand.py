"""OR-1.1 to OR-2 demand adapter and invertible guide kinematics."""

from __future__ import annotations

import math

import numpy as np

from orbital_ring.config import Scenario
from orbital_ring.geometry import rotate_vector
from orbital_ring.magnetic_results import GuideCapabilityResult, GuideDemand
from orbital_ring.results import SimulationResult

GUIDE_KINEMATICS_FIDELITY = "M1-GUIDE-KINEMATICS"


def build_guide_demand(
    scenario: Scenario,
    accepted_result: SimulationResult,
    *,
    transition_identity: str = "normal-node",
) -> GuideDemand:
    """Adapt accepted OR-1.1 output without calling any orbital solver."""

    ballistic = accepted_result.ballistic
    if ballistic is None:
        raise ValueError("OR-2 GuideDemand currently requires an accepted L1 result")
    if accepted_result.manifest.configuration_hash != scenario.configuration_hash:
        raise ValueError("scenario and accepted result configuration hashes differ")
    target_angle = (
        ballistic.node_angular_spacing_rad
        + scenario.earth.rotation_rate_rad_s * ballistic.flight_time_s
    )
    incoming_local = rotate_vector(
        np.asarray(ballistic.incoming_velocity_m_s), -target_angle
    )
    outgoing_local = np.asarray(ballistic.outgoing_velocity_m_s)
    rotor = accepted_result.rotor_stream
    if rotor.ideal_interaction_time_s <= 0.0:
        raise ValueError("accepted interaction time must be positive")
    representative_speed = (
        rotor.physical_guide_length_estimate_m / rotor.ideal_interaction_time_s
    )
    element_mass = scenario.rotor.element_mass_kg
    net_impulse = element_mass * rotor.required_delta_v_m_s
    integrated_lateral_impulse = (
        element_mass * rotor.inertial_rotor_speed_m_s * rotor.inertial_turn_angle_rad
    )
    return GuideDemand(
        scenario_id=scenario.scenario_id,
        configuration_hash=scenario.configuration_hash,
        node_count=scenario.ring.node_count,
        transition_identity=transition_identity,
        incoming_local_inertial_velocity_m_s=(
            float(incoming_local[0]),
            float(incoming_local[1]),
        ),
        outgoing_local_inertial_velocity_m_s=(
            float(outgoing_local[0]),
            float(outgoing_local[1]),
        ),
        guide_tangential_velocity_m_s=(
            scenario.earth.rotation_rate_rad_s * scenario.radius_m
        ),
        inertial_rotor_speed_m_s=rotor.inertial_rotor_speed_m_s,
        inertial_turn_angle_rad=rotor.inertial_turn_angle_rad,
        required_delta_v_m_s=rotor.required_delta_v_m_s,
        rotor_element_mass_kg=element_mass,
        net_impulse_per_element_n_s=net_impulse,
        integrated_lateral_impulse_per_element_n_s=integrated_lateral_impulse,
        element_passage_frequency_hz=rotor.element_passage_frequency_per_node_hz,
        total_mean_node_reaction_force_n=rotor.average_node_reaction_force_mdot_n,
        guide_relative_entry_speed_m_s=(
            rotor.earth_fixed_guide_relative_entry_speed_m_s
        ),
        guide_relative_exit_speed_m_s=(rotor.earth_fixed_guide_relative_exit_speed_m_s),
        representative_guide_relative_speed_m_s=representative_speed,
        guide_frame_element_spacing_m=rotor.mean_guide_frame_element_spacing_m,
        legacy_acceleration_m_s2=scenario.magnetic.max_lateral_acceleration_m_s2,
        legacy_physical_guide_length_m=rotor.physical_guide_length_estimate_m,
        legacy_interaction_time_s=rotor.ideal_interaction_time_s,
        source_model_version=accepted_result.manifest.model_version,
        source_commit=accepted_result.manifest.source_commit,
    )


def _guide_result(
    demand: GuideDemand,
    *,
    acceleration_m_s2: float,
    mode: str,
) -> GuideCapabilityResult:
    if acceleration_m_s2 <= 0.0:
        raise ValueError("lateral acceleration must be positive")
    scaling = demand.legacy_acceleration_m_s2 / acceleration_m_s2
    length = demand.legacy_physical_guide_length_m * scaling
    interaction_time = demand.legacy_interaction_time_s * scaling
    force = demand.rotor_element_mass_kg * acceleration_m_s2
    node_from_impulse = (
        demand.element_passage_frequency_hz * demand.net_impulse_per_element_n_s
    )
    relative_error = (
        node_from_impulse - demand.total_mean_node_reaction_force_n
    ) / demand.total_mean_node_reaction_force_n
    return GuideCapabilityResult(
        fidelity=GUIDE_KINEMATICS_FIDELITY,
        mode=mode,
        physical_guide_length_m=length,
        required_lateral_acceleration_m_s2=acceleration_m_s2,
        required_force_per_element_n=force,
        interaction_time_s=interaction_time,
        net_impulse_per_element_n_s=demand.net_impulse_per_element_n_s,
        integrated_lateral_impulse_per_element_n_s=(
            demand.integrated_lateral_impulse_per_element_n_s
        ),
        mean_elements_in_guide=(demand.element_passage_frequency_hz * interaction_time),
        node_mean_force_from_impulse_n=node_from_impulse,
        accepted_node_mean_force_n=demand.total_mean_node_reaction_force_n,
        node_mean_force_relative_error=relative_error,
        assumptions=(
            "Accepted OR-1.1 endpoint velocities and guide-relative speed integral are fixed.",
            "The inertial velocity vector rotates at constant magnitude and angular rate.",
            "Gravity and local Earth-frame rotation during the finite guide interaction are omitted.",
        ),
        warnings=(
            "This is an ideal kinematic inversion, not a magnet or structural design.",
        ),
    )


def solve_acceleration_for_guide_length(
    demand: GuideDemand, target_physical_guide_length_m: float
) -> GuideCapabilityResult:
    """Length-driven mode: solve constant-normal-acceleration demand."""

    if target_physical_guide_length_m <= 0.0:
        raise ValueError("target guide length must be positive")
    acceleration = (
        demand.legacy_acceleration_m_s2
        * demand.legacy_physical_guide_length_m
        / target_physical_guide_length_m
    )
    result = _guide_result(demand, acceleration_m_s2=acceleration, mode="length-driven")
    if not math.isclose(
        result.physical_guide_length_m,
        target_physical_guide_length_m,
        rel_tol=1.0e-12,
    ):
        raise AssertionError("guide inversion failed")
    return result


def solve_guide_length_for_acceleration(
    demand: GuideDemand, available_acceleration_m_s2: float
) -> GuideCapabilityResult:
    """Capability-driven mode for an available constant normal acceleration."""

    return _guide_result(
        demand,
        acceleration_m_s2=available_acceleration_m_s2,
        mode="capability-driven-acceleration",
    )


def solve_guide_length_for_force(
    demand: GuideDemand, available_force_per_element_n: float
) -> GuideCapabilityResult:
    """Capability-driven mode for an available per-element force."""

    if available_force_per_element_n <= 0.0:
        raise ValueError("available force must be positive")
    return _guide_result(
        demand,
        acceleration_m_s2=(
            available_force_per_element_n / demand.rotor_element_mass_kg
        ),
        mode="capability-driven-force",
    )
