"""First-order longitudinal ripple, skin-depth, eddy, and R-L loop models."""

from __future__ import annotations

import math

from orbital_ring.magnetic_field import MU_0_H_M
from orbital_ring.magnetic_results import ConductiveLoopResult, RippleLossResult
from orbital_ring.magnetic_rotors import circular_loop_inductance_h
from orbital_ring.materials import MaterialRegistry


def ripple_frequency_hz(
    guide_relative_speed_m_s: float, longitudinal_pitch_m: float
) -> float:
    if guide_relative_speed_m_s <= 0.0 or longitudinal_pitch_m <= 0.0:
        raise ValueError("guide-relative speed and pitch must be positive")
    return guide_relative_speed_m_s / longitudinal_pitch_m


def skin_depth_m(
    *,
    frequency_hz: float,
    electrical_resistivity_ohm_m: float,
    relative_permeability: float,
) -> float:
    if frequency_hz <= 0.0 or electrical_resistivity_ohm_m <= 0.0:
        raise ValueError("frequency and resistivity must be positive")
    if relative_permeability <= 0.0:
        raise ValueError("relative permeability must be positive")
    omega = 2.0 * math.pi * frequency_hz
    return math.sqrt(
        2.0 * electrical_resistivity_ohm_m / (omega * MU_0_H_M * relative_permeability)
    )


def lamination_eddy_loss_density_w_m3(
    *,
    ripple_flux_density_amplitude_t: float,
    section_thickness_m: float,
    frequency_hz: float,
    electrical_resistivity_ohm_m: float,
) -> float:
    if ripple_flux_density_amplitude_t < 0.0:
        raise ValueError("ripple flux-density amplitude cannot be negative")
    if section_thickness_m <= 0.0 or frequency_hz <= 0.0:
        raise ValueError("section thickness and frequency must be positive")
    if electrical_resistivity_ohm_m <= 0.0:
        raise ValueError("electrical resistivity must be positive")
    return (
        math.pi**2
        * ripple_flux_density_amplitude_t**2
        * section_thickness_m**2
        * frequency_hz**2
        / (6.0 * electrical_resistivity_ohm_m)
    )


def evaluate_ripple_loss(
    registry: MaterialRegistry,
    *,
    material_identifier: str,
    guide_relative_speed_m_s: float,
    longitudinal_pitch_m: float,
    ripple_flux_density_amplitude_t: float,
    section_thickness_m: float,
    relative_permeability: float,
) -> RippleLossResult:
    material = registry.get(material_identifier)
    resistivity = material.value("electrical_resistivity_ohm_m")
    frequency = ripple_frequency_hz(guide_relative_speed_m_s, longitudinal_pitch_m)
    depth = skin_depth_m(
        frequency_hz=frequency,
        electrical_resistivity_ohm_m=resistivity,
        relative_permeability=relative_permeability,
    )
    ratio = section_thickness_m / depth
    thin_valid = ratio <= 0.3
    source_supported: bool | None = None
    warnings = [
        "The smooth transverse guide gradient is separated from prescribed longitudinal sinusoidal ripple.",
        "Classical eddy loss excludes hysteresis, anomalous loss, temperature rise, and 3-D geometry.",
    ]
    if material_identifier == "tdk_n87":
        source_supported = (
            material.value("recommended_frequency_min_hz")
            <= frequency
            <= material.value("recommended_frequency_max_hz")
        )
        if not source_supported:
            warnings.append(
                "Ripple frequency lies outside the source preferred frequency range; no manufacturer core-loss value is extrapolated."
            )
    if not thin_valid:
        warnings.append(
            "Section thickness exceeds 0.3 skin depth; the uniform-flux thin-section eddy approximation is invalid."
        )
    return RippleLossResult(
        fidelity="LOSS-L1",
        material_identifier=material_identifier,
        guide_relative_speed_m_s=guide_relative_speed_m_s,
        longitudinal_pitch_m=longitudinal_pitch_m,
        ripple_frequency_hz=frequency,
        ripple_flux_density_amplitude_t=ripple_flux_density_amplitude_t,
        section_thickness_m=section_thickness_m,
        electrical_resistivity_ohm_m=resistivity,
        relative_permeability=relative_permeability,
        skin_depth_m=depth,
        thickness_to_skin_depth_ratio=ratio,
        classical_eddy_loss_density_w_m3=lamination_eddy_loss_density_w_m3(
            ripple_flux_density_amplitude_t=ripple_flux_density_amplitude_t,
            section_thickness_m=section_thickness_m,
            frequency_hz=frequency,
            electrical_resistivity_ohm_m=resistivity,
        ),
        thin_section_valid=thin_valid,
        source_frequency_domain_supported=source_supported,
        assumptions=(
            "Ripple is B(s)=DeltaB sin(2 pi s/lambda) sampled at constant guide-relative speed.",
            "The supplied relative permeability is a study input at the ripple condition.",
            "Thin-section loss uses pi^2 Bp^2 t^2 f^2/(6 rho).",
        ),
        warnings=tuple(warnings),
    )


