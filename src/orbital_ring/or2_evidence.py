"""Reproducible OR-2 magnetic feasibility studies and canonical evidence."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.config import Scenario, load_scenario
from orbital_ring.constants import STANDARD_GRAVITY_M_S2 as G0_M_S2
from orbital_ring.evidence import dataframe_to_markdown
from orbital_ring.magnetic_demand import (
    build_guide_demand,
    solve_acceleration_for_guide_length,
    solve_guide_length_for_acceleration,
)
from orbital_ring.magnetic_field import (
    evaluate_aligned_dipole,
    evaluate_maxwell_pressure_bound,
    evaluate_quadrupole,
    required_gradient_t_m,
)
from orbital_ring.magnetic_geometry import (
    evaluate_aperture,
    evaluate_neighbor_coupling,
    evaluate_stream_packing,
    loop_envelope_geometry,
    sphere_geometry,
)
from orbital_ring.magnetic_losses import (
    evaluate_conductive_loop,
    evaluate_ripple_loss,
    ripple_frequency_hz,
)
from orbital_ring.magnetic_rotors import (
    evaluate_permanent_magnet,
    evaluate_persistent_current_loop,
    evaluate_saturated_ferromagnet,
    rebco_tape_mass_per_length_kg_m,
)
from orbital_ring.materials import MaterialRegistry, load_material_registry

PRIMARY_NODE_COUNTS = (96, 960)
SCALING_NODE_COUNTS = (48, 96, 192, 480, 960, 1920)
ELEMENT_MASSES_KG = (1.0, 0.5, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001, 0.0005, 0.0001)
ACCELERATION_G0 = (100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0)
SPECIFIC_MOMENTS_A_M2_KG = (10.0, 50.0, 100.0, 200.0, 500.0)
RIPPLE_PITCHES_M = (10.0, 1.0, 0.1)
TARGET_GUIDE_LENGTHS_M = (50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0)
CLEARANCE_FACTOR = 2.5
NAVIGATION_MARGIN_M = 0.005
OPERATING_OFFSET_FRACTION = 0.5
REQUIRED_SURFACE_GAP_FACTOR = 1.0


def _scenario(
    scenario: Scenario, *, node_count: int, element_mass_kg: float
) -> Scenario:
    return scenario.with_overrides(
        {
            "ring.node_count": node_count,
            "rotor.element_mass_kg": element_mass_kg,
            "transfer.node_stride": 1,
        }
    )


def _demand(scenario: Scenario, *, node_count: int, element_mass_kg: float):
    sized = _scenario(scenario, node_count=node_count, element_mass_kg=element_mass_kg)
    return build_guide_demand(sized, evaluate_scenario(sized))


def magnetic_demand_scaling_table(
    scenario: Scenario,
    *,
    node_counts: Iterable[int] = PRIMARY_NODE_COUNTS,
    element_masses_kg: Iterable[float] = ELEMENT_MASSES_KG,
    accelerations_g0: Iterable[float] = ACCELERATION_G0,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for node_count in node_counts:
        for element_mass in element_masses_kg:
            demand = _demand(
                scenario, node_count=node_count, element_mass_kg=element_mass
            )
            for acceleration_g0 in accelerations_g0:
                capability = solve_guide_length_for_acceleration(
                    demand, acceleration_g0 * G0_M_S2
                )
                rows.append(
                    {
                        "node_count": node_count,
                        "target_acceleration_g0": acceleration_g0,
                        "element_mass_g": element_mass * 1000.0,
                        "physical_guide_length_m": capability.physical_guide_length_m,
                        "force_per_element_n": capability.required_force_per_element_n,
                        "net_impulse_per_element_n_s": capability.net_impulse_per_element_n_s,
                        "integrated_lateral_impulse_per_element_n_s": capability.integrated_lateral_impulse_per_element_n_s,
                        "interaction_time_s": capability.interaction_time_s,
                        "mean_elements_in_guide": capability.mean_elements_in_guide,
                        "node_mean_force_n": capability.node_mean_force_from_impulse_n,
                        "accepted_node_mean_force_n": capability.accepted_node_mean_force_n,
                        "node_mean_force_relative_error": capability.node_mean_force_relative_error,
                        "fidelity": capability.fidelity,
                        "assumptions": " | ".join(capability.assumptions),
                        "warnings": " | ".join(capability.warnings),
                    }
                )
    return pd.DataFrame(rows)


def node_count_magnetic_scaling_table(scenario: Scenario) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for node_count in SCALING_NODE_COUNTS:
        demand = _demand(scenario, node_count=node_count, element_mass_kg=0.05)
        capability = solve_guide_length_for_acceleration(demand, 1000.0 * G0_M_S2)
        rows.append(
            {
                "node_count": node_count,
                "turn_angle_rad": demand.inertial_turn_angle_rad,
                "delta_v_m_s": demand.required_delta_v_m_s,
                "guide_length_at_1000g0_m": capability.physical_guide_length_m,
                "force_per_50g_element_n": capability.required_force_per_element_n,
                "net_impulse_per_50g_element_n_s": capability.net_impulse_per_element_n_s,
                "node_mean_force_n": capability.node_mean_force_from_impulse_n,
                "fidelity": capability.fidelity,
                "assumptions": " | ".join(capability.assumptions),
                "warnings": " | ".join(capability.warnings),
            }
        )
    return pd.DataFrame(rows)


def guide_length_inversion_table(scenario: Scenario) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for node_count in PRIMARY_NODE_COUNTS:
        demand = _demand(scenario, node_count=node_count, element_mass_kg=0.05)
        for target_length in TARGET_GUIDE_LENGTHS_M:
            result = solve_acceleration_for_guide_length(demand, target_length)
            rows.append(
                {
                    "node_count": node_count,
                    "target_physical_guide_length_m": target_length,
                    "required_acceleration_m_s2": result.required_lateral_acceleration_m_s2,
                    "required_acceleration_g0": result.required_lateral_acceleration_m_s2
                    / G0_M_S2,
                    "required_force_per_50g_element_n": result.required_force_per_element_n,
                    "interaction_time_s": result.interaction_time_s,
                    "net_impulse_per_50g_element_n_s": result.net_impulse_per_element_n_s,
                    "node_mean_force_n": result.node_mean_force_from_impulse_n,
                    "node_mean_force_relative_error": result.node_mean_force_relative_error,
                    "mode": result.mode,
                    "fidelity": result.fidelity,
                    "assumptions": " | ".join(result.assumptions),
                    "warnings": " | ".join(result.warnings),
                }
            )
    return pd.DataFrame(rows)


def specific_moment_gradient_table() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for acceleration_g0 in ACCELERATION_G0:
        acceleration = acceleration_g0 * G0_M_S2
        for specific_moment in SPECIFIC_MOMENTS_A_M2_KG:
            gradient = required_gradient_t_m(acceleration, specific_moment)
            for mass in (1.0, 0.05, 0.0001):
                dipole = evaluate_aligned_dipole(
                    magnetic_moment_a_m2=specific_moment * mass,
                    element_mass_kg=mass,
                    gradient_t_m=gradient,
                )
                rows.append(
                    {
                        "target_acceleration_g0": acceleration_g0,
                        "specific_magnetic_moment_a_m2_kg": specific_moment,
                        "element_mass_g": mass * 1000.0,
                        "magnetic_moment_a_m2": dipole.magnetic_moment_a_m2,
                        "force_per_element_n": dipole.force_n,
                        "required_gradient_t_m": gradient,
                        "recovered_acceleration_m_s2": dipole.acceleration_m_s2,
                        "gradient_mass_independent_at_fixed_specific_moment": True,
                        "fidelity": dipole.fidelity,
                        "orientation_assumption": dipole.orientation_assumption,
                        "field_seeking_classification": dipole.field_seeking_classification,
                        "assumptions": " | ".join(dipole.assumptions),
                        "warnings": " | ".join(dipole.warnings),
                    }
                )
    return pd.DataFrame(rows)


def maxwell_pressure_table() -> pd.DataFrame:
    requested_force = 0.05 * 1000.0 * G0_M_S2
    rows: list[dict[str, object]] = []
    for field in (0.5, 1.0, 2.0, 5.0, 10.0):
        result = evaluate_maxwell_pressure_bound(
            field_t=field, requested_force_n=requested_force
        )
        row = asdict(result)
        row["assumptions"] = " | ".join(result.assumptions)
        row["warnings"] = " | ".join(result.warnings)
        rows.append(row)
    return pd.DataFrame(rows)


def aperture_field_energy_table(
    scenario: Scenario, registry: MaterialRegistry
) -> pd.DataFrame:
    benchmark_gradient = registry.get("mqxf_benchmark").value("nominal_gradient_t_m")
    fe_co_specific = evaluate_saturated_ferromagnet(
        registry,
        material_identifier="vacoflux_50",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=0.8,
        utilization_factor=0.7,
        required_acceleration_m_s2=1000.0 * G0_M_S2,
        available_gradient_t_m=benchmark_gradient,
    ).specific_magnetic_moment_a_m2_kg
    gradient = required_gradient_t_m(1000.0 * G0_M_S2, fe_co_specific)
    density = registry.get("vacoflux_50").value("density_kg_m3")
    rows: list[dict[str, object]] = []
    for element_mass in ELEMENT_MASSES_KG:
        geometry = sphere_geometry(mass_kg=element_mass, density_kg_m3=density)
        aperture = evaluate_aperture(
            rotor_radius_m=geometry.radius_m,
            clearance_factor=CLEARANCE_FACTOR,
            navigation_margin_m=NAVIGATION_MARGIN_M,
        )
        quadrupole = evaluate_quadrupole(
            gradient_t_m=gradient,
            aperture_radius_m=aperture.aperture_radius_m,
            operating_offset_m=(OPERATING_OFFSET_FRACTION * aperture.aperture_radius_m),
        )
        rows.append(
            {
                "element_mass_g": element_mass * 1000.0,
                "specific_magnetic_moment_a_m2_kg": fe_co_specific,
                "required_gradient_t_m": gradient,
                "rotor_radius_m": geometry.radius_m,
                "clearance_factor": CLEARANCE_FACTOR,
                "navigation_margin_m": NAVIGATION_MARGIN_M,
                "aperture_radius_m": aperture.aperture_radius_m,
                "navigation_floor_active": aperture.navigation_floor_active,
                "operating_offset_m": quadrupole.operating_offset_m,
                "operating_field_t": quadrupole.operating_field_t,
                "pole_tip_field_t": quadrupole.aperture_edge_field_t,
                "aperture_edge_pressure_pa": quadrupole.aperture_edge_pressure_pa,
                "aperture_field_energy_per_length_j_m": quadrupole.aperture_field_energy_per_length_j_m,
                "fidelity": quadrupole.fidelity,
                "geometry_fidelity": geometry.fidelity,
                "aperture_fidelity": aperture.fidelity,
                "assumptions": " | ".join(
                    geometry.assumptions + aperture.assumptions + quadrupole.assumptions
                ),
                "warnings": " | ".join(
                    geometry.warnings + aperture.warnings + quadrupole.warnings
                ),
            }
        )
    return pd.DataFrame(rows)


def _concept_rows(
    scenario: Scenario, registry: MaterialRegistry
) -> list[dict[str, object]]:
    benchmark_gradient = registry.get("mqxf_benchmark").value("nominal_gradient_t_m")
    demand = _demand(scenario, node_count=96, element_mass_kg=0.05)
    target_acceleration = 1000.0 * G0_M_S2
    fe_co = evaluate_saturated_ferromagnet(
        registry,
        material_identifier="vacoflux_50",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=0.8,
        utilization_factor=0.7,
        required_acceleration_m_s2=target_acceleration,
        available_gradient_t_m=benchmark_gradient,
    )
    permanent = evaluate_permanent_magnet(
        registry,
        material_identifier="vacodym_902_tp",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=1.0,
        utilization_factor=0.85,
        required_acceleration_m_s2=target_acceleration,
        available_gradient_t_m=benchmark_gradient,
    )
    ferrite = evaluate_saturated_ferromagnet(
        registry,
        material_identifier="tdk_n87",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=1.0,
        utilization_factor=0.65,
        required_acceleration_m_s2=target_acceleration,
        available_gradient_t_m=benchmark_gradient,
        polarization_property="reference_flux_density_t",
    )
    conductor_length = 2.0 * 3.141592653589793 * 0.01 * 100
    conductor_mass = conductor_length * rebco_tape_mass_per_length_kg_m(registry)
    superconducting = evaluate_persistent_current_loop(
        registry,
        loop_mean_radius_m=0.01,
        turns=100,
        operating_current_a=80.0,
        support_mass_kg=0.05 - conductor_mass,
        operating_temperature_k=77.0,
        external_field_t=1.0,
        external_field_orientation="perpendicular-to-tape",
        effective_conductor_radius_m=0.0005,
        required_acceleration_m_s2=target_acceleration,
        available_gradient_t_m=benchmark_gradient,
    )
    concepts: list[tuple[object, float, str]] = [
        (
            fe_co,
            fe_co.characteristic_radius_m,
            "classical eddy/ripple comparison; hysteresis unresolved",
        ),
        (
            permanent,
            permanent.characteristic_radius_m,
            "temperature and demagnetization load line unresolved",
        ),
        (
            ferrite,
            ferrite.characteristic_radius_m,
            "classical eddy comparison; manufacturer loss not extrapolated",
        ),
    ]
    sc_geometry = loop_envelope_geometry(
        total_mass_kg=superconducting.total_rotor_mass_kg,
        effective_density_kg_m3=5000.0,
        loop_mean_radius_m=superconducting.loop_mean_radius_m,
        radial_build_m=0.001,
    )
    concepts.append(
        (
            superconducting,
            sc_geometry.radius_m,
            "REBCO in-field Ic and external-field AC loss unresolved",
        )
    )
    rows: list[dict[str, object]] = []
    for concept, radius, loss_status in concepts:
        aperture = evaluate_aperture(
            rotor_radius_m=radius,
            clearance_factor=CLEARANCE_FACTOR,
            navigation_margin_m=NAVIGATION_MARGIN_M,
        )
        quadrupole = evaluate_quadrupole(
            gradient_t_m=concept.required_gradient_t_m,
            aperture_radius_m=aperture.aperture_radius_m,
            operating_offset_m=OPERATING_OFFSET_FRACTION * aperture.aperture_radius_m,
        )
        guide_at_benchmark = solve_guide_length_for_acceleration(
            demand, concept.available_acceleration_m_s2
        )
        demag_scale = getattr(concept, "demagnetizing_field_scale_t", None)
        current_supported = getattr(concept, "current_source_condition_supported", True)
        rows.append(
            {
                "concept": concept.concept,
                "fidelity": concept.fidelity,
                "material_identifier": concept.material_identifier,
                "element_mass_g": (
                    (
                        concept.element_mass_kg
                        if hasattr(concept, "element_mass_kg")
                        else concept.total_rotor_mass_kg
                    )
                    * 1000.0
                ),
                "characteristic_radius_m": radius,
                "magnetic_moment_a_m2": concept.magnetic_moment_a_m2,
                "specific_magnetic_moment_a_m2_kg": concept.specific_magnetic_moment_a_m2_kg,
                "gradient_for_1000g0_t_m": concept.required_gradient_t_m,
                "available_acceleration_at_mqxf_gradient_g0": concept.available_acceleration_m_s2
                / G0_M_S2,
                "guide_length_at_mqxf_gradient_m": guide_at_benchmark.physical_guide_length_m,
                "aperture_radius_m": aperture.aperture_radius_m,
                "navigation_floor_active": aperture.navigation_floor_active,
                "pole_tip_field_for_1000g0_t": quadrupole.aperture_edge_field_t,
                "magnetic_pressure_scale_pa": quadrupole.aperture_edge_pressure_pa,
                "aperture_field_energy_per_length_j_m": quadrupole.aperture_field_energy_per_length_j_m,
                "demagnetizing_field_scale_t": demag_scale,
                "pole_tip_to_demagnetizing_scale": (
                    None
                    if demag_scale is None
                    else quadrupole.aperture_edge_field_t / demag_scale
                ),
                "demagnetization_scale_flag": (
                    "not-applicable"
                    if demag_scale is None
                    else (
                        "pole-tip-exceeds-mu0-HcJ-scale"
                        if quadrupole.aperture_edge_field_t >= demag_scale
                        else "below-mu0-HcJ-scale"
                    )
                ),
                "source_condition_supported": getattr(
                    concept, "source_condition_supported", current_supported
                ),
                "loss_model_status": loss_status,
                "field_model_fidelity": quadrupole.fidelity,
                "aperture_model_fidelity": aperture.fidelity,
                "assumptions": " | ".join(
                    concept.assumptions + aperture.assumptions + quadrupole.assumptions
                ),
                "warnings": " | ".join(
                    concept.warnings + aperture.warnings + quadrupole.warnings
                ),
            }
        )
    return rows


def rotor_concept_comparison_table(
    scenario: Scenario, registry: MaterialRegistry
) -> pd.DataFrame:
    return pd.DataFrame(_concept_rows(scenario, registry))


def ripple_loss_table(scenario: Scenario, registry: MaterialRegistry) -> pd.DataFrame:
    demand = _demand(scenario, node_count=96, element_mass_kg=0.05)
    rows: list[dict[str, object]] = []
    cases = (
        ("vacoflux_50", 0.001, 1.0),
        ("tdk_n87", 0.0005, registry.get("tdk_n87").value("initial_permeability")),
    )
    for material, thickness, relative_permeability in cases:
        for pitch in RIPPLE_PITCHES_M:
            result = evaluate_ripple_loss(
                registry,
                material_identifier=material,
                guide_relative_speed_m_s=demand.representative_guide_relative_speed_m_s,
                longitudinal_pitch_m=pitch,
                ripple_flux_density_amplitude_t=0.01,
                section_thickness_m=thickness,
                relative_permeability=relative_permeability,
            )
            row = asdict(result)
            row["assumptions"] = " | ".join(result.assumptions)
            row["warnings"] = " | ".join(result.warnings)
            rows.append(row)
    tape = registry.get("superpower_ap_4mm")
    tape_thickness = tape.value("substrate_thickness_m") + tape.value(
        "total_copper_thickness_m"
    )
    for pitch in RIPPLE_PITCHES_M:
        rows.append(
            {
                "fidelity": "LOSS-L1",
                "material_identifier": "superpower_ap_4mm",
                "guide_relative_speed_m_s": demand.representative_guide_relative_speed_m_s,
                "longitudinal_pitch_m": pitch,
                "ripple_frequency_hz": ripple_frequency_hz(
                    demand.representative_guide_relative_speed_m_s, pitch
                ),
                "ripple_flux_density_amplitude_t": 0.01,
                "section_thickness_m": tape_thickness,
                "electrical_resistivity_ohm_m": None,
                "relative_permeability": None,
                "skin_depth_m": None,
                "thickness_to_skin_depth_ratio": None,
                "classical_eddy_loss_density_w_m3": None,
                "thin_section_valid": None,
                "source_frequency_domain_supported": False,
                "assumptions": "Ripple frequency is reported without an REBCO loss model.",
                "warnings": (
                    "Detailed REBCO external-field AC loss is unresolved; "
                    "no loss is inferred from the 77 K self-field current range."
                ),
            }
        )
    return pd.DataFrame(rows)


def conductive_loop_table(
    scenario: Scenario, registry: MaterialRegistry
) -> pd.DataFrame:
    demand = _demand(scenario, node_count=96, element_mass_kg=0.05)
    rows: list[dict[str, object]] = []
    for conductor in ("copper_c10810", "aluminum_1050_o"):
        for pitch in RIPPLE_PITCHES_M:
            result = evaluate_conductive_loop(
                registry,
                conductor_identifier=conductor,
                loop_radius_m=0.005,
                conductor_radius_m=0.0005,
                guide_relative_speed_m_s=demand.representative_guide_relative_speed_m_s,
                longitudinal_pitch_m=pitch,
                ripple_flux_density_amplitude_t=0.01,
            )
            row = asdict(result)
            row["assumptions"] = " | ".join(result.assumptions)
            row["warnings"] = " | ".join(result.warnings)
            rows.append(row)
    return pd.DataFrame(rows)


def small_element_limit_table(
    scenario: Scenario, registry: MaterialRegistry
) -> pd.DataFrame:
    benchmark_gradient = registry.get("mqxf_benchmark").value("nominal_gradient_t_m")
    material = registry.get("vacoflux_50")
    density = material.value("density_kg_m3")
    reference_concept = evaluate_saturated_ferromagnet(
        registry,
        material_identifier="vacoflux_50",
        element_mass_kg=0.05,
        magnetic_material_mass_fraction=0.8,
        utilization_factor=0.7,
        required_acceleration_m_s2=1000.0 * G0_M_S2,
        available_gradient_t_m=benchmark_gradient,
    )
    specific_moment = reference_concept.specific_magnetic_moment_a_m2_kg
    gradient = reference_concept.required_gradient_t_m
    rows: list[dict[str, object]] = []
    for mass in ELEMENT_MASSES_KG:
        demand = _demand(scenario, node_count=96, element_mass_kg=mass)
        geometry = sphere_geometry(mass_kg=mass, density_kg_m3=density)
        packing = evaluate_stream_packing(
            rotor_longitudinal_envelope_m=geometry.longitudinal_envelope_m,
            guide_frame_spacing_m=demand.guide_frame_element_spacing_m,
            required_surface_gap_factor=REQUIRED_SURFACE_GAP_FACTOR,
        )
        aperture = evaluate_aperture(
            rotor_radius_m=geometry.radius_m,
            clearance_factor=CLEARANCE_FACTOR,
            navigation_margin_m=NAVIGATION_MARGIN_M,
        )
        quadrupole = evaluate_quadrupole(
            gradient_t_m=gradient,
            aperture_radius_m=aperture.aperture_radius_m,
            operating_offset_m=OPERATING_OFFSET_FRACTION * aperture.aperture_radius_m,
        )
        moment = specific_moment * mass
        guide_force = mass * 1000.0 * G0_M_S2
        coupling = evaluate_neighbor_coupling(
            magnetic_moment_a_m2=moment,
            center_spacing_m=demand.guide_frame_element_spacing_m,
            rotor_characteristic_radius_m=geometry.radius_m,
            guide_force_n=guide_force,
            guide_operating_field_t=quadrupole.operating_field_t,
            magnetic_state="soft-ferromagnet guide-magnetized worst case",
        )
        rows.append(
            {
                "element_mass_g": mass * 1000.0,
                "kinetic_energy_per_element_j": 0.5
                * mass
                * demand.inertial_rotor_speed_m_s**2,
                "force_per_element_at_1000g0_n": guide_force,
                "specific_magnetic_moment_a_m2_kg": specific_moment,
                "magnetic_moment_a_m2": moment,
                "required_gradient_at_1000g0_t_m": gradient,
                "guide_frame_spacing_m": demand.guide_frame_element_spacing_m,
                "rotor_diameter_m": geometry.longitudinal_envelope_m,
                "packing_ratio": packing.packing_ratio,
                "required_center_separation_m": packing.required_center_separation_m,
                "separation_margin_m": packing.separation_margin_m,
                "infeasible_overlap": packing.infeasible_overlap,
                "aperture_radius_m": aperture.aperture_radius_m,
                "navigation_floor_active": aperture.navigation_floor_active,
                "pole_tip_field_t": quadrupole.aperture_edge_field_t,
                "aperture_field_energy_per_length_j_m": quadrupole.aperture_field_energy_per_length_j_m,
                "neighbor_field_t": coupling.nearest_neighbor_field_t,
                "neighbor_force_n": coupling.nearest_neighbor_force_n,
                "neighbor_force_fraction_of_guide": coupling.force_fraction_of_guide,
                "neighbor_field_fraction_of_operating": coupling.field_fraction_of_guide,
                "separation_to_diameter_ratio": coupling.separation_to_diameter_ratio,
                "point_dipole_valid": coupling.point_dipole_valid,
                "geometry_fidelity": geometry.fidelity,
                "packing_fidelity": packing.fidelity,
                "coupling_fidelity": coupling.fidelity,
                "assumptions": " | ".join(
                    geometry.assumptions
                    + packing.assumptions
                    + aperture.assumptions
                    + quadrupole.assumptions
                    + coupling.assumptions
                ),
                "warnings": " | ".join(
                    geometry.warnings
                    + packing.warnings
                    + aperture.warnings
                    + quadrupole.warnings
                    + coupling.warnings
                ),
                "coupling_warning": " | ".join(coupling.warnings),
            }
        )
    return pd.DataFrame(rows)


def source_registry_table(registry: MaterialRegistry) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for identifier in registry.identifiers:
        record = registry.get(identifier)
        for property_name, prop in record.properties.items():
            rows.append(
                {
                    "material_identifier": identifier,
                    "category": record.category,
                    "material": record.material,
                    "grade": record.grade,
                    "property_name": property_name,
                    "value": prop.value,
                    "unit": prop.unit,
                    "temperature": prop.temperature,
                    "field_condition": prop.field_condition,
                    "source_organization": record.source_organization,
                    "source_title": record.source_title,
                    "source_url": record.source_url,
                    "publication_date": record.publication_date,
                    "accessed_date": record.accessed_date,
                    "notes": prop.notes,
                }
            )
    return pd.DataFrame(rows)


def generate_or2_evidence(
    scenario_path: str | Path, output_directory: str | Path
) -> Path:
    scenario = load_scenario(scenario_path)
    registry = load_material_registry()

    # Capture source provenance before any output writes, matching OR-1.1B.
    reference_scenario = _scenario(scenario, node_count=96, element_mass_kg=0.05)
    reference = evaluate_scenario(reference_scenario)
    reference_demand = build_guide_demand(reference_scenario, reference)

    tables = {
        "magnetic-demand-scaling.csv": magnetic_demand_scaling_table(scenario),
        "guide-length-inversion.csv": guide_length_inversion_table(scenario),
        "node-count-magnetic-scaling.csv": node_count_magnetic_scaling_table(scenario),
        "specific-moment-gradient-map.csv": specific_moment_gradient_table(),
        "maxwell-pressure-bounds.csv": maxwell_pressure_table(),
        "rotor-concept-comparison.csv": rotor_concept_comparison_table(
            scenario, registry
        ),
        "aperture-field-energy.csv": aperture_field_energy_table(scenario, registry),
        "ripple-loss-map.csv": ripple_loss_table(scenario, registry),
        "conductive-loop-benchmark.csv": conductive_loop_table(scenario, registry),
        "small-element-limit.csv": small_element_limit_table(scenario, registry),
        "source-registry.csv": source_registry_table(registry),
    }
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    for filename, frame in tables.items():
        frame.to_csv(output / filename, index=False)

    manifest = asdict(reference.manifest)
    manifest.update(
        {
            "evidence_kind": "OR-2 M0/M1 magnetic feasibility studies",
            "magnetic_fidelity_labels": [
                "M0-PRESSURE",
                "M1-GUIDE-KINEMATICS",
                "M1-QUADRUPOLE",
                "M1-DIPOLE",
                "M1-FERRO",
                "M1-PM",
                "M1-SCLOOP",
                "M1-INDUCTIVE",
                "M1-GEOMETRY",
                "M1-APERTURE",
                "M1-PACKING",
                "M1-DIPOLE-COUPLING",
                "LOSS-L1",
            ],
            "material_registry_version": registry.version,
            "material_registry_path": "data/materials/registry.json",
            "evidence_files": list(tables),
            "study_matrix": {
                "primary_node_counts": list(PRIMARY_NODE_COUNTS),
                "scaling_node_counts": list(SCALING_NODE_COUNTS),
                "element_masses_kg": list(ELEMENT_MASSES_KG),
                "accelerations_g0": list(ACCELERATION_G0),
                "specific_moments_a_m2_kg": list(SPECIFIC_MOMENTS_A_M2_KG),
                "ripple_pitches_m": list(RIPPLE_PITCHES_M),
                "target_guide_lengths_m": list(TARGET_GUIDE_LENGTHS_M),
            },
            "study_assumptions": {
                "clearance_factor": CLEARANCE_FACTOR,
                "navigation_margin_m": NAVIGATION_MARGIN_M,
                "operating_offset_fraction_of_aperture": OPERATING_OFFSET_FRACTION,
                "required_surface_gap_factor_of_envelope": REQUIRED_SURFACE_GAP_FACTOR,
                "ripple_flux_density_amplitude_t": 0.01,
                "fe_co_mass_fraction": 0.8,
                "fe_co_utilization": 0.7,
                "permanent_magnet_mass_fraction": 1.0,
                "permanent_magnet_utilization": 0.85,
                "ferrite_mass_fraction": 1.0,
                "ferrite_utilization": 0.65,
                "concept_comparison_element_mass_kg": 0.05,
                "superconducting_loop_radius_m": 0.01,
                "superconducting_loop_turns": 100,
                "superconducting_loop_current_a": 80.0,
                "superconducting_loop_temperature_k": 77.0,
                "superconducting_loop_external_field_t": 1.0,
                "superconducting_loop_external_field_orientation": "perpendicular-to-tape",
                "superconducting_loop_effective_conductor_radius_m": 0.0005,
                "superconducting_loop_effective_envelope_density_kg_m3": 5000.0,
                "conductive_loop_radius_m": 0.005,
                "conductive_loop_conductor_radius_m": 0.0005,
                "vacoflux_ripple_section_thickness_m": 0.001,
                "vacoflux_ripple_relative_permeability": 1.0,
                "n87_ripple_section_thickness_m": 0.0005,
                "n87_ripple_relative_permeability": registry.get("tdk_n87").value(
                    "initial_permeability"
                ),
                "mqxf_gradient_t_m": registry.get("mqxf_benchmark").value(
                    "nominal_gradient_t_m"
                ),
            },
            "guide_demand_adapter": asdict(reference_demand),
        }
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8"
    )

    demand = tables["magnetic-demand-scaling.csv"]
    demand_summary = demand[(demand["element_mass_g"] == 50.0)][
        [
            "node_count",
            "target_acceleration_g0",
            "physical_guide_length_m",
            "force_per_element_n",
            "net_impulse_per_element_n_s",
            "interaction_time_s",
            "node_mean_force_n",
            "node_mean_force_relative_error",
            "fidelity",
        ]
    ].reset_index(drop=True)
    length_summary = tables["guide-length-inversion.csv"][
        [
            "node_count",
            "target_physical_guide_length_m",
            "required_acceleration_g0",
            "required_force_per_50g_element_n",
            "interaction_time_s",
            "node_mean_force_n",
            "mode",
            "fidelity",
        ]
    ]
    node_summary = tables["node-count-magnetic-scaling.csv"][
        [
            "node_count",
            "turn_angle_rad",
            "delta_v_m_s",
            "guide_length_at_1000g0_m",
            "force_per_50g_element_n",
            "net_impulse_per_50g_element_n_s",
            "node_mean_force_n",
            "fidelity",
        ]
    ]
    gradient = tables["specific-moment-gradient-map.csv"]
    mass_cancel = gradient[
        (gradient["target_acceleration_g0"] == 1000.0)
        & (gradient["specific_magnetic_moment_a_m2_kg"] == 100.0)
    ][
        [
            "target_acceleration_g0",
            "specific_magnetic_moment_a_m2_kg",
            "element_mass_g",
            "magnetic_moment_a_m2",
            "force_per_element_n",
            "required_gradient_t_m",
            "recovered_acceleration_m_s2",
            "gradient_mass_independent_at_fixed_specific_moment",
        ]
    ].reset_index(drop=True)
    maxwell_summary = tables["maxwell-pressure-bounds.csv"][
        [
            "fidelity",
            "field_t",
            "magnetic_pressure_pa",
            "field_energy_density_j_m3",
            "requested_force_n",
            "ideal_interaction_area_m2",
        ]
    ]
    concept_summary = tables["rotor-concept-comparison.csv"][
        [
            "concept",
            "fidelity",
            "material_identifier",
            "element_mass_g",
            "specific_magnetic_moment_a_m2_kg",
            "gradient_for_1000g0_t_m",
            "available_acceleration_at_mqxf_gradient_g0",
            "guide_length_at_mqxf_gradient_m",
            "aperture_radius_m",
            "pole_tip_field_for_1000g0_t",
            "aperture_field_energy_per_length_j_m",
            "demagnetization_scale_flag",
            "source_condition_supported",
            "loss_model_status",
        ]
    ]
    aperture_summary = tables["aperture-field-energy.csv"][
        [
            "element_mass_g",
            "required_gradient_t_m",
            "rotor_radius_m",
            "aperture_radius_m",
            "navigation_floor_active",
            "pole_tip_field_t",
            "aperture_field_energy_per_length_j_m",
        ]
    ]
    ripple_summary = tables["ripple-loss-map.csv"][
        [
            "material_identifier",
            "longitudinal_pitch_m",
            "ripple_frequency_hz",
            "ripple_flux_density_amplitude_t",
            "skin_depth_m",
            "thickness_to_skin_depth_ratio",
            "classical_eddy_loss_density_w_m3",
            "thin_section_valid",
            "source_frequency_domain_supported",
        ]
    ]
    conductive_summary = tables["conductive-loop-benchmark.csv"][
        [
            "conductor_identifier",
            "ripple_frequency_hz",
            "resistance_ohm",
            "inductance_h",
            "induced_emf_amplitude_v",
            "current_amplitude_a",
            "average_joule_power_w",
            "loop_formula_valid",
        ]
    ]
    small_summary = tables["small-element-limit.csv"][
        [
            "element_mass_g",
            "kinetic_energy_per_element_j",
            "force_per_element_at_1000g0_n",
            "required_gradient_at_1000g0_t_m",
            "guide_frame_spacing_m",
            "rotor_diameter_m",
            "packing_ratio",
            "infeasible_overlap",
            "aperture_radius_m",
            "navigation_floor_active",
            "pole_tip_field_t",
            "neighbor_force_fraction_of_guide",
            "separation_to_diameter_ratio",
            "point_dipole_valid",
        ]
    ]
    report = f"""# OR-2 magnetic rotor and guide feasibility evidence

