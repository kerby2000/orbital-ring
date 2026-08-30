"""Immutable OR-2 magnetic feasibility result records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuideDemand:
    scenario_id: str
    configuration_hash: str
    node_count: int
    transition_identity: str
    incoming_local_inertial_velocity_m_s: tuple[float, float]
    outgoing_local_inertial_velocity_m_s: tuple[float, float]
    guide_tangential_velocity_m_s: float
    inertial_rotor_speed_m_s: float
    inertial_turn_angle_rad: float
    required_delta_v_m_s: float
    rotor_element_mass_kg: float
    net_impulse_per_element_n_s: float
    integrated_lateral_impulse_per_element_n_s: float
    element_passage_frequency_hz: float
    total_mean_node_reaction_force_n: float
    guide_relative_entry_speed_m_s: float
    guide_relative_exit_speed_m_s: float
    representative_guide_relative_speed_m_s: float
    guide_frame_element_spacing_m: float
    legacy_acceleration_m_s2: float
    legacy_physical_guide_length_m: float
    legacy_interaction_time_s: float
    source_model_version: str
    source_commit: str | None


@dataclass(frozen=True)
class GuideCapabilityResult:
    fidelity: str
    mode: str
    physical_guide_length_m: float
    required_lateral_acceleration_m_s2: float
    required_force_per_element_n: float
    interaction_time_s: float
    net_impulse_per_element_n_s: float
    integrated_lateral_impulse_per_element_n_s: float
    mean_elements_in_guide: float
    node_mean_force_from_impulse_n: float
    accepted_node_mean_force_n: float
    node_mean_force_relative_error: float
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class MaxwellPressureResult:
    fidelity: str
    field_t: float
    magnetic_pressure_pa: float
    field_energy_density_j_m3: float
    requested_force_n: float
    ideal_interaction_area_m2: float
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class QuadrupoleResult:
    fidelity: str
    gradient_t_m: float
    aperture_radius_m: float
    operating_offset_m: float
    operating_field_t: float
    aperture_edge_field_t: float
    aperture_edge_pressure_pa: float
    aperture_field_energy_per_length_j_m: float
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class DipoleForceResult:
    fidelity: str
    magnetic_moment_a_m2: float
    element_mass_kg: float
    specific_magnetic_moment_a_m2_kg: float
    gradient_t_m: float
    force_n: float
    acceleration_m_s2: float
    orientation_assumption: str
    field_seeking_classification: str
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RotorConceptResult:
    fidelity: str
    concept: str
    material_identifier: str
    element_mass_kg: float
    magnetic_material_mass_fraction: float
    utilization_factor: float
    magnetic_volume_m3: float
    magnetic_moment_a_m2: float
    specific_magnetic_moment_a_m2_kg: float
    characteristic_radius_m: float
    required_gradient_t_m: float
    available_acceleration_m_s2: float
    demagnetizing_field_scale_t: float | None
    temperature_warning_threshold_c: float | None
    source_condition_supported: bool
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PersistentLoopResult:
    fidelity: str
    concept: str
    material_identifier: str
    loop_mean_radius_m: float
    turns: int
    operating_current_a: float
    conductor_length_m: float
    conductor_mass_kg: float
    support_mass_kg: float
    total_rotor_mass_kg: float
    magnetic_moment_a_m2: float
    specific_magnetic_moment_a_m2_kg: float
    required_gradient_t_m: float
    available_acceleration_m_s2: float
    approximate_inductance_h: float | None
    stored_magnetic_energy_j: float | None
    critical_current_margin_fraction: float | None
    current_source_condition_supported: bool
    loop_formula_valid: bool
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ConductiveLoopResult:
    fidelity: str
    conductor_identifier: str
    loop_radius_m: float
    conductor_radius_m: float
    resistance_ohm: float
    inductance_h: float
    ripple_frequency_hz: float
    external_flux_amplitude_wb: float
    induced_emf_amplitude_v: float
    current_amplitude_a: float
    current_phase_lag_rad: float
    average_joule_power_w: float
    loop_formula_valid: bool
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RippleLossResult:
    fidelity: str
    material_identifier: str
    guide_relative_speed_m_s: float
    longitudinal_pitch_m: float
    ripple_frequency_hz: float
    ripple_flux_density_amplitude_t: float
    section_thickness_m: float
    electrical_resistivity_ohm_m: float
    relative_permeability: float
    skin_depth_m: float
    thickness_to_skin_depth_ratio: float
    classical_eddy_loss_density_w_m3: float
    thin_section_valid: bool
    source_frequency_domain_supported: bool | None
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class RotorGeometryResult:
    fidelity: str
    geometry: str
    mass_kg: float
    density_kg_m3: float
    volume_m3: float
    radius_m: float
    longitudinal_envelope_m: float
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ApertureResult:
    fidelity: str
    rotor_radius_m: float
    clearance_factor: float
    navigation_margin_m: float
    aperture_radius_m: float
    navigation_floor_active: bool
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PackingResult:
    fidelity: str
    rotor_longitudinal_envelope_m: float
    guide_frame_spacing_m: float
    packing_ratio: float
    required_surface_gap_m: float
    required_center_separation_m: float
    separation_margin_m: float
    infeasible_overlap: bool
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class NeighborCouplingResult:
    fidelity: str
    magnetic_moment_a_m2: float
    center_spacing_m: float
    rotor_characteristic_radius_m: float
    nearest_neighbor_field_t: float
    nearest_neighbor_force_n: float
    guide_force_n: float
    guide_operating_field_t: float
    force_fraction_of_guide: float
    field_fraction_of_guide: float
    separation_to_diameter_ratio: float
    point_dipole_valid: bool
    magnetic_state: str
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
