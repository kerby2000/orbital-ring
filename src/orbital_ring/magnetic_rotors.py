"""Source-backed M1 magnetic rotor concept models."""

from __future__ import annotations

import math

from orbital_ring.magnetic_field import (
    MU_0_H_M,
    available_acceleration_m_s2,
    required_gradient_t_m,
)
from orbital_ring.magnetic_geometry import sphere_geometry
from orbital_ring.magnetic_results import PersistentLoopResult, RotorConceptResult
from orbital_ring.materials import MaterialRegistry


def _validate_fraction(name: str, value: float) -> None:
    if not 0.0 < value <= 1.0:
        raise ValueError(f"{name} must lie in (0, 1]")


def evaluate_saturated_ferromagnet(
    registry: MaterialRegistry,
    *,
    material_identifier: str,
    element_mass_kg: float,
    magnetic_material_mass_fraction: float,
    utilization_factor: float,
    required_acceleration_m_s2: float,
    available_gradient_t_m: float,
    polarization_property: str = "saturation_polarization_t",
) -> RotorConceptResult:
    """Saturated-moment upper bound mu = eta (J/mu0) V."""

    if element_mass_kg <= 0.0:
        raise ValueError("element mass must be positive")
    _validate_fraction(
        "magnetic material mass fraction", magnetic_material_mass_fraction
    )
    _validate_fraction("utilization factor", utilization_factor)
    material = registry.get(material_identifier)
    density = material.value("density_kg_m3")
    polarization = material.value(polarization_property)
    magnetic_mass = element_mass_kg * magnetic_material_mass_fraction
    magnetic_volume = magnetic_mass / density
    saturation_magnetization = polarization / MU_0_H_M
    moment = utilization_factor * saturation_magnetization * magnetic_volume
    specific = moment / element_mass_kg
    geometry = sphere_geometry(mass_kg=element_mass_kg, density_kg_m3=density)
    warnings = [
        "The source polarization does not guarantee saturation for the selected rotor shape and applied field.",
        "Demagnetization, hysteresis, stress, containment, and thermal rejection are not solved.",
    ]
    if polarization_property != "saturation_polarization_t":
        warnings.append(
            "The selected reference flux density is used as a moment surrogate, not a proven saturation magnetization."
        )
    return RotorConceptResult(
        fidelity="M1-FERRO",
        concept="saturated-soft-ferromagnet",
        material_identifier=material_identifier,
        element_mass_kg=element_mass_kg,
        magnetic_material_mass_fraction=magnetic_material_mass_fraction,
        utilization_factor=utilization_factor,
        magnetic_volume_m3=magnetic_volume,
        magnetic_moment_a_m2=moment,
        specific_magnetic_moment_a_m2_kg=specific,
        characteristic_radius_m=geometry.radius_m,
        required_gradient_t_m=required_gradient_t_m(
            required_acceleration_m_s2, specific
        ),
        available_acceleration_m_s2=available_acceleration_m_s2(
            specific, available_gradient_t_m
        ),
        demagnetizing_field_scale_t=None,
        temperature_warning_threshold_c=None,
        source_condition_supported=(
            polarization_property == "saturation_polarization_t"
        ),
        assumptions=(
            "Magnetic material volume is mass fraction times total mass divided by source density.",
            "Moment equals utilization times source polarization/mu0 times magnetic volume.",
            "The rotor envelope is represented by an equal-density sphere.",
        ),
        warnings=tuple(warnings),
    )


def evaluate_permanent_magnet(
    registry: MaterialRegistry,
    *,
    material_identifier: str,
    element_mass_kg: float,
    magnetic_material_mass_fraction: float,
    utilization_factor: float,
    required_acceleration_m_s2: float,
    available_gradient_t_m: float,
) -> RotorConceptResult:
    """Permanent-dipole moment from remanence with explicit utilization."""

    if element_mass_kg <= 0.0:
        raise ValueError("element mass must be positive")
    _validate_fraction(
        "magnetic material mass fraction", magnetic_material_mass_fraction
    )
    _validate_fraction("utilization factor", utilization_factor)
    material = registry.get(material_identifier)
    density = material.value("density_kg_m3")
    remanence = material.value("remanence_t")
    magnetic_volume = element_mass_kg * magnetic_material_mass_fraction / density
    moment = utilization_factor * (remanence / MU_0_H_M) * magnetic_volume
    specific = moment / element_mass_kg
    geometry = sphere_geometry(mass_kg=element_mass_kg, density_kg_m3=density)
    coercivity_scale = MU_0_H_M * material.value("intrinsic_coercivity_a_m")
    temperature_threshold = material.value("consult_manufacturer_above_temperature_c")
    return RotorConceptResult(
        fidelity="M1-PM",
        concept="permanent-magnet-dipole",
        material_identifier=material_identifier,
        element_mass_kg=element_mass_kg,
        magnetic_material_mass_fraction=magnetic_material_mass_fraction,
        utilization_factor=utilization_factor,
        magnetic_volume_m3=magnetic_volume,
        magnetic_moment_a_m2=moment,
        specific_magnetic_moment_a_m2_kg=specific,
        characteristic_radius_m=geometry.radius_m,
        required_gradient_t_m=required_gradient_t_m(
            required_acceleration_m_s2, specific
        ),
        available_acceleration_m_s2=available_acceleration_m_s2(
            specific, available_gradient_t_m
        ),
        demagnetizing_field_scale_t=coercivity_scale,
        temperature_warning_threshold_c=temperature_threshold,
        source_condition_supported=True,
        assumptions=(
            "Moment equals utilization times Br/mu0 times magnetic material volume.",
            "The rotor is adiabatically aligned and represented by an equal-density sphere.",
        ),
        warnings=(
            "The mu0*HcJ comparison is only a field scale; it is not a load-line demagnetization analysis.",
            f"Consult the manufacturer above {temperature_threshold:g} degC; this is not a guaranteed grade maximum.",
            "Radiation, fatigue, coating, containment, and temperature rise are unresolved.",
        ),
    )


