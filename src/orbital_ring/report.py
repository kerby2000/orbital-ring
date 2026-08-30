"""Baseline Markdown report and fixed-parameter plot generation."""

from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.ballistic import solve_ballistic_intercept
from orbital_ring.config import Scenario, load_scenario
from orbital_ring.orbit import continuous_magnetic_support_acceleration, evaluate_closed_form


REPORT_NODE_COUNTS = (10, 16, 24, 32, 48, 64, 96, 192, 480, 960, 1920)
REPORT_VELOCITIES_M_S = (8_000, 9_000, 10_000, 11_000, 12_000, 15_000, 20_000, 30_000)
REPORT_ELEMENT_MASSES_KG = (0.001, 0.010, 0.050, 0.100, 0.500)


def _plot(
    output_path: Path,
    x,
    y,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    fixed_parameters: str,
    xscale: str | None = None,
    yscale: str | None = None,
) -> None:
    figure, axis = plt.subplots(figsize=(8.0, 4.8))
    axis.plot(x, y, marker="o", linewidth=1.8)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True, alpha=0.3)
    if xscale:
        axis.set_xscale(xscale)
    if yscale:
        axis.set_yscale(yscale)
    figure.text(0.5, 0.01, f"Fixed: {fixed_parameters}", ha="center", fontsize=8)
    figure.tight_layout(rect=(0.0, 0.045, 1.0, 1.0))
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def _minimum_altitudes(scenario: Scenario, node_stride: int) -> list[float]:
    values: list[float] = []
    for node_count in REPORT_NODE_COUNTS:
        transfer = solve_ballistic_intercept(
            earth_radius_m=scenario.earth.mean_radius_m,
            altitude_m=scenario.ring.altitude_m,
            node_count=node_count,
            rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
            mu_m3_s2=scenario.earth.gravitational_parameter_m3_s2,
            earth_rotation_rad_s=scenario.earth.rotation_rate_rad_s,
            minimum_safe_altitude_m=scenario.safety.minimum_safe_altitude_m,
            node_stride=node_stride,
        )
        values.append(transfer.minimum_altitude_m / 1_000.0)
    return values