Scenario: `{scenario.scenario_id}`

Configuration hash: `{reference.manifest.configuration_hash}`

Source commit at generation: `{reference.manifest.source_commit}`

Source worktree dirty at generation: `{reference.manifest.source_worktree_dirty}`

Material registry version: `{registry.version}`

OR-2 consumes accepted OR-1.1 output through an immutable `GuideDemand`. No
magnetic model calls the ballistic solver or duplicates orbital equations.
The 1000-g0 guide remains a regression point, not a fixed capability.

## Reference magnetic demand

The full bounded matrix covers N=96/960, ten element masses from 1000 g to
0.1 g, and six acceleration points. The 50-g slice is shown here.

{dataframe_to_markdown(demand_summary)}

## Length-driven guide inversion

{dataframe_to_markdown(length_summary)}

## Node-count scaling

{dataframe_to_markdown(node_summary)}

## Specific moment and gradient

At fixed specific magnetic moment, moment and force scale with element mass,
but `G = a/(mu/m)` does not. The 100 A m2/kg, 1000-g0 regression is:

{dataframe_to_markdown(mass_cancel)}

The complete acceleration/specific-moment/mass map is in
`specific-moment-gradient-map.csv`.

## M0 Maxwell-pressure bounds

{dataframe_to_markdown(maxwell_summary)}

