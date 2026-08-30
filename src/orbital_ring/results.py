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
    magnetic_turning_angle_rad: float
    magnetic_curvature_radius_m: float
    total_guide_length_m: float
    guide_length_per_node_m: float
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
    skip_nodes: int
    terminal_position_error_m: float
    solver_evaluations: int


@dataclass(frozen=True)
class RotorStreamResult:
    number_of_elements: float
    circulation_period_s: float
    element_passage_frequency_per_node_hz: float
    mean_element_spacing_m: float
    elements_simultaneously_in_guide: float
    kinetic_energy_per_element_j: float
    active_guide_length_per_node_m: float
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
    git_commit: str | None
    timestamp_utc: str
    configuration_hash: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SimulationResult:
    manifest: Manifest
    closed_form: ClosedFormResult
    ballistic: BallisticResult | None
    rotor_stream: RotorStreamResult

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

