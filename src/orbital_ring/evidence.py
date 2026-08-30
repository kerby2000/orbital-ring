"""OR-1.1 reproducible validation and design-space evidence tables."""

from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.config import Scenario, load_scenario
from orbital_ring.geometry import rotate_vector
from orbital_ring.network import evaluate_failure_route
from orbital_ring.rotor import evaluate_rotor_stream


FORCE_CLOSURE_NODE_COUNTS = (48, 96, 192, 480, 960, 1920)
DESIGN_SPACE_NODE_COUNTS = (10, 16, 24, 32, 48, 64, 96, 192, 480, 960, 1920)
BYPASS_NODE_COUNTS = (48, 96, 192, 480, 960)
ROTOR_ELEMENT_MASSES_KG = (1.0, 0.5, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001)


def _direct_scenario(scenario: Scenario, node_count: int | None = None) -> Scenario:
    overrides: dict[str, float | int] = {"transfer.node_stride": 1}
    if node_count is not None:
        overrides["ring.node_count"] = node_count
    return scenario.with_overrides(overrides)


def force_closure_table(
    scenario: Scenario,
    node_counts: Iterable[int] = FORCE_CLOSURE_NODE_COUNTS,
) -> pd.DataFrame:
    """Compare summed finite-node L1 reactions with continuous support force."""

    rows: list[dict[str, float | int]] = []
    for node_count in node_counts:
        result = evaluate_scenario(_direct_scenario(scenario, node_count))
        ballistic = result.ballistic
        if ballistic is None:
            raise ValueError("force-closure evidence requires L1 fidelity")
        target_angle = (
            ballistic.node_angular_spacing_rad
            + scenario.earth.rotation_rate_rad_s * ballistic.flight_time_s
        )
        outgoing_next = rotate_vector(
            np.asarray(ballistic.outgoing_velocity_m_s), target_angle
        )
        incoming = np.asarray(ballistic.incoming_velocity_m_s)
        rotor_delta_v = outgoing_next - incoming
        radial_unit = np.array([math.cos(target_angle), math.sin(target_angle)])
        mass_flow_per_node = (
            scenario.rotor.total_moving_mass_kg
            / (node_count * ballistic.flight_time_s)
        )
        radial_reaction_per_node = -mass_flow_per_node * float(
            np.dot(rotor_delta_v, radial_unit)
        )
        summed_l1 = node_count * radial_reaction_per_node
        continuous = (
            scenario.rotor.total_moving_mass_kg
            * result.closed_form.continuous_support_acceleration_m_s2
        )
        signed_error = (summed_l1 - continuous) / continuous
        rows.append(
            {
                "node_count": node_count,
                "summed_l1_node_force_n": summed_l1,
                "continuous_support_force_n": continuous,
                "signed_relative_error": signed_error,
                "absolute_relative_error": abs(signed_error),
            }
        )
    return pd.DataFrame(rows)


def node_count_l1_table(
    scenario: Scenario,
    node_counts: Iterable[int] = DESIGN_SPACE_NODE_COUNTS,
) -> pd.DataFrame:
    rows: list[dict[str, float | int | bool]] = []
    for node_count in node_counts:
        result = evaluate_scenario(_direct_scenario(scenario, node_count))
        ballistic = result.ballistic
        if ballistic is None:
            raise ValueError("node-count L1 evidence requires L1 fidelity")
        guide_per_node = result.rotor_stream.active_guide_length_per_node_m
        rows.append(
            {
                "node_count": node_count,
                "direct_flight_time_s": ballistic.flight_time_s,
                "minimum_free_flight_altitude_m": ballistic.minimum_altitude_m,
                "active_deflection_angle_rad": (
                    ballistic.required_active_deflection_angle_rad
                ),
                "l1_guide_length_per_node_m": guide_per_node,
                "total_l1_active_guide_length_m": node_count * guide_per_node,
                "node_delta_v_m_s": ballistic.required_delta_v_m_s,
                "average_node_reaction_force_n": (
                    result.rotor_stream.average_node_reaction_force_mdot_n
                ),
                "intersects_earth": ballistic.intersects_earth,
                "violates_minimum_safe_altitude": (
                    ballistic.violates_minimum_safe_altitude
                ),
            }
        )
    return pd.DataFrame(rows)


def bypass_table(
    scenario: Scenario,
    node_counts: Iterable[int] = BYPASS_NODE_COUNTS,
) -> pd.DataFrame:
    """Report local bypass geometry for one or two adjacent failed nodes."""

    rows: list[dict[str, object]] = []
    for node_count in node_counts:
        sized = _direct_scenario(scenario, node_count)
        for failure_count, failure_label in (
            (1, "one_failed_node"),
            (2, "two_adjacent_failed_nodes"),
        ):
            failed_nodes = tuple(range(1, 1 + failure_count))
            route = evaluate_failure_route(sized, failed_nodes)
            if len(route.bypass_legs) != 1:
                raise AssertionError("adjacent failure case must produce one bypass leg")
            bypass = route.bypass_legs[0]
            ballistic = bypass.ballistic
            guide_length = (
                scenario.rotor.geocentric_velocity_m_s**2
                * ballistic.required_active_deflection_angle_rad
                / scenario.magnetic.max_lateral_acceleration_m_s2
            )
            rows.append(
                {
                    "node_count": node_count,
                    "failure_case": failure_label,
                    "failed_nodes": ",".join(str(node) for node in failed_nodes),
                    "active_node_count": route.active_node_count,
                    "unaffected_normal_leg_count": route.normal_leg_count,
                    "bypass_start_node": bypass.start_node,
                    "bypass_target_node": bypass.target_node,
                    "node_stride": ballistic.node_stride,
                    "bypassed_node_count": len(bypass.bypassed_nodes),
                    "local_bypass_flight_time_s": ballistic.flight_time_s,
                    "local_bypass_minimum_altitude_m": ballistic.minimum_altitude_m,
                    "local_bypass_deflection_angle_rad": (
                        ballistic.required_active_deflection_angle_rad
                    ),
                    "local_bypass_guide_length_m": guide_length,
                    "local_bypass_delta_v_m_s": ballistic.required_delta_v_m_s,
                    "route_circulation_period_s": route.route_circulation_period_s,
                    "normal_reference_circulation_period_s": (
                        route.normal_reference_circulation_period_s
                    ),
                    "active_node_passage_frequency_hz": (
                        route.active_node_passage_frequency_hz
                    ),
                    "normal_reference_passage_frequency_hz": (
                        route.normal_reference_passage_frequency_hz
                    ),
                    "intersects_earth": ballistic.intersects_earth,
                    "violates_minimum_safe_altitude": (
                        ballistic.violates_minimum_safe_altitude
                    ),
                }
            )
    return pd.DataFrame(rows)


