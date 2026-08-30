"""OR-2 rotor envelopes, aperture floor, packing, and neighbor coupling."""

from __future__ import annotations

import math

from orbital_ring.magnetic_field import MU_0_H_M
from orbital_ring.magnetic_results import (
    ApertureResult,
    NeighborCouplingResult,
    PackingResult,
    RotorGeometryResult,
)


def sphere_geometry(*, mass_kg: float, density_kg_m3: float) -> RotorGeometryResult:
    if mass_kg <= 0.0 or density_kg_m3 <= 0.0:
        raise ValueError("mass and density must be positive")
    volume = mass_kg / density_kg_m3
    radius = (3.0 * volume / (4.0 * math.pi)) ** (1.0 / 3.0)
    return RotorGeometryResult(
        fidelity="M1-GEOMETRY",
        geometry="sphere",
        mass_kg=mass_kg,
        density_kg_m3=density_kg_m3,
        volume_m3=volume,
        radius_m=radius,
        longitudinal_envelope_m=2.0 * radius,
        assumptions=("Uniform-density spherical envelope.",),
        warnings=("Containment and internal structure are not represented.",),
    )


def cylinder_geometry(
    *, mass_kg: float, density_kg_m3: float, length_to_diameter_ratio: float
) -> RotorGeometryResult:
    if mass_kg <= 0.0 or density_kg_m3 <= 0.0:
        raise ValueError("mass and density must be positive")
    if length_to_diameter_ratio <= 0.0:
        raise ValueError("length-to-diameter ratio must be positive")
    volume = mass_kg / density_kg_m3
    radius = (volume / (2.0 * math.pi * length_to_diameter_ratio)) ** (1.0 / 3.0)
    length = 2.0 * radius * length_to_diameter_ratio
    return RotorGeometryResult(
        fidelity="M1-GEOMETRY",
        geometry="cylinder",
        mass_kg=mass_kg,
        density_kg_m3=density_kg_m3,
        volume_m3=volume,
        radius_m=radius,
        longitudinal_envelope_m=length,
        assumptions=("Uniform-density right circular cylinder.",),
        warnings=("Containment and internal structure are not represented.",),
    )


def loop_envelope_geometry(
    *,
    total_mass_kg: float,
    effective_density_kg_m3: float,
    loop_mean_radius_m: float,
    radial_build_m: float,
) -> RotorGeometryResult:
    if total_mass_kg <= 0.0 or effective_density_kg_m3 <= 0.0:
        raise ValueError("mass and effective density must be positive")
    if loop_mean_radius_m <= 0.0 or radial_build_m <= 0.0:
        raise ValueError("loop radius and build must be positive")
    radius = loop_mean_radius_m + radial_build_m
    return RotorGeometryResult(
        fidelity="M1-GEOMETRY",
        geometry="loop-envelope",
        mass_kg=total_mass_kg,
        density_kg_m3=effective_density_kg_m3,
        volume_m3=total_mass_kg / effective_density_kg_m3,
        radius_m=radius,
        longitudinal_envelope_m=2.0 * radius,
        assumptions=("Loop envelope is a circular outer-radius bound.",),
        warnings=("Axial winding build and detailed support geometry are omitted.",),
    )


def evaluate_aperture(
    *, rotor_radius_m: float, clearance_factor: float, navigation_margin_m: float
) -> ApertureResult:
    if rotor_radius_m <= 0.0:
        raise ValueError("rotor radius must be positive")
    if clearance_factor <= 1.0:
        raise ValueError("clearance factor must be greater than one")
    if navigation_margin_m <= 0.0:
        raise ValueError("navigation margin must be positive")
    geometric = clearance_factor * rotor_radius_m
    aperture = max(geometric, navigation_margin_m)
    return ApertureResult(
        fidelity="M1-APERTURE",
        rotor_radius_m=rotor_radius_m,
        clearance_factor=clearance_factor,
        navigation_margin_m=navigation_margin_m,
        aperture_radius_m=aperture,
        navigation_floor_active=navigation_margin_m >= geometric,
        assumptions=(
            "Aperture radius is max(clearance_factor * rotor radius, navigation margin).",
            "The navigation margin is a study input, not a demonstrated control tolerance.",
        ),
        warnings=("Finite guide geometry and orbit-clearance dynamics are omitted.",),
    )


