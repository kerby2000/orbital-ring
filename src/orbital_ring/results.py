"""Serializable result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ClosedFormResult:
    gravity_m_s2: float
    circular_velocity_m_s: float
    escape_velocity_m_s: float
    continuous_support_acceleration_m_s2: float
    magnetic_turning_angle_inertial_period_rad: float
    earth_relative_rotor_speed_m_s: float
    earth_relative_circuit_period_s: float
    earth_fixed_magnetic_turning_angle_rad: float
    magnetic_curvature_radius_m: float
    total_physical_guide_length_m: float
    physical_guide_length_per_node_m: float
    approximation: str


@dataclass(frozen=True)
class BallisticResult:
    node_angular_spacing_rad: float
    surface_arc_separation_m: float
    flight_time_s: float
    outgoing_velocity_m_s: tuple[float, float]
    incoming_velocity_m_s: tuple[float, float]
    required_active_deflection_angle_rad: float
    required_delta_v_m_s: float
    minimum_altitude_m: float
    intersects_earth: bool
    violates_minimum_safe_altitude: bool
    node_stride: int
    terminal_position_error_m: float
    solver_evaluations: int


@dataclass(frozen=True)
class RotorStreamResult:
    inertial_rotor_speed_m_s: float
    earth_fixed_guide_relative_entry_speed_m_s: float
    earth_fixed_guide_relative_exit_speed_m_s: float
    ideal_interaction_time_s: float
    inertial_turn_angle_rad: float
    required_delta_v_m_s: float
    physical_guide_length_estimate_m: float
    inertial_turn_path_length_m: float
    number_of_elements: float
    circulation_period_s: float
    element_passage_frequency_per_node_hz: float
    mean_inertial_element_spacing_m: float
    mean_guide_frame_element_spacing_m: float
    elements_simultaneously_in_guide: float
    kinetic_energy_per_element_j: float
    mass_flow_per_node_kg_s: float
    average_node_reaction_force_mdot_n: float
    average_node_reaction_force_summed_n: float
    force_consistency_relative_error: float


@dataclass(frozen=True)
class Manifest:
    scenario_id: str
    input_parameters: dict[str, Any]
    derived_parameters: dict[str, Any]
    model_version: str
    fidelity: str
    source_commit: str | None
    source_worktree_dirty: bool | None
    artifact_commit: str | None
    timestamp_utc: str
    configuration_hash: str
    python_version: str
    numpy_version: str
    scipy_version: str
    pint_version: str
    platform_information: str
    numerical_integrator: str
    integrator_rtol: float
    integrator_atol: float
    integrator_max_step_policy: str
    terminal_position_tolerance_m: float
    solver_algorithm: str
    maximum_solver_evaluations: int
    guide_kinematics_model: str
    guide_quadrature_method: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SimulationResult:
    manifest: Manifest
    closed_form: ClosedFormResult
    ballistic: BallisticResult | None
    rotor_stream: RotorStreamResult

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouteLeg:
    start_node: int
    target_node: int
    node_stride: int
    bypassed_nodes: tuple[int, ...]


@dataclass(frozen=True)
class FailureBypassResult:
    start_node: int
    target_node: int
    bypassed_nodes: tuple[int, ...]
    ballistic: BallisticResult


@dataclass(frozen=True)
class GuideKinematicsResult:
    inertial_rotor_speed_m_s: float
    guide_tangential_speed_m_s: float
    guide_relative_entry_speed_m_s: float
    guide_relative_exit_speed_m_s: float
    representative_guide_relative_speed_m_s: float
    ideal_interaction_time_s: float
    inertial_turn_angle_rad: float
    required_delta_v_m_s: float
    physical_guide_length_estimate_m: float
    inertial_turn_path_length_m: float
    quadrature_method: str


@dataclass(frozen=True)
class NodeTransitionResult:
    node_index: int
    incoming_leg_stride: int
    outgoing_leg_stride: int
    incoming_local_velocity_m_s: tuple[float, float]
    outgoing_local_velocity_m_s: tuple[float, float]
    actual_transition_angle_rad: float
    actual_transition_delta_v_m_s: float
    ideal_interaction_time_s: float
    guide_relative_entry_speed_m_s: float
    guide_relative_exit_speed_m_s: float
    physical_guide_length_estimate_m: float
    inertial_turn_path_length_m: float
    is_failure_related: bool


@dataclass(frozen=True)
class FailureRouteResult:
    scenario_id: str
    failed_nodes: tuple[int, ...]
    active_node_count: int
    normal_leg_count: int
    route_circulation_period_s: float
    normal_reference_circulation_period_s: float
    active_node_passage_frequency_hz: float
    normal_reference_passage_frequency_hz: float
    route_legs: tuple[RouteLeg, ...]
    bypass_legs: tuple[FailureBypassResult, ...]
    node_transitions: tuple[NodeTransitionResult, ...]
    normal_global_reference: SimulationResult

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