def rebco_tape_mass_per_length_kg_m(registry: MaterialRegistry) -> float:
    tape = registry.get("superpower_ap_4mm")
    width = tape.value("width_m")
    substrate = tape.value("substrate_thickness_m")
    copper = tape.value("total_copper_thickness_m")
    return width * (
        substrate * registry.get("hastelloy_c276").value("density_kg_m3")
        + copper * registry.get("copper_c10810").value("density_kg_m3")
    )


def circular_loop_inductance_h(
    *, loop_radius_m: float, effective_conductor_radius_m: float, turns: int
) -> tuple[float | None, bool]:
    """Thin circular-loop approximation with R/a >= 10 validity gate."""

    if loop_radius_m <= 0.0 or effective_conductor_radius_m <= 0.0:
        raise ValueError("loop and conductor radii must be positive")
    if turns <= 0:
        raise ValueError("turn count must be positive")
    ratio = loop_radius_m / effective_conductor_radius_m
    if ratio <= math.e / 8.0:
        return None, False
    inductance = MU_0_H_M * turns**2 * loop_radius_m * (math.log(8.0 * ratio) - 2.0)
    return inductance, ratio >= 10.0


def evaluate_persistent_current_loop(
    registry: MaterialRegistry,
    *,
    loop_mean_radius_m: float,
    turns: int,
    operating_current_a: float,
    support_mass_kg: float,
    operating_temperature_k: float,
    external_field_t: float,
    external_field_orientation: str,
    effective_conductor_radius_m: float,
    required_acceleration_m_s2: float,
    available_gradient_t_m: float,
) -> PersistentLoopResult:
    if loop_mean_radius_m <= 0.0 or turns <= 0 or operating_current_a <= 0.0:
        raise ValueError("loop radius, turns, and current must be positive")
    if support_mass_kg < 0.0:
        raise ValueError("support mass cannot be negative")
    tape = registry.get("superpower_ap_4mm")
    conductor_length = 2.0 * math.pi * loop_mean_radius_m * turns
    conductor_mass = conductor_length * rebco_tape_mass_per_length_kg_m(registry)
    total_mass = conductor_mass + support_mass_kg
    moment = turns * operating_current_a * math.pi * loop_mean_radius_m**2
    specific = moment / total_mass
    inductance, loop_valid = circular_loop_inductance_h(
        loop_radius_m=loop_mean_radius_m,
        effective_conductor_radius_m=effective_conductor_radius_m,
        turns=turns,
    )
    self_field_supported = (
        math.isclose(operating_temperature_k, 77.0, abs_tol=1.0e-9)
        and math.isclose(external_field_t, 0.0, abs_tol=1.0e-12)
        and external_field_orientation == "self-field"
    )
    current_margin = None
    warnings = [
        "Tape mass includes sourced substrate and copper only; REBCO, silver, insulation, joints, and terminals are omitted.",
        "Persistent-joint feasibility, rotor cryogenics, quench propagation, and external-field AC loss are unresolved.",
    ]
    if self_field_supported:
        critical_current = tape.value("critical_current_min_a")
        current_margin = (critical_current - operating_current_a) / critical_current
        if current_margin < 0.0:
            warnings.append(
                "Operating current exceeds the sourced minimum self-field critical current."
            )
    else:
        warnings.append(
            "Requested current condition is outside the tabulated 77 K self-field point; no critical-current margin is inferred."
        )
    if 2.0 * loop_mean_radius_m < tape.value("minimum_bending_diameter_m"):
        warnings.append(
            "Loop diameter is below the sourced 77 K minimum bending diameter."
        )
        loop_valid = False
    if not loop_valid:
        warnings.append(
            "Thin circular-loop inductance approximation is outside R/a >= 10 validity."
        )
    return PersistentLoopResult(
        fidelity="M1-SCLOOP",
        concept="persistent-current-REBCO-loop",
        material_identifier="superpower_ap_4mm",
        loop_mean_radius_m=loop_mean_radius_m,
        turns=turns,
        operating_current_a=operating_current_a,
        conductor_length_m=conductor_length,
        conductor_mass_kg=conductor_mass,
        support_mass_kg=support_mass_kg,
        total_rotor_mass_kg=total_mass,
        magnetic_moment_a_m2=moment,
        specific_magnetic_moment_a_m2_kg=specific,
        required_gradient_t_m=required_gradient_t_m(
            required_acceleration_m_s2, specific
        ),
        available_acceleration_m_s2=available_acceleration_m_s2(
            specific, available_gradient_t_m
        ),
        approximate_inductance_h=inductance,
        stored_magnetic_energy_j=(
            None if inductance is None else 0.5 * inductance * operating_current_a**2
        ),
        critical_current_margin_fraction=current_margin,
        current_source_condition_supported=self_field_supported,
        loop_formula_valid=loop_valid,
        assumptions=(
            "All turns share one mean radius and carry the prescribed persistent current.",
            "Moment is N I A; conductor length is 2 pi R N.",
            "Support mass is a study input and includes no detailed cryogenic system.",
        ),
        warnings=tuple(warnings),
    )