def evaluate_stream_packing(
    *,
    rotor_longitudinal_envelope_m: float,
    guide_frame_spacing_m: float,
    required_surface_gap_factor: float,
) -> PackingResult:
    if rotor_longitudinal_envelope_m <= 0.0 or guide_frame_spacing_m <= 0.0:
        raise ValueError("rotor envelope and spacing must be positive")
    if required_surface_gap_factor < 0.0:
        raise ValueError("surface-gap factor cannot be negative")
    surface_gap = required_surface_gap_factor * rotor_longitudinal_envelope_m
    required_center = rotor_longitudinal_envelope_m + surface_gap
    separation_margin = guide_frame_spacing_m - required_center
    overlap = separation_margin < 0.0
    warnings: list[str] = []
    if overlap:
        warnings.append(
            "Required center separation exceeds guide-frame stream spacing."
        )
    return PackingResult(
        fidelity="M1-PACKING",
        rotor_longitudinal_envelope_m=rotor_longitudinal_envelope_m,
        guide_frame_spacing_m=guide_frame_spacing_m,
        packing_ratio=rotor_longitudinal_envelope_m / guide_frame_spacing_m,
        required_surface_gap_m=surface_gap,
        required_center_separation_m=required_center,
        separation_margin_m=separation_margin,
        infeasible_overlap=overlap,
        assumptions=(
            "Elements are uniformly phased at the OR-1.1 mean guide-frame spacing.",
            "Required surface gap is a fixed multiple of the longitudinal envelope.",
        ),
        warnings=tuple(warnings),
    )


def evaluate_neighbor_coupling(
    *,
    magnetic_moment_a_m2: float,
    center_spacing_m: float,
    rotor_characteristic_radius_m: float,
    guide_force_n: float,
    guide_operating_field_t: float,
    magnetic_state: str,
) -> NeighborCouplingResult:
    """Worst-case axial aligned point-dipole nearest-neighbor estimate."""

    if magnetic_moment_a_m2 < 0.0:
        raise ValueError("magnetic moment cannot be negative")
    if center_spacing_m <= 0.0 or rotor_characteristic_radius_m <= 0.0:
        raise ValueError("spacing and rotor radius must be positive")
    if guide_force_n <= 0.0 or guide_operating_field_t <= 0.0:
        raise ValueError("guide force and operating field must be positive")
    field = (
        MU_0_H_M * 2.0 * magnetic_moment_a_m2 / (4.0 * math.pi * center_spacing_m**3)
    )
    force = (
        3.0 * MU_0_H_M * magnetic_moment_a_m2**2 / (2.0 * math.pi * center_spacing_m**4)
    )
    separation_to_diameter = center_spacing_m / (2.0 * rotor_characteristic_radius_m)
    valid = separation_to_diameter >= 5.0
    warnings: list[str] = []
    if not valid:
        warnings.append(
            "Point-dipole estimate is not reliable because separation is below five rotor diameters."
        )
    if (
        "ferro" in magnetic_state.lower()
        or "guide-magnetized" in magnetic_state.lower()
    ):
        warnings.append(
            "Soft-ferromagnetic free-flight moment may be much lower than this guide-magnetized worst case."
        )
    return NeighborCouplingResult(
        fidelity="M1-DIPOLE-COUPLING",
        magnetic_moment_a_m2=magnetic_moment_a_m2,
        center_spacing_m=center_spacing_m,
        rotor_characteristic_radius_m=rotor_characteristic_radius_m,
        nearest_neighbor_field_t=field,
        nearest_neighbor_force_n=force,
        guide_force_n=guide_force_n,
        guide_operating_field_t=guide_operating_field_t,
        force_fraction_of_guide=force / guide_force_n,
        field_fraction_of_guide=field / guide_operating_field_t,
        separation_to_diameter_ratio=separation_to_diameter,
        point_dipole_valid=valid,
        magnetic_state=magnetic_state,
        assumptions=(
            "Neighbor dipoles are coaxial, aligned, and represented as ideal point dipoles.",
            "Only the nearest neighbor is reported; collective chain dynamics are omitted.",
        ),
        warnings=tuple(warnings),
    )