def rotor_element_scaling_table(
    scenario: Scenario,
    element_masses_kg: Iterable[float] = ROTOR_ELEMENT_MASSES_KG,
) -> pd.DataFrame:
    reference = evaluate_scenario(_direct_scenario(scenario, 96))
    ballistic = reference.ballistic
    if ballistic is None:
        raise ValueError("rotor-element evidence requires L1 fidelity")
    rows: list[dict[str, float]] = []
    for element_mass_kg in element_masses_kg:
        rotor = evaluate_rotor_stream(
            total_rotor_mass_kg=scenario.rotor.total_moving_mass_kg,
            element_mass_kg=element_mass_kg,
            rotor_velocity_m_s=scenario.rotor.geocentric_velocity_m_s,
            node_count=96,
            node_stride=1,
            flight_time_s=ballistic.flight_time_s,
            active_deflection_angle_rad=ballistic.required_active_deflection_angle_rad,
            required_delta_v_m_s=ballistic.required_delta_v_m_s,
            allowed_lateral_acceleration_m_s2=(
                scenario.magnetic.max_lateral_acceleration_m_s2
            ),
        )
        rows.append(
            {
                "element_mass_g": element_mass_kg * 1000.0,
                "total_number_of_elements": rotor.number_of_elements,
                "kinetic_energy_per_element_j": rotor.kinetic_energy_per_element_j,
                "passage_frequency_per_node_hz": (
                    rotor.element_passage_frequency_per_node_hz
                ),
                "mean_element_spacing_m": rotor.mean_element_spacing_m,
                "simultaneous_elements_in_guide": (
                    rotor.elements_simultaneously_in_guide
                ),
                "force_per_individual_element_n": (
                    element_mass_kg
                    * scenario.magnetic.max_lateral_acceleration_m_s2
                ),
                "total_mean_node_force_n": (
                    rotor.average_node_reaction_force_mdot_n
                ),
            }
        )
    return pd.DataFrame(rows)


def _format_markdown_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        if abs(value) >= 1.0e6 or abs(value) < 1.0e-4:
            return f"{value:.8e}"
        return f"{value:.8f}".rstrip("0").rstrip(".")
    return str(value)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_format_markdown_value(value) for value in row) + " |")
    return "\n".join(lines)


def generate_hardening_evidence(
    scenario_path: str | Path, output_directory: str | Path
) -> Path:
    scenario = load_scenario(scenario_path)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)

    closure = force_closure_table(scenario)
    nodes = node_count_l1_table(scenario)
    bypasses = bypass_table(scenario)
    elements = rotor_element_scaling_table(scenario)
    tables = {
        "global-force-closure.csv": closure,
        "node-count-l1.csv": nodes,
        "failure-bypasses.csv": bypasses,
        "rotor-element-scaling.csv": elements,
    }
    for filename, frame in tables.items():
        frame.to_csv(output / filename, index=False)

    reference = evaluate_scenario(_direct_scenario(scenario, 96))
    manifest = asdict(reference.manifest)
    manifest["evidence_files"] = list(tables)
    manifest["evidence_kind"] = "OR-1.1 hardening tables"
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8"
    )

    report = f"""# OR-1.1 physics-kernel hardening evidence

Scenario: `{scenario.scenario_id}`

Configuration hash: `{reference.manifest.configuration_hash}`

Source commit at generation: `{reference.manifest.source_commit}`

Source worktree dirty at generation: `{reference.manifest.source_worktree_dirty}`

The ballistic primitive uses **node stride**: stride 1 targets the next node,
stride 2 bypasses one node, and stride 3 bypasses two nodes. Failure-route rows
contain one local bypass leg plus the reported count of unaffected stride-one
legs. They do not model the whole ring as a homogeneous stride-two stream.

## Global force closure

The summed finite-node value is `N × mean L1 node reaction force`. The
continuous value is `M × (v²/r − μ/r²)`. Signed and absolute relative errors
show the finite-node convergence.

{dataframe_to_markdown(closure)}

## L1 node-count design space

{dataframe_to_markdown(nodes)}

## Local failed-node bypasses

{dataframe_to_markdown(bypasses)}

## Rotor-element scaling at fixed total mass

{dataframe_to_markdown(elements)}

Reducing element mass reduces kinetic energy and instantaneous force per
element in direct proportion to mass. Element count, passage frequency, and
simultaneous guide occupancy rise inversely, leaving the total mean node force
unchanged for fixed total rotor mass and trajectory.
"""
    report_path = output / "OR-1.1-EVIDENCE.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path