These are absolute pressure/energy-density scales, never a rotor force law.

## Rotor-concept comparison

{dataframe_to_markdown(concept_summary)}

No concept is ranked as best because critical thermal, structural, control,
and loss models remain unresolved. The MQXF gradient is an external scale,
not a mass-feasibility claim.

## Aperture and field energy

{dataframe_to_markdown(aperture_summary)}

The gradient stays fixed for the common Fe-Co specific moment. Smaller rotors
reduce aperture, pole-tip field, and ideal aperture energy until the 5-mm
navigation floor becomes active.

## Longitudinal ripple and loss

{dataframe_to_markdown(ripple_summary)}

## Conductive R-L loop benchmark

{dataframe_to_markdown(conductive_summary)}

The smooth transverse gradient is separate from longitudinal ripple. Detailed
REBCO external-field AC loss remains explicitly unresolved.

## Small-element packing and coupling

{dataframe_to_markdown(small_summary)}

Smaller elements reduce per-element force and kinetic energy, but increase
frequency and reduce spacing. Gradient remains mass-independent at fixed
specific moment; the navigation floor limits aperture benefits, while packing
and neighbor coupling eventually worsen. Point-dipole rows outside their
separation validity domain are warnings, not trusted predictions.

## Source registry

The complete flattened registry is in `source-registry.csv`; human-readable
source boundaries are documented in `MAGNETIC_SOURCES.md`.

## Remaining limits and OR-3 recommendation

OR-2 omits 3-D FEM, real coil/yoke geometry, stress support, finite guide ends,
detailed REBCO in-field current and AC loss, persistent joints, cryogenics,
quench protection, thermal rejection, magnet/rotor fatigue, active alignment,
navigation dynamics, collective stream dynamics, and global optimization.

OR-3 should validate one or two non-ranked concept envelopes with a 2-D/3-D
field-and-force model, measured in-field material curves, thermal/loss budgets,
mechanical stress/containment, finite-length end fields, and a local
alignment/navigation controller before any system-level optimization.
"""
    report_path = output / "OR-2-EVIDENCE.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path