def evaluate_conductive_loop(
    registry: MaterialRegistry,
    *,
    conductor_identifier: str,
    loop_radius_m: float,
    conductor_radius_m: float,
    guide_relative_speed_m_s: float,
    longitudinal_pitch_m: float,
    ripple_flux_density_amplitude_t: float,
) -> ConductiveLoopResult:
    """Analytic sinusoidal steady state of L di/dt + R i = -dPhi/dt."""

    if loop_radius_m <= 0.0 or conductor_radius_m <= 0.0:
        raise ValueError("loop and conductor radii must be positive")
    material = registry.get(conductor_identifier)
    resistivity = material.value("electrical_resistivity_ohm_m")
    loop_length = 2.0 * math.pi * loop_radius_m
    conductor_area = math.pi * conductor_radius_m**2
    resistance = resistivity * loop_length / conductor_area
    inductance, valid = circular_loop_inductance_h(
        loop_radius_m=loop_radius_m,
        effective_conductor_radius_m=conductor_radius_m,
        turns=1,
    )
    if inductance is None:
        raise ValueError(
            "loop geometry does not produce a positive thin-loop inductance"
        )
    frequency = ripple_frequency_hz(guide_relative_speed_m_s, longitudinal_pitch_m)
    omega = 2.0 * math.pi * frequency
    flux = ripple_flux_density_amplitude_t * math.pi * loop_radius_m**2
    emf = omega * flux
    impedance = math.hypot(resistance, omega * inductance)
    current = emf / impedance
    warnings = [
        "The conductive loop is a ripple-loss benchmark, not a demonstrated primary guide-force architecture.",
        "Temperature dependence, radiation, proximity effect, and mechanical loads are omitted.",
    ]
    if not valid:
        warnings.append("Thin circular-loop inductance is outside R/a >= 10 validity.")
    return ConductiveLoopResult(
        fidelity="M1-INDUCTIVE",
        conductor_identifier=conductor_identifier,
        loop_radius_m=loop_radius_m,
        conductor_radius_m=conductor_radius_m,
        resistance_ohm=resistance,
        inductance_h=inductance,
        ripple_frequency_hz=frequency,
        external_flux_amplitude_wb=flux,
        induced_emf_amplitude_v=emf,
        current_amplitude_a=current,
        current_phase_lag_rad=math.atan2(omega * inductance, resistance),
        average_joule_power_w=0.5 * current**2 * resistance,
        loop_formula_valid=valid,
        assumptions=(
            "External ripple field is uniform over the loop area and sinusoidal in time.",
            "Reported current is the steady-state amplitude of the linear R-L equation.",
            "Conductor properties are evaluated at the registry temperature.",
        ),
        warnings=tuple(warnings),
    )
