"""Clean public orchestration API for L0/L1 scenario evaluation."""

from __future__ import annotations

import math

from orbital_ring.ballistic import solve_ballistic_intercept
from orbital_ring.config import Scenario
from orbital_ring.geometry import node_angular_spacing
from orbital_ring.manifest import build_manifest
from orbital_ring.orbit import evaluate_closed_form
from orbital_ring.results import BallisticResult, SimulationResult
from orbital_ring.rotor import evaluate_rotor_stream


def _scenario_warnings(
    scenario: Scenario, closed_form, ballistic: BallisticResult | None
) -> list[str]:
    warnings: list[str] = []
    if scenario.rotor.geocentric_velocity_m_s <= closed_form.circular_velocity_m_s:
        warnings.append(
            "Rotor velocity is at or below circular velocity; L0 magnetic support and "
            "turning-angle signs do not represent outward support."
        )
    if scenario.rotor.geocentric_velocity_m_s >= closed_form.escape_velocity_m_s:
        warnings.append("Rotor speed is at or above local two-body escape velocity.")
    element_count = (
        scenario.rotor.total_moving_mass_kg / scenario.rotor.element_mass_kg
    )
    if not math.isclose(element_count, round(element_count), rel_tol=0.0, abs_tol=1.0e-9):
        warnings.append("Total mass divided by element mass is not an integer element count.")
    if ballistic is not None:
        if ballistic.intersects_earth:
            warnings.append("The numerical free-flight trajectory intersects Earth.")
        elif ballistic.violates_minimum_safe_altitude:
            warnings.append("The numerical trajectory violates the minimum-safe altitude.")
        if scenario.transfer.skip_nodes > 1:
            warnings.append(
                f"This trajectory intentionally bypasses {scenario.transfer.skip_nodes - 1} "
                "intermediate node(s)."
            )
    warnings.append("L0 guide lengths are large-N scaling approximations.")
    return warnings


def evaluate_scenario(scenario: Scenario) -> SimulationResult:
    """Evaluate one strict configuration without mutating it."""

    closed = evaluate_closed_form(
        mu_m3_s2=scenario.earth.gravitational_parameter_m3_s2,
        radius_m=scenario.radius_m,
        rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
        allowed_lateral_acceleration_m_s2=(
            scenario.magnetic.max_lateral_acceleration_m_s2
        ),
        node_count=scenario.ring.node_count,
    )

    ballistic: BallisticResult | None = None
    if scenario.model.fidelity == "L1":
        ballistic = solve_ballistic_intercept(
            earth_radius_m=scenario.earth.mean_radius_m,
            altitude_m=scenario.ring.altitude_m,
            node_count=scenario.ring.node_count,
            rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
            mu_m3_s2=scenario.earth.gravitational_parameter_m3_s2,
            earth_rotation_rad_s=scenario.earth.rotation_rate_rad_s,
            minimum_safe_altitude_m=scenario.safety.minimum_safe_altitude_m,
            skip_nodes=scenario.transfer.skip_nodes,
        )
        flight_time = ballistic.flight_time_s
        active_angle = ballistic.required_active_deflection_angle_rad
        delta_v = ballistic.required_delta_v_m_s
    else:
        relative_angular_rate = (
            scenario.rotor.geocentric_velocity_m_s / scenario.radius_m
            - scenario.earth.rotation_rate_rad_s
        )
        if relative_angular_rate <= 0.0:
            raise ValueError("L0 circulation requires positive Earth-relative angular rate")
        flight_time = (
            node_angular_spacing(
                scenario.ring.node_count, scenario.transfer.skip_nodes
            )
            / relative_angular_rate
        )
        active_angle = (
            closed.magnetic_turning_angle_rad
            * scenario.transfer.skip_nodes
            / scenario.ring.node_count
        )
        delta_v = 2.0 * scenario.rotor.geocentric_velocity_m_s * math.sin(
            active_angle / 2.0
        )

    rotor = evaluate_rotor_stream(
        total_rotor_mass_kg=scenario.rotor.total_moving_mass_kg,
        element_mass_kg=scenario.rotor.element_mass_kg,
        rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
        node_count=scenario.ring.node_count,
        skip_nodes=scenario.transfer.skip_nodes,
        flight_time_s=flight_time,
        active_deflection_angle_rad=active_angle,
        required_delta_v_m_s=delta_v,
        allowed_lateral_acceleration_m_s2=(
            scenario.magnetic.max_lateral_acceleration_m_s2
        ),
    )
    derived = {
        "geocentric_radius_m": scenario.radius_m,
        "circular_velocity_m_s": closed.circular_velocity_m_s,
        "escape_velocity_m_s": closed.escape_velocity_m_s,
        "node_angular_spacing_rad": node_angular_spacing(
            scenario.ring.node_count, scenario.transfer.skip_nodes
        ),
        "number_of_rotor_elements": rotor.number_of_elements,
    }
    manifest = build_manifest(
        scenario,
        derived_parameters=derived,
        warnings=_scenario_warnings(scenario, closed, ballistic),
        fidelity=scenario.model.fidelity,
    )
    return SimulationResult(
        manifest=manifest,
        closed_form=closed,
        ballistic=ballistic,
        rotor_stream=rotor,
    )