def generate_baseline_report(
    scenario_path: str | Path, output_directory: str | Path
) -> Path:
    scenario = load_scenario(scenario_path)
    if scenario.model.fidelity != "L1":
        raise ValueError("baseline report requires model.fidelity: L1")
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    result = evaluate_scenario(scenario)

    l0_total_km: list[float] = []
    l0_node_km: list[float] = []
    for node_count in REPORT_NODE_COUNTS:
        closed = evaluate_closed_form(
            mu_m3_s2=scenario.earth.gravitational_parameter_m3_s2,
            radius_m=scenario.radius_m,
            rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
            allowed_lateral_acceleration_m_s2=(
                scenario.magnetic.max_lateral_acceleration_m_s2
            ),
            node_count=node_count,
            earth_rotation_rad_s=scenario.earth.rotation_rate_rad_s,
        )
        l0_total_km.append(closed.total_physical_guide_length_m / 1_000.0)
        l0_node_km.append(closed.physical_guide_length_per_node_m / 1_000.0)

    fixed_node = (
        f"h={scenario.ring.altitude_m / 1_000:g} km; "
        f"v={scenario.rotor.geocentric_velocity_m_s / 1_000:g} km/s; "
        f"a={scenario.magnetic.max_lateral_acceleration_m_s2 / 9.80665:g} g_0"
    )
    _plot(
        output / "node_count_vs_guide_length_per_node.png",
        REPORT_NODE_COUNTS,
        l0_node_km,
        xlabel="Node count",
        ylabel="L0 physical guide length per node (km)",
        title="Node count vs Earth-fixed physical guide length per node (large-N L0)",
        fixed_parameters=fixed_node,
        xscale="log",
        yscale="log",
    )
    _plot(
        output / "node_count_vs_total_guide_length.png",
        REPORT_NODE_COUNTS,
        l0_total_km,
        xlabel="Node count",
        ylabel="L0 total physical guide length (km)",
        title="Node count vs total Earth-fixed physical guide length (large-N L0)",
        fixed_parameters=fixed_node,
        xscale="log",
    )

    one_node_min_km = _minimum_altitudes(scenario, 1)
    bypass_min_km = _minimum_altitudes(scenario, 2)
    fixed_ballistic = (
        f"h={scenario.ring.altitude_m / 1_000:g} km; "
        f"v={scenario.rotor.geocentric_velocity_m_s / 1_000:g} km/s; "
        f"Earth rotation={scenario.earth.rotation_rate_rad_s:.8g} rad/s; L1"
    )
    _plot(
        output / "node_count_vs_minimum_ballistic_altitude.png",
        REPORT_NODE_COUNTS,
        one_node_min_km,
        xlabel="Node count",
        ylabel="Minimum altitude (km)",
        title="Node count vs one-node-transfer minimum ballistic altitude",
        fixed_parameters=fixed_ballistic,
        xscale="log",
    )
    _plot(
        output / "node_count_vs_bypass_minimum_altitude.png",
        REPORT_NODE_COUNTS,
        bypass_min_km,
        xlabel="Node count",
        ylabel="Minimum altitude (km)",
        title="Node count vs one-node-bypass minimum altitude (node stride=2)",
        fixed_parameters=fixed_ballistic,
        xscale="log",
    )

    support = [
        continuous_magnetic_support_acceleration(
            velocity,
            scenario.earth.gravitational_parameter_m3_s2,
            scenario.radius_m,
        )
        for velocity in REPORT_VELOCITIES_M_S
    ]
    _plot(
        output / "rotor_velocity_vs_support_acceleration.png",
        np.array(REPORT_VELOCITIES_M_S) / 1_000.0,
        np.array(support) / 9.80665,
        xlabel="Geocentric rotor velocity (km/s)",
        ylabel="Continuous support acceleration (g_0)",
        title="Rotor velocity vs continuous magnetic support acceleration (L0)",
        fixed_parameters=f"h={scenario.ring.altitude_m / 1_000:g} km; Earth mu and radius from scenario",
    )

    kinetic_mj = [
        0.5 * mass * scenario.rotor.geocentric_velocity_m_s**2 / 1.0e6
        for mass in REPORT_ELEMENT_MASSES_KG
    ]
    _plot(
        output / "element_mass_vs_kinetic_energy.png",
        np.array(REPORT_ELEMENT_MASSES_KG) * 1_000.0,
        kinetic_mj,
        xlabel="Element mass (g)",
        ylabel="Kinetic energy per element (MJ)",
        title="Element mass vs kinetic energy",
        fixed_parameters=f"v={scenario.rotor.geocentric_velocity_m_s / 1_000:g} km/s",
        xscale="log",
        yscale="log",
    )
    circulation_period = result.rotor_stream.circulation_period_s
    passage_frequency = [
        (scenario.rotor.total_moving_mass_kg / mass) / circulation_period
        for mass in REPORT_ELEMENT_MASSES_KG
    ]
    _plot(
        output / "element_mass_vs_passage_frequency.png",
        np.array(REPORT_ELEMENT_MASSES_KG) * 1_000.0,
        passage_frequency,
        xlabel="Element mass (g)",
        ylabel="Element passage frequency per node (Hz)",
        title="Element mass vs passage frequency at constant total rotor mass",
        fixed_parameters=(
            f"M={scenario.rotor.total_moving_mass_kg / 1_000:g} tonnes; "
            f"N={scenario.ring.node_count}; node stride=1; L1 period={circulation_period:.3f} s"
        ),
        xscale="log",
        yscale="log",
    )

    (output / "baseline_results.json").write_text(
        json.dumps(result.to_dict(), indent=2, allow_nan=False), encoding="utf-8"
    )
    (output / "manifest.json").write_text(
        json.dumps(result.to_dict()["manifest"], indent=2, allow_nan=False), encoding="utf-8"
    )

    closed = result.closed_form
    ballistic = result.ballistic
    assert ballistic is not None
    rotor = result.rotor_stream
    report = f"""# OR-0 / OR-1 baseline report

Scenario: `{scenario.scenario_id}`  
Configuration hash: `{result.manifest.configuration_hash}`  
Fidelity: L0 closed-form scaling and L1 numerical two-body propagation

## Reference results

| Quantity | Value |
|---|---:|
| Geocentric radius | {scenario.radius_m / 1_000:.3f} km |
| Gravity at ring | {closed.gravity_m_s2:.6f} m/s² |
| Circular velocity | {closed.circular_velocity_m_s / 1_000:.6f} km/s |
| Escape velocity | {closed.escape_velocity_m_s / 1_000:.6f} km/s |
| Continuous magnetic support | {closed.continuous_support_acceleration_m_s2:.6f} m/s² |
| L0 magnetic turn over inertial-period circuit | {closed.magnetic_turning_angle_inertial_period_rad:.6f} rad |
| L0 magnetic turn over Earth-relative circuit | {closed.earth_fixed_magnetic_turning_angle_rad:.6f} rad |
| L0 magnetic curvature radius | {closed.magnetic_curvature_radius_m / 1_000:.6f} km |
| L0 total Earth-fixed physical guide length | {closed.total_physical_guide_length_m / 1_000:.6f} km |
| L0 physical guide length per node | {closed.physical_guide_length_per_node_m:.3f} m |
| L1 flight time | {ballistic.flight_time_s:.6f} s |
| L1 minimum altitude | {ballistic.minimum_altitude_m / 1_000:.6f} km |
| L1 active deflection angle | {ballistic.required_active_deflection_angle_rad:.8f} rad |
| L1 required delta-v | {ballistic.required_delta_v_m_s:.6f} m/s |
| L1 ideal interaction time | {rotor.ideal_interaction_time_s:.8f} s |
| L1 inertial turn path length | {rotor.inertial_turn_path_length_m:.6f} m |
| L1 Earth-fixed physical guide estimate | {rotor.physical_guide_length_estimate_m:.6f} m |
| Elements | {rotor.number_of_elements:,.0f} |
| Passage frequency per node | {rotor.element_passage_frequency_per_node_hz:,.6f} Hz |
| Kinetic energy per element | {rotor.kinetic_energy_per_element_j / 1.0e6:.6f} MJ |
| Average node reaction force | {rotor.average_node_reaction_force_mdot_n / 1_000:.6f} kN |
| Force cross-check relative error | {rotor.force_consistency_relative_error:.3e} |

L0 guide-length results are large-N scaling approximations. L1 treats nodes as
points and integrates only spherical two-body gravity while the target node
rotates with Earth.

## Plots

![Node count vs guide length per node](node_count_vs_guide_length_per_node.png)

![Node count vs total guide length](node_count_vs_total_guide_length.png)

![Node count vs minimum ballistic altitude](node_count_vs_minimum_ballistic_altitude.png)

![Node count vs one-node-bypass minimum altitude](node_count_vs_bypass_minimum_altitude.png)

![Rotor velocity vs support acceleration](rotor_velocity_vs_support_acceleration.png)

![Element mass vs kinetic energy](element_mass_vs_kinetic_energy.png)

![Element mass vs passage frequency](element_mass_vs_passage_frequency.png)

## Warnings

""" + "\n".join(f"- {warning}" for warning in result.manifest.warnings) + "\n"
    report_path = output / "BASELINE_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path
