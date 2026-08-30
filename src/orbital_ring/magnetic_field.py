"""M0 magnetic bounds and M1 ideal gradient/dipole relationships."""

from __future__ import annotations

import math
from typing import Literal

from scipy.integrate import quad

from orbital_ring.magnetic_results import (
    DipoleForceResult,
    MaxwellPressureResult,
    QuadrupoleResult,
)

# 2022 CODATA vacuum magnetic permeability in SI.
MU_0_H_M = 1.25663706127e-6


def magnetic_pressure_pa(field_t: float) -> float:
    if field_t < 0.0:
        raise ValueError("field magnitude cannot be negative")
    return field_t**2 / (2.0 * MU_0_H_M)


def evaluate_maxwell_pressure_bound(
    *, field_t: float, requested_force_n: float
) -> MaxwellPressureResult:
    """Absolute M0 force-density scale; this is not a rotor force law."""

    if field_t <= 0.0:
        raise ValueError("field magnitude must be positive")
    if requested_force_n < 0.0:
        raise ValueError("requested force cannot be negative")
    pressure = magnetic_pressure_pa(field_t)
    return MaxwellPressureResult(
        fidelity="M0-PRESSURE",
        field_t=field_t,
        magnetic_pressure_pa=pressure,
        field_energy_density_j_m3=pressure,
        requested_force_n=requested_force_n,
        ideal_interaction_area_m2=requested_force_n / pressure,
        assumptions=(
            "Vacuum field energy density equals Maxwell magnetic pressure scale.",
        ),
        warnings=(
            "Magnetic pressure is an absolute force-density bound, not a rotor force law.",
            "Coils, yokes, stress support, fringe fields, and efficiency are omitted.",
        ),
    )


def quadrupole_aperture_energy_per_length_j_m(
    gradient_t_m: float, aperture_radius_m: float
) -> float:
    if gradient_t_m < 0.0:
        raise ValueError("gradient magnitude cannot be negative")
    if aperture_radius_m <= 0.0:
        raise ValueError("aperture radius must be positive")
    return math.pi * gradient_t_m**2 * aperture_radius_m**4 / (4.0 * MU_0_H_M)


def quadrupole_field_xy_t(
    *, x_m: float, y_m: float, gradient_t_m: float
) -> tuple[float, float]:
    """Ideal normal quadrupole B=(G x, -G y), with |B|=G r."""

    if gradient_t_m < 0.0:
        raise ValueError("gradient magnitude cannot be negative")
    return gradient_t_m * x_m, -gradient_t_m * y_m


def quadrupole_aperture_energy_numerical_j_m(
    gradient_t_m: float, aperture_radius_m: float
) -> float:
    """Numerically integrate B^2/(2 mu0) across an ideal circular aperture."""

    if gradient_t_m < 0.0:
        raise ValueError("gradient magnitude cannot be negative")
    if aperture_radius_m <= 0.0:
        raise ValueError("aperture radius must be positive")

    def annulus_energy(radius_m: float) -> float:
        field = gradient_t_m * radius_m
        return magnetic_pressure_pa(field) * 2.0 * math.pi * radius_m

    return float(quad(annulus_energy, 0.0, aperture_radius_m, epsabs=1.0e-12)[0])


def evaluate_quadrupole(
    *,
    gradient_t_m: float,
    aperture_radius_m: float,
    operating_offset_m: float,
) -> QuadrupoleResult:
    """Ideal two-dimensional current-free circular-aperture quadrupole."""

    if gradient_t_m < 0.0:
        raise ValueError("gradient magnitude cannot be negative")
    if aperture_radius_m <= 0.0:
        raise ValueError("aperture radius must be positive")
    if not 0.0 <= operating_offset_m <= aperture_radius_m:
        raise ValueError("operating offset must lie inside the aperture")
    edge_field = gradient_t_m * aperture_radius_m
    return QuadrupoleResult(
        fidelity="M1-QUADRUPOLE",
        gradient_t_m=gradient_t_m,
        aperture_radius_m=aperture_radius_m,
        operating_offset_m=operating_offset_m,
        operating_field_t=gradient_t_m * operating_offset_m,
        aperture_edge_field_t=edge_field,
        aperture_edge_pressure_pa=magnetic_pressure_pa(edge_field),
        aperture_field_energy_per_length_j_m=(
            quadrupole_aperture_energy_per_length_j_m(gradient_t_m, aperture_radius_m)
        ),
        assumptions=(
            "Ideal 2-D current-free quadrupole with |B| = G r in a circular aperture.",
            "The gradient and aperture are uniform along the reported guide length.",
        ),
        warnings=(
            "Aperture field energy excludes coil, yoke, end, and fringe-field energy.",
            "Pole-tip field is an aperture-edge scale, not a conductor peak-field prediction.",
        ),
    )


def required_gradient_t_m(
    acceleration_m_s2: float, specific_magnetic_moment_a_m2_kg: float
) -> float:
    if acceleration_m_s2 < 0.0:
        raise ValueError("acceleration magnitude cannot be negative")
    if specific_magnetic_moment_a_m2_kg <= 0.0:
        raise ValueError("specific magnetic moment must be positive")
    return acceleration_m_s2 / specific_magnetic_moment_a_m2_kg


def available_acceleration_m_s2(
    specific_magnetic_moment_a_m2_kg: float, gradient_t_m: float
) -> float:
    if specific_magnetic_moment_a_m2_kg < 0.0 or gradient_t_m < 0.0:
        raise ValueError("specific moment and gradient magnitudes cannot be negative")
    return specific_magnetic_moment_a_m2_kg * gradient_t_m


def evaluate_aligned_dipole(
    *,
    magnetic_moment_a_m2: float,
    element_mass_kg: float,
    gradient_t_m: float,
    field_seeking: Literal["high", "low"] = "high",
) -> DipoleForceResult:
    """M1 adiabatically aligned point-dipole force F ~= mu grad(|B|)."""

    if magnetic_moment_a_m2 < 0.0:
        raise ValueError("magnetic moment magnitude cannot be negative")
    if element_mass_kg <= 0.0:
        raise ValueError("element mass must be positive")
    if gradient_t_m < 0.0:
        raise ValueError("gradient magnitude cannot be negative")
    if field_seeking not in ("high", "low"):
        raise ValueError("field_seeking must be 'high' or 'low'")
    specific_moment = magnetic_moment_a_m2 / element_mass_kg
    force = magnetic_moment_a_m2 * gradient_t_m
    warnings = [
        "Point-dipole approximation requires field variation length scales larger than the rotor."
    ]
    if field_seeking == "high":
        warnings.append(
            "Static three-dimensional passive stability is not guaranteed for a high-field-seeking dipole."
        )
    else:
        warnings.append(
            "Low-field-seeking behavior requires a maintained anti-aligned or effective magnetic state."
        )
    return DipoleForceResult(
        fidelity="M1-DIPOLE",
        magnetic_moment_a_m2=magnetic_moment_a_m2,
        element_mass_kg=element_mass_kg,
        specific_magnetic_moment_a_m2_kg=specific_moment,
        gradient_t_m=gradient_t_m,
        force_n=force,
        acceleration_m_s2=force / element_mass_kg,
        orientation_assumption="adiabatic alignment with local |B| gradient",
        field_seeking_classification=f"{field_seeking}-field-seeking",
        assumptions=(
            "The dipole moment magnitude is constant over the interaction.",
            "Torque aligns the dipole sufficiently rapidly for the scalar force approximation.",
        ),
        warnings=tuple(warnings),
    )
